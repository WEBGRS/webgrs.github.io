# Regenerate README screenshots of the site
import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=["--lang=en-US"])
    for theme in ["light", "dark"]:
        page = b.new_page(viewport={"width": 1200, "height": 800}, locale="en-US", color_scheme=theme)
        page.goto((ROOT / "index.html").as_uri())
        page.evaluate("document.querySelectorAll('.rv').forEach(e => e.classList.add('in'))")
        page.wait_for_timeout(1500)
        page.screenshot(path=str(OUT / f"{theme}.png"), full_page=True)
        page.close()
    b.close()

# Shrink PNGs
from PIL import Image
for f in OUT.glob("*.png"):
    Image.open(f).convert("RGB").save(f.with_suffix(".jpg"), quality=85, optimize=True)
    f.unlink()
print("saved to", OUT)
