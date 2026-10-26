"""DotStuff command line: install, mode, restore, status."""
import argparse
import os
import re
import subprocess
import sys

from . import __version__, steps
from .restore import restore
from .settings import GioSettings, load_state, save_state


def _parts(value):
    parts = [p.strip() for p in (value or "").split(",") if p.strip()]
    bad = [p for p in parts if p not in steps.STEP_NAMES]
    if bad:
        raise SystemExit(f"unknown part(s): {', '.join(bad)} (choose from {', '.join(steps.STEP_NAMES)})")
    return parts


TESTED_CINNAMON = ("6.4",)


def cinnamon_version():
    try:
        out = subprocess.run(["cinnamon", "--version"], capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    m = re.search(r"(\d+)\.(\d+)", out)
    return f"{m.group(1)}.{m.group(2)}" if m else None


def cmd_install(a, backend):
    if "cinnamon" not in os.environ.get("XDG_CURRENT_DESKTOP", "").lower() and not a.force:
        raise SystemExit("DotStuff targets Cinnamon; this session is not Cinnamon (use --force to continue anyway)")
    version = cinnamon_version()
    if version and version not in TESTED_CINNAMON:
        print(f"Note: DotStuff was tested on Cinnamon {', '.join(TESTED_CINNAMON)}; this is Cinnamon {version}. "
              "It should work; if something looks wrong, ./install.sh --restore undoes everything.")
    only, skip = _parts(a.only), _parts(a.skip)
    chosen = [(n, f) for n, f in steps.ALL if (not only or n in only) and n not in skip]
    if a.prompt or "prompt" in only:
        chosen += steps.OPTIONAL
    state = load_state()
    c = steps.Ctx(state, backend, dry_run=a.dry_run, shape=a.shape, reload=not a.no_reload, prompt=a.prompt,
                  mode=a.mode)
    print("DotStuff " + ("dry run: nothing will be changed" if a.dry_run else "install"))
    try:
        for name, fn in chosen:
            print(f"[{name}]")
            fn(c)
            if not a.dry_run:
                save_state(state)          # progress is saved, so restore works after a failure too
    except (KeyboardInterrupt, subprocess.CalledProcessError) as e:
        stopped = isinstance(e, KeyboardInterrupt) or e.returncode == 130
        print("\nStopped." if stopped else f"\n[{name}] failed.",
              "Everything done so far is kept: run ./install.sh again to continue "
              "(finished parts are skipped), or ./install.sh --restore to undo.")
        raise SystemExit(130 if stopped else 1)
    finally:
        if not a.dry_run:
            backend.sync()
            save_state(state)
    if not a.dry_run:
        steps.reload_shell(c)
        print("Done. Undo everything with: ./install.sh --restore")


def cmd_mode(a, backend):
    state = load_state()
    c = steps.Ctx(state, backend, dry_run=a.dry_run, mode=a.mode)
    try:
        steps.set_mode(c)
    finally:
        if not a.dry_run:
            backend.sync()
            save_state(state)
    print(f"{a.mode.capitalize()} mode." + (" (dry run)" if a.dry_run else ""))


def cmd_restore(a, backend):
    restore(backend, purge=a.purge)
    print("Restored." + ("" if a.purge else " Installed files were kept; add --purge to delete them too."))


def cmd_status(a, backend):
    s = load_state()
    print(f"settings changed by DotStuff: {len(s['settings'])}")
    print(f"files edited (with backups):  {len(s['files'])}")
    print(f"files/folders installed:      {len(s['owned'])}")
    print(f"desklets placed:              {len(s['desklets'])}")
    print(f"icon watcher enabled by it:   {bool(s.get('watcher'))}")


def main(argv=None):
    p = argparse.ArgumentParser(prog="dotstuff", description="Nothing-inspired desktop setup for Cinnamon.")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)

    i = sub.add_parser("install", help="install and configure everything (default)")
    i.add_argument("--shape", choices=("circle", "squircle"), default="circle", help="app icon tile shape")
    i.add_argument("--mode", choices=("dark", "light"), default="dark", help="start in dark or light mode")
    i.add_argument("--only", help="comma-separated parts: " + ",".join(steps.STEP_NAMES))
    i.add_argument("--skip", help="comma-separated parts to leave out")
    i.add_argument("--prompt", action="store_true", help="also colour the bash prompt (white user, red path)")
    i.add_argument("--dry-run", action="store_true", help="show what would change, change nothing")
    i.add_argument("--no-reload", action="store_true", help="do not restart Cinnamon at the end")
    i.add_argument("--force", action="store_true", help="run even if the session is not Cinnamon")
    i.set_defaults(func=cmd_install)

    m = sub.add_parser("mode", help="switch between dark and light (theme, icons, desklets)")
    m.add_argument("mode", choices=("dark", "light"))
    m.add_argument("--dry-run", action="store_true", help="show what would change, change nothing")
    m.set_defaults(func=cmd_mode)

    r = sub.add_parser("restore", help="put every setting and edited file back the way it was")
    r.add_argument("--purge", action="store_true", help="also delete everything DotStuff installed")
    r.set_defaults(func=cmd_restore)
    sub.add_parser("status", help="show what DotStuff has changed").set_defaults(func=cmd_status)

    a = p.parse_args(argv)
    sys.stdout.reconfigure(line_buffering=True)     # keep our lines in order with monotile's output
    a.func(a, GioSettings())
    return 0


if __name__ == "__main__":
    sys.exit(main())
