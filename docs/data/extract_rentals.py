# Aggregate the rentals dataset into the numbers the two madison-rentals figures draw.
#   python docs/data/extract_rentals.py [path/to/properties.js]
# Reads the public dataset of the madison-rentals site (a sibling checkout by default) and writes
# docs/data/rentals.json: counts only, no addresses, names or contact details.
import collections, json, math, pathlib, random, statistics as st, sys

HERE = pathlib.Path(__file__).resolve().parent
SRC = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent.parent.parent / "madison-rentals-site" / "data" / "properties.js"

raw = SRC.read_text(encoding="utf-8")
data = json.loads(raw[raw.index("=") + 1:].rstrip().rstrip(";"))
props, meta = data["properties"], data["meta"]

# Where each property field came from. prov is site / uw / inferred / absent; a field with no entry has no value at all
FIELDS = [("deposit", "Deposit"), ("utilities", "Utilities"), ("pets", "Pets"), ("parking", "Parking"),
          ("laundry", "Laundry"), ("ac", "Air conditioning"), ("furnished", "Furnished")]
prov = []
for key, label in FIELDS:
    c = collections.Counter()
    for p in props:
        s = (p.get("prov") or {}).get(key)
        c[{"official": "site", "uw": "uw", "inferred": "inferred"}.get(s, "none")] += 1
    assert sum(c.values()) == len(props)
    prov.append({"field": key, "label": label, **{k: c[k] for k in ("site", "uw", "inferred", "none")}})

# Rent per person against distance from Bascom Hall, one point per property (its median listing)
rows = [(p["id"], p["dist"], u["beds"], u["per_bed"]) for p in props for u in p["listings"]
        if u["per_bed"] and not u["shared"] and u["beds"] and 1 <= u["beds"] <= 5 and u["term"] in ("2027-28", "now / 2026-27")]
by_beds = {b: st.median(r[3] for r in rows if r[2] == b) for b in range(1, 6)}
per = collections.defaultdict(list)
for pid, dist, b, v in rows:
    per[pid].append((dist, v, v / by_beds[b]))
pts = sorted((v[0][0], st.median(x[1] for x in v), st.median(x[2] for x in v)) for v in per.values())


def rank(a):
    order = sorted(range(len(a)), key=lambda i: a[i])
    r = [0] * len(a)
    for k, i in enumerate(order):
        r[i] = k
    return r


def spearman(x, y):
    rx, ry = rank(x), rank(y)
    n = len(x); mx = my = (n - 1) / 2
    return sum((a - mx) * (b - my) for a, b in zip(rx, ry)) / math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))


dist = [p[0] for p in pts]
adj = [p[2] for p in pts]          # rent as a share of the median for the same bedroom count
rho = spearman(dist, adj)
rnd, ys, hits = random.Random(1), adj[:], 0
for _ in range(2000):
    rnd.shuffle(ys)
    hits += abs(spearman(dist, ys)) >= abs(rho)
bands = []
for lo, hi in [(0, .4), (.4, .6), (.6, .8), (.8, 1), (1, 1.25), (1.25, 1.6), (1.6, 2.0)]:
    v = [p[1] for p in pts if lo <= p[0] < hi]
    bands.append({"lo": lo, "hi": hi, "n": len(v), "median": round(st.median(v))})

out = {
    "built": meta["built"], "properties": meta["properties"], "listings": meta["listings"], "landlords": meta["landlords"],
    "prov": prov,
    "distance": {"n": len(pts), "rho_adjusted": round(rho, 3), "p": round((hits + 1) / 2001, 4),
                 "points": [[round(p[0], 2), round(p[1])] for p in pts], "bands": bands},
}
(HERE / "rentals.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8", newline="\n")
print(f"{meta['properties']} properties, {len(pts)} with a rent per person; rho {rho:.3f} (adjusted for bedrooms), p {(hits + 1) / 2001:.4f}")
for b in bands:
    print(f"  {b['lo']}-{b['hi']} mi: n={b['n']}, median ${b['median']}")
