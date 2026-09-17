# Pixelart Maker

Single-file browser PWA that turns a grid of shapes into pixel art — converted from an
uploaded image, or sampled live from the camera. No build step, no dependencies,
no framework. Open `index.html` and it runs.

## Running locally

A plain file:// open works for most things, but the service worker and camera need a real origin:

```bash
python3 -m http.server 8000     # then open http://localhost:8000
```

Camera (Live mode) requires `localhost` or HTTPS. On the deployed site the SW caches
aggressively — `?nosw=1` / the reset helper in the INIT section clears it.

## Layout of the repo

| Path | What it is |
|---|---|
| `index.html` | **The entire app** — 3278 lines: CSS (44–1346), markup (1349–1474), JS (1475–3276) |
| `frame.html` | Phone-shaped shell (see below). Not the app — just an `<iframe>` + centering CSS |
| `sw.js` | Service worker. Network-first for navigation, cache-first for assets |
| `manifest.json` | PWA manifest |
| `docs/index.html` | Redirect stub to `../index.html` (GitHub Pages) |
| `color pallete/` | 21 reference PNG palettes — source material only, **not loaded at runtime** |
| `palette_list/` | **Live-loaded** palette source (see below) — the opposite of `color pallete/` |
| `icon.svg`, `camera-switch.svg`, `ratio_icon.png` | Icons |
| `APP_STORES.md`, `ICON_INSTRUCTIONS.md` | Hebrew notes on store packaging + home-screen icons |
| `.tmp_pillow/` | 38MB of vendored numpy/Pillow from a one-off icon script. Gitignored, unused |

## Map of index.html

Everything lives in one `<script>`. Banner comments (`// ═══ NAME`) mark the sections:

- **1496 `tracePath`** — draws a cell. Cells are always square now (shape picker and the
  bezier "Custom Shape" editor were removed); it just does `ctx.rect(...)`.
- **1506 `state`** — the single mutable object holding everything. `state.cells[r][c]` is a
  hex color string or `null` for empty. `state.mode` is `'image' | 'live'`.
- **1530 GRID CANVAS** — `cellLayout()` computes square cells centered in the canvas;
  `drawGridToContext()` is the one renderer used by screen, hi-res export and video frames.
  In Live mode this is a **cover** fit (fills the screen, crops overflow — no white margins);
  Breakpoints: `BP_MOBILE = 700`, `BP_TABLET = 1024`.
- **1739 CONTROLS WIRING** — all DOM event binding.
- **~1840 palettes** — `BRAND_PALETTE_ALL`, `PALETTE_PRESETS`, `PALETTE_LABELS`. `PALETTE_PRESETS`
  starts with hardcoded hex arrays transcribed from `color pallete/*.png`, curated down to ones
  that render photos/live camera clearly (currently: Moldy, SLSO8, Chasm, Citrink, Eulbink,
  Gothic, Pollen8, PSPixel, Vanilla, 31) — several presets that shipped in the PNGs were
  deliberately dropped for being too low-contrast, too narrow in hue, or missing a dark/light
  anchor. **Ask before adding one back or removing one of these ten** — they're hand-picked,
  not folder-driven.
  `loadFolderPalettes()` (near INIT) then fetches `palette_list/manifest.json` and merges its
  entries into the same `PALETTE_PRESETS`/`PALETTE_LABELS` objects, so the palette bar always
  shows built-ins + whatever `palette_list/` currently has — see the "Live palette folder"
  section below. Never hand-edit that merge to add/remove a specific palette; add/remove the
  PNG and regenerate instead.
- **~2010 EXPORT / EXPORT PREVIEW** — hi-res re-render at export size, preview modal,
  PNG + video download. Exports are plain — no title/date/credit frame around them (removed).
- **2252 LIVE CAMERA** — getUserMedia (video + audio), per-breakpoint constraints,
  aspect-ratio cycling, `liveLoop()` sampling frames into the grid, MediaRecorder video capture
  (recorded video includes the mic audio track when permission is granted).
  **Zoom** is a curved drag-to-scrub dial (`#mob-zoom-dial`, an SVG arc — geometry constants
  `ZOOM_DIAL_*`, `zoomValueToAngle`/`zoomAngleToValue`/`zoomAnglePoint`), styled after a phone
  camera's zoom ruler, not a plain slider — don't replace it with an `<input type=range>`.
  **Swiping left/right on the viewfinder** (in Live mode only) toggles `state.captureMode`
  between image/video, same as the `#mob-capture-mode` button — both go through
  `setCaptureMode()`, so wire any future mode-switch entry point through that too.
- **2816 / 2919 MOBILE** — drawer panel and camera buttons. The panel (`#panel.panel-open`)
  is `z-index: 200` — deliberately above every floating control (zoom, shutter, download,
  mode header) so it's never partially hidden behind them, in both Upload and Live.
- **3092 INIT** — defaults to Live mode on load (starts the camera immediately).

There is no Draw (freehand paint) mode — only **Upload** (image) and **Live** (camera). It was
removed; don't reintroduce brush/undo/reference-image code without being asked. There is also no
shape picker, no custom-shape bezier editor, and no grid rotation control — cells are always an
unrotated square. The Upload drop zone (`#upload-zone`) lives inside `#main`, overlaying the
canvas itself (shown only in Upload mode with no photo loaded yet) — not in the side panel.

## Phone-only format

The app is meant to always look and behave like it's on a phone, even in a desktop browser.
This is done with a redirect, not by rewriting the app's own responsive CSS:

- A tiny inline script at the very top of `index.html`'s `<head>` checks: is this the
  top-level window (`window.self === window.top`), is it NOT already the embedded instance
  (no `?pmFrame=1` in the query), and is `window.innerWidth > 700` (wider than `BP_MOBILE`)?
  If all three, it does `location.replace('frame.html' + location.search + location.hash)`.
- `frame.html` is a small static shell: a dark centered page with a phone-shaped `#pm-frame`
  box (`width: min(420px, 100vw, calc(95dvh * 9 / 19.5))`, `aspect-ratio: 9/19.5`) containing
  an `<iframe>` whose `src` is `index.html?pmFrame=1` (plus the original query/hash).
- Inside that iframe, `index.html` sees `?pmFrame=1` and skips the redirect, rendering itself
  normally — but because the iframe itself is phone-width, `window.innerWidth` genuinely is
  ≤420 there, so every existing mobile media query and `getLayoutMode()` check fires exactly
  as it would on a real phone. No changes were made to the app's own breakpoint logic.
- On a real phone, `window.innerWidth` is already ≤700, so the redirect never fires — the app
  renders index.html directly, full-screen, exactly as before this feature existed.
- Net effect: **tablet and desktop layout code in `index.html` (`isTabletLayout()`,
  `isDesktopLayout()`, `getLayoutMode() === 'desktop'` branches, the `@media` blocks above
  700px) is still there but effectively unreachable** through normal navigation — nothing was
  deleted, since ripping out three-way breakpoint logic wasn't the goal, just always showing
  the mobile one. Don't be surprised if you find dead-looking desktop/tablet branches; they're
  harmless leftovers, not bugs.
- `frame.html` doesn't register the service worker or link the manifest — it's a presentation
  shell, not something meant to be installed. Only `index.html` (loaded on a real phone) is
  the installable PWA.

## Live palette folder (`palette_list/`)

The user drops palette PNGs (standard lospec.com export: a single row of N equal-width square
swatches, e.g. a 12-color palette at 32px/swatch is 384×32) into `palette_list/`, and the app's
palette bar is supposed to reflect exactly what's in that folder — add a file, get a button;
delete a file, lose the button — without anyone touching `index.html`.

Since this is a static site (GitHub Pages / Netlify, no server-side code), the browser can't list
a folder's contents on its own. The mechanism:

- **`palette_list/build_manifest.py`** scans `palette_list/*.png`, and for each one sample the
  center pixel of every swatch (swatch size = image height; color count = width ÷ height) to get
  its hex colors, then writes `palette_list/manifest.json` — an array of
  `{key, label, file, colors}`, one entry per PNG currently in the folder, nothing else.
  **Run this (`python3 palette_list/build_manifest.py`) every time a PNG is added or removed** —
  it's the one manual step; everything downstream is automatic. It uses PIL (`from PIL import
  Image`), already available in this environment.
- `index.html`'s `loadFolderPalettes()` (near INIT, after the built-in `renderPresetBar()` call)
  fetches that `manifest.json` at load (`cache: 'no-store'`) and merges each entry straight into
  `PALETTE_PRESETS`/`PALETTE_LABELS`, then re-renders the preset bar. A palette that isn't in the
  manifest was, by construction, not in the folder when it was last generated — it just won't be
  merged in, which is the whole point (no per-palette code to write or delete).
- If the fetch fails (offline, blocked, opened via `file://`) it fails silently and the app just
  shows the ten built-ins — never let a broken/missing manifest break the rest of the app.
- The PNGs themselves are never fetched by the running app (like `color pallete/`, they're source
  material for the script only) — only the generated `manifest.json` is loaded at runtime.
- The palette bar (`.palette-presets`) is a fixed 4-column grid so every button — built-in or
  folder-sourced, short label or long — is exactly the same size; long labels clip with an
  ellipsis (`title` attribute still carries the full name) rather than resizing their button.
- The ten built-in palettes in `PALETTE_PRESETS` are separate and unaffected by any of this —
  they're not sourced from `palette_list/`, don't touch them for this feature.

## Conventions that matter here

- **One file.** New features go inline in `index.html`, in the section they belong to. Don't
  split into modules or add a bundler unless explicitly asked.
- **`state` is the source of truth.** Mutate it, then call `renderGrid()`. There's no undo
  system — Upload/Live both regenerate `state.cells` wholesale from the source (image or
  camera frame) rather than mutating individual cells.
- **No persistence.** There is no localStorage; a reload is a clean slate. Intentional.
- **Bump `CACHE` in `sw.js`** (currently `pixel-maker-v55`) on any deploy, or returning
  users keep the old `index.html`.
- **The app's CSS/JS still has three layout code paths** (mobile / tablet / desktop —
  panel behavior, Live preview fill cover vs contain) but **only mobile is reachable** in
  normal use, because of the phone-only redirect above. Don't spend effort fixing
  tablet/desktop-only bugs unless asked; do keep the mobile path working.
- **iOS quirks are deliberate.** The explicit text-color overrides on buttons exist because
  iOS tints them blue; the `-webkit` bits and `isIOSSafari()` branches are load-bearing.
- Hebrew appears in comments and docs. UI strings are English.

## Git

Three remotes point at three GitHub repos: `origin` → `pixelmakegrid` (the live one),
plus `pixelart` and `pixelmaker`. Deployed at
`https://shakedkleter92-ux.github.io/pixelmakegrid/` and on Netlify.
Work on `main` unless told otherwise.
