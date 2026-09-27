#!/usr/bin/env python3
"""Build the inline SVG map of Malawi for index.html.

Real geography from Natural Earth (public domain, 1:10m): Malawi and its
neighbours, Lake Malawi, Lake Malombe and the Shire and Zambezi rivers, plus a
small Africa inset. The result replaces everything between the MAP:START and
MAP:END markers in index.html.

    python3 tools/build_map.py

Downloads the Natural Earth files into tools/.cache on first run.
"""

import json
import math
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "tools" / ".cache"
NE_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/{}.geojson"

# View window (degrees) and projection. Equirectangular, scaled by cos(lat0),
# which is plenty accurate for a country this size.
LON_MIN, LON_MAX = 32.35, 36.15
LAT_MAX, LAT_MIN = -9.10, -17.30
LAT0 = -13.2
COS0 = math.cos(math.radians(LAT0))
WIDTH = 300.0
K = WIDTH / ((LON_MAX - LON_MIN) * COS0)  # px per degree of latitude
HEIGHT = (LAT_MAX - LAT_MIN) * K

# The school: near the lakeshore about 15 km south of Nkhotakota town
# (roughly 13.05 S). Its longitude is snapped to the shoreline below.
SCHOOL = (-13.046, None)
TOWNS = [
    # name, lat, lon, label anchor, dx, dy
    ("Mzuzu", -11.46, 34.02, "end", -6, 4),
    ("Lilongwe", -13.9833, 33.7833, "start", 7, 4),
    ("Blantyre", -15.79, 34.99, "start", 6, 4),
]
COUNTRIES = [
    # label, lat, lon, rotation
    ("TANZANIA", -9.62, 35.30, 0),
    ("ZAMBIA", -11.55, 32.78, 0),
    ("MOZAMBIQUE", -12.55, 35.55, 0),
]


def fetch(name):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{name}.geojson"
    if not path.exists():
        print("downloading", name)
        urllib.request.urlretrieve(NE_URL.format(name), path)
    return json.loads(path.read_text())


def proj(lon, lat):
    return ((lon - LON_MIN) * COS0 * K, (LAT_MAX - lat) * K)


def rings(geom):
    if geom["type"] == "Polygon":
        return list(geom["coordinates"])
    if geom["type"] == "MultiPolygon":
        return [r for poly in geom["coordinates"] for r in poly]
    return []


def lines(geom):
    if not geom:
        return []
    if geom["type"] == "LineString":
        return [geom["coordinates"]]
    if geom["type"] == "MultiLineString":
        return list(geom["coordinates"])
    return []


def clip_ring(ring, x0, y0, x1, y1):
    """Sutherland-Hodgman against an axis-aligned rectangle (projected px)."""
    def clip(pts, inside, cross):
        out = []
        for i, cur in enumerate(pts):
            prev = pts[i - 1]
            if inside(cur):
                if not inside(prev):
                    out.append(cross(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(cross(prev, cur))
        return out

    def at_x(x):
        return lambda a, b: (x, a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0]))

    def at_y(y):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]), y)

    pts = ring
    for inside, cross in (
        (lambda p: p[0] >= x0, at_x(x0)),
        (lambda p: p[0] <= x1, at_x(x1)),
        (lambda p: p[1] >= y0, at_y(y0)),
        (lambda p: p[1] <= y1, at_y(y1)),
    ):
        if not pts:
            break
        pts = clip(pts, inside, cross)
    return pts


def rdp(pts, eps):
    """Ramer-Douglas-Peucker simplification."""
    if len(pts) < 3:
        return pts
    ax, ay = pts[0]
    bx, by = pts[-1]
    dx, dy = bx - ax, by - ay
    norm = math.hypot(dx, dy)
    best, idx = -1.0, 0
    for i in range(1, len(pts) - 1):
        px, py = pts[i]
        if norm == 0:
            d = math.hypot(px - ax, py - ay)
        else:
            d = abs(dy * px - dx * py + bx * ay - by * ax) / norm
        if d > best:
            best, idx = d, i
    if best > eps:
        return rdp(pts[: idx + 1], eps)[:-1] + rdp(pts[idx:], eps)
    return [pts[0], pts[-1]]


def simplify_ring(pts, eps):
    if len(pts) < 4:
        return pts
    # split the closed ring at its farthest point so RDP keeps the shape
    far = max(range(len(pts)), key=lambda i: (pts[i][0] - pts[0][0]) ** 2 + (pts[i][1] - pts[0][1]) ** 2)
    a = rdp(pts[: far + 1], eps)
    b = rdp(pts[far:] + [pts[0]], eps)
    return a[:-1] + b[:-1]


def fmt(v):
    """Shortest one-decimal form: 12.0 -> 12, 0.5 -> .5, -0.5 -> -.5."""
    s = f"{v:.1f}"
    if s.endswith(".0"):
        s = s[:-2]
    if s == "-0":
        s = "0"
    if s.startswith("0."):
        s = s[1:]
    elif s.startswith("-0."):
        s = "-" + s[2:]
    return s


def seq(nums):
    """Join path numbers, letting a minus sign stand in for the separator."""
    out = ""
    for n in nums:
        if out and not n.startswith("-"):
            out += " "
        out += n
    return out


def rel_path(pts, close):
    """Relative path through points rounded to 0.1px, tracking the rounded
    cursor so rounding never accumulates."""
    cx, cy = round(pts[0][0], 1), round(pts[0][1], 1)
    steps = []
    for x, y in pts[1:]:
        tx, ty = round(x, 1), round(y, 1)
        if (tx, ty) == (cx, cy):
            continue
        steps += [fmt(tx - cx), fmt(ty - cy)]
        cx, cy = tx, ty
    if len(steps) < (4 if close else 2):
        return ""
    return "M" + seq([fmt(pts[0][0]), fmt(pts[0][1])]) + "l" + seq(steps) + ("z" if close else "")


def ring_path(pts):
    if len(pts) < 3:
        return ""
    return rel_path(pts, close=True)


def poly_path(geom, eps, clip=True, project=proj):
    pad = 20
    parts = []
    for ring in rings(geom):
        pts = [project(lon, lat) for lon, lat in ring]
        if clip:
            pts = clip_ring(pts, -pad, -pad, WIDTH + pad, HEIGHT + pad)
        pts = simplify_ring(pts, eps)
        d = ring_path(pts)
        if d:
            parts.append(d)
    return "".join(parts)


def line_path(geom, eps):
    pad = 20
    parts = []
    for line in lines(geom):
        run = []
        for lon, lat in line:
            x, y = proj(lon, lat)
            if -pad <= x <= WIDTH + pad and -pad <= y <= HEIGHT + pad:
                run.append((x, y))
            elif run:
                parts.append(run)
                run = []
        if run:
            parts.append(run)
    out = []
    for run in parts:
        run = rdp(run, eps)
        if len(run) < 2:
            continue
        out.append(rel_path(run, close=False))
    return "".join(out)


def shore_crossings(lake_ring, lat):
    """Longitudes where a parallel crosses the lake's outer ring."""
    xs = []
    for (lon1, lat1), (lon2, lat2) in zip(lake_ring, lake_ring[1:] + lake_ring[:1]):
        if (lat1 - lat) * (lat2 - lat) < 0:
            xs.append(lon1 + (lon2 - lon1) * (lat - lat1) / (lat2 - lat1))
    return sorted(xs)


def main():
    countries = fetch("ne_10m_admin_0_countries")["features"]
    lakes = fetch("ne_10m_lakes")["features"]
    rivers = fetch("ne_10m_rivers_lake_centerlines")["features"]

    by_code = {f["properties"]["ADM0_A3"]: f for f in countries}
    malawi = by_code["MWI"]
    neighbours = [by_code[c] for c in ("TZA", "MOZ", "ZMB")]

    lake_feats = []
    for f in lakes:
        xs = [p[0] for r in rings(f["geometry"]) for p in r]
        ys = [p[1] for r in rings(f["geometry"]) for p in r]
        if max(xs) > LON_MIN and min(xs) < LON_MAX and max(ys) > LAT_MIN and min(ys) < LAT_MAX:
            rank = f["properties"].get("scalerank")
            if rank is not None and rank <= 3:
                lake_feats.append(f)
    lake_malawi = next(f for f in lake_feats if f["properties"].get("name") == "Lake Malawi")
    lake_outer = max(rings(lake_malawi["geometry"]), key=len)

    river_feats = [f for f in rivers if f["properties"].get("name") in ("Shire", "Zambezi")
                   and f["properties"].get("featurecla") == "River"]

    eps = 0.45
    nbr_d = "".join(poly_path(f["geometry"], eps) for f in neighbours)
    mw_d = poly_path(malawi["geometry"], eps)
    lake_d = "".join(poly_path(f["geometry"], 0.35) for f in lake_feats)
    river_d = "".join(line_path(f["geometry"], 0.6) for f in river_feats)

    # Centreline of the lake from north to south, for the italic label
    centre = []
    lat = -10.55
    while lat >= -12.15:
        xs = shore_crossings(lake_outer, lat)
        if len(xs) >= 2:
            # widest water segment at this latitude
            segs = [(xs[i], xs[i + 1]) for i in range(0, len(xs) - 1, 2)]
            a, b = max(segs, key=lambda s: s[1] - s[0])
            centre.append(proj((a + b) / 2, lat))
        lat -= 0.2
    # smooth the centreline with a simple moving average
    sm = []
    for i in range(len(centre)):
        win = centre[max(0, i - 2): i + 3]
        sm.append((sum(p[0] for p in win) / len(win), sum(p[1] for p in win) / len(win)))
    label_d = rel_path(sm, close=False)

    # School pin: on the western shore at the school's latitude
    s_lat = SCHOOL[0]
    west_shore = shore_crossings(lake_outer, s_lat)[0]
    sx, sy = proj(west_shore - 0.03, s_lat)

    # Africa inset, bottom left over Mozambique's Tete province
    IN_X, IN_Y, IN_W = 12.0, HEIGHT - 118.0, 92.0
    AF_LON0, AF_LON1, AF_LAT0, AF_LAT1 = -18.5, 52.5, 38.0, -35.5
    ik = IN_W / (AF_LON1 - AF_LON0)
    IN_H = (AF_LAT0 - AF_LAT1) * ik

    def iproj(lon, lat):
        return (IN_X + (lon - AF_LON0) * ik, IN_Y + (AF_LAT0 - lat) * ik)

    africa_d = "".join(
        poly_path(f["geometry"], 0.5, clip=False, project=iproj)
        for f in countries
        if f["properties"]["CONTINENT"] == "Africa" and f["properties"]["ADM0_A3"] != "MWI"
    )
    af_mw_d = poly_path(malawi["geometry"], 0.2, clip=False, project=iproj)

    # Scale bar: 100 km at the map's latitude
    km_px = COS0 * K / (111.32 * math.cos(math.radians(LAT0)))
    bar = 100 * km_px
    bx, by = WIDTH - 14 - bar, 86.0

    W, H = fmt(WIDTH), fmt(HEIGHT)
    svg = []
    svg.append(
        f'<svg class="map" viewBox="0 0 {W} {H}" role="img" aria-labelledby="map-title map-desc">'
        '<title id="map-title">Map of Malawi</title>'
        '<desc id="map-desc">Chankhasi Primary School is near the western shore of Lake Malawi, about 15 km '
        'south of Nkhotakota town in central Malawi, north-east of the capital, Lilongwe.</desc>'
        f'<defs><clipPath id="map-clip"><rect width="{W}" height="{H}" rx="6"/></clipPath>'
        f'<path id="lake-label-path" d="{label_d}"/></defs>'
        '<g clip-path="url(#map-clip)">'
        f'<rect class="m-sea" width="{W}" height="{H}"/>'
        f'<path class="m-nbr" d="{nbr_d}"/>'
        f'<path class="m-land" d="{mw_d}"/>'
        f'<path class="m-river" d="{river_d}"/>'
        f'<path class="m-lake" d="{lake_d}"/>'
    )
    for name, lat, lon, rot in COUNTRIES:
        x, y = proj(lon, lat)
        svg.append(f'<text class="m-country" x="{fmt(x)}" y="{fmt(y)}" text-anchor="middle">{name}</text>')
    svg.append(
        '<text class="m-lake-label"><textPath href="#lake-label-path" startOffset="50%" '
        'text-anchor="middle">Lake Malawi</textPath></text>'
    )
    for name, lat, lon, anchor, dx, dy in TOWNS:
        x, y = proj(lon, lat)
        cls = "m-town m-capital" if name == "Lilongwe" else "m-town"
        svg.append(f'<circle class="{cls}" cx="{fmt(x)}" cy="{fmt(y)}" r="2.4"/>')
        svg.append(
            f'<text class="m-town-label" x="{fmt(x + dx)}" y="{fmt(y + dy)}" text-anchor="{anchor}">{name}</text>'
        )
    # the school
    svg.append(
        f'<g class="m-school" transform="translate({fmt(sx)} {fmt(sy)})">'
        '<circle class="m-school-halo" r="11"/>'
        '<circle class="m-school-dot" r="4.2"/>'
        '<text class="m-school-label" x="-12" y="-3" text-anchor="end">Chankhasi</text>'
        '<text class="m-school-sub" x="-12" y="10" text-anchor="end">near Nkhotakota</text>'
        '</g>'
    )
    # scale bar
    svg.append(
        f'<g class="m-scale" transform="translate({fmt(bx)} {fmt(by)})">'
        f'<path d="M0 -3V0H{fmt(bar)}V-3"/>'
        f'<text x="{fmt(bar / 2)}" y="-6" text-anchor="middle">100 km</text></g>'
    )
    # Africa inset
    svg.append(
        f'<g class="m-inset"><rect x="{fmt(IN_X - 6)}" y="{fmt(IN_Y - 6)}" width="{fmt(IN_W + 12)}" '
        f'height="{fmt(IN_H + 12)}" rx="4"/>'
        f'<path class="m-inset-land" d="{africa_d}"/>'
        f'<path class="m-inset-mw" d="{af_mw_d}"/>'
        f'<text x="{fmt(IN_X + 6)}" y="{fmt(IN_Y + 70)}">Africa</text></g>'
    )
    svg.append("</g></svg>")
    out = "".join(svg)

    index = ROOT / "index.html"
    html = index.read_text()
    new, n = re.subn(
        r"(<!-- MAP:START -->).*?(<!-- MAP:END -->)",
        lambda m: m.group(1) + out + m.group(2),
        html,
        flags=re.S,
    )
    if n != 1:
        raise SystemExit("MAP markers not found in index.html")
    index.write_text(new)
    print(f"map: {len(out) / 1024:.1f} KB, {W}x{H}, school at {sx:.1f},{sy:.1f}")


if __name__ == "__main__":
    main()
