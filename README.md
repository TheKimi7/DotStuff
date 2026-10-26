# DotStuff

**A Nothing-inspired black, white and red desktop for Linux Mint and other Cinnamon desktops,
installed and configured with one script, and undone with one more.**

| Dark | Light |
|---|---|
| ![Monotile-Circle-Dark](https://raw.githubusercontent.com/TheKimi7/monotile/main/docs/demo-circle-dark.png) | ![Monotile-Circle-Light](https://raw.githubusercontent.com/TheKimi7/monotile/main/docs/demo-circle-light.png) |
| ![Monotile-Squircle-Dark](https://raw.githubusercontent.com/TheKimi7/monotile/main/docs/demo-squircle-dark.png) | ![Monotile-Squircle-Light](https://raw.githubusercontent.com/TheKimi7/monotile/main/docs/demo-squircle-light.png) |

![Folders, file types and devices](https://raw.githubusercontent.com/TheKimi7/monotile/main/docs/demo-system.png)

> Unofficial fan project, not affiliated with or endorsed by Nothing Technology Limited.
> See [NOTICE.md](NOTICE.md) for credits.

## What you get

| Part | Details |
|---|---|
| **DotStuff-Dark and DotStuff-Light themes** | Android / Nothing OS look in a fixed charcoal or white palette with Nothing red: pill buttons and text fields, Material 3 switches, rounded cards, menus and dialogs, pill tabs. Black (or white) panel, bold NType 82 for the panel clock and a dot-matrix font for menus and the calendar. Apps keep your normal font. Built from [Orchis](https://github.com/vinceliuice/Orchis-theme). |
| **Light and dark mode** | `./install.sh mode light` / `./install.sh mode dark` switches the theme, icons, desktop widgets, wallpaper and terminal profile together. The lock screen stays dark. |
| **Lock screen** | Big dot-matrix clock, black pill password field with a red typing line, round avatar, black panels, red error messages. Styled from the DotStuff theme, so no extra software. |
| **Monochrome icons** | Icon themes made by [monotile](https://github.com/TheKimi7/monotile), downloaded during the install: **Monotile-Circle-Dark** and **Monotile-Squircle-Dark**, plus **Monotile-Circle-Light** and **Monotile-Squircle-Light** for light mode (black symbol on a light-grey tile). Every app, settings and session icon becomes a white stencil on a dark tile; folders are black and file types greyscale; devices and coloured status icons become white line art. New apps are converted automatically. No other icon theme is needed: monotile includes the icons it starts from. |
| **Desktop widgets** | Five native Cinnamon desklets: clock (12-dot dial), date, weather, RAM/disk rings and a 24-dot day bar. They follow light and dark mode. Right-click > Configure to change them. |
| **Fonts** | Nothing's Ndot, NType 82 and Lettera Mono (from [xeji01/nothingfont](https://github.com/xeji01/nothingfont)), Space Mono/Grotesk and JetBrains Mono. |
| **Cursor** | [AOSP Cursors](https://github.com/Tech-Tac/aosp-cursors), Android's cursor set, at size 18. |
| **Wallpapers** | Three Nothing wallpapers: a dark one by default, its light version in light mode, and one more dark one to pick in *Backgrounds*. |
| **Terminal** | Two GNOME Terminal profiles (GNOME Terminal is Linux Mint's default terminal): **DotStuff Dark** (grey text on black) and **DotStuff Light** (dark grey on light grey), both in Lettera Mono LL 11. The one for the current mode is the default; your own profiles stay, and other terminals are left alone. |
| **Menu button** | A white disc (black in light mode) with a red centre dot. |
| **Bash prompt** (optional) | White `user@host`, red path. |

## Install

Linux Mint, Ubuntu or Debian, logged in to a **Cinnamon** session:

```sh
git clone https://github.com/TheKimi7/DotStuff.git
cd DotStuff
./install.sh --dry-run     # see everything it would change first
./install.sh               # install and configure
```

`install.sh` checks for the packages it needs (`python3-pil python3-gi gir1.2-gdkpixbuf-2.0
librsvg2-common gtk-update-icon-cache fontconfig`) and offers to install
the missing ones with `sudo apt-get`. That is the only step that needs root; everything else
goes into your home folder. The first run takes about 5 to 10 minutes (it converts roughly 10,000
icons into four icon themes, about 1.1 GB) and restarts Cinnamon at the end so the new fonts and theme show up; your windows stay open.

### Options

| Option | Effect |
|---|---|
| `--mode light` | start in light mode (default: dark); switch any time with `./install.sh mode dark` |
| `--shape squircle` | squircle app icons instead of circles (both icon themes are always installed; switch any time in *System Settings > Themes*) |
| `--only fonts,theme,...` / `--skip ...` | install only some parts: `fonts wallpaper theme cursor fontsettings terminal icons menu desklets prompt` |
| `--prompt` | also colour the bash prompt (added as a marked block in `~/.bashrc`) |
| `--dry-run` | list what would change, change nothing |
| `--no-reload` | do not restart Cinnamon at the end |
| `--status` | show what DotStuff has changed |

Running `./install.sh` again is safe: anything already in place is skipped.

## Undo

```sh
./install.sh --restore           # every setting and edited file back the way it was
./install.sh --restore --purge   # ...and delete the themes, fonts, cursor and widgets it installed
```

Before changing anything, DotStuff records the original value of every setting and keeps a
copy of every file it edits (`~/.local/share/dotstuff/`). Settings that were at their defaults
are reset rather than pinned. Restore only removes desklets DotStuff placed, and `--purge` only
deletes what DotStuff itself installed. Things it found already in place (for example an
existing AOSP cursor install, or a menu button with your own custom icon) are left alone.

## What it changes

| Setting | Value |
|---|---|
| Applications, desktop (panel) and window-border theme | DotStuff-Dark (or DotStuff-Light) |
| Icon theme | Monotile-Circle-Dark or Monotile-Squircle-Dark (the -Light versions in light mode) |
| Cursor | aosp-cursors, size 18 |
| Window title font / desktop icon font | Ndot57Caps 12 / Ndot55Caps 10 |
| Font smoothing | RGBA anti-aliasing, slight hinting |
| Lock screen fonts (time / date / messages) | Ndot 57 112 / Ndot57Caps 22 / NType 82 14 |
| Wallpaper | NothingWallpaper-1 (NothingWallpaper-2 in light mode), zoom |
| GNOME Terminal default profile | DotStuff Dark (DotStuff Light in light mode) |
| Colour scheme (GTK4, Electron and Firefox apps) | prefer dark (prefer light in light mode) |
| `~/.config/gtk-4.0` | links to the DotStuff theme so libadwaita apps use it (skipped if you have your own files there) |
| Desklets | Mono Date, Clock, Weather, System, Day at the top left |
| Menu applet | custom icon `dotstuff-menu-symbolic`, no label (only if it does not already use a custom icon) |

Your normal application font is not changed.

## Limitations

- **Cinnamon only** for now. Other desktops can still use the icon themes, cursor and GTK theme.
- **Tested on Debian 13 with Cinnamon 6.4.** Linux Mint 22.x should work the same way; the
  installer says so when your Cinnamon version differs. Reports welcome.
- **Per user.** Everything goes into your home folder; other accounts on the same computer are
  not changed. Run the installer once per user.
- **Needs internet for the first install**: fonts and the cursor are downloaded from their
  original sources. The first run also converts about 10,000 icons (5 to 10 minutes).
- **Apps that draw their own look** are not themed:
  - Qt and KDE apps.
  - Flatpak apps (they cannot see `~/.themes`).
  - Tray icons that an app sends as a ready-made picture instead of a theme icon name; some
    Electron apps and clipboard managers do this. Those keep their own colours, so they may not
    switch between light and dark.
- Some windows (browser web apps, some Electron apps) show their own runtime icon in the panel
  instead of the themed one. See the [monotile README](https://github.com/TheKimi7/monotile#limitations).
- Desktop widgets are placed at the top left of the main screen for a 1080p-sized desktop; drag
  them anywhere afterwards.
- The weather desklet uses [wttr.in](https://wttr.in); everything else works offline.

## Light and dark

```sh
./install.sh mode light    # DotStuff-Light, Monotile -Light icons, white desklet cards, light wallpaper
./install.sh mode dark     # back to black
```

Your tile shape is kept, the desklets switch by themselves, the wallpaper only switches if it
is a DotStuff one, new terminal windows use the DotStuff Light or Dark profile (unless you picked another default), the lock screen stays dark, and `--restore` still puts back
whatever you had before DotStuff, however often you switch.

## Development

```sh
python3 -m unittest discover -s tests          # DotStuff
```

monotile is its own project ([TheKimi7/monotile](https://github.com/TheKimi7/monotile)). The
installer downloads the commit pinned in `dotstuff/pins.py` into `~/.local/share/dotstuff/monotile`.
After pushing a monotile change, pin it with `python3 tools/pin_monotile.py <commit>` (default:
`main`). To try an unpushed monotile, point the installer at your checkout:
`DOTSTUFF_MONOTILE=~/path/to/monotile ./install.sh`.

The themes in `theme/` are built from Orchis's source (the pinned tag in `theme-src/build.py`)
with `python3 theme-src/build.py /path/to/Orchis-theme` (needs the `libsass` Python package);
the Android / Nothing layer lives in `theme-src/overlay/`.

Tests run against temporary home folders and an in-memory settings store; they never touch your
desktop or the network. `DOTSTUFF_CACHE=/path/to/files` makes the installer use pre-downloaded
files (checked against the same SHA-256 hashes).

## Licence

GPL-3.0-or-later. Third-party parts and their terms are listed in [NOTICE.md](NOTICE.md).
