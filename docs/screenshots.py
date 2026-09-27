# Regenerate README screenshots of the site
import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=["--lang=en-US"])
    for theme in ["light", "dark"]:
        page = b.new_page(viewport={"width": 1440, "height": 900}, locale="en-US", color_scheme=theme)
        # Dark is opt-in via the toggle, stored in localStorage
        page.add_init_script(f"localStorage.setItem('theme', '{theme}'); sessionStorage.setItem('intro', '1')")
        page.goto((ROOT / "index.html").as_uri())
        # Wait for the terrain reveal and intro to finish
        page.wait_for_timeout(3500)
        page.screenshot(path=str(OUT / f"{theme}.png"), full_page=False)
        page.close()
        if theme == "light":
            # Case study with its figure drawn in
            page = b.new_page(viewport={"width": 1440, "height": 900}, locale="en-US")
            page.add_init_script("sessionStorage.setItem('intro', '1')")
            page.goto((ROOT / "index.html").as_uri())
            page.wait_for_timeout(1500)
            page.evaluate("scrollTo({top: document.getElementById('datamap').getBoundingClientRect().top + scrollY, behavior: 'instant'})")
            page.wait_for_timeout(2500)
            page.screenshot(path=str(OUT / "work.png"), full_page=False)
            page.close()
    b.close()

# Shrink PNGs
from PIL import Image
for f in OUT.glob("*.png"):
    Image.open(f).convert("RGB").save(f.with_suffix(".jpg"), quality=85, optimize=True)
    f.unlink()
print("saved to", OUT)
