"""Undo DotStuff: settings back to what they were, edited files restored, only
DotStuff's own desklets removed; with purge, also delete the files DotStuff created."""
import os
import shutil
import subprocess
import sys

from . import monotile as mt
from . import paths
from .settings import UNSET, load_state, state_path
from .steps import PROMPT_BEGIN, PROMPT_END


def _strip_prompt_block(path):
    if not os.path.exists(path):
        return False
    text = open(path, encoding="utf-8").read()
    if PROMPT_BEGIN not in text:
        return False
    start = text.index(PROMPT_BEGIN)
    end = text.index(PROMPT_END, start) + len(PROMPT_END)
    new = text[:start].rstrip("\n") + "\n" + text[end:].lstrip("\n")
    with open(path + ".tmp", "w", encoding="utf-8") as f:
        f.write(new)
    os.replace(path + ".tmp", path)
    return True


def restore(backend, purge=False, log=print):
    state = load_state()
    if not (state["settings"] or state["files"] or state["owned"] or state["desklets"] or state.get("created_dirs")
            or state.get("links")):
        log("nothing to restore (DotStuff has not changed anything)")
        return state

    for sk, value in sorted(state["settings"].items()):
        schema, key = sk.split(" ", 1)
        if not backend.has(schema, key):
            continue
        if value is UNSET:
            backend.reset(schema, key)
            log(f"  reset {schema} {key}")
        else:
            backend.set(schema, key, value)
            log(f"  restored {schema} {key} = {value!r}")

    for path, copy in state["files"].items():
        if path == paths.bashrc():
            if _strip_prompt_block(path):
                log("  removed the DotStuff prompt block from ~/.bashrc")
        elif copy and os.path.exists(copy):
            shutil.copyfile(copy, path + ".tmp")
            os.replace(path + ".tmp", path)
            log(f"  restored {path}")

    for link in state.get("links", []):
        if os.path.islink(link):
            os.unlink(link)
    if state.get("links"):
        log(f"  removed {len(state['links'])} GTK4 theme links from ~/.config/gtk-4.0")
    for d in sorted(state.get("created_dirs", []), key=len, reverse=True):
        try:
            os.rmdir(d)                                  # only if empty
        except OSError:
            pass

    if state["desklets"] and backend.has("org.cinnamon", "enabled-desklets"):
        current = list(backend.current("org.cinnamon", "enabled-desklets"))
        keep = [d for d in current if d not in state["desklets"]]
        if keep != current:
            if keep:
                backend.set("org.cinnamon", "enabled-desklets", keep)
            else:                                    # nothing else there: back to "never set"
                backend.reset("org.cinnamon", "enabled-desklets")
                backend.reset("org.cinnamon", "next-desklet-id")
            log(f"  removed {len(current) - len(keep)} DotStuff desklets from the desktop")

    env = dict(os.environ, PYTHONPATH=mt.location())
    if not mt.installed():
        log("  monotile is no longer installed; its icon themes and watcher were left as they are")
    elif state.get("watcher"):
        subprocess.run([sys.executable, "-m", "monotile", "watch", "disable"], env=env, check=False)
        log("  stopped the icon watcher")

    if purge and mt.installed():
        subprocess.run([sys.executable, "-c",
                        "from monotile import config, theme; theme.remove_all(config.load())"],
                       env=env, check=False)
    if purge:
        for p in sorted(state["owned"], key=len, reverse=True):     # files before their folders
            if os.path.isdir(p) and not os.path.islink(p):
                shutil.rmtree(p, ignore_errors=True)
            elif os.path.lexists(p):
                os.unlink(p)
        for d in sorted(state.get("created_dirs", []), key=len, reverse=True):
            try:
                os.rmdir(d)                              # only if empty
            except OSError:
                pass
        log(f"  deleted {len(state['owned'])} files/folders DotStuff installed and the Monotile icon themes")

    backend.sync()
    shutil.rmtree(os.path.join(paths.state_dir(), "files"), ignore_errors=True)
    if os.path.exists(state_path()):
        os.unlink(state_path())
    return state
