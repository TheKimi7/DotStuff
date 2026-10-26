#!/usr/bin/env python3
"""Build the DotStuff-Dark and DotStuff-Light themes from Orchis's source.

    python3 theme-src/build.py /path/to/Orchis-theme [output-dir]

Needs the `libsass` Python package (only for building; DotStuff ships the result).
Reproduces the parts of Orchis's own build that Cinnamon uses (GTK 2/3/4, Cinnamon,
window borders) with the options: red accent, full black, solid panel, primary-coloured
checks and radios, 16 px corners. Then it swaps Orchis's red for Nothing red and appends
DotStuff's layers: the Android / Nothing OS look, shell fonts and the lock screen.

Orchis is by vinceliuice (https://github.com/vinceliuice/Orchis-theme), GPL-3.0.
Pinned source: tag 2024-11-03, commit fb8d14a37ed97ca7988720ed1c8e872db742d35d.
"""
import colorsys
import os
import re
import shutil
import sys
import tempfile

import sass
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
NOTHING_RED = "#D71921"
ORCHIS_REDS = ("#E53935", "#F44336")
CORNER = "16px"

TOKENS = {
    "dark": {
        "bg": "#000000", "card": "#121212", "raised": "#1a1a1a", "button": "#222222",
        "panel": "#000000", "fg": "#ffffff", "fg_dim": "rgba(255, 255, 255, 0.6)",
        "fg_faint": "rgba(255, 255, 255, 0.25)", "outline": "rgba(255, 255, 255, 0.10)",
        "outline_strong": "rgba(255, 255, 255, 0.35)", "hover": "rgba(255, 255, 255, 0.08)",
        "press": "rgba(255, 255, 255, 0.12)", "selected": "rgba(255, 255, 255, 0.14)",
        "tooltip": "#e6e6e6", "tooltip_fg": "#000000", "hover_shade": "1.35", "press_shade": "1.6",
    },
    "light": {
        "bg": "#f2f2f2", "card": "#ffffff", "raised": "#ffffff", "button": "#e6e6e6",
        "panel": "#ffffff", "fg": "#000000", "fg_dim": "rgba(0, 0, 0, 0.6)",
        "fg_faint": "rgba(0, 0, 0, 0.25)", "outline": "rgba(0, 0, 0, 0.10)",
        "outline_strong": "rgba(0, 0, 0, 0.35)", "hover": "rgba(0, 0, 0, 0.06)",
        "press": "rgba(0, 0, 0, 0.10)", "selected": "rgba(0, 0, 0, 0.10)",
        "tooltip": "#1a1a1a", "tooltip_fg": "#ffffff", "hover_shade": "0.94", "press_shade": "0.88",
    },
}


def tweak(src):
    """Write _tweaks-temp.scss the way Orchis's install script does for our options."""
    s = open(os.path.join(src, "_sass", "_tweaks.scss")).read()
    for var, old, new in (("theme", "default", "red"), ("blackness", "false", "true"),
                          ("opacity", "default", "solid"), ("check_radio", "default", "primary"),
                          ("default_corner", "12px", CORNER)):
        s, n = re.subn(rf"(\${var}:\s*'?){re.escape(old)}('?)", rf"\g<1>{new}\g<2>", s, count=1)
        if n != 1:
            raise SystemExit(f"Orchis source changed: could not set ${var}")
    open(os.path.join(src, "_sass", "_tweaks-temp.scss"), "w").write(s)
    pal = os.path.join(src, "_sass", "_color-palette-default.scss")
    p = open(pal).read()
    p, n = re.subn(r"(\$red-(?:light|dark):\s*)#[0-9A-Fa-f]{6}", rf"\g<1>{NOTHING_RED}", p)
    if n != 2:
        raise SystemExit("Orchis source changed: red palette entries not found")
    open(pal, "w").write(p)


def compile_scss(path, out):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w").write(sass.compile(filename=path, output_style="expanded"))


def copytree(a, b):
    shutil.copytree(a, b, dirs_exist_ok=True)


def recolor(root):
    """Orchis bakes its red into SVG and PNG assets: swap it for Nothing red."""
    target = tuple(int(NOTHING_RED[i:i + 2], 16) for i in (1, 3, 5))
    th, ts, tv = colorsys.rgb_to_hsv(*(c / 255 for c in target))
    for d, _, files in os.walk(root):
        for f in files:
            p = os.path.join(d, f)
            if os.path.islink(p):
                continue
            if f.endswith((".svg", ".css", "rc")):
                s = open(p, encoding="utf-8", errors="surrogateescape").read()
                o = s
                for red in ORCHIS_REDS:
                    s = re.sub(re.escape(red), NOTHING_RED, s, flags=re.I)
                if s != o:
                    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
            elif f.endswith(".png"):
                im = Image.open(p).convert("RGBA")
                px, changed = im.load(), False
                for y in range(im.height):
                    for x in range(im.width):
                        r, g, b, a = px[x, y]
                        if a and r > 150 and g < 110 and b < 110:          # Orchis red family
                            h, s_, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
                            nr, ng, nb = colorsys.hsv_to_rgb(th, ts, min(1.0, v * tv / 0.9))
                            px[x, y] = (round(nr * 255), round(ng * 255), round(nb * 255), a)
                            changed = True
                if changed:
                    im.save(p)


def fill(template, tokens):
    out = template
    for k, v in tokens.items():
        out = out.replace("{{" + k + "}}", v)
    out = out.replace("{{accent}}", NOTHING_RED)
    if "{{" in out:
        raise SystemExit("unfilled placeholder in cinnamon overlay: " + out[out.index("{{"):][:40])
    return out


def gtk_overlay(tokens):
    defs = "".join(f"@define-color ds_{k} {v};\n" for k, v in tokens.items()
                   if k not in ("hover_shade", "press_shade"))
    defs += f"@define-color ds_accent {NOTHING_RED};\n"
    body = open(os.path.join(HERE, "overlay", "android-gtk3.css")).read()
    body = body.replace("@ds_hover_shade", tokens["hover_shade"]).replace("@ds_press_shade", tokens["press_shade"])
    return "\n" + defs + body


def build_variant(src, out_dir, mode):
    dark = mode == "dark"
    color = "-Dark" if dark else "-Light"
    else_dark = "-Dark" if dark else ""
    name = "DotStuff-Dark" if dark else "DotStuff-Light"
    t = os.path.join(out_dir, name)
    shutil.rmtree(t, ignore_errors=True)
    os.makedirs(t)

    # GTK 2
    g2 = os.path.join(t, "gtk-2.0")
    os.makedirs(g2)
    for rc in ("apps.rc", "hacks.rc", "main.rc"):
        shutil.copy(os.path.join(src, "gtk-2.0", "common", rc), g2)
    copytree(os.path.join(src, "gtk-2.0", "assets-folder", f"assets-common{else_dark}"), os.path.join(g2, "assets"))
    for f in os.listdir(os.path.join(src, "gtk-2.0", "assets-folder", f"assets-Red{else_dark}")):
        if f.endswith(".png"):
            shutil.copy(os.path.join(src, "gtk-2.0", "assets-folder", f"assets-Red{else_dark}", f), os.path.join(g2, "assets"))
    rc = open(os.path.join(src, "gtk-2.0", f"gtkrc{else_dark}")).read()
    rc = re.sub("#3281EA" if dark else "#1A73E8", NOTHING_RED, rc, flags=re.I)
    tk = TOKENS[mode]
    if dark:
        rc = re.sub(r"(bg_color:)#212121", rf"\g<1>{tk['bg']}", rc)
    open(os.path.join(g2, "gtkrc"), "w").write(rc)

    # GTK 3 and 4
    for ver, outdir in (("3.0", "gtk-3.0"), ("4.0", "gtk-4.0")):
        d = os.path.join(t, outdir)
        copytree(os.path.join(src, "gtk", "assets-Red"), os.path.join(d, "assets"))
        copytree(os.path.join(src, "gtk", "scalable"), os.path.join(d, "assets", "scalable"))
        compile_scss(os.path.join(src, "gtk", ver, f"gtk{color}.scss"), os.path.join(d, "gtk.css"))
        compile_scss(os.path.join(src, "gtk", ver, "gtk-Dark.scss"), os.path.join(d, "gtk-dark.css"))
    shutil.copy(os.path.join(src, "gtk", "thumbnails", f"thumbnail-Red{else_dark}.png"),
                os.path.join(t, "gtk-3.0", "thumbnail.png"))

    # Cinnamon
    c = os.path.join(t, "cinnamon")
    copytree(os.path.join(src, "cinnamon", "common-assets"), os.path.join(c, "assets"))
    for f in os.listdir(os.path.join(src, "cinnamon", f"assets{else_dark}")):
        if f.endswith(".svg"):
            shutil.copy(os.path.join(src, "cinnamon", f"assets{else_dark}", f), os.path.join(c, "assets"))
    for f in ("add-workspace-active", "corner-ripple", "toggle-on", "checkbox", "radiobutton"):
        shutil.copy(os.path.join(src, "cinnamon", "theme-Red", f"{f}{else_dark}.svg"), os.path.join(c, "assets", f + ".svg"))
    compile_scss(os.path.join(src, "cinnamon", f"cinnamon{else_dark}.scss"), os.path.join(c, "cinnamon.css"))
    shutil.copy(os.path.join(src, "cinnamon", "thumbnails", f"thumbnail-Red{else_dark}.png"), os.path.join(c, "thumbnail.png"))

    # window borders
    m = os.path.join(t, "metacity-1")
    os.makedirs(m)
    shutil.copy(os.path.join(src, "metacity-1", "metacity-theme-3.xml"), m)
    copytree(os.path.join(src, "metacity-1", "assets"), os.path.join(m, "assets"))
    shutil.copy(os.path.join(src, "metacity-1", f"thumbnail{else_dark}.png"), os.path.join(m, "thumbnail.png"))
    for n in ("metacity-theme-1.xml", "metacity-theme-2.xml"):
        os.symlink("metacity-theme-3.xml", os.path.join(m, n))

    recolor(t)

    # DotStuff layers
    lock = open(os.path.join(HERE, "overlay", "lockscreen-gtk3.css")).read()
    for ver in ("gtk-3.0", "gtk-4.0"):
        for f, variant in (("gtk.css", mode), ("gtk-dark.css", "dark")):
            with open(os.path.join(t, ver, f), "a") as fh:
                fh.write(gtk_overlay(TOKENS[variant]))
                if ver == "gtk-3.0":
                    fh.write("\n" + lock)
    with open(os.path.join(c, "cinnamon.css"), "a") as fh:
        fh.write(fill(open(os.path.join(HERE, "overlay", "cinnamon.css.in")).read(), TOKENS[mode]))

    open(os.path.join(t, "index.theme"), "w").write(
        "[Desktop Entry]\nType=X-GNOME-Metatheme\n"
        f"Name={name}\n"
        f"Comment=Nothing / Android style {mode} theme for Cinnamon, built from Orchis by vinceliuice (GPL-3.0)\n"
        "Encoding=UTF-8\n\n[X-GNOME-Metatheme]\n"
        f"GtkTheme={name}\nMetacityTheme={name}\n"
        f"IconTheme=Monotile-{'Circle' if dark else 'Light-Circle'}\nCursorTheme=aosp-cursors\n"
        "ButtonLayout=close,minimize,maximize:menu\n")
    shutil.copy(os.path.join(os.path.dirname(src), "COPYING"), t)
    return t


def main():
    orchis = os.path.abspath(sys.argv[1])
    out = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "theme"))
    with tempfile.TemporaryDirectory(prefix="dotstuff-build-") as work:
        src = os.path.join(work, "src")
        shutil.copytree(os.path.join(orchis, "src"), src, symlinks=True)
        shutil.copy(os.path.join(orchis, "COPYING"), work)
        tweak(src)
        for mode in ("dark", "light"):
            print("built", build_variant(src, out, mode))


if __name__ == "__main__":
    main()
