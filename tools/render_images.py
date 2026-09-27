#!/usr/bin/env python3
"""Render the share card and icons with headless Chrome.

Needs the local preview server running on port 8940, because the share
card borrows the hero art straight from index.html.

    python3 tools/render_images.py

Writes assets/img/og.jpg, apple-touch-icon.png and favicon-32.png.
"""

import subprocess
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "assets" / "img"
BASE = "http://localhost:8940"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def shoot(url, size, out, transparent=False):
    args = [
        CHROME,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--force-device-scale-factor=1",
        "--virtual-time-budget=6000",
        f"--window-size={size[0]},{size[1]}",
        f"--screenshot={out}",
    ]
    if transparent:
        args.append("--default-background-color=00000000")
    subprocess.run(args + [url], check=True, capture_output=True)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)

        shoot(f"{BASE}/tools/og.html", (1200, 630), tmp / "og.png")
        Image.open(tmp / "og.png").convert("RGB").save(IMG / "og.jpg", quality=86, optimize=True, progressive=True)

        shoot(f"{BASE}/tools/icon.html?shape=square", (512, 512), tmp / "square.png")
        sq = Image.open(tmp / "square.png").convert("RGB")
        sq.resize((180, 180), Image.LANCZOS).save(IMG / "apple-touch-icon.png", optimize=True)

        shoot(f"{BASE}/tools/icon.html", (512, 512), tmp / "round.png", transparent=True)
        rd = Image.open(tmp / "round.png").convert("RGBA")
        rd.resize((32, 32), Image.LANCZOS).save(IMG / "favicon-32.png", optimize=True)

    for name in ("og.jpg", "apple-touch-icon.png", "favicon-32.png"):
        print(name, (IMG / name).stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
