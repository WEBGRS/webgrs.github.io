# Regenerate the README screenshots: the hero in both themes, three pages of the work section,
# the contact section, and three phone screens side by side. Needs Playwright with Chromium;
# WebGL runs on SwiftShader headless.
import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs"
# ?fx=2 keeps the WebGL tier on a software GPU; ?lab exposes filmGo() for turning pages
URL = (ROOT / "index.html").as_uri() + "?fx=2&lab"
ARGS = ["--lang=en-US", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]


def page(b, theme):
    pg = b.new_page(viewport={"width": 1440, "height": 900}, locale="en-US")
    # Dark is opt-in via the toggle, stored in localStorage; skip the once-per-session intro
    pg.add_init_script(f"localStorage.setItem('theme', '{theme}'); sessionStorage.setItem('intro', '1')")
    pg.goto(URL)
    pg.wait_for_timeout(4000)
    return pg


def shot(pg, name):
    pg.screenshot(path=str(OUT / f"{name}.jpg"), type="jpeg", quality=84, timeout=120000)


def to(pg, el_id, extra=0):
    pg.evaluate(f"scrollTo({{top: document.getElementById('{el_id}').getBoundingClientRect().top + scrollY + {extra}, behavior: 'instant'}})")


with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=ARGS)
    for theme in ["light", "dark"]:
        pg = page(b, theme)
        shot(pg, theme)
        pg.close()
    # Work section: an overview page, a how-it-works page, and a project in the dark theme
    pg = page(b, "light")
    to(pg, "film"); pg.wait_for_timeout(6000)
    shot(pg, "work-overview")
    pg.evaluate("filmGo(1)"); pg.wait_for_timeout(6000)
    shot(pg, "work-notes")
    # Contact: click once so the particles gather into the word
    to(pg, "contact"); pg.wait_for_timeout(2500)
    box = pg.locator("#dust").bounding_box()
    pg.mouse.click(box["x"] + 40, box["y"] + box["height"] - 40); pg.mouse.move(5, 5)
    pg.wait_for_timeout(4000)
    shot(pg, "contact")
    pg.close()
    pg = page(b, "dark")
    to(pg, "film"); pg.wait_for_timeout(5000)
    pg.evaluate("filmGo(2)"); pg.wait_for_timeout(6000)
    shot(pg, "work-dark")
    pg.close()
    # Phone: three screens side by side (hero, a project in the one-column list, contact)
    from PIL import Image
    ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True, locale="en-US")
    pg = ctx.new_page()
    pg.add_init_script("localStorage.setItem('theme', 'light'); sessionStorage.setItem('intro', '1')")
    pg.goto(URL); pg.wait_for_timeout(4000)
    frames = []
    for el, extra in [(None, 0), ("uw-course-lookup", -24), ("contact", 0)]:
        if el: to(pg, el, extra); pg.wait_for_timeout(3000)
        pg.screenshot(path=str(OUT / "_m.png"), timeout=120000); frames.append(Image.open(OUT / "_m.png").convert("RGB").resize((390, 844)))
    (OUT / "_m.png").unlink()
    sheet = Image.new("RGB", (390 * 3 + 40 * 2, 844), (255, 255, 255))
    for i, f in enumerate(frames): sheet.paste(f, (i * 430, 0))
    sheet.save(OUT / "mobile.jpg", quality=84)
    ctx.close()
    b.close()
print("saved to", OUT)
