# Write the chosen wordmark into index.html: hero h1, header mark and intro.
# Other variants stay in build.py; change FINAL and rerun to swap.
# Reads <FINAL>.svg.html written by build.py, so it needs no geometry libraries.
import pathlib, re

HERE = pathlib.Path(__file__).parent
PAGE = HERE.resolve().parents[1] / "index.html"
FINAL = "a"
s = PAGE.read_text(encoding="utf-8")
art = (HERE / f"{FINAL}.svg.html").read_text(encoding="utf-8").strip()
small = art.replace('<svg class="wm"', '<svg class="wm-s"', 1)

s, n1 = re.subn(r'(<h1 id="name" aria-label="H\. Gu"><span class="mask"><span class="l" style="--i:0">).*?(</span></span></h1>)',
                lambda m: m.group(1) + art + m.group(2), s, flags=re.S)
s, n2 = re.subn(r'(<a class="mark" href="#top" aria-label="H\. Gu">).*?(</a>)', lambda m: m.group(1) + small + m.group(2), s, flags=re.S)
s, n3 = re.subn(r'(<p class="intro-t" aria-label="H\. Gu">).*?(</p>)', lambda m: m.group(1) + small + m.group(2), s, flags=re.S)
assert (n1, n2, n3) == (1, 1, 1), (n1, n2, n3)
# Variant picker and its plumbing, if an earlier run left them
s = re.sub(r'<nav class="wm-pick".*?</nav>\n?', "", s, flags=re.S)
s = re.sub(r"/\* wm:variants \*/.*?/\* /wm:variants \*/\n?", "", s, flags=re.S)
s = re.sub(r"\n  var wmv = '[a-z]', wq = [^\n]*", "", s)
s = re.sub(r"\.wmv\{display:none\}\n", "", s)
s = re.sub(r"\.wm-pick[^\n]*\n", "", s)
s = re.sub(r":root\.pick \.wm-pick[^\n]*\n", "", s)
PAGE.write_text(s, encoding="utf-8")
print("embedded", FINAL)
