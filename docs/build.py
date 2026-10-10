# Build the Selected work section from docs/work/*.json and write it into index.html and README.md.
#   python docs/build.py            write the regions
#   python docs/build.py --check    exit 1 if a file is out of date (nothing is written)
# "tool": N on a project puts it in the Toolbox under the hero (N = position); it needs a Live site link, a GitHub
# Source link and a screenshot.
# Each region sits between <!-- work:NAME --> and <!-- /work:NAME -->; everything else is hand-written.
# Every project has an English file (<slug>.json) and a Chinese one (<slug>.zh.json). The page carries both; CSS shows
# the one that matches <html lang>. Figures are drawn once per language (strings in work/_figs.zh.json).
import colorsys, html, json, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import figures  # noqa: E402

TIERS = ("major", "minor")
HEX = re.compile(r"^[0-9A-Fa-f]{6}$")


def die(msg):
    sys.exit(f"build.py: {msg}")


def load():
    specs = []
    for f in sorted((HERE / "work").glob("*.json")):
        if f.name.startswith("_") or f.name.endswith(".zh.json"):
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        zf = f.with_name(f.stem + ".zh.json")
        if not zf.is_file():
            die(f"{f.name}: needs a Chinese companion {zf.name}")
        d["zh"] = json.loads(zf.read_text(encoding="utf-8"))
        d["_file"] = f.name
        for k in ("slug", "name", "order", "tier", "kind", "summary"):
            if k not in d:
                die(f"{f.name}: missing '{k}'")
        d.setdefault("links", [])
        if d["tier"] not in TIERS:
            die(f"{f.name}: tier must be one of {TIERS}")
        if d["slug"] != f.stem:
            die(f"{f.name}: slug '{d['slug']}' must match the file name")
        for _, href in d["links"]:
            if not href.startswith("https://"):
                die(f"{f.name}: link {href!r} must be https")
        if d.get("tool"):
            ln = dict(d["links"])
            if "Live site" not in ln or not ln.get("Source", "").startswith("https://github.com/"):
                die(f"{f.name}: a tool needs a 'Live site' link and a GitHub 'Source' link")
            if "shot" not in d:
                die(f"{f.name}: a tool needs a 'shot'")
        if d["tier"] == "major" and not d["links"]:
            die(f"{f.name}: a major project needs at least one link")
        if d["tier"] == "minor" and "shot" in d:
            for key in ("src",):
                if not (ROOT / d["shot"][key]).is_file():
                    die(f"{f.name}: {d['shot'][key]} does not exist")
            if "w" not in d["shot"] or "h" not in d["shot"]:
                from PIL import Image
                with Image.open(ROOT / d["shot"]["src"]) as im:
                    d["shot"]["w"], d["shot"]["h"] = im.size
        if d["tier"] == "major":
            for k in ("shot", "hook", "built", "color"):
                if k not in d:
                    die(f"{f.name}: a major project needs '{k}'")
            if not all(HEX.match(c) for c in d["color"]) or len(d["color"]) != 2:
                die(f"{f.name}: color must be [body, rim] as 6-digit hex")
            sh = d["shot"]
            for key in ("src", "peek"):
                if key in sh and not (ROOT / sh[key]).is_file():
                    die(f"{f.name}: {sh[key]} does not exist")
            if "w" not in sh or "h" not in sh:
                from PIL import Image
                with Image.open(ROOT / sh["src"]) as im:
                    sh["w"], sh["h"] = im.size
            for pg in d.get("pages", []):
                if "fig" in pg and pg["fig"] not in figures.FIGS:
                    die(f"{f.name}: figure '{pg['fig']}' is not registered in docs/figures.py")
                if "fig" in pg and "caption" not in pg:
                    die(f"{f.name}: a page with a figure needs a 'caption'")
        check_zh(d)
        specs.append(d)
    slugs = [d["slug"] for d in specs]
    if len(set(slugs)) != len(slugs):
        die("duplicate slug")
    specs.sort(key=lambda d: (d["order"], d["slug"]))
    return specs


def esc(s):
    return html.escape(s, quote=False)


def attr(s):
    return html.escape(s, quote=False).replace('"', "&quot;")


def hue(hexs):
    r, g, b = (int(hexs[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return colorsys.rgb_to_hsv(r, g, b)[0] * 360


ZH_LINKS = {"Live site": "在线站点", "Source": "源码"}


def L(en, zh):
    """Both versions of a text; the page shows the one that matches <html lang>."""
    if not zh or zh == en:
        return en
    return f'<span class="en">{en}</span><span class="zh" lang="zh-CN">{zh}</span>'


def check_zh(d):
    """The Chinese companion must cover every field the page prints."""
    z, name = d["zh"], d["_file"]
    need = ["kind", "summary"] + (["hook"] if d["tier"] == "major" else [])
    if d.get("credit"):
        need.append("credit")
    for k in need:
        if not z.get(k):
            die(f"{name}: Chinese companion is missing '{k}'")
    if d["tier"] == "major":
        zp = z.get("pages", [])
        if len(zp) != len(d.get("pages") or []):
            die(f"{name}: Chinese companion needs {len(d.get('pages') or [])} pages, has {len(zp)}")
        for i, (pg, zq) in enumerate(zip(d.get("pages") or [], zp)):
            for key in ("title", "caption"):
                if key in pg and not zq.get(key):
                    die(f"{name}: page {i + 1} is missing Chinese '{key}'")
            if len(pg.get("notes", [])) != len(zq.get("notes", [])):
                die(f"{name}: page {i + 1} needs {len(pg.get('notes', []))} Chinese notes")
            if "extra_cap" in pg and not zq.get("extra_cap"):
                die(f"{name}: page {i + 1} is missing Chinese 'extra_cap'")


def link_row(links):
    return "".join(f'<a href="{attr(h)}" target="_blank" rel="noopener">{L(esc(t), ZH_LINKS.get(t, t))}</a>' for t, h in links)


def index_entries(specs):
    feat = [d for d in specs if d["tier"] == "major"]
    out = []
    for i, d in enumerate(feat):
        out.append(f'        <li><a href="#{d["slug"]}" data-i="{i}"><span class="nm">{esc(d["name"])}</span>'
                   f'<span class="ds">{L(d["summary"], d["zh"]["summary"])}</span><span class="kd">{L(esc(d["kind"]), esc(d["zh"]["kind"]))}</span></a></li>')
    return "\n".join(out)


STAR_SVG = ('<svg viewBox="0 0 16 16" width="15" height="15" aria-hidden="true" focusable="false"><path d="M8 1.2l2.1 4.5 4.9.6-3.6 3.4.9 4.9L8 12.2 3.7 14.6l.9-4.9L1 6.3l4.9-.6z" '
            'fill="currentColor" stroke="currentColor" stroke-width="1" stroke-linejoin="round"/></svg>')


def tool_cards(specs):
    """Toolbox: one card per live web tool, a thumbnail, one line, and two links (open it, star its repository)."""
    tools = sorted((d for d in specs if d.get("tool")), key=lambda d: d["tool"])
    out = []
    for d in tools:
        ln = dict(d["links"])
        live, src = ln["Live site"], ln["Source"]
        sh, name = d["shot"], esc(d["name"])
        img = f'<img src="{attr(sh["src"])}" width="{sh["w"]}" height="{sh["h"]}" alt="" loading="lazy" decoding="async">'
        out.append("        <li>")
        out.append(f'          <a class="tbx-shot" href="{attr(live)}" target="_blank" rel="noopener" tabindex="-1" aria-hidden="true">{img}</a>')
        out.append('          <div class="tbx-tx">')
        out.append(f"            <h3>{name}</h3>")
        out.append(f'            <p class="tbx-ds">{L(d["summary"], d["zh"]["summary"])}</p>')
        out.append('            <p class="tbx-go">')
        out.append(f'              <a class="open" href="{attr(live)}" target="_blank" rel="noopener">'
                   f'<span class="en">Open<span class="sr"> {name}</span></span><span class="zh" lang="zh-CN">打开<span class="sr"> {name}</span></span></a>')
        out.append(f'              <a class="star" href="{attr(src)}" target="_blank" rel="noopener">{STAR_SVG}'
                   f'<span class="en">Star<span class="sr"> {name} on GitHub</span></span><span class="zh" lang="zh-CN">点星<span class="sr"> {name}（GitHub）</span></span></a>')
        out.append("            </p>")
        out.append("          </div>")
        out.append("        </li>")
    return "\n".join(out)


def minor_block(specs):
    """Minor projects: small cards under the deck, a thumbnail beside one sentence and the links."""
    minor = [d for d in specs if d["tier"] == "minor"]
    if not minor:
        return ""
    out = ['    <div class="wrap minor">',
           '      <div class="shead"><h3 id="minor-h"><span class="en" data-split="char">Smaller projects</span><span class="zh" lang="zh-CN" data-split="char">其他小项目</span></h3></div>',
           '      <ul class="mini">']
    for d in minor:
        href = (dict(d["links"]).get("Live site") or d["links"][0][1]) if d["links"] else None
        out.append('        <li>' if "shot" in d else '        <li class="noshot">')
        if "shot" in d:
            sh = d["shot"]
            img = f'<img src="{attr(sh["src"])}" width="{sh["w"]}" height="{sh["h"]}" alt="{attr(sh.get("alt", ""))}" loading="lazy" decoding="async">'
            if href:   # a linked card hides its decorative link from screen readers; an unlinked one keeps the alt text
                img = img.replace(f'alt="{attr(sh.get("alt", ""))}"', 'alt=""')
                out.append(f'          <a class="mini-shot" href="{attr(href)}" target="_blank" rel="noopener" tabindex="-1" aria-hidden="true">{img}</a>')
            else:
                out.append(f'          <div class="mini-shot">{img}</div>')
        out.append('          <div class="mini-tx">')
        out.append(f'            <p class="mini-kd">{L(esc(d["kind"]), esc(d["zh"]["kind"]))}</p>')
        out.append(f'            <h4>{esc(d["name"])}</h4>')
        out.append(f'            <p class="mini-ds">{L(d["summary"], d["zh"]["summary"])}</p>')
        if d["links"]:
            out.append(f'            <p class="links">{link_row(d["links"])}</p>')
        if d.get("credit"):
            out.append(f'            <p class="mini-cr">{L(d["credit"], d["zh"]["credit"])}</p>')
        out.append("          </div>")
        out.append("        </li>")
    out += ['      </ul>', '    </div>']
    return "\n".join(out)


def notes_html(notes, zh_notes, k):
    if not notes:
        return [], k
    out = ["            <ul>"]
    for n, zn in zip(notes, zh_notes):
        out.append(f'              <li data-k style="--k:{k}">{L(n, zn)}</li>')
        k += 1
    out.append("            </ul>")
    return out, k


def tail_html(pg, zq, k, slug):
    out = []
    if pg.get("extra"):
        extra = pg["extra"].replace("{k}", str(k)).replace("{cap}", L(pg.get("extra_cap", ""), zq.get("extra_cap", "")))
        out.append("            " + extra)
        k += 1
    if pg.get("fig"):
        name = pg["fig"]
        out.append(f'            <figure class="fig" data-k style="--k:{k}"><!-- fig:{name} -->')
        out.append(figures.render(name, "en"))
        out.append(figures.render(name, "zh"))
        out.append(f'<!-- /fig:{name} --><figcaption>{L(pg["caption"], zq["caption"])}</figcaption></figure>')
        k += 1
    return out, k


def caps(specs):
    feat = [d for d in specs if d["tier"] == "major"]
    total = f"{len(feat):02d}"
    out = []
    for i, d in enumerate(feat):
        sh = d["shot"]
        side = "l" if i % 2 == 0 else "r"
        a = f'data-src="{attr(sh["src"])}"' + (f' data-thumb="{attr(sh["peek"])}"' if "peek" in sh else "")
        out.append(f'        <li class="cap {side}" id="{d["slug"]}" {a} data-c="{d["color"][0]}" data-f="{d["color"][1]}" style="--i:{i}">')
        out.append(f'          <figure class="cap-shot"><img src="{attr(sh["src"])}" width="{sh["w"]}" height="{sh["h"]}" '
                   f'alt="{attr(sh["alt"])}" loading="lazy" decoding="async"></figure>')
        pages = d.get("pages") or [{}]
        zpages = d["zh"].get("pages") or [{} for _ in pages]
        for p, (pg, zq) in enumerate(zip(pages, zpages)):
            out.append('          <div class="pg"><div class="pg-in">')
            if p == 0:
                # Letters per word; a long name wraps between words, never inside one
                words, c = [], 0
                for w in d["name"].split(" "):
                    words.append("".join(f'<span class="ch" style="--c:{c + j}">{esc(ch)}</span>' for j, ch in enumerate(w)))
                    c += len(w) + 1
                letters = " ".join(f'<span class="wd">{w}</span>' for w in words) if len(words) > 1 else words[0]
                out.append(f'            <p class="cap-n" data-k style="--k:0">{i + 1:02d} / {total} &middot; {L(esc(d["kind"]), esc(d["zh"]["kind"]))}</p>')
                out.append(f'            <h3 aria-label="{attr(d["name"])}"><span aria-hidden="true">{letters}</span></h3>')
                out.append(f'            <p class="hook" data-k style="--k:2">{L(d["hook"], d["zh"]["hook"])}</p>')
                out.append(f'            <p class="links" data-k style="--k:3">{link_row(d["links"])}</p>')
                out.append(f'            <p class="built" data-k style="--k:3">{L(d["built"], d["zh"].get("built"))}</p>')
                k = 4
            else:
                out.append(f'            <p class="pg-h" data-k style="--k:0"><b>{esc(d["name"])}</b> &middot; {L(esc(pg.get("title", "How it works")), esc(zq.get("title", "运作方式")))}</p>')
                k = 1
            lines, k = notes_html(pg.get("notes"), zq.get("notes", []), k)
            out += lines
            lines, k = tail_html(pg, zq, k, d["slug"])
            out += lines
            out.append("          </div></div>")
        out.append("        </li>")
    return "\n".join(out)


def pair_order(specs):
    """Constellation order: 'this site' first, then each project next to the one it shares most tools with."""
    site = json.loads((HERE / "work" / "_site.json").read_text(encoding="utf-8"))
    items = [("this site", site["stack"], site["data_sources"])]
    todo = [(d["name"], d.get("stack", []), d.get("data_sources", [])) for d in specs if d.get("stack")]
    while todo:
        last = set(items[-1][1])
        best = max(range(len(todo)), key=lambda j: (len(last & set(todo[j][1])), -j))
        items.append(todo.pop(best))
    return items


def stack_data(specs):
    items = pair_order(specs)
    lines = ",\n".join(f"  {json.dumps(n, ensure_ascii=False)}: {json.dumps(s, ensure_ascii=False)}" for n, s, _ in items)
    return '    <script type="application/json" id="stack-data">\n{\n' + lines + '\n}\n    </script>'


def sr_sentence(specs):
    items = pair_order(specs)
    data = {x for _, _, ds in items for x in ds}
    seen, tools, srcs = set(), [], []
    for _, stack, _ in items[1:] + items[:1]:
        for x in stack:
            if x in seen:
                continue
            seen.add(x)
            (srcs if x in data else tools).append(x)
    en = f"Tools used in these projects: {', '.join(tools)}. Data sources: {', '.join(srcs)}."
    zh = f"这些项目用到的工具：{'、'.join(tools)}。数据来源：{'、'.join(srcs)}。"
    return L(en, zh)


def readme_list(specs):
    return "\n".join(f"- [{d['slug']}]({d['repo']}): {d['blurb']}" for d in specs if d.get("repo"))


def splice(text, name, body, inline=False):
    a, b = f"<!-- work:{name} -->", f"<!-- /work:{name} -->"
    i, j = text.find(a), text.find(b)
    if i < 0 or j < 0 or j < i:
        die(f"markers for region '{name}' not found")
    if inline:
        return text[:i + len(a)] + body + text[j:]
    indent = text[text.rfind("\n", 0, j) + 1:j]
    return text[:i + len(a)] + ("\n" + body if body else "") + "\n" + indent + text[j:]


def check_palette(specs):
    feat = [d for d in specs if d["tier"] == "major"]
    for a, b in zip(feat, feat[1:]):
        dh = abs(hue(a["color"][0]) - hue(b["color"][0]))
        dh = min(dh, 360 - dh)
        if dh < 40:
            print(f"warning: {a['slug']} and {b['slug']} are neighbours with similar colours ({dh:.0f} degrees apart)")


def main():
    specs = load()
    check_palette(specs)
    page, readme = ROOT / "index.html", ROOT / "README.md"
    s = page.read_text(encoding="utf-8")
    s = splice(s, "index", index_entries(specs))
    s = splice(s, "caps", caps(specs))
    s = splice(s, "minor", minor_block(specs))
    s = splice(s, "tools", tool_cards(specs))
    s = splice(s, "stack", stack_data(specs))
    s = splice(s, "sr", sr_sentence(specs), inline=True)
    r = readme.read_text(encoding="utf-8")
    r = splice(r, "readme", readme_list(specs))
    if "--check" in sys.argv:
        stale = [p.name for p, new in ((page, s), (readme, r)) if p.read_text(encoding="utf-8") != new]
        if stale:
            die("out of date: " + ", ".join(stale) + " (run python docs/build.py)")
        print("up to date")
        return
    page.write_text(s, encoding="utf-8", newline="\n")
    readme.write_text(r, encoding="utf-8", newline="\n")
    feat = sum(d["tier"] == "major" for d in specs)
    print(f"built {feat} major + {len(specs) - feat} minor")


main()
