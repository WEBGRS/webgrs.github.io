# Aggregate the Madison Eats data into the numbers the two food-map figures and the card text use.
#   python docs/data/extract_food.py [path/to/worker/data.json]
# Reads the public copy of the dataset that the guarded Worker serves (worker/data.json in the private madison-eats
# repo: no review text, no Google photos), and writes docs/data/food.json: counts and rating statistics only.
import collections, itertools, json, math, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
EATS = HERE.parent.parent.parent / "madison-eats"
SRC = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else EATS / "worker" / "data.json"

data = json.loads(SRC.read_text(encoding="utf-8"))
places, details = data["places"], data["details"]
shown = [p for p in places if not p.get("cl")]        # places that look closed or replaced are hidden by default

# Orderable places: a store link flagged true. The public README states the same totals.
cover = collections.Counter()
orderable = 0
for p in shown:
    apps = {e[0] for e in details[str(p["i"])].get("lk") or [] if e[2] is True}
    orderable += bool(apps)
    cover.update(apps)

# Star ratings by source, over the places shown
ratings = collections.defaultdict(dict)
for p in shown:
    for src, stars, count, _url in details[str(p["i"])]["rt"]:
        ratings[src][p["i"]] = stars
SOURCES = ["google", "dd", "ue", "gh", "es", "toast"]
assert set(ratings) == set(SOURCES), set(ratings)


def rank(a):
    """Ranks with ties averaged (star ratings tie constantly)."""
    order = sorted(range(len(a)), key=lambda i: a[i])
    r = [0.0] * len(a)
    i = 0
    while i < len(a):
        j = i
        while j + 1 < len(a) and a[order[j + 1]] == a[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2
        i = j + 1
    return r


def spearman(x, y):
    rx, ry = rank(x), rank(y)
    n = len(x); m = (n - 1) / 2
    return sum((a - m) * (b - m) for a, b in zip(rx, ry)) / math.sqrt(sum((a - m) ** 2 for a in rx) * sum((b - m) ** 2 for b in ry))


pairs = []
for a, b in itertools.combinations(SOURCES, 2):
    ids = [i for i in ratings[a] if i in ratings[b]]
    if len(ids) >= 20:                                 # a correlation over fewer places says nothing
        pairs.append([a, b, round(spearman([ratings[a][i] for i in ids], [ratings[b][i] for i in ids]), 2), len(ids)])

# The award check lives in the project's own calibration report (it needs the scoring internals)
report = (EATS / "data" / "calibration.txt").read_text(encoding="utf-8")
m = re.search(r"award winners \(taste categories\): n=(\d+); AUC of taste \(bonus removed\) vs non-winners: ([\d.]+)", report)
assert m, "calibration line not found"

out = {
    "built": data["meta"]["built"],
    "places_total": len(places), "places_shown": len(shown),
    "orderable": orderable, "coverage": dict(cover),
    "ratings": {s: {"n": len(v), "mean": round(sum(v.values()) / len(v), 2)} for s, v in ratings.items()},
    "agreement": {"sources": SOURCES, "pairs": pairs},
    "award": {"n": int(m.group(1)), "auc": float(m.group(2))},
}
(HERE / "food.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print(f"{len(shown)} places shown of {len(places)}; {orderable} orderable; coverage {dict(cover)}")
print("mean stars:", {s: v["mean"] for s, v in out["ratings"].items()})
print("pairs:", len(pairs), "award AUC", out["award"])
