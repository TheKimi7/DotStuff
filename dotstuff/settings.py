"""Desktop settings through GSettings, plus the one-time pristine backup.

Values are read and written with Gio.Settings, so DotStuff can tell a value the user
set from a default (restore then resets instead of pinning the old default).
"""
import json
import os
import shutil

from . import paths

UNSET = None     # recorded for keys that were at their default


class GioSettings:
    def __init__(self):
        import gi
        gi.require_version("Gio", "2.0")
        from gi.repository import Gio, GLib
        self.Gio, self.GLib = Gio, GLib
        self.source = Gio.SettingsSchemaSource.get_default()
        self._cache = {}

    def _s(self, schema):
        if schema not in self._cache:
            self._cache[schema] = self.Gio.Settings.new(schema)
        return self._cache[schema]

    def has(self, schema, key):
        sc = self.source.lookup(schema, True)
        return bool(sc and sc.has_key(key))

    def get(self, schema, key):
        """The user's value as a Python object, or UNSET if the key is at its default."""
        v = self._s(schema).get_user_value(key)
        return UNSET if v is None else v.unpack()

    def current(self, schema, key):
        return self._s(schema).get_value(key).unpack()

    def set(self, schema, key, value):
        s = self._s(schema)
        s.set_value(key, self.GLib.Variant(s.get_value(key).get_type_string(), value))

    def reset(self, schema, key):
        self._s(schema).reset(key)

    def sync(self):
        self.Gio.Settings.sync()


# ---------------------------------------------------------------- state file

def state_path():
    return os.path.join(paths.state_dir(), "state.json")


def load_state():
    try:
        with open(state_path(), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"settings": {}, "files": {}, "owned": [], "desklets": [], "watcher": False}


def save_state(state):
    os.makedirs(paths.state_dir(), exist_ok=True)
    tmp = state_path() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)
    os.replace(tmp, state_path())


def remember_setting(state, backend, schema, key):
    """Record the value before DotStuff first changes it (never overwritten later)."""
    k = f"{schema} {key}"
    if k not in state["settings"]:
        state["settings"][k] = backend.get(schema, key)


def remember_file(state, path):
    """Keep a copy of a file before DotStuff first edits it (None if it did not exist)."""
    if path in state["files"]:
        return
    if os.path.exists(path):
        os.makedirs(os.path.join(paths.state_dir(), "files"), exist_ok=True)
        copy = os.path.join(paths.state_dir(), "files", f"{len(state['files']):03d}-{os.path.basename(path)}")
        shutil.copy2(path, copy)
        state["files"][path] = copy
    else:
        state["files"][path] = None


def apply_setting(state, backend, schema, key, value, dry_run, log):
    if not backend.has(schema, key):
        log(f"  skip {schema} {key} (not available on this system)")
        return
    if backend.current(schema, key) == value:
        return
    log(f"  set {schema} {key} = {value!r}")
    if not dry_run:
        remember_setting(state, backend, schema, key)
        backend.set(schema, key, value)
