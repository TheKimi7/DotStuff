"""Where DotStuff reads and writes (XDG base directories)."""
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THEMES_SRC = os.path.join(REPO, "theme")            # DotStuff-Dark, DotStuff-Light
WALLPAPERS_SRC = os.path.join(REPO, "wallpapers")
MENU_ICON_SRC = os.path.join(REPO, "assets", "dotstuff-menu-symbolic.svg")
MONOTILE = os.path.join(REPO, "vendor", "monotile")


def _xdg(var, default):
    v = os.environ.get(var)
    return v if v and os.path.isabs(v) else os.path.expanduser(default)


def home():
    return os.path.expanduser("~")


def data_home():
    return _xdg("XDG_DATA_HOME", "~/.local/share")


def config_home():
    return _xdg("XDG_CONFIG_HOME", "~/.config")


def state_dir():
    return os.path.join(data_home(), "dotstuff")


def cache_dir():
    return os.path.join(_xdg("XDG_CACHE_HOME", "~/.cache"), "dotstuff")


def fonts_dir():
    return os.path.join(data_home(), "fonts", "dotstuff")


def wallpapers_dir():
    return os.path.join(data_home(), "backgrounds", "dotstuff")


def themes_dir():
    return os.path.join(home(), ".themes")


def icons_dir():
    return os.path.join(data_home(), "icons")


def cursors_parent():
    return os.path.join(home(), ".icons")


def menu_icon_path():
    return os.path.join(data_home(), "icons", "hicolor", "scalable", "apps", "dotstuff-menu-symbolic.svg")


def menu_applet_configs():
    d = os.path.join(config_home(), "cinnamon", "spices", "menu@cinnamon.org")
    if not os.path.isdir(d):
        return []
    return sorted(os.path.join(d, f) for f in os.listdir(d) if f.endswith(".json"))


def bashrc():
    return os.path.join(home(), ".bashrc")
