# webgrs.github.io

H. Gu's portfolio site, live at **<https://webgrs.github.io>**. It's a single `index.html`: no framework, no build step, no analytics. The one outside request is the Archivo typeface from Google Fonts.

![The hero in the light theme: a contour map of Madison with the name over it](docs/light.jpg)

<details><summary>Dark theme</summary>

![The hero in the dark theme](docs/dark.jpg)

</details>

## What's on the page

| Section | What it shows |
|---|---|
| Hero | A contour map of Madison drawn from real elevation data, with the name and a one-line intro |
| Selected work | Six projects, each with its screenshot, notes and a figure of how it works |
| Decisions I'd defend | Three engineering calls from those projects |
| Stack and Now | The tools and data sources, linked by project; what's happening this term |
| Contact | Email and GitHub, with the two lakes redrawn as particles |

### Hero

The map is traced from USGS 3DEP elevation (via Terrain Tiles on AWS) at a 5 m contour interval. Marching squares runs in a worker on an OffscreenCanvas, and the map reveals outward from campus. The contour under the pointer lights up in a soft patch that spreads slowly; on the WebGL tier the contours 5 m above and below light up with it, fainter. Hovering also reads out coordinates and elevation.

Once per session a short loader plays first: five real contour lines of a hill northwest of Madison (43.132° N, 89.512° W, 337 m), drawn stroke by stroke while fonts and terrain load.

### Selected work

![route-animator's overview page: notes and a dotted globe on the left, the screenshot on the right with a teal orb behind it](docs/work-overview.jpg)

The index lists the six projects. Hovering one shows its screenshot beside the cursor, with edges that ripple while the picture inside stays still.

Below the index the projects become pages on one pinned stage: an overview with links and what it's built with, then the decisions behind it and a figure of how it works. Route-animator and photo-organizer have enough to say for two pages; the rest fit on one. Every page uses the same type scale, the largest at which all of them fit.

![route-animator's second page: three points and the altitude figure](docs/work-notes.jpg)

Paging works like slides. One wheel notch, key press or swipe plays the whole turn and holds the rest of the gesture until it goes quiet, so a transition never stops halfway; dragging the scrollbar lands on the nearest page. Between projects the screenshot glides to the other side while the next one dissolves in over it. Within a project only the notes change. The blocks of each page arrive in turn: the title letter by letter, then the summary, links, each point, and the figure, which draws itself in.

Behind the screenshot sits a translucent liquid orb in a different colour for each project. It's drawn flat, a distance field with a rippling edge lit as if it were a sphere, so it costs little. With every project it swings to its next place and the new colour washes across it from the side it's heading to. A small droplet orbits it and merges with it now and then, and a few motes circle it on tilted orbits with fading trails, speeding up while it travels and easing off after.

![uw-course-lookup in the dark theme, with a red orb behind the screenshot](docs/work-dark.jpg)

### Contact

![The contact section: the email address, mail and GitHub buttons, and particles forming the word hello](docs/contact.jpg)

Lake Mendota and Lake Monona return as particles on springs. Every few seconds they sweep into the word "hello" and back, changing from water blue to ink, but never while the pointer is over them or for ten seconds after a click. The pointer pushes them aside and a click switches the shape. Clicking the address copies it.

### Behind the page

The terrain continues behind everything as a faint sheet that scrolls slower than the content (a ScrollTimeline, so it moves on the compositor), and fades out while the work pages fill the screen. Elsewhere: the stack as a constellation in which tools used by the same project are linked, a raymarched liquid sphere half past the edge of the Now list, and a sine-wave signal line above the footer.

## Performance and accessibility

The page picks an effects tier on load and logs the choice and the reason to the console:

| Tier | What runs | Chosen when |
|---|---|---|
| 2 | WebGL map and effects | the default |
| 1 | Canvas 2D | 4 or fewer CPU threads or 4 GB or less memory, or a software GPU |
| 0 | Static | reduced motion, Save-Data, or 2 or fewer threads or 2 GB or less memory |

`?fx=0`, `?fx=1` or `?fx=2` forces a tier. Every decorative canvas draws only while it's on screen, and canvases on work pages that aren't showing stop drawing. With `prefers-reduced-motion`, or in a window narrower than 900 px or shorter than 560 px, the work section becomes a plain list with the same content. Screen readers get plain-text copies of the animated headings. Secondary text is never grey; it's set in the ink colour and told apart by size and weight.

## Projects shown

- [route-animator](https://github.com/WEBGRS/route-animator): satellite-globe route videos in the browser
- [uw-course-lookup](https://github.com/WEBGRS/uw-course-lookup): UW–Madison course lookup, linking to MadGrades and Rate My Professors
- [photo-organizer](https://github.com/WEBGRS/photo-organizer): offline CLIP photo sorter
- [datamap](https://github.com/WEBGRS/datamap): paste data, get a choropleth map
- [geo-spoof](https://github.com/WEBGRS/geo-spoof): Chrome extension that overrides the Geolocation API
- [tophat-watch](https://github.com/WEBGRS/tophat-watch): Chrome extension that alerts when a Top Hat question opens

## Run locally

```sh
git clone https://github.com/WEBGRS/webgrs.github.io
cd webgrs.github.io
python -m http.server 8792
```

Then open <http://localhost:8792>. Opening `index.html` straight from disk works too, except the hover preview, which falls back to a plain box because WebGL can't read `file:` images.

## Scripts

| Script | What it does |
|---|---|
| `docs/screenshots.py` | Rebuilds the images in this README (Playwright with Chromium) |
| `docs/figures.py` | Redraws the how-it-works figures and writes them into `index.html` |
| `docs/terrain/build_terrain.py` | Re-fetches the elevation tiles and rewrites the terrain data embedded in `index.html` |
| `docs/land/build_land.py` | Rebuilds the 1° land mask for the route-animator globe |

## Credits

Motion patterns borrowed from Olivier Larose's [awwwards-landing-page](https://github.com/olivierlarose/awwwards-landing-page) (hover preview), [Lenis](https://github.com/darkroomengineering/lenis) (the `damp` function), Emil Kowalski's [animation tips](https://emilkowal.ski/ui/7-practical-animation-tips), and Vercel's [Web Interface Guidelines](https://github.com/vercel-labs/web-interface-guidelines). Some of the decorative effects started from a local gallery of motion studies.
