"""The individual install steps. Each is idempotent and honours dry-run."""
import json
import os
import shutil
import subprocess
import sys

from . import fetch, paths, pins
from .settings import apply_setting, remember_file

MARKER = ".dotstuff"
DESKLET_LAYOUT = [("mono-date@monotile", 40, 70), ("mono-clock@monotile", 196, 70),
                  ("mono-weather@monotile", 40, 222), ("mono-system@monotile", 196, 222),
                  ("mono-day@monotile", 40, 374)]
PROMPT_BEGIN = "# >>> DotStuff prompt >>>"
PROMPT_END = "# <<< DotStuff prompt <<<"


class Ctx:
    def __init__(self, state, backend, dry_run=False, log=print, shape="circle", reload=True, prompt=False):
        self.state, self.backend, self.dry_run, self.log = state, backend, dry_run, log
        self.shape, self.reload, self.prompt = shape, reload, prompt

    def own(self, path):
        if path not in self.state["owned"]:
            self.state["owned"].append(path)

    def owns(self, path):
        return path in self.state["owned"]


def _copy(src, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copyfile(src, dest + ".tmp")
    os.replace(dest + ".tmp", dest)


def _monotile(*args, check=True):
    env = dict(os.environ, PYTHONPATH=paths.MONOTILE)
    return subprocess.run([sys.executable, "-m", "monotile", *args], env=env, check=check)


# ---------------------------------------------------------------- steps

def _own_dir(c, path):
    """A folder used only by DotStuff: created if needed and deleted whole on purge."""
    if not os.path.isdir(path):
        if not c.dry_run:
            os.makedirs(path, exist_ok=True)
        c.own(path)


def _container(c, path):
    """A shared folder DotStuff had to create (e.g. ~/.local/share/icons/hicolor):
    purge removes it only if it is empty, so anything else put there survives."""
    if not os.path.isdir(path):
        if not c.dry_run:
            os.makedirs(path, exist_ok=True)
        dirs = c.state.setdefault("created_dirs", [])
        if path not in dirs:
            dirs.append(path)


def fonts(c):
    _own_dir(c, paths.fonts_dir())
    changed = False
    for name, sha in pins.FONTS.items():
        dest = os.path.join(paths.fonts_dir(), name)
        if os.path.isfile(dest) and fetch.sha256(dest) == sha:
            continue
        c.log(f"  font {name}")
        if not c.dry_run:
            _copy(fetch.get(pins.FONT_URLS[name], sha, name), dest)
            c.own(dest)
        changed = True
    jb = [os.path.join(paths.fonts_dir(), f) for f in pins.JETBRAINS_FILES]
    if not all(os.path.isfile(p) for p in jb):
        c.log("  font JetBrains Mono")
        if not c.dry_run:
            zipped = fetch.get(pins.JETBRAINS_URL, pins.JETBRAINS_SHA)
            for p in fetch.extract_zip_files(zipped, set(pins.JETBRAINS_FILES), paths.fonts_dir()):
                c.own(p)
        changed = True
    if changed and not c.dry_run and shutil.which("fc-cache"):
        subprocess.run(["fc-cache", "-f", paths.fonts_dir()], check=False)


def wallpaper(c):
    dest = paths.wallpaper_path()
    _own_dir(c, os.path.dirname(dest))
    if not (os.path.isfile(dest) and fetch.sha256(dest) == pins.WALLPAPER_SHA):
        c.log("  wallpaper NothingWall")
        if not c.dry_run:
            _copy(fetch.get(pins.WALLPAPER_URL, pins.WALLPAPER_SHA), dest)
            c.own(dest)
    apply_setting(c.state, c.backend, "org.cinnamon.desktop.background", "picture-uri",
                  "file://" + dest, c.dry_run, c.log)
    apply_setting(c.state, c.backend, "org.cinnamon.desktop.background", "picture-options",
                  "zoom", c.dry_run, c.log)


def _tree_digest(root):
    import hashlib
    h = hashlib.sha256()
    for d, dirs, files in sorted(os.walk(root)):
        dirs.sort()
        for f in sorted(files):
            if f == MARKER:
                continue
            p = os.path.join(d, f)
            h.update(os.path.relpath(p, root).encode())
            h.update(os.readlink(p).encode() if os.path.islink(p) else open(p, "rb").read())
    return h.hexdigest()


def theme(c):
    dest = os.path.join(paths.themes_dir(), "DotStuff")
    if os.path.exists(dest) and not os.path.exists(os.path.join(dest, MARKER)):
        c.log(f"  skip theme: {dest} exists and was not installed by DotStuff")
        return
    if not (os.path.isdir(dest) and _tree_digest(dest) == _tree_digest(paths.THEME_SRC)):
        c.log("  theme DotStuff (GTK 2/3/4, Cinnamon panel and menus, window borders)")
    else:
        dest = None
    if dest and not c.dry_run:
        tmp = dest + ".new"
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.copytree(paths.THEME_SRC, tmp, symlinks=True)
        open(os.path.join(tmp, MARKER), "w").close()
        shutil.rmtree(dest, ignore_errors=True)
        os.replace(tmp, dest)
        c.own(dest)
    for schema, key in (("org.cinnamon.desktop.interface", "gtk-theme"), ("org.gnome.desktop.interface", "gtk-theme"),
                        ("org.cinnamon.theme", "name"), ("org.cinnamon.desktop.wm.preferences", "theme")):
        apply_setting(c.state, c.backend, schema, key, "DotStuff", c.dry_run, c.log)
    apply_setting(c.state, c.backend, "org.gnome.desktop.interface", "color-scheme", "prefer-dark", c.dry_run, c.log)


def cursor(c):
    dest = os.path.join(paths.cursors_parent(), pins.CURSOR_DIR)
    if os.path.isdir(dest) and not c.owns(dest):
        c.log("  cursor: AOSP cursors already installed, using them")
    elif not os.path.isdir(dest):
        c.log("  cursor AOSP cursors 1.3.1")
        if not c.dry_run:
            os.makedirs(paths.cursors_parent(), exist_ok=True)
            fetch.extract_tar(fetch.get(pins.CURSOR_URL, pins.CURSOR_SHA), paths.cursors_parent(), pins.CURSOR_DIR)
            c.own(dest)
    for schema in ("org.cinnamon.desktop.interface", "org.gnome.desktop.interface"):
        apply_setting(c.state, c.backend, schema, "cursor-theme", pins.CURSOR_DIR, c.dry_run, c.log)
        apply_setting(c.state, c.backend, schema, "cursor-size", 18, c.dry_run, c.log)


def fontsettings(c):
    b = c.backend
    apply_setting(c.state, b, "org.cinnamon.desktop.wm.preferences", "titlebar-font", "Ndot57Caps 12", c.dry_run, c.log)
    apply_setting(c.state, b, "org.nemo.desktop", "font", "Ndot55Caps 10", c.dry_run, c.log)
    apply_setting(c.state, b, "org.cinnamon.settings-daemon.plugins.xsettings", "antialiasing", "rgba", c.dry_run, c.log)
    apply_setting(c.state, b, "org.cinnamon.settings-daemon.plugins.xsettings", "hinting", "slight", c.dry_run, c.log)
    # lock screen (cinnamon-screensaver); its colours and shapes come from the DotStuff theme
    apply_setting(c.state, b, "org.cinnamon.desktop.screensaver", "font-time", "Ndot 57 112", c.dry_run, c.log)
    apply_setting(c.state, b, "org.cinnamon.desktop.screensaver", "font-date", "Ndot57Caps 22", c.dry_run, c.log)
    apply_setting(c.state, b, "org.cinnamon.desktop.screensaver", "font-message", "NType 82 14", c.dry_run, c.log)


def icons(c):
    from . import paths as P
    mcfg = os.path.join(P.config_home(), "monotile")
    _container(c, mcfg)                    # monotile's settings folder, if DotStuff creates it
    c.log(f"  icons Monotile-Circle and Monotile-Squircle (applying {c.shape})")
    _monotile("generate", "--shape", c.shape, *(["--dry-run"] if c.dry_run else []))
    name = "Monotile-" + c.shape.capitalize()
    for schema in ("org.cinnamon.desktop.interface", "org.gnome.desktop.interface"):
        apply_setting(c.state, c.backend, schema, "icon-theme", name, c.dry_run, c.log)
    if c.dry_run:
        return
    env = dict(os.environ, PYTHONPATH=paths.MONOTILE)
    status = subprocess.run([sys.executable, "-m", "monotile", "watch", "status"], env=env,
                            capture_output=True, text=True).stdout.strip()
    if status == "active":
        return
    r = subprocess.run([sys.executable, "-m", "monotile", "watch", "enable"], env=env,
                       capture_output=True, text=True)
    if r.returncode == 0:
        c.state["watcher"] = True
        c.log("  icon watcher on: new apps get monochrome icons automatically")
    else:
        c.log("  icon watcher not enabled (no systemd user session); run `vendor/monotile/run-monotile watch enable` later")


def menu(c):
    dest = paths.menu_icon_path()
    for d in (os.path.dirname(os.path.dirname(os.path.dirname(dest))), os.path.dirname(os.path.dirname(dest)), os.path.dirname(dest)):
        _container(c, d)
    if not os.path.exists(dest):
        c.log("  menu button icon dotstuff-menu")
        if not c.dry_run:
            _copy(paths.MENU_ICON_SRC, dest)
            c.own(dest)
    configs = paths.menu_applet_configs()
    if not configs:
        c.log("  menu applet not configured yet; open its settings once, then re-run to set the icon")
    for cfg in configs:
        with open(cfg, encoding="utf-8") as f:
            data = json.load(f)
        if data.get("menu-custom", {}).get("value"):
            c.log(f"  menu applet {os.path.basename(cfg)} already uses a custom icon; left as it is")
            continue
        c.log(f"  menu applet {os.path.basename(cfg)}: icon dotstuff-menu, no label")
        if not c.dry_run:
            remember_file(c.state, cfg)
            data["menu-custom"]["value"] = True
            data["menu-icon"]["value"] = "dotstuff-menu"
            data["menu-label"]["value"] = ""
            with open(cfg + ".tmp", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            os.replace(cfg + ".tmp", cfg)


def desklets(c):
    root = os.path.join(paths.data_home(), "cinnamon", "desklets")
    new = [u for u, _, _ in DESKLET_LAYOUT if not os.path.isdir(os.path.join(root, u))]
    if new:
        c.log("  desklets Mono Clock, Date, Weather, System, Day")
    if c.dry_run:
        return
    subprocess.run(["bash", os.path.join(paths.MONOTILE, "desklets", "install.sh")], check=True,
                   stdout=subprocess.DEVNULL)
    for u in new:
        c.own(os.path.join(root, u))
    b = c.backend
    current = list(b.current("org.cinnamon", "enabled-desklets"))
    present = {d.split(":")[0] for d in current}
    next_id = b.current("org.cinnamon", "next-desklet-id")
    for uuid, x, y in DESKLET_LAYOUT:
        if uuid not in present:
            entry = f"{uuid}:{next_id}:{x}:{y}"
            current.append(entry)
            c.state["desklets"].append(entry)
            next_id += 1
    b.set("org.cinnamon", "enabled-desklets", current)
    b.set("org.cinnamon", "next-desklet-id", next_id)


def prompt(c):
    rc = paths.bashrc()
    text = open(rc, encoding="utf-8").read() if os.path.exists(rc) else ""
    if PROMPT_BEGIN in text:
        return
    if "38;2;215;25;33" in text:
        c.log("  prompt: ~/.bashrc already has a red/white prompt; left as it is")
        return
    c.log("  prompt: white user@host, red path (marked block in ~/.bashrc)")
    if not c.dry_run:
        remember_file(c.state, rc)
        block = (f"\n{PROMPT_BEGIN}\n"
                 "if [ -n \"$PS1\" ]; then\n"
                 "    PS1='\\[\\033[01;37m\\]\\u@\\h\\[\\033[00m\\]:\\[\\033[01;38;2;215;25;33m\\]\\w\\[\\033[00m\\]\\$ '\n"
                 f"fi\n{PROMPT_END}\n")
        with open(rc, "a", encoding="utf-8") as f:
            f.write(block)


def reload_shell(c):
    if c.dry_run or not c.reload or "cinnamon" not in os.environ.get("XDG_CURRENT_DESKTOP", "").lower():
        return
    c.log("  restarting Cinnamon so it picks up the new fonts and theme (windows stay open)")
    subprocess.run(["dbus-send", "--session", "--dest=org.Cinnamon", "--type=method_call",
                    "/org/Cinnamon", "org.Cinnamon.RestartCinnamon", "boolean:false"], check=False)


ALL = [("fonts", fonts), ("wallpaper", wallpaper), ("theme", theme), ("cursor", cursor),
       ("fontsettings", fontsettings), ("icons", icons), ("menu", menu), ("desklets", desklets)]
OPTIONAL = [("prompt", prompt)]
STEP_NAMES = [n for n, _ in ALL + OPTIONAL]
