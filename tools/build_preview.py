#!/usr/bin/env python3
"""Bundle the site into one self-contained page for a shareable preview link.

The preview host wraps the page in its own <html>/<head>/<body>, only allows
inline CSS and JS, and serves images published alongside the page. So this
inlines site.css (with the fonts as data URIs) and site.js, keeps the body,
and leaves the photos as relative files to publish next to it.

    python3 tools/build_preview.py OUT_DIR

Writes OUT_DIR/index.html and prints the photo files it references.
"""

import base64
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Things that only make sense on the real website
PREVIEW_CSS = """
/* Preview only: the share button would copy the preview's internal address */
[data-share] { display: none !important; }
"""


def font_data_uri(path):
    data = base64.b64encode((ROOT / "assets" / path).read_bytes()).decode()
    return f'url("data:font/woff2;base64,{data}")'


def main():
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / ".preview"
    out_dir.mkdir(parents=True, exist_ok=True)

    html = (ROOT / "index.html").read_text()
    css = (ROOT / "assets" / "site.css").read_text()
    js = (ROOT / "assets" / "site.js").read_text()

    css = re.sub(r'url\("(fonts/[^"]+\.woff2)"\)', lambda m: font_data_uri(m.group(1)), css)

    body = re.search(r"<body>(.*)</body>", html, flags=re.S).group(1).strip()
    draft = 'class="draft"' in html.split("<head>", 1)[0]

    parts = [
        "<title>Chankhasi Private School</title>",
        "<style>\n" + css + PREVIEW_CSS + "</style>",
    ]
    parts.append("<script>document.documentElement.classList.add('js');</script>")
    if draft:
        parts.append("<script>document.documentElement.classList.add('draft');</script>")
    parts.append(body)
    parts.append("<script>\n" + js + "</script>")

    page = "\n".join(parts) + "\n"
    (out_dir / "index.html").write_text(page)

    photos = sorted(set(re.findall(r'assets/img/photos/[\w.-]+\.webp', body)))
    print(f"wrote {out_dir / 'index.html'} ({len(page) // 1024} KB)")
    for p in photos:
        print("photo:", p)


if __name__ == "__main__":
    main()
