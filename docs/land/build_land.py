"""Build the 1-degree land mask used by the route globe.

Reads a world-atlas TopoJSON (the `land` object), rasterises it to a 360 x 180
equirectangular bitmap, packs it to bits and writes the base64 string into
index.html between `const LAND = '` and `';`.

    python docs/land/build_land.py [path/to/world-countries-50m.json]
"""
import base64, json, pathlib, re, sys
from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / "datamap" / "data" / "world-countries-50m.json"
W, H, SS = 360, 180, 4  # mask size, supersampling

topo = json.loads(SRC.read_text(encoding="utf-8"))
sx, sy = topo["transform"]["scale"]
tx, ty = topo["transform"]["translate"]

# Decode delta-encoded arcs
arcs = []
for a in topo["arcs"]:
    x = y = 0
    pts = []
    for dx, dy in a:
        x += dx; y += dy
        pts.append((x * sx + tx, y * sy + ty))
    arcs.append(pts)

def ring(ids):
    out = []
    for i in ids:
        pts = arcs[i] if i >= 0 else arcs[~i][::-1]
        out.extend(pts if not out else pts[1:])
    return out

def unwrap(pts):
    # Keep longitudes continuous across the antimeridian
    out, off = [], 0.0
    for k, (lon, lat) in enumerate(pts):
        if k and lon + off - out[-1][0] > 180: off -= 360
        elif k and lon + off - out[-1][0] < -180: off += 360
        out.append((lon + off, lat))
    return out

img = Image.new("L", (W * SS * 3, H * SS), 0)
dr = ImageDraw.Draw(img)
def px(lon, lat): return ((lon + 540) * SS, (90 - lat) * SS)

land = topo["objects"]["land"]
geoms = land["geometries"] if land["type"] == "GeometryCollection" else [land]
for g in geoms:
    polys = g["arcs"] if g["type"] == "MultiPolygon" else [g["arcs"]]
    for poly in polys:
        for k, r in enumerate(poly):
            pts = unwrap(ring(r))
            span = max(p[0] for p in pts) - min(p[0] for p in pts)
            # A ring that wraps the whole globe (Antarctica) is closed along the pole
            if span > 350 and k == 0:
                pts = pts + [(pts[-1][0], -90), (pts[0][0], -90)]
            for o in (-360, 0, 360):
                dr.polygon([px(lon + o, lat) for lon, lat in pts], fill=0 if k else 255)

mid = img.crop((W * SS, 0, W * SS * 2, H * SS)).resize((W, H), Image.BOX)
bits = bytearray((W * H + 7) // 8)
for j in range(H):
    for i in range(W):
        if mid.getpixel((i, j)) >= 110:
            n = j * W + i
            bits[n >> 3] |= 1 << (n & 7)
b64 = base64.b64encode(bytes(bits)).decode()

html = ROOT / "index.html"
s = html.read_text(encoding="utf-8")
s2, n = re.subn(r"const LAND = '[^']*';", f"const LAND = '{b64}';", s)
if n:
    html.write_text(s2, encoding="utf-8", newline="\n")
print(f"{len(b64)} chars, {'written' if n else 'no LAND marker found'}")
