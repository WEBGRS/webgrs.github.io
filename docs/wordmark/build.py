# Draw the "H. Gu" wordmark as filled outlines (no fonts): an athletic slab family after UW's Motion W.
# Output next to this file: <v>.svg.html for every variant, and test.html with all of them.
# Colours come from CSS: --wm-ink (letters), --wm-dot (the full stop). y grows downward; cap height 0..100.
import math, pathlib
from geo import rect, poly, union, move, skew, svg_d, line
from shapely.geometry import Polygon, MultiPolygon, LineString
from shapely import affinity

OUT = pathlib.Path(__file__).parent
W = 25                       # stem width
HX, GX, UX = 10, 136, 252    # letter origins


def octo(x0, y0, x1, y1, c):
    return poly((x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c), (x1 - c, y1), (x0 + c, y1), (x0, y1 - c), (x0, y0 + c))


def serifs(x, y, style, head=True):
    # The pair of serifs at one end of a stem; head = the stem runs down from y
    s = 1 if head else -1
    def pair(left):
        if style == "wedge":
            return poly((x - 10, y), (x, y), (x, y + s * 15)) if left else poly((x + W, y), (x + W + 10, y), (x + W, y + s * 15))
        if style == "flare":
            return poly((x - 7, y), (x, y), (x, y + s * 36)) if left else poly((x + W, y), (x + W + 7, y), (x + W, y + s * 36))
        if style == "slab":
            return rect(x - 9, y, x, y + s * 12) if left else rect(x + W, y, x + W + 9, y + s * 12)
        if style == "bracket":
            if left:
                return union(rect(x - 9, y, x, y + s * 13), poly((x - 9, y + s * 13), (x, y + s * 13), (x, y + s * 21)))
            return union(rect(x + W, y, x + W + 9, y + s * 13), poly((x + W, y + s * 13), (x + W + 9, y + s * 13), (x + W, y + s * 21)))
        if style == "tuscan":
            if left:
                return rect(x - 11, y, x, y + s * 16).difference(poly((x - 12, y + s * 3), (x - 4.5, y + s * 8), (x - 12, y + s * 13)))
            return rect(x + W, y, x + W + 11, y + s * 16).difference(poly((x + W + 12, y + s * 3), (x + W + 4.5, y + s * 8), (x + W + 12, y + s * 13)))
        return None
    return union(pair(True), pair(False))


def letters(style):
    H = union(rect(HX, 0, HX + W, 100), rect(HX + 64, 0, HX + 64 + W, 100), rect(HX + W, 41, HX + 64, 61),
              serifs(HX, 0, style), serifs(HX, 100, style, False), serifs(HX + 64, 0, style), serifs(HX + 64, 100, style, False))
    g = GX
    G = octo(g, 0, g + 90, 100, 26).difference(octo(g + W, W, g + 90 - W, 100 - W, 8))
    G = G.difference(rect(g + 56, W, g + 92, 50))
    term = {"wedge": poly((g + 62, W), (g + 89.5, W), (g + 89.5, 44)),
            "flare": poly((g + 64, W), (g + 89.5, W), (g + 89.5, 46)),
            "slab": rect(g + 70, W, g + 89.5, W + 13),
            "tuscan": rect(g + 70, W, g + 89.5, W + 16).difference(poly((g + 90.5, W + 3), (g + 83, W + 8), (g + 90.5, W + 13))),
            "bracket": union(rect(g + 70, W, g + 89.5, W + 13), poly((g + 70, W + 13), (g + 89.5, W + 13), (g + 89.5, W + 21)))}.get(style)
    G = union(G, term, rect(g + 46, 50, g + 90, 70))
    u = UX
    U = union(rect(u, 30, u + W, 76), serifs(u, 30, style),
              poly((u, 74), (u + W, 74), (u + W, 75), (u + 60, 75), (u + 60, 100), (u + 20, 100), (u, 84)),
              rect(u + 60, 30, u + 60 + W, 100), serifs(u + 60, 30, style), serifs(u + 60, 100, style, False))
    return H, G, U


def dot_shape(kind="para"):
    return poly((116, 76), (132, 76), (128, 100), (112, 100)) if kind == "para" else poly((112, 76), (130, 76), (130, 100), (112, 100))


def inline(g, inset=5.6, w=1.7):
    # A paper-coloured stripe running inside every stroke, as on a jersey
    inner = g.buffer(-inset, join_style="mitre", mitre_limit=3)
    rings = []
    for p in getattr(inner, "geoms", [inner]):
        if isinstance(p, Polygon) and not p.is_empty:
            rings += [LineString(p.exterior.coords)] + [LineString(r.coords) for r in p.interiors]
    return g.difference(union(*[r.buffer(w / 2, join_style="mitre", mitre_limit=3) for r in rings]))


def trail(x1=-4, y0=46, n=4):
    # Motion stripes trailing off the H's left edge, shortest at the bottom
    return union(*[rect(x1 - L, y0 + k * 13, x1, y0 + k * 13 + 7) for k, L in enumerate([64, 50, 36, 22][:n])])


def arch(geoms, rise=11, mid=175, half=190):
    # Set each letter on an arch, turned to follow it, like a jersey front
    out = []
    for gm in geoms:
        cx = (gm.bounds[0] + gm.bounds[2]) / 2
        t = (cx - mid) / half
        dy = -rise * (1 - t * t)
        ang = math.degrees(math.atan(2 * rise * t / half))
        out.append(affinity.rotate(move(gm, 0, dy), ang, origin=(cx, 50 + dy)))
    return out


def shadow(g, dx=-4, dy=4):
    # A solid shadow trailing down-left, as under the Motion W
    return move(g, dx, dy).difference(g)


def barbs(points, size=9, half=7):
    # Triangular barbs on stem sides: (x, y, direction) with direction -1 = left, 1 = right
    return union(*[poly((x, y - half), (x + d * size, y), (x, y + half)) for x, y, d in points])


def bulbs(points, r=5.5):
    from geo import disc
    return union(*[disc(x, y, r) for x, y in points])


def warp(gs, fn, step=2):
    import shapely, numpy as np
    def f(c):
        out = np.array([fn(x, y) for x, y in c])
        return out
    return [shapely.transform(shapely.segmentize(g, step), f) for g in gs]


def motion():
    H, G, U = letters("wedge")
    return skew(union(H, G, U), 12), skew(dot_shape(), 12)


def pennant():
    # The Motion W itself: stems lean 6°, the word climbs to the right, a sky shadow trails down-left
    H, G, U = letters("wedge")
    up = lambda g: affinity.skew(skew(g, 6), ys=-7, origin=(0, 100))
    g, d = up(union(H, G, U)), up(dot_shape())
    return g, d, [(shadow(union(g, d)), "var(--wm-shadow)")]


def barbed():
    # Iowa's bracketed slab at 10°, with Patriots-style barbs at crossbar height
    H, G, U = letters("bracket")
    b = barbs([(HX, 51, -1), (HX + 64 + W, 51, 1), (GX + 90, 60, 1), (UX, 58, -1), (UX + 60 + W, 58, 1)])
    return skew(union(H, G, U, b), 10), skew(dot_shape(), 10)


def tuscan():
    H, G, U = letters("tuscan")
    k = bulbs([(HX, 51), (HX + 64 + W, 51), (GX, 50), (UX, 56), (UX + 60 + W, 62)])
    return skew(union(H, G, U, k), 7), skew(dot_shape(), 7)


def jersey():
    # Minnesota-style two-tone: a sky band set inside every stroke
    H, G, U = letters("wedge")
    g = union(H, G, U)
    inner = g.buffer(-6.2, join_style="mitre", mitre_limit=3)
    rings = []
    for q in getattr(inner, "geoms", [inner]):
        if isinstance(q, Polygon) and not q.is_empty:
            rings += [LineString(q.exterior.coords)] + [LineString(r.coords) for r in q.interiors]
    band = union(*[r.buffer(1.5, join_style="mitre", mitre_limit=3) for r in rings]).intersection(g)
    return skew(g, 12), skew(dot_shape(), 12), [(skew(band, 12), "var(--wm-band)", "over")]


def dash():
    H, G, U = letters("wedge")
    return skew(union(trail(), H, G, U), 12), skew(dot_shape(), 12)


def arched():
    # Harvard / Bulls arch: stems stay upright, the whole line bows upward
    H, G, U = letters("bracket")
    mid, half, rise = 175, 185, 24
    f = lambda x, y: (x, y - rise * (1 - ((x - mid) / half) ** 2))
    H, G, U, d = warp([H, G, U, dot_shape("square")], f)
    return union(H, G, U), d


def chevron():
    # Purdue: a flat top and a bottom edge that folds into a shallow V under the stop
    H, G, U = letters("wedge")
    mid, half, depth = 121, 240, 16
    f = lambda x, y: (x, y + (y / 100) * depth * max(0, 1 - abs(x - mid) / half))
    H, G, U, d = warp([H, G, U, dot_shape("square")], f)
    return union(H, G, U), d


VARIANTS = {"a": ("Motion 原版", motion), "b": ("Pennant 校旗", pennant), "c": ("Barbed 倒刺", barbed),
            "d": ("Tuscan 托斯卡纳", tuscan), "e": ("Jersey 双色内线", jersey), "f": ("Dash 拖尾", dash),
            "g": ("Arch 拱形", arched), "h": ("Chevron V 底", chevron)}


def svg(v, cls="wm"):
    out = VARIANTS[v][1]()
    g, dot, extra = out if len(out) == 3 else (*out, [])
    x0, y0, x1, y1 = union(g, dot, *[e[0] for e in extra]).bounds
    m = 2
    vb = f"{x0 - m:.1f} {y0 - m:.1f} {x1 - x0 + 2 * m:.1f} {y1 - y0 + 2 * m:.1f}"
    under = "".join(f'<path fill="{c}" d="{svg_d(e)}"/>' for e, c, *pos in extra if not pos)
    over = "".join(f'<path fill="{c}" d="{svg_d(e)}"/>' for e, c, *pos in extra if pos)
    return (f'<svg class="{cls}" viewBox="{vb}" aria-hidden="true" focusable="false">{under}'
            f'<path fill="var(--wm-ink)" fill-rule="evenodd" d="{svg_d(g)}"/>{over}'
            f'<path fill="var(--wm-dot)" d="{svg_d(dot)}"/></svg>')


if __name__ == "__main__":
    for old in OUT.glob("*.svg.html"):
        old.unlink()
    for v in VARIANTS:
        (OUT / f"{v}.svg.html").write_text(svg(v), encoding="utf-8")
    cells = "".join(f'<div class="c"><small>{v.upper()} · {name}</small>{svg(v)}'
                    f'<div class="row">{svg(v, "wm-s")}<span class="dark">{svg(v, "wm-s")}</span></div></div>'
                    for v, (name, _) in VARIANTS.items())
    (OUT / "test.html").write_text(f"""<!doctype html><meta charset="utf-8"><style>
body{{margin:0; display:grid; grid-template-columns:1fr 1fr; font:14px system-ui; --wm-ink:#0B1A2C; --wm-dot:#FACC15; --wm-shadow:#38BDF8; --wm-band:#38BDF8}}
.c{{padding:22px 40px 26px; border:1px solid #e3e8ee}}
small{{display:block; margin-bottom:14px; font-weight:600}}
.wm{{display:block; height:150px; width:auto; max-width:100%}}
.row{{display:flex; gap:16px; align-items:center; margin-top:18px}}
.wm-s{{display:block; height:24px; width:auto}}
.dark{{background:#082F49; padding:8px 12px; --wm-ink:#F1F5F9}}
</style>{cells}""", encoding="utf-8")
