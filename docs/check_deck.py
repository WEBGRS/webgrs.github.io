# Smoke-test the work deck: turn every page, then look at the stack constellation, and report console
# errors. Needs Playwright with Chromium.
#   python docs/check_deck.py [--shots DIR] [--url URL] [--theme dark] [--lang zh] [--size 390x844]
import argparse, pathlib, sys
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--shots", help="save a screenshot of every page into this folder")
ap.add_argument("--url", default=(ROOT / "index.html").as_uri())
ap.add_argument("--theme", default="light")
ap.add_argument("--lang", default="en", choices=["en", "zh"])
ap.add_argument("--size", default="1440x900")
a = ap.parse_args()
W, H = map(int, a.size.split("x"))
# ?fx=2 keeps the WebGL tier on a software GPU; ?lab exposes filmGo() and filmState()
URL = a.url + ("&" if "?" in a.url else "?") + "fx=2&lab"
ARGS = ["--lang=en-US", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]
shots = pathlib.Path(a.shots) if a.shots else None
if shots:
    shots.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=ARGS)
    pg = b.new_page(viewport={"width": W, "height": H}, locale="en-US")
    problems = []
    pg.on("console", lambda m: problems.append(f"console {m.type}: {m.text}") if m.type in ("error", "warning") else None)
    pg.on("pageerror", lambda e: problems.append(f"pageerror: {e}"))
    pg.on("requestfailed", lambda r: problems.append(f"request failed: {r.url}"))
    pg.add_init_script(f"localStorage.setItem('theme', '{a.theme}'); localStorage.setItem('lang', '{a.lang}'); sessionStorage.setItem('intro', '1')")
    pg.goto(URL)
    pg.wait_for_timeout(3500)
    pg.evaluate("scrollTo({top: document.getElementById('film').getBoundingClientRect().top + scrollY, behavior: 'instant'})")
    pg.wait_for_timeout(3500)
    if not pg.evaluate("typeof filmState === 'function'"):
        print("deck is not live (plain-list fallback); nothing to page through")
    else:
        P = pg.evaluate("filmState().P")
        names = pg.evaluate("[...document.querySelectorAll('.film .pg')].map(p => (p.querySelector('h3') ? p.querySelector('h3').getAttribute('aria-label') : p.querySelector('.pg-h b').textContent) + (p.querySelector('h3') ? '' : ' (notes)'))")
        print(f"{P} pages, {pg.evaluate('document.querySelectorAll(\".film .cap\").length')} projects")
        for i in range(P):
            pg.evaluate(f"filmGo({i})")
            pg.wait_for_timeout(2600)
            st = pg.evaluate("filmState()")
            ok = st["cur"] == i and not st["tr"]
            fit = pg.evaluate("[...document.querySelectorAll('.film .pg.on .pg-in')].every(e => e.offsetHeight <= e.parentElement.clientHeight + 2)")
            print(f"  {i + 1:>2}. {names[i]:<28} {'ok' if ok else 'NOT SETTLED'}  {'fits' if fit else 'OVERFLOWS'}")
            if not ok: problems.append(f"page {i} did not settle: {st}")
            if not fit: problems.append(f"page {i} ({names[i]}) overflows its column")
            if shots:
                pg.screenshot(path=str(shots / f"page-{i + 1:02d}.png"), timeout=120000)
    pg.evaluate("scrollTo({top: document.getElementById('now').getBoundingClientRect().top + scrollY - 80, behavior: 'instant'})")
    pg.wait_for_timeout(3000)
    if shots:
        pg.screenshot(path=str(shots / "stack.png"), timeout=120000)
    more = pg.evaluate("document.querySelectorAll('.mini li').length")
    print(f"minor cards: {more}")
    b.close()

# The effects-tier line the page logs on load is information, not a problem
problems = [x for x in problems if "WebGL" not in x or "GPU stall" not in x]
for x in problems:
    print("PROBLEM:", x)
print("OK" if not problems else f"{len(problems)} problem(s)")
sys.exit(len(problems))
