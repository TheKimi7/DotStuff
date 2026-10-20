"""DotStuff command line: install, restore, status."""
import argparse
import os
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


def cmd_install(a, backend):
    if "cinnamon" not in os.environ.get("XDG_CURRENT_DESKTOP", "").lower() and not a.force:
        raise SystemExit("DotStuff targets Cinnamon; this session is not Cinnamon (use --force to continue anyway)")
    only, skip = _parts(a.only), _parts(a.skip)
    chosen = [(n, f) for n, f in steps.ALL if (not only or n in only) and n not in skip]
    if a.prompt or "prompt" in only:
        chosen += steps.OPTIONAL
    state = load_state()
    c = steps.Ctx(state, backend, dry_run=a.dry_run, shape=a.shape, reload=not a.no_reload, prompt=a.prompt)
    print("DotStuff " + ("dry run: nothing will be changed" if a.dry_run else "install"))
    try:
        for name, fn in chosen:
            print(f"[{name}]")
            fn(c)
            if not a.dry_run:
                save_state(state)          # progress is saved, so restore works after a failure too
    finally:
        if not a.dry_run:
            backend.sync()
            save_state(state)
    if not a.dry_run:
        steps.reload_shell(c)
        print("Done. Undo everything with: ./install.sh --restore")


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
    i.add_argument("--only", help="comma-separated parts: " + ",".join(steps.STEP_NAMES))
    i.add_argument("--skip", help="comma-separated parts to leave out")
    i.add_argument("--prompt", action="store_true", help="also colour the bash prompt (white user, red path)")
    i.add_argument("--dry-run", action="store_true", help="show what would change, change nothing")
    i.add_argument("--no-reload", action="store_true", help="do not restart Cinnamon at the end")
    i.add_argument("--force", action="store_true", help="run even if the session is not Cinnamon")
    i.set_defaults(func=cmd_install)

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
