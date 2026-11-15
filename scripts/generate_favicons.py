#!/usr/bin/env python3
"""Rasterise the Roadie Labs icon (web/rl-icon.svg) into the root icon files.

Writes, into web/ (tracked, pushed to the site root by
`push_wordpress.py --sync-favicons`):
  favicon.ico           16x16 + 32x32
  favicon-32x32.png     32x32
  apple-touch-icon.png  180x180

Needs `rsvg-convert` (librsvg; `brew install librsvg`). Fails if it is
missing: the icons are never drawn from anything but the logo SVG.

Usage:
    python3 scripts/generate_favicons.py
"""

import io
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_SVG = PROJECT_ROOT / "web" / "rl-icon.svg"
OUT_DIR = PROJECT_ROOT / "web"

FAVICON_FILES = ("favicon.ico", "favicon-32x32.png", "apple-touch-icon.png")


def rasterise(svg: Path, size: int) -> Image.Image:
    exe = shutil.which("rsvg-convert")
    if not exe:
        raise RuntimeError("rsvg-convert not found; install librsvg")
    png = subprocess.run(
        [exe, "-w", str(size), "-h", str(size), str(svg)],
        check=True, capture_output=True,
    ).stdout
    return Image.open(io.BytesIO(png)).convert("RGBA")


def build(out_dir: Path = OUT_DIR, svg: Path = SOURCE_SVG) -> list:
    out_dir.mkdir(parents=True, exist_ok=True)
    icon16, icon32, icon180 = (rasterise(svg, s) for s in (16, 32, 180))
    ico = out_dir / "favicon.ico"
    # Each size rendered from the SVG at that size, not downscaled from 32.
    icon32.save(ico, format="ICO", sizes=[(16, 16), (32, 32)], append_images=[icon16])
    icon32.save(out_dir / "favicon-32x32.png", format="PNG", optimize=True)
    icon180.convert("RGB").save(out_dir / "apple-touch-icon.png", format="PNG", optimize=True)
    return [out_dir / name for name in FAVICON_FILES]


def main():
    try:
        paths = build()
    except (RuntimeError, subprocess.CalledProcessError) as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    for p in paths:
        print(f"  wrote {p.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
