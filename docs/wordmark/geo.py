# Geometry helpers for drawing letters as filled outlines (shapely): primitives, booleans, SVG export
import math
from shapely.geometry import Polygon, MultiPolygon, LineString, Point, box
from shapely.ops import unary_union
from shapely import affinity

RES = 48  # segments per quarter circle


def rect(x0, y0, x1, y1):
    return box(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))


def poly(*p):
    return Polygon(p)


def disc(cx, cy, r):
    return Point(cx, cy).buffer(r, quad_segs=RES)


def ellipse(cx, cy, rx, ry):
    return affinity.translate(affinity.scale(Point(0, 0).buffer(1, quad_segs=RES), rx, ry), cx, cy)


def ring(cx, cy, rx, ry, w):
    return ellipse(cx, cy, rx, ry).difference(ellipse(cx, cy, rx - w, ry - w))


def line(pts, w, cap="flat", join="mitre"):
    return LineString(pts).buffer(w / 2, quad_segs=RES, cap_style=cap, join_style=join, mitre_limit=8)


def bez(p0, p1, p2, p3, n=40):
    out = []
    for i in range(n + 1):
        t = i / n
        a = (1 - t) ** 3; b = 3 * (1 - t) ** 2 * t; c = 3 * (1 - t) * t * t; d = t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def arc(cx, cy, rx, ry, a0, a1, n=64):
    # angles in degrees, 0 = +x, 90 = +y (down in SVG)
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def wedge(cx, cy, r, a0, a1):
    return Polygon([(cx, cy)] + arc(cx, cy, r, r, a0, a1))


def union(*g):
    return unary_union([x for x in g if x is not None and not x.is_empty])


def move(g, dx=0, dy=0):
    return affinity.translate(g, dx, dy)


def skew(g, deg, origin=(0, 100)):
    return affinity.skew(g, xs=-deg, origin=origin)


def round_corners(g, r):
    return g.buffer(-r, quad_segs=RES, join_style="round").buffer(r, quad_segs=RES, join_style="round") if r else g


def svg_d(g, prec=2):
    polys = list(g.geoms) if isinstance(g, MultiPolygon) else [g] if isinstance(g, Polygon) else [p for p in getattr(g, "geoms", []) if isinstance(p, Polygon)]
    f = lambda v: f"{round(v, prec):g}"
    parts = []
    for p in polys:
        for r in [p.exterior] + list(p.interiors):
            c = list(r.coords)[:-1]
            parts.append("M" + " L".join(f"{f(x)} {f(y)}" for x, y in c) + "Z")
    return " ".join(parts)


def bounds(*gs):
    b = union(*gs).bounds
    return b
