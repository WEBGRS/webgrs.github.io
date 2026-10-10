# Aggregate the Madison Essentials data into the numbers the two campus-guide figures and the card text use.
#   python docs/data/extract_guide.py [path/to/madison-essentials]
# Reads the entries (data/places, data/faq) and the demand table in docs/SIGNALS.md, which already holds only
# aggregate counts (distinct askers per topic). Writes docs/data/guide.json: counts only, no text or names.
import collections, json, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
SRC = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent.parent.parent / "madison-essentials"


def read(p):
    return json.loads(p.read_text(encoding="utf-8"))


places = [read(f) for f in sorted((SRC / "data" / "places").glob("*/*.json"))]
faq = [read(f) for f in sorted((SRC / "data" / "faq").glob("*.json"))]
ev = [e for x in places + faq for e in x["evidence"]]
claims = collections.Counter(re.split(r"[:.]", e["claim"])[0] for e in ev)

# Demand table: | topic | WeChat | r/UWMadison | r/madisonwi | what the site does |
sig = (SRC / "docs" / "SIGNALS.md").read_text(encoding="utf-8")
num = lambda s: int(re.sub(r"\D", "", s) or 0)
topics, sources = [], {}
for line in sig.splitlines():
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) == 4 and re.fullmatch(r"[\d,]+", cells[2]):
        name = cells[0].split(" (")[0]
        name = "15 chat groups" if "WeChat" in name else name   # same wording as the guide's public README
        sources[name] = {"messages": num(cells[2]), "questions": num(cells[3])}
    if len(cells) != 5 or not re.fullmatch(r"[–\-\d*]+", cells[1]):
        continue
    does = cells[4]
    tool = ("rentals" if "Rentals" in does else "eats" if "Eats" in does
            else "courses" if does.startswith("out of scope") else None)
    chat, uw, wi = (num(c) for c in cells[1:4])
    topics.append({"topic": cells[0], "chat": chat, "uw": uw, "wi": wi, "total": chat + uw + wi,
                   "tool": tool, "new": "**new**" in does})
topics.sort(key=lambda t: -t["total"])
assert len(sources) == 3 and len(topics) > 20, (sources, len(topics))

out = {
    "checked": places[0]["checked"],
    "places": len(places),
    "answers": len(faq),
    "quotes": len(ev),
    "claims": dict(claims.most_common()),
    "pages": len({e["url"] for e in ev}),
    "categories": dict(collections.Counter(p["cat"] for p in places).most_common()),
    "signals": {"sources": sources, "topics": topics},
}
(HERE / "guide.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
