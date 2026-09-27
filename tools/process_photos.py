#!/usr/bin/env python3
"""Crop, resize and compress the site's photos.

Originals live in tools/photos-src/ (kept out of git). Only photos listed in
CLEARED are approved for the site. No photos of people go on it without
explicit approval, and no child's face goes on it until their family has
agreed: pupils appear only in crops that cannot identify them. Each photo is
cropped once, optionally lightened, then saved as WebP at two or three widths
for srcset. Re-saving strips any metadata, including location data. Never
upscale: every width must be no wider than the crop.

    python3 tools/process_photos.py
"""

from pathlib import Path

from PIL import Image, ImageEnhance

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "tools" / "photos-src"
OUT = ROOT / "assets" / "img" / "photos"

# name: (crop box in original pixels as left, top, right, bottom; output widths; (brightness, contrast) or None)
PHOTOS = {
    "school-sign": ((270, 130, 1770, 1255), (1200, 700), None),
    "classroom": ((0, 134, 2000, 1334), (1600, 1200, 800), None),
    "visit": ((0, 80, 2000, 1280), (1600, 1200, 800), None),
    "classrooms": ((0, 380, 2000, 1180), (1600, 1200, 800), None),
    # Pupils' photos: not used. The site uses illustrations instead, so no child can be identified.
    "class-blackboard": ((0, 110, 1066, 821), (1066, 540), None),
    "pupil-writing": ((0, 815, 759, 1321), (759, 480), (1.12, 1.05)),
    # Held until her family agrees: her T-shirt makes her recognisable to people who know her.
    "pupil-bench": ((466, 728, 940, 1044), (474,), None),
}
CLEARED = {"school-sign", "classrooms"}
QUALITY = 74


def source(name):
    matches = sorted(SRC.glob(f"{name}.*"))
    if not matches:
        raise SystemExit(f"no original for {name} in {SRC}")
    return matches[0]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (box, widths, lift) in PHOTOS.items():
        if name not in CLEARED:
            continue
        img = Image.open(source(name)).convert("RGB").crop(box)
        if lift:
            img = ImageEnhance.Brightness(img).enhance(lift[0])
            img = ImageEnhance.Contrast(img).enhance(lift[1])
        for w in widths:
            if w > img.width:
                raise SystemExit(f"{name}: {w} px is wider than the {img.width} px crop")
            h = round(img.height * w / img.width)
            out = OUT / f"{name}-{w}.webp"
            img.resize((w, h), Image.LANCZOS).save(out, "WEBP", quality=QUALITY, method=6)
            print(f"{out.name}: {w}x{h}, {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
