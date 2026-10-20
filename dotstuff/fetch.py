"""Downloads with SHA-256 verification, a local cache, and safe archive extraction."""
import hashlib
import os
import shutil
import tarfile
import tempfile
import urllib.request
import zipfile

from . import paths


class ChecksumError(RuntimeError):
    pass


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def get(url, sha, name=None):
    """Return a local path to the verified file, downloading it into the cache if needed.

    $DOTSTUFF_CACHE may point at a folder of pre-downloaded files (offline installs)."""
    name = name or url.rsplit("/", 1)[-1]
    for folder in filter(None, [os.environ.get("DOTSTUFF_CACHE"), paths.cache_dir()]):
        p = os.path.join(folder, name)
        if os.path.isfile(p) and sha256(p) == sha:
            return p
    os.makedirs(paths.cache_dir(), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=paths.cache_dir(), prefix=".dl-")
    os.close(fd)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "DotStuff-installer"})
        with urllib.request.urlopen(req, timeout=60) as r, open(tmp, "wb") as f:
            shutil.copyfileobj(r, f)
        got = sha256(tmp)
        if got != sha:
            raise ChecksumError(f"{name}: checksum mismatch (expected {sha[:12]}…, got {got[:12]}…)")
        dest = os.path.join(paths.cache_dir(), name)
        os.replace(tmp, dest)
        return dest
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _inside(base, target):
    base = os.path.realpath(base)
    return os.path.realpath(target) == base or os.path.realpath(target).startswith(base + os.sep)


def extract_tar(archive, dest_parent, top):
    """Extract only `top/` from a tar archive, refusing absolute paths, `..`, devices,
    and links that point outside `top/`."""
    with tarfile.open(archive) as t:
        members = []
        for m in t.getmembers():
            parts = m.name.split("/")
            if m.name.startswith("/") or ".." in parts or parts[0] != top:
                raise RuntimeError(f"unsafe or unexpected path in archive: {m.name}")
            if m.isdev() or m.isfifo():
                raise RuntimeError(f"device file in archive: {m.name}")
            if m.issym() or m.islnk():
                target = os.path.normpath(os.path.join(os.path.dirname(m.name), m.linkname))
                if m.linkname.startswith("/") or not (target == top or target.startswith(top + "/")):
                    raise RuntimeError(f"link escapes the archive: {m.name} -> {m.linkname}")
            members.append(m)
        staging = tempfile.mkdtemp(dir=dest_parent, prefix=".extract-")
        try:
            t.extractall(staging, members=members, filter="tar")
            final = os.path.join(dest_parent, top)
            os.replace(os.path.join(staging, top), final)
            return final
        finally:
            shutil.rmtree(staging, ignore_errors=True)


def extract_zip_files(archive, wanted, dest):
    """Copy only the named files (matched by base name) out of a zip."""
    os.makedirs(dest, exist_ok=True)
    out = []
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            base = os.path.basename(info.filename)
            if base in wanted and not info.is_dir():
                p = os.path.join(dest, base)
                with z.open(info) as src, open(p + ".tmp", "wb") as dst:
                    shutil.copyfileobj(src, dst)
                os.replace(p + ".tmp", p)
                out.append(p)
    return out
