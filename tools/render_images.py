#!/usr/bin/env python3
"""Render the share card (og.jpg) with headless Chrome.

The favicons and home-screen icons are drawn from the vector badge and
shield in assets/img/logo and are not generated here.

Needs the local preview server running on port 8940, because the share
card borrows the hero art straight from index.html.

    python3 tools/render_images.py

Writes assets/img/og.jpg.
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


    for name in ("og.jpg",):
        print(name, (IMG / name).stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
