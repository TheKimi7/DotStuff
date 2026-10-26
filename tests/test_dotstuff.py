"""DotStuff tests: isolated temp HOME/XDG folders and an in-memory settings backend.
They never touch the real desktop and never use the network."""
import hashlib
import io
import json
import os
import shutil
import sys
import tarfile
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotstuff import fetch, paths, pins, steps  # noqa: E402
from dotstuff.restore import restore  # noqa: E402
from dotstuff.settings import UNSET, load_state, save_state  # noqa: E402

VARS = ("HOME", "XDG_DATA_HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "DOTSTUFF_CACHE")


class FakeSettings:
    def __init__(self, user=None, defaults=None):
        self.defaults = defaults or {
            ("org.cinnamon.desktop.interface", "gtk-theme"): "Mint-Y",
            ("org.cinnamon.theme", "name"): "Mint-Y-Dark",
            ("org.gnome.desktop.interface", "color-scheme"): "default",
            ("org.cinnamon.desktop.interface", "icon-theme"): "Mint-Y",
            ("org.cinnamon.desktop.interface", "cursor-size"): 24,
            ("org.cinnamon", "enabled-desklets"): [],
            ("org.cinnamon", "next-desklet-id"): 0,
        }
        self.user = dict(user or {})

    def has(self, schema, key):
        return (schema, key) in self.defaults

    def get(self, schema, key):
        return self.user.get((schema, key), UNSET)

    def current(self, schema, key):
        return self.user.get((schema, key), self.defaults[(schema, key)])

    def set(self, schema, key, value):
        self.user[(schema, key)] = value

    def reset(self, schema, key):
        self.user.pop((schema, key), None)

    def sync(self):
        pass


class Isolated(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="dotstuff-test-")
        self.saved = {k: os.environ.get(k) for k in VARS}
        home = os.path.join(self.root, "home")
        os.environ.update(HOME=home, XDG_DATA_HOME=os.path.join(home, ".local/share"),
                          XDG_CONFIG_HOME=os.path.join(home, ".config"),
                          XDG_CACHE_HOME=os.path.join(home, ".cache"))
        os.environ.pop("DOTSTUFF_CACHE", None)
        os.makedirs(home)
        self.logs = []

    def tearDown(self):
        for k, v in self.saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(self.root, ignore_errors=True)

    def ctx(self, backend, **kw):
        return steps.Ctx(load_state(), backend, log=self.logs.append, **kw)


class Fetch(Isolated):
    def test_cache_hit_and_checksum(self):
        cache = os.path.join(self.root, "offline")
        os.makedirs(cache)
        with open(os.path.join(cache, "a.bin"), "wb") as f:
            f.write(b"hello")
        os.environ["DOTSTUFF_CACHE"] = cache
        good = hashlib.sha256(b"hello").hexdigest()
        self.assertTrue(fetch.get("https://invalid.example/a.bin", good).endswith("a.bin"))

    def test_mismatch_is_rejected(self):
        cache = os.path.join(self.root, "offline")
        os.makedirs(cache)
        with open(os.path.join(cache, "a.bin"), "wb") as f:
            f.write(b"tampered")
        os.environ["DOTSTUFF_CACHE"] = cache
        with self.assertRaises(Exception):   # cache miss -> tries the (invalid) network URL and fails
            fetch.get("https://invalid.example/a.bin", hashlib.sha256(b"hello").hexdigest())

    def _tar(self, members):
        p = os.path.join(self.root, "t.tar")
        with tarfile.open(p, "w") as t:
            for name, kind, target in members:
                ti = tarfile.TarInfo(name)
                if kind == "file":
                    ti.size = 2
                    t.addfile(ti, io.BytesIO(b"ok"))
                else:
                    ti.type, ti.linkname = tarfile.SYMTYPE, target
                    t.addfile(ti)
        return p

    def test_extract_safe_archive(self):
        p = self._tar([("top/a", "file", None), ("top/b", "link", "a")])
        out = fetch.extract_tar(p, self.root, "top")
        self.assertTrue(os.path.islink(os.path.join(out, "b")))

    def test_extract_rejects_escapes(self):
        for members in ([("top/../evil", "file", None)], [("other/a", "file", None)],
                        [("top/x", "link", "../../etc/passwd")], [("top/y", "link", "/etc/passwd")]):
            with self.assertRaises(RuntimeError, msg=members):
                fetch.extract_tar(self._tar(members), self.root, "top")


class SettingsAndRestore(Isolated):
    def test_restore_resets_defaults_and_keeps_user_values(self):
        b = FakeSettings(user={("org.cinnamon.desktop.interface", "cursor-size"): 32})
        c = self.ctx(b)
        from dotstuff.settings import apply_setting
        apply_setting(c.state, b, "org.cinnamon.desktop.interface", "gtk-theme", "DotStuff", False, self.logs.append)
        apply_setting(c.state, b, "org.cinnamon.desktop.interface", "cursor-size", 18, False, self.logs.append)
        apply_setting(c.state, b, "org.cinnamon.desktop.interface", "cursor-size", 20, False, self.logs.append)
        save_state(c.state)
        restore(b, log=self.logs.append)
        self.assertEqual(b.get("org.cinnamon.desktop.interface", "gtk-theme"), UNSET)    # was default
        self.assertEqual(b.get("org.cinnamon.desktop.interface", "cursor-size"), 32)     # first value kept

    def test_unchanged_value_is_not_recorded(self):
        b = FakeSettings(user={("org.cinnamon.desktop.interface", "gtk-theme"): "DotStuff"})
        c = self.ctx(b)
        from dotstuff.settings import apply_setting
        apply_setting(c.state, b, "org.cinnamon.desktop.interface", "gtk-theme", "DotStuff", False, self.logs.append)
        self.assertEqual(c.state["settings"], {})

    def test_dry_run_changes_nothing(self):
        b = FakeSettings()
        c = self.ctx(b, dry_run=True)
        steps.theme(c)
        steps.menu(c)
        self.assertEqual(b.user, {})
        self.assertFalse(os.path.exists(os.path.join(paths.themes_dir(), "DotStuff-Dark")))
        self.assertFalse(os.path.exists(paths.state_dir()))


class Steps(Isolated):
    def menu_config(self, custom):
        d = os.path.join(os.environ["XDG_CONFIG_HOME"], "cinnamon/spices/menu@cinnamon.org")
        os.makedirs(d)
        p = os.path.join(d, "0.json")
        with open(p, "w") as f:
            json.dump({"menu-custom": {"value": custom}, "menu-icon": {"value": "my-icon"},
                       "menu-label": {"value": "Menu"}}, f)
        return p

    def test_menu_icon_set_and_restored(self):
        p = self.menu_config(False)
        b = FakeSettings()
        c = self.ctx(b)
        steps.menu(c)
        save_state(c.state)
        with open(p) as f:
            data = json.load(f)
        self.assertEqual((data["menu-custom"]["value"], data["menu-icon"]["value"], data["menu-label"]["value"]),
                         (True, "dotstuff-menu", ""))
        self.assertTrue(os.path.exists(paths.menu_icon_path()))
        restore(b, purge=True, log=self.logs.append)
        with open(p) as f:
            self.assertEqual(json.load(f)["menu-icon"]["value"], "my-icon")
        self.assertFalse(os.path.exists(paths.menu_icon_path()))

    def test_existing_custom_menu_icon_is_left_alone(self):
        p = self.menu_config(True)
        steps.menu(self.ctx(FakeSettings()))
        with open(p) as f:
            self.assertEqual(json.load(f)["menu-icon"]["value"], "my-icon")

    def test_theme_installed_marked_and_idempotent(self):
        b = FakeSettings()
        c = self.ctx(b)
        steps.theme(c)
        for name in ("DotStuff-Dark", "DotStuff-Light"):
            self.assertTrue(os.path.exists(os.path.join(paths.themes_dir(), name, steps.MARKER)))
        dest = os.path.join(paths.themes_dir(), "DotStuff-Dark")
        self.assertEqual(b.current("org.cinnamon.desktop.interface", "gtk-theme"), "DotStuff-Dark")
        self.assertEqual(b.current("org.gnome.desktop.interface", "color-scheme"), "prefer-dark")
        before = os.stat(os.path.join(dest, "index.theme")).st_mtime_ns
        self.logs.clear()
        steps.theme(c)
        self.assertEqual(os.stat(os.path.join(dest, "index.theme")).st_mtime_ns, before)
        self.assertFalse([m for m in self.logs if "theme DotStuff" in m])        # not reinstalled

    def test_foreign_theme_folder_is_not_touched(self):
        dest = os.path.join(paths.themes_dir(), "DotStuff-Dark")
        os.makedirs(dest)
        open(os.path.join(dest, "mine.css"), "w").close()
        b = FakeSettings()
        steps.theme(self.ctx(b))
        self.assertEqual(os.listdir(dest), ["mine.css"])
        self.assertEqual(b.current("org.cinnamon.desktop.interface", "gtk-theme"), "Mint-Y")

    def test_old_single_theme_is_replaced(self):
        old = os.path.join(paths.themes_dir(), "DotStuff")
        os.makedirs(old)
        open(os.path.join(old, steps.MARKER), "w").close()
        c = self.ctx(FakeSettings())
        c.own(old)
        steps.theme(c)
        self.assertFalse(os.path.exists(old))
        self.assertNotIn(old, c.state["owned"])

    def test_mode_switches_theme_icons_and_back(self):
        b = FakeSettings(user={("org.cinnamon.desktop.interface", "icon-theme"): "Monotile-Squircle"})
        c = self.ctx(b)
        steps.theme(c)
        os.makedirs(os.path.join(paths.icons_dir(), "Monotile-Light-Squircle"))
        os.makedirs(os.path.join(paths.icons_dir(), "Monotile-Squircle"))
        c.mode = "light"
        steps.set_mode(c)
        self.assertEqual(b.current("org.cinnamon.theme", "name"), "DotStuff-Light")
        self.assertEqual(b.current("org.gnome.desktop.interface", "color-scheme"), "prefer-light")
        self.assertEqual(b.current("org.cinnamon.desktop.interface", "icon-theme"), "Monotile-Light-Squircle")
        c.mode = "dark"
        steps.set_mode(c)
        self.assertEqual(b.current("org.cinnamon.theme", "name"), "DotStuff-Dark")
        self.assertEqual(b.current("org.cinnamon.desktop.interface", "icon-theme"), "Monotile-Squircle")
        save_state(c.state)
        restore(b, log=self.logs.append)                  # originals survive any number of switches
        self.assertEqual(b.current("org.cinnamon.desktop.interface", "icon-theme"), "Monotile-Squircle")
        self.assertEqual(b.current("org.cinnamon.theme", "name"), "Mint-Y-Dark")

    def test_mode_needs_installed_theme(self):
        c = self.ctx(FakeSettings(), mode="light")
        with self.assertRaises(SystemExit):
            steps.set_mode(c)

    def test_prompt_block_added_once_and_removed(self):
        rc = paths.bashrc()
        with open(rc, "w") as f:
            f.write("alias ll='ls -l'\n")
        b = FakeSettings()
        c = self.ctx(b, prompt=True)
        steps.prompt(c)
        steps.prompt(c)
        save_state(c.state)
        text = open(rc).read()
        self.assertEqual(text.count(steps.PROMPT_BEGIN), 1)
        restore(b, log=self.logs.append)
        self.assertEqual(open(rc).read(), "alias ll='ls -l'\n")

    def test_existing_red_prompt_respected(self):
        rc = paths.bashrc()
        with open(rc, "w") as f:
            f.write("PS1='\\[\\033[01;38;2;215;25;33m\\]\\w'\n")
        steps.prompt(self.ctx(FakeSettings(), prompt=True))
        self.assertNotIn(steps.PROMPT_BEGIN, open(rc).read())

    def test_restore_removes_only_dotstuff_desklets(self):
        b = FakeSettings(user={("org.cinnamon", "enabled-desklets"): ["clock@cinnamon.org:0:100:100"],
                               ("org.cinnamon", "next-desklet-id"): 1})
        c = self.ctx(b)
        steps.desklets(c)
        save_state(c.state)
        self.assertEqual(len(b.current("org.cinnamon", "enabled-desklets")), 6)
        restore(b, purge=True, log=self.logs.append)
        self.assertEqual(b.current("org.cinnamon", "enabled-desklets"), ["clock@cinnamon.org:0:100:100"])
        self.assertFalse(os.path.exists(os.path.join(paths.data_home(), "cinnamon/desklets/mono-clock@monotile")))

    def test_pins_are_complete(self):
        self.assertEqual(set(pins.FONTS), set(pins.FONT_URLS))
        for sha in list(pins.FONTS.values()) + [pins.WALLPAPER_SHA, pins.CURSOR_SHA, pins.JETBRAINS_SHA]:
            self.assertRegex(sha, r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
