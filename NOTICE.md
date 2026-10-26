# Credits and third-party terms

DotStuff is free software under the GNU GPL v3.0 or later (see `LICENSE`).
It is an unofficial fan project and is **not affiliated with or endorsed by Nothing Technology Limited**.

## Included in this repository

| Part | Author | Licence | Notes |
|---|---|---|---|
| `theme/DotStuff-Dark`, `theme/DotStuff-Light` | built from the source of [Orchis](https://github.com/vinceliuice/Orchis-theme) by vinceliuice (tag 2024-11-03, commit fb8d14a) with `theme-src/build.py` | GPL-3.0 | Orchis options: red accent, full black, solid panel, 16 px corners; its red swapped for Nothing red. DotStuff adds an Android / Nothing OS layer (pill buttons and fields, Material 3 switches, rounded cards, menus and dialogs), dot-matrix shell fonts and lock-screen styles (the lock-screen rules follow the structure of cinnamon-screensaver's own stylesheet, GPL-2.0+). Orchis's licence is included in each theme as `COPYING`. |
| `vendor/monotile` | monotile | GPL-3.0 | Icon theme generator and desklets used by DotStuff. |
| `vendor/monotile/base` | [Papirus icon theme](https://github.com/PapirusDevelopmentTeam/papirus-icon-theme) by the Papirus Development Team | GPL-3.0 | Trimmed copy (one size per icon, default and black folders) that monotile converts and the icon themes inherit; see `base/PAPIRUS-COPYRIGHT`. |
| `assets/dotstuff-menu-symbolic.svg` | DotStuff | GPL-3.0 | |
| `wallpapers/NothingWallpaper-1, -2, -3` | Nothing Technology Limited | © Nothing; not covered by DotStuff's licence | Nothing's wallpapers, included for personal use. |

## Downloaded at install time (not redistributed by DotStuff)

Each file is fetched from its original source, pinned to an exact commit or release and
checked against a SHA-256 hash (see `dotstuff/pins.py`).

| Part | Source | Terms |
|---|---|---|
| Ndot 55, Ndot 57, NType 82, Lettera Mono LL | [xeji01/nothingfont](https://github.com/xeji01/nothingfont) | Nothing's typefaces (© Nothing Technology Limited), collected in that repository, which states no licence. DotStuff downloads them for your personal use only. |
| Space Mono, Space Grotesk | [xeji01/nothingfont](https://github.com/xeji01/nothingfont) | SIL Open Font License 1.1 (Colophon Foundry / Florian Karsten). |
| JetBrains Mono | [JetBrains/JetBrainsMono](https://github.com/JetBrains/JetBrainsMono) v2.304 | SIL Open Font License 1.1. |
| AOSP Cursors | [Tech-Tac/aosp-cursors](https://github.com/Tech-Tac/aosp-cursors) 1.3.1 | GPL-3.0; cursor artwork from the Android Open Source Project (Apache-2.0). |

## Installed from your distribution

| Part | Licence |
|---|---|

## Inspiration

Nothing OS's monochrome look, and [Panacea](https://github.com/EnsixD/Panacea) by EnsixD.
