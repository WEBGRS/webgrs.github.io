# Rebuild the hero contour map data embedded in index.html
# Source: Terrain Tiles on AWS (Terrarium encoding, USGS 3DEP in the US)
import base64, io, math, pathlib, re, urllib.request
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = pathlib.Path(__file__).resolve().parents[2]
Z = 13                                          # ~14 m per pixel at this latitude
WEST, EAST, SOUTH, NORTH = -89.56, -89.24, 43.005, 43.150
F = 4                                           # downsample factor
URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"


def tile_xy(lon, lat):
    n = 2 ** Z
    return (lon + 180) / 360 * n, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n


# Fetch and mosaic tiles
x0, y0 = tile_xy(WEST, NORTH)
x1, y1 = tile_xy(EAST, SOUTH)
tx0, ty0, tx1, ty1 = int(x0), int(y0), int(x1), int(y1)
mos = np.zeros(((ty1 - ty0 + 1) * 256, (tx1 - tx0 + 1) * 256))
for ty in range(ty0, ty1 + 1):
    for tx in range(tx0, tx1 + 1):
        raw = urllib.request.urlopen(URL.format(z=Z, x=tx, y=ty)).read()
        a = np.asarray(Image.open(io.BytesIO(raw)).convert("RGB")).astype(float)
        mos[(ty - ty0) * 256:(ty - ty0 + 1) * 256, (tx - tx0) * 256:(tx - tx0 + 1) * 256] = \
            a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768

# Crop to extent
px0, py0 = int((x0 - tx0) * 256), int((y0 - ty0) * 256)
px1, py1 = int((x1 - tx0) * 256), int((y1 - ty0) * 256)
dem = mos[py0:py1, px0:px1]

# Water: large flat low areas
flat = ndimage.generic_filter(dem, np.ptp, size=5) < 0.6
water = ndimage.binary_opening((dem < 262) & flat, iterations=3)
lab, n = ndimage.label(water)
sizes = ndimage.sum(water, lab, range(1, n + 1))
water = ndimage.binary_closing(np.isin(lab, np.where(sizes > 3000)[0] + 1), iterations=2)

# Flatten lakes, smooth, downsample
e = np.clip(dem, 256, None)
e[water] = 257
e = ndimage.gaussian_filter(e, 2.5)
h, w = (e.shape[0] // F) * F, (e.shape[1] // F) * F
es = e[:h, :w].reshape(h // F, F, w // F, F).mean((1, 3))

# Quantize to 8-bit grayscale PNG
lo, hi = 256.0, float(np.ceil(es.max()))
q = np.round((es - lo) / (hi - lo) * 255).clip(0, 255).astype("uint8")
buf = io.BytesIO()
Image.fromarray(q, "L").save(buf, "PNG", optimize=True)
b64 = base64.b64encode(buf.getvalue()).decode()

# Patch index.html
meta = {"w": w // F, "h": h // F, "lo": lo, "hi": hi, "z": Z, "tx0": x0, "ty0": y0, "per": 256 // F}
page = ROOT / "index.html"
s = page.read_text(encoding="utf-8")
s = re.sub(r"const META = \{[^}]*\};", "const META = { " + ", ".join(f"{k}: {v:g}" if isinstance(v, float) and v.is_integer() else f"{k}: {v}" for k, v in meta.items()) + " };", s, count=1)
s = re.sub(r"data:image/png;base64,[A-Za-z0-9+/=]+", "data:image/png;base64," + b64, s, count=1)
page.write_text(s, encoding="utf-8", newline="\n")
print(f"grid {w // F}x{h // F}, {lo}-{hi} m, PNG {len(buf.getvalue()) // 1024} KB")
