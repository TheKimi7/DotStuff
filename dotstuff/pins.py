"""Third-party downloads, pinned to exact commits/releases and checked by SHA-256.

Nothing here is redistributed by DotStuff: files are fetched from their original
source at install time. See NOTICE.md for credits and terms.
"""

NOTHINGFONT = "9d8b51d2e89fcf4d71f4d31e346a2b0ee4350716"   # github.com/xeji01/nothingfont

_FONT_URL = f"https://raw.githubusercontent.com/xeji01/nothingfont/{NOTHINGFONT}/fonts/"

# Nothing's typefaces (Ndot, NType 82, Lettera Mono LL) plus Space Mono / Space Grotesk,
# as collected in xeji01/nothingfont.
FONTS = {
    "Ndot57-Regular.otf": "8f99a991d2cab1010eaf79520a7ba9bb17d287b4757ba99ae9ff99c4db44367c",
    "Ndot57Caps-Regular.otf": "01621ee999e3a30cd49730a1de215e4d2c3f46f3a971920ae98f0d7a9e33e529",
    "Ndot55-Regular.otf": "ef081f6c1fd2041a31ec4258960b4e871817f8544beaa82a565615c5b9947e60",
    "Ndot55Caps-Regular.otf": "2ca128bd28c27bcfcc561cdf4539f780446f58b1505278475dc68af702f02d9c",
    "NType82-Regular.otf": "f99bd828d330b73e088cef5dbc16885c6b17f089365039ffaa808aff1739ab0c",
    "NType82-Headline.otf": "34ea6eb65cef614092c529db949a4cd6b01581b050af33891c60d4fde51b9de1",
    "NType82Mono-Regular.otf": "51afd15702d82b7ceb4819fd7b39805b18de67ed8df8f4ceaf39aa40e208efc3",
    "LetteraMonoLL-Regular.otf": "84090ef0f4d2393e12f53008cff0b5cc3f0d3e06b96eb62ac1a1032fcb78d04e",
    "LetteraMonoLL-Light.otf": "325292c4db1f109fbdbf78ba226a3fe441abf481615fe596e75158848aca9a47",
    "LetteraMonoLL-Medium.otf": "1a6277e58cb1f553765fb41974a892c3cb2dea512d3e58a25e06d4aeb36a4ce8",
    "SpaceMono-Regular.otf": "757b5c3b95bb3117f8aaaf3dc69af2682e697361f8db90949e5dcf346c5b3045",
    "SpaceGrotesk-Regular.otf": "e42cdf830afdeb2988213fb4e14fc6a82f62a958daeaebf0dbce99145363cf1d",
}
FONT_URLS = {name: _FONT_URL + name for name in FONTS}

# JetBrains Mono (SIL OFL 1.1), used by the desklets' labels
JETBRAINS_URL = "https://github.com/JetBrains/JetBrainsMono/releases/download/v2.304/JetBrainsMono-2.304.zip"
JETBRAINS_SHA = "6f6376c6ed2960ea8a963cd7387ec9d76e3f629125bc33d1fdcd7eb7012f7bbf"
JETBRAINS_FILES = ["JetBrainsMono-Regular.ttf", "JetBrainsMono-Medium.ttf",
                   "JetBrainsMono-Bold.ttf", "JetBrainsMono-Light.ttf"]

# AOSP Cursors by Tech-Tac (GPL-3.0), Android's cursor set for Linux
CURSOR_URL = "https://github.com/Tech-Tac/aosp-cursors/releases/download/1.3.1/aosp-cursors-linux-1.3.1.tar.xz"
CURSOR_SHA = "d271d2be20a6d7ac13747e4d9224a28ddbf7e2c1fab2e805cdf03bde05a0a3ae"
CURSOR_DIR = "aosp-cursors"
