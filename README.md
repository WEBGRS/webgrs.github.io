# webgrs.github.io

Personal portfolio site: **<https://webgrs.github.io>**

![Portfolio site, light theme](docs/light.jpg)

![DataMap's case study on its band, with the screenshot and a figure of its color ramps](docs/work.jpg)

<details><summary>Dark theme</summary>

![Portfolio site, dark theme](docs/dark.jpg)

</details>

One `index.html` plus project screenshots in `assets/`; no framework, trackers, or build step. It opens in the light theme; a toggle switches to dark and remembers the choice.

- **Intro:** once per session, a loader over a pale aurora shader. The mark is five real contour lines of a hill northwest of Madison (43.132 N, 89.512 W, 337 m) drawn stroke by stroke; the percentage follows fonts, terrain decoding and the first map paint, then the sheet slides away.
- **Hero:** a contour map of Madison drawn from real USGS 3DEP elevation data (5 m interval, marching squares in a worker on an OffscreenCanvas), revealed outward from campus. The contour under the pointer lights up in a soft patch that widens slowly and follows the pointer; on the WebGL tier the contours 5 m above and below light up with it, fainter. When the level changes the old patch shrinks back where it stands. Hovering also reads out coordinates and elevation, and a north arrow draws itself in the legend.
- **Effects tier:** 2 (WebGL), 1 (canvas) or 0 (lite), chosen from CPU threads, device memory, save-data, reduced motion and the GPU; a software GPU falls back to canvas. The console logs the tier and why. `?fx=0`, `?fx=1` or `?fx=2` forces a tier.
- **Work index:** hovering a project shows its screenshot in a slowly morphing blob beside the cursor, following it with frame-rate independent damping, while a stroke wave runs through the name.
- **Case studies:** a different layout for each project (a wide feature, text-left, image-left, a full-bleed band and a pair of cards), each with its own scroll-timeline entrance and a pointer tilt on the screenshot. Every project has a small figure of how it works, drawn from its own code. route-animator also gets a dotted globe with the route from its screenshot flown by a small plane.
- **Background:** the same terrain continues behind the page as a faint sheet that scrolls slower than the content. Behind the decisions, particles run downhill over the real terrain; the tools and data sources are a constellation in which anything used by the same project is linked; a small raymarched liquid sphere sits by the Now list; a sine-wave signal line sits above the footer.
- **Type:** the name rises letter by letter while Archivo's width axis opens from 62% to 125%. Headings arrive letter by letter with a slight turn and blur, paragraphs word by word, and the email address drops in. Screen readers get the plain text from a hidden copy.
- **Contact:** Lake Mendota and Lake Monona again, as particles on springs, which turn into the word "hello" and back. The pointer pushes them aside; a click switches the shape.
- Motion respects `prefers-reduced-motion`, and every decorative canvas runs only while it is on screen.

Motion patterns borrowed from Olivier Larose's [awwwards-landing-page](https://github.com/olivierlarose/awwwards-landing-page) (hover preview), [Lenis](https://github.com/darkroomengineering/lenis) (the `damp` function), Emil Kowalski's [animation tips](https://emilkowal.ski/ui/7-practical-animation-tips), and Vercel's [Web Interface Guidelines](https://github.com/vercel-labs/web-interface-guidelines). Some of the decorative effects started from a local gallery of motion studies.

## Projects linked

- [route-animator](https://github.com/WEBGRS/route-animator): satellite-globe route videos in the browser
- [uw-course-lookup](https://github.com/WEBGRS/uw-course-lookup): UW–Madison course lookup, linking to MadGrades and Rate My Professors
- [photo-organizer](https://github.com/WEBGRS/photo-organizer): offline CLIP photo sorter
- [datamap](https://github.com/WEBGRS/datamap): paste data, get a choropleth map
- [geo-spoof](https://github.com/WEBGRS/geo-spoof): Chrome extension that overrides the Geolocation API
- [tophat-watch](https://github.com/WEBGRS/tophat-watch): Chrome extension that alerts when a Top Hat question opens

## Run locally

Open `index.html` in a browser. `python docs/screenshots.py` rebuilds the images above. `python docs/figures.py` redraws the case-study figures. `python docs/terrain/build_terrain.py` re-fetches the elevation tiles and rewrites the terrain data embedded in `index.html`.
