"""monotile, the icon generator DotStuff uses (github.com/TheKimi7/monotile).

Downloaded at install time at the commit pinned in pins.py, checked against its SHA-256 and
kept in ~/.local/share/dotstuff/monotile, so the icon watcher keeps working after the
DotStuff folder is deleted. $DOTSTUFF_MONOTILE may point at a local checkout instead.
"""
import os
import shutil

from . import fetch, paths, pins

STAMP = ".dotstuff-commit"


def location():
    return os.environ.get("DOTSTUFF_MONOTILE") or os.path.join(paths.state_dir(), "monotile")


def installed():
    return os.path.isfile(os.path.join(location(), "monotile", "__init__.py"))


def ensure(c):
    """Make the pinned monotile available. Returns its folder, or None in a dry run when it
    would have to be downloaded first."""
    if os.environ.get("DOTSTUFF_MONOTILE"):
        return location()
    dest = location()
    stamp = os.path.join(dest, STAMP)
    if os.path.exists(stamp) and open(stamp, encoding="utf-8").read().strip() == pins.MONOTILE_COMMIT:
        return dest
    c.log(f"  download monotile {pins.MONOTILE_COMMIT[:7]} from github.com/TheKimi7/monotile (about 9 MB)")
    if c.dry_run:
        return dest if installed() else None
    archive = fetch.get(pins.MONOTILE_URL, pins.MONOTILE_SHA, name=f"monotile-{pins.MONOTILE_COMMIT}.tar.gz")
    parent = os.path.dirname(dest)
    os.makedirs(parent, exist_ok=True)
    top = f"monotile-{pins.MONOTILE_COMMIT}"
    shutil.rmtree(os.path.join(parent, top), ignore_errors=True)
    new = fetch.extract_tar(archive, parent, top)
    with open(os.path.join(new, STAMP), "w", encoding="utf-8") as f:
        f.write(pins.MONOTILE_COMMIT + "\n")
    shutil.rmtree(dest, ignore_errors=True)
    os.replace(new, dest)
    c.own(dest)
    c.log(f"  installed monotile in {dest.replace(paths.home(), '~', 1)}")
    return dest
