#!/usr/bin/env python3
"""Crop, resize and compress the site's photos.

Originals live in tools/photos-src/ (kept out of git). Only photos listed in
CLEARED are approved for the site, and no photos of people go on it without
explicit approval. Each photo is cropped once, then saved as WebP at two or
three widths for srcset. Re-saving strips any
metadata, including location data.

    python3 tools/process_photos.py
"""

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "tools" / "photos-src"
OUT = ROOT / "assets" / "img" / "photos"

# name: (crop box in original pixels as left, top, right, bottom; output widths)
PHOTOS = {
    "school-sign": ((270, 130, 1770, 1255), (1200, 700)),
    "classroom": ((0, 134, 2000, 1334), (1600, 1200, 800)),
    "visit": ((0, 80, 2000, 1280), (1600, 1200, 800)),
    "classrooms": ((0, 380, 2000, 1180), (1600, 1200, 800)),
}
CLEARED = {"school-sign", "classrooms"}
QUALITY = 74


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (box, widths) in PHOTOS.items():
        if name not in CLEARED:
            continue
        src = Image.open(SRC / f"{name}.webp").convert("RGB").crop(box)
        for w in widths:
            h = round(src.height * w / src.width)
            out = OUT / f"{name}-{w}.webp"
            src.resize((w, h), Image.LANCZOS).save(out, "WEBP", quality=QUALITY, method=6)
            print(f"{out.name}: {w}x{h}, {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
