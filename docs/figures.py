# The "how it works" figures, as functions that return an SVG. docs/build.py calls render(name)
# and writes the result between <!-- fig:NAME --> and <!-- /fig:NAME --> in index.html.
import json, math, pathlib, random, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "docs" / "data"   # aggregates written by docs/data/extract_*.py
CW, SW = 7.5, 6.5          # approx. glyph width at 14px / 12px


class Fig:
    def __init__(self, name, w, h, label):
        self.name, self.w, self.h, self.label, self.parts = name, w, h, label, []

    def add(self, s):
        self.parts.append(s)

    def node(self, x, y, text, sub=None, d=0, w=None, accent=False):
        w = w or max(len(text) * CW, len(sub or "") * SW) + 26
        h = 50 if sub else 34
        cls = "n acc" if accent else "n"
        s = f'<g class="{cls}" style="--d:{d}"><rect x="{x}" y="{y}" width="{w:.0f}" height="{h}" rx="6"/>'
        s += f'<text x="{x + 13}" y="{y + 22}" class="k">{text}</text>'
        if sub:
            s += f'<text x="{x + 13}" y="{y + 39}" class="s">{sub}</text>'
        self.add(s + "</g>")
        return x, y, w, h

    def edge(self, pts, d=0, accent=False, dashed=False, arrow=True):
        path = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
        cls = "e" + (" acc" if accent else "") + (" dash n" if dashed else " draw")
        extra = "" if dashed else ' pathLength="1"'
        self.add(f'<path class="{cls}" style="--d:{d}" d="{path}"{extra}/>')
        if arrow:
            (x0, y0), (x1, y1) = pts[-2], pts[-1]
            a = math.atan2(y1 - y0, x1 - x0)
            p = [(x1, y1), (x1 - 7 * math.cos(a - .45), y1 - 7 * math.sin(a - .45)),
                 (x1 - 7 * math.cos(a + .45), y1 - 7 * math.sin(a + .45))]
            cls = "tip n acc" if accent else "tip n"
            self.add(f'<path class="{cls}" style="--d:{d + 4}" d="M{p[0][0]:.1f} {p[0][1]:.1f} L{p[1][0]:.1f} {p[1][1]:.1f} L{p[2][0]:.1f} {p[2][1]:.1f}Z"/>')

    def rect(self, x, y, w, h, cls, d=0):
        self.add(f'<rect class="n {cls}" style="--d:{d}" x="{x:.1f}" y="{y:.1f}" width="{max(w, 0):.1f}" height="{h}" rx="2"/>')

    def dot(self, x, y, r=3, cls="dot", d=0):
        self.add(f'<circle class="{cls} n" style="--d:{d}" cx="{x:.1f}" cy="{y:.1f}" r="{r}"/>')

    def text(self, x, y, s, cls="s", anchor="start", d=0):
        self.add(f'<text class="{cls} n" style="--d:{d}" x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}">{s}</text>')

    def svg(self):
        body = "\n".join(self.parts)
        return (f'<svg viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{self.label}">\n{body}\n</svg>')


# route-animator: altitude over one flying leg, from altOf() and easeP()
def route():
    CLIMB, ROLL, K = 0.28, 0.05, 2.2
    smooth = lambda t: t * t * (3 - 2 * t)
    clamp = lambda v: max(0.0, min(1.0, v))
    ease = lambda t: (2 * t) ** K / 2 if t < .5 else 1 - (2 * (1 - t)) ** K / 2

    def alt(u):
        if u < CLIMB: return smooth(clamp((u - ROLL) / (CLIMB - ROLL)))
        if u > 1 - CLIMB: return smooth(clamp(((1 - u) - ROLL) / (CLIMB - ROLL)))
        return 1.0

    f = Fig("route-animator", 520, 230, "Altitude over one flying leg, keyed to time versus keyed to eased distance")
    x0, x1, yg, yc = 58, 512, 180, 52
    X = lambda u: x0 + (x1 - x0) * u
    Y = lambda a: yg - (yg - yc) * a
    f.edge([(x0, yg), (x1, yg)], d=0, arrow=False)
    f.text(x0 - 10, yc + 4, "cruise", anchor="end")
    f.text(x0 - 10, yg + 4, "ground", anchor="end")
    f.text(x0, yg + 26, "leg start")
    f.text(x1, yg + 26, "leg end", anchor="end")
    us = [i / 400 for i in range(401)]
    f.edge([(X(u), Y(alt(ease(u)))) for u in us], d=2, arrow=False)
    f.edge([(X(u), Y(alt(u))) for u in us], d=1, accent=True, arrow=False)
    # Where each version finishes climbing
    for u, lab, acc in [(0.28, "28%", True), (0.5 * 0.56 ** (1 / K), "38%", False)]:
        f.add(f'<path class="e dash n{" acc" if acc else ""}" style="--d:6" d="M{X(u):.1f} {yc - 6} L{X(u):.1f} {yg}"/>')
        f.text(X(u), yc - 12, lab, cls="k" + (" a" if acc else ""), anchor="middle", d=6)
    # Legend
    f.add('<path class="e acc n" style="--d:7" d="M300 14 L324 14"/>')
    f.text(332, 18, "keyed to time (shipped)", d=7)
    f.add('<path class="e n" style="--d:7" d="M300 34 L324 34"/>')
    f.text(332, 38, "keyed to eased distance", d=7)
    return f


# uw-course-lookup: build pipeline
def courses():
    f = Fig("uw-course-lookup", 520, 206, "Build pipeline from chat counts and public APIs to a static page")
    f.node(104, 8, "MadGrades API", d=0)
    f.node(254, 8, "Course Search API", d=0)
    f.node(0, 82, "chat counts", d=1)
    bx, by, bw, bh = f.node(146, 82, "build_db.py", d=2)
    f.node(300, 82, "uwcourses.db", d=4)
    f.node(270, 158, "build_site.py", d=5)
    f.node(412, 158, "static page", w=108, d=7, accent=True)
    f.edge([(170, 42), (170, 82)], d=1)
    f.edge([(330, 42), (330, 62), (230, 62), (230, 82)], d=1)
    f.edge([(108, 99), (146, 99)], d=2)
    f.edge([(bx + bw, 99), (300, 99)], d=3)
    f.edge([(340, 116), (340, 158)], d=5)
    f.edge([(394, 175), (412, 175)], d=6, accent=True)
    f.add(f'<path class="e dash n" style="--d:4" d="M200 116 L200 150"/>')
    f.text(146, 170, "26 codes that are")
    f.text(146, 188, "not real courses")
    return f


# photo-organizer: pipeline plus a schematic of HDBSCAN clusters
def photos():
    f = Fig("photo-organizer", 520, 214, "Photos are embedded with CLIP, split into people and scenery, and scenery is clustered")
    f.node(0, 4, "7,346 files", w=206, d=0)
    f.node(0, 70, "CLIP ViT-B/32", "cached by path, size, mtime", w=206, d=2)
    f.node(0, 152, "people or scenery", "zero-shot text prompts", w=206, d=4)
    f.edge([(40, 38), (40, 70)], d=1)
    f.edge([(40, 120), (40, 152)], d=3)
    f.edge([(206, 177), (262, 177), (262, 110), (286, 110)], d=5)
    f.text(274, 204, "scenery only", anchor="middle")
    rnd = random.Random(7)
    clusters = [(338, 58, 22, 14), (430, 44, 26, 12), (402, 132, 24, 16), (482, 150, 18, 11)]
    i = 0
    for cx, cy, rx, ry in clusters:
        f.add(f'<ellipse class="e dash acc n" style="--d:8" cx="{cx}" cy="{cy}" rx="{rx + 12}" ry="{ry + 12}"/>')
        for _ in range(9):
            a, r = rnd.uniform(0, 6.283), rnd.uniform(0, 1) ** .6
            f.add(f'<circle class="dot n" style="--d:{6 + i % 5}" cx="{cx + math.cos(a) * rx * r:.1f}" cy="{cy + math.sin(a) * ry * r:.1f}" r="3"/>')
            i += 1
    for x, y in [(310, 118), (370, 176), (500, 88)]:
        f.add(f'<circle class="dot faint n" style="--d:9" cx="{x}" cy="{y}" r="3"/>')
    f.text(430, 14, "trip clusters", anchor="middle", d=9)
    f.text(372, 196, "misc", anchor="middle", d=9)
    return f


# DataMap: real 7-class ramps from datamap/src/color.js buildRamp()
def datamap():
    ramps = {
        "blue": ["#c9defa", "#9ec3f4", "#71a7ed", "#408ae6", "#266fc6", "#17559f", "#0b3e78"],
        "teal": ["#c3e6d3", "#90d1b0", "#55bb8e", "#00a26f", "#00845a", "#006745", "#004b31"],
        "orange": ["#f7d3c6", "#eeaf98", "#e28a6a", "#d56236", "#b64819", "#91340a", "#6d2301"],
    }
    L = ["0.89", "0.81", "0.72", "0.63", "0.54", "0.45", "0.37"]
    f = Fig("datamap", 520, 168, "Blue, teal and orange seven-class ramps that share one lightness track")
    for r, (name, cols) in enumerate(ramps.items()):
        y = 6 + r * 40
        f.text(0, y + 21, name, cls="k")
        for c, hexv in enumerate(cols):
            f.add(f'<rect class="n" style="--d:{c}" x="{70 + c * 64}" y="{y}" width="60" height="32" rx="3" fill="{hexv}"/>')
    f.text(0, 150, "L", cls="k")
    for c, v in enumerate(L):
        f.text(100 + c * 64, 150, v, anchor="middle", d=c)
    f.edge([(70, 132), (514, 132)], d=3, arrow=False)
    return f


# geo-spoof: isolated world to main world
def geo():
    f = Fig("geo-spoof", 520, 214, "Settings flow from the popup through bridge.js to inject.js, which answers the page")
    f.node(0, 8, "popup map picker", d=0)
    f.node(196, 8, "chrome.storage", w=140, d=1)
    f.node(196, 72, "bridge.js", "isolated world", w=140, d=3)
    f.node(196, 156, "inject.js", "main world", w=140, d=5, accent=True)
    f.node(374, 156, "web page", "calls geolocation", w=146, d=6)
    f.edge([(146, 25), (196, 25)], d=1)
    f.edge([(266, 42), (266, 72)], d=2)
    f.edge([(266, 122), (266, 156)], d=4)
    f.text(276, 144, "CustomEvent", d=4)
    f.edge([(374, 172), (336, 172)], d=6)
    f.edge([(336, 192), (374, 192)], d=7, accent=True)
    f.text(184, 176, "returns a spoofed fix", anchor="end", d=7)
    f.text(184, 194, "toString(): [native code]", anchor="end", d=7)
    return f


# tophat-watch: detection to three alert channels
def tophat():
    f = Fig("tophat-watch", 520, 222, "The content script reports to the service worker, which alerts through three channels")
    f.node(0, 4, "Classroom tab", w=196, d=0)
    f.node(0, 68, "content.js", "DOM observer, 5 s rescan", w=196, d=2)
    f.node(0, 160, "service worker", "alerts once per opening", w=196, d=4, accent=True)
    f.edge([(40, 38), (40, 68)], d=1)
    f.edge([(40, 118), (40, 160)], d=3)
    outs = [(40, "desktop notification"), (104, "beep, offscreen page"), (168, "ntfy push to phone")]
    for i, (y, t) in enumerate(outs):
        f.node(318, y, t, w=202, d=7 + i)
        f.edge([(196, 185), (258, 185), (258, y + 17), (318, y + 17)], d=5 + i, accent=(i == 2))
    return f


def load(name):
    return json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))


# madison-rentals: where each property field came from, from docs/data/rentals.json
def rentals_provenance():
    d = load("rentals")
    total = d["properties"]
    f = Fig("madison-rentals-provenance", 520, 232, "Stacked bars: for seven property fields, the share of 605 properties whose value came from the landlord site, the UW list, a description, or no source")
    x0, W = 128, 342
    legend = [("s1", "landlord site", 0), ("s2", "UW list", 108), ("s3", "read from description", 184), ("s0", "not stated (%)", 352)]
    for cls, text, dx in legend:
        f.rect(dx, 2, 11, 11, f"seg {cls}", d=0)
        f.text(dx + 17, 12, text, d=0)
    for r, row in enumerate(d["prov"]):
        y = 30 + r * 28
        f.text(x0 - 12, y + 14, row["label"], cls="k", anchor="end", d=r)
        x = x0
        for cls, key in (("s1", "site"), ("s2", "uw"), ("s3", "inferred"), ("s0", "none")):
            w = W * row[key] / total
            if w > 0:
                f.rect(x, y, w, 20, f"seg {cls}", d=r + 1)
            x += w
        f.text(520, y + 14, f"{round(100 * row['none'] / total)}%", cls="k a" if row["none"] / total > .5 else "k", anchor="end", d=r + 2)
    return f


# madison-rentals: rent per person against distance, from docs/data/rentals.json
def rentals_distance():
    d = load("rentals")["distance"]
    f = Fig("madison-rentals-distance", 520, 236, "Scatter of rent per person against distance from campus for 403 properties, with the median of each distance band rising toward campus")
    L, R, T, B = 46, 512, 10, 190
    X = lambda mi: L + (R - L) * mi / 2.0
    Y = lambda usd: B - (B - T) * (usd - 500) / 2000
    for usd in (1000, 1500, 2000):
        f.add(f'<path class="e dash n" style="--d:0" d="M{L} {Y(usd):.1f} L{R} {Y(usd):.1f}"/>')
        f.text(L - 8, Y(usd) + 4, f"${usd:,}", anchor="end", d=0)
    f.edge([(L, B), (R, B)], d=0, arrow=False)
    for mi in (0, .5, 1, 1.5, 2):
        f.text(X(mi), B + 18, f"{mi:g}", anchor="middle", d=0)
    f.text((L + R) / 2, B + 38, "miles from Bascom Hall", anchor="middle", d=0)
    # One path per stagger step: a zero-length round-capped segment is a dot, and far fewer nodes than circles
    for step in range(3):
        seg = "".join(f"M{X(mi):.1f} {Y(usd):.1f}h0" for i, (mi, usd) in enumerate(d["points"]) if i % 3 == step)
        f.add(f'<path class="pts n" style="--d:{1 + step}" d="{seg}"/>')
    pts = [(X((b["lo"] + b["hi"]) / 2), Y(b["median"])) for b in d["bands"]]
    f.edge(pts, d=5, accent=True, arrow=False)
    for (x, y), b in zip(pts, d["bands"]):
        f.dot(x, y, 3.8, "dot hi", d=9)
    first, last = d["bands"][0], d["bands"][4]
    f.text(pts[0][0] + 8, pts[0][1] - 9, f"${first['median']:,}", cls="k a halo", d=10)
    f.text(pts[4][0], pts[4][1] + 20, f"${last['median']:,}", cls="k a halo", anchor="middle", d=10)
    f.text(R, T + 8, f"rank correlation {d['rho_adjusted']:.2f}, n = {d['n']}".replace("-", "−"), anchor="end", d=10)
    return f


# uw-course-lookup: build and serve, as the repo does it
def course_arch():
    f = Fig("uw-course-architecture", 520, 218, "Public sources feed a local SQLite build, which is deployed to a Cloudflare Worker that the GitHub Pages page queries")
    f.node(0, 4, "Public sources", "MadGrades, Enroll, Reddit, chat", w=230, d=0)
    f.node(0, 76, "build_db.py", "SQLite, never committed", w=230, d=2)
    f.node(290, 76, "Cloudflare Worker", "origin check, rate limit", w=230, d=5, accent=True)
    f.node(290, 160, "Page on GitHub Pages", "vanilla JS, 60 rows a time", w=230, d=7)
    f.edge([(115, 54), (115, 76)], d=1)
    f.edge([(230, 101), (290, 101)], d=3, accent=True)
    f.text(260, 92, "deploy", anchor="middle", d=4)
    f.edge([(405, 160), (405, 126)], d=6)
    f.text(397, 148, "only from the site's origin", anchor="end", d=6)
    return f


# uw-course-lookup: same course, different instructor, from docs/data/course.json
def course_spread():
    d = load("course")
    rows = d["spread"][:8]
    f = Fig("uw-course-spread", 520, 222, "For eight courses, the span from the lowest to the highest instructor GPA in the same course")
    L, R, T = 112, 452, 30
    X = lambda g: L + (R - L) * (g - 1.8) / 2.2
    for g in (2.0, 2.5, 3.0, 3.5, 4.0):
        f.add(f'<path class="e dash n" style="--d:0" d="M{X(g):.1f} {T - 8} L{X(g):.1f} {T + len(rows) * 21 - 6}"/>')
        f.text(X(g), T - 14, f"{g:.1f}", anchor="middle", d=0)
    f.text(520, T - 14, "gap", anchor="end", d=0)
    for i, r in enumerate(rows):
        y = T + i * 21 + 6
        f.text(L - 12, y + 5, r["code"], cls="k", anchor="end", d=i)
        f.edge([(X(r["low"]), y), (X(r["high"]), y)], d=i, accent=True, arrow=False)
        f.dot(X(r["low"]), y, 4.2, "dot", d=i + 3)
        f.dot(X(r["high"]), y, 4.2, "dot hi", d=i + 3)
        f.text(520, y + 5, f"{r['spread']:.2f}", cls="k", anchor="end", d=i + 4)
    f.dot(L, T + len(rows) * 21 + 18, 4.2, "dot", d=8)
    f.text(L + 12, T + len(rows) * 21 + 23, "lowest instructor", d=8)
    f.dot(L + 158, T + len(rows) * 21 + 18, 4.2, "dot hi", d=8)
    f.text(L + 170, T + len(rows) * 21 + 23, "highest instructor", d=8)
    return f


# Every "fig" name used in docs/work/*.json must be registered here
FIGS = {
    "route-animator": route,
    "uw-course-lookup": courses,
    "photo-organizer": photos,
    "datamap": datamap,
    "geo-spoof": geo,
    "tophat-watch": tophat,
    "madison-rentals-provenance": rentals_provenance,
    "madison-rentals-distance": rentals_distance,
    "uw-course-architecture": course_arch,
    "uw-course-spread": course_spread,
}


def render(name):
    if name not in FIGS:
        raise KeyError(f"no figure named {name!r} in docs/figures.py (known: {', '.join(FIGS)})")
    return FIGS[name]().svg()
