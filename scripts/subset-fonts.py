"""Build the self-hosted Archivo files from @fontsource-variable/archivo.

Limits the variable axes to the ranges the type scale uses (wght 400-800,
wdth 100-125) and splits the rupee sign into its own file so pages without
prices never download it. Run after upgrading the font package:

    python scripts/subset-fonts.py

Requires: pip install fonttools brotli
"""
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "node_modules/@fontsource-variable/archivo/files"
OUT = ROOT / "public/fonts"
AXES = {"wght": (400, 800), "wdth": (100, 125)}


def build(src: str, out: str, unicodes: str | None = None) -> None:
    font = TTFont(SRC / src)
    font = instancer.instantiateVariableFont(font, AXES)
    if unicodes:
        opts = subset.Options()
        opts.layout_features = ["*"]
        sub = subset.Subsetter(opts)
        sub.populate(unicodes=subset.parse_unicodes(unicodes))
        sub.subset(font)
    font.flavor = "woff2"
    font.save(OUT / out)
    print(f"{out}: {(OUT / out).stat().st_size / 1024:.1f} KB")


OUT.mkdir(parents=True, exist_ok=True)
build("archivo-latin-wdth-normal.woff2", "archivo-latin-var.woff2")
build("archivo-latin-ext-wdth-normal.woff2", "archivo-rupee-var.woff2", "U+20B9")

# IBM Plex Mono ships as static weights; copy the Latin files as-is.
PLEX = ROOT / "node_modules/@fontsource/ibm-plex-mono/files"
for weight in (400, 500):
    name = f"ibm-plex-mono-latin-{weight}-normal.woff2"
    (OUT / f"plex-mono-{weight}.woff2").write_bytes((PLEX / name).read_bytes())
    print(f"plex-mono-{weight}.woff2 copied")
