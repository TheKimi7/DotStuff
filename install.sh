#!/bin/bash
# DotStuff installer for Cinnamon (Debian / Ubuntu / Linux Mint).
#   ./install.sh                     install and configure everything
#   ./install.sh --shape squircle    squircle app icons instead of circles
#   ./install.sh --mode light        start in light mode (default dark)
#   ./install.sh mode light|dark     switch an installed setup between light and dark
#   ./install.sh --dry-run           show what would change
#   ./install.sh --only icons,cursor (parts: fonts wallpaper theme cursor fontsettings terminal icons menu desklets prompt)
#   ./install.sh --prompt            also colour the bash prompt
#   ./install.sh --restore [--purge] undo (and optionally delete what was installed)
#   ./install.sh --status
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"

cmd=install
case "${1:-}" in
    --restore) cmd=restore; shift ;;
    --status) cmd=status; shift ;;
    mode) cmd=mode; shift ;;
esac

if [ "$cmd" = install ] && [[ " $* " != *" --skip-deps "* ]]; then
    missing=()
    python3 -c 'import PIL' 2>/dev/null || missing+=(python3-pil)
    python3 -c 'import gi; gi.require_version("GdkPixbuf", "2.0"); gi.require_version("Gio", "2.0")' 2>/dev/null \
        || missing+=(python3-gi gir1.2-gdkpixbuf-2.0)
    ls /usr/lib/*/gdk-pixbuf-2.0/*/loaders/libpixbufloader*svg* >/dev/null 2>&1 || missing+=(librsvg2-common)
    command -v gtk-update-icon-cache >/dev/null || missing+=(gtk-update-icon-cache)
    command -v fc-cache >/dev/null || missing+=(fontconfig)
    if [ ${#missing[@]} -gt 0 ]; then
        echo "Missing packages: ${missing[*]}"
        if [ -t 0 ] && command -v apt-get >/dev/null; then
            read -r -p "Install them now with sudo apt-get? [y/N] " ok
            [[ "$ok" =~ ^[Yy]$ ]] || { echo "Install them first: sudo apt-get install ${missing[*]}"; exit 1; }
            sudo apt-get install -y "${missing[@]}"
        else
            echo "Install them first: sudo apt-get install ${missing[*]}"
            exit 1
        fi
    fi
fi

args=()
for a in "$@"; do [ "$a" = --skip-deps ] || args+=("$a"); done
cd "$HERE"
exec python3 -m dotstuff "$cmd" "${args[@]}"
