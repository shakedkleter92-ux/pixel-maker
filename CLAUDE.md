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
aggressively — open `?__sw_reset=1` once to force-unregister it and clear all caches (or run
`forceAppUpdate()` from Safari's console). The `__BUILD`/`__SW_URL` version strings near INIT
and `sw.js`'s `CACHE` constant should all be bumped together on every deploy-worthy change —
Safari in particular won't reliably notice `sw.js` changed otherwise.

## Layout of the repo

| Path | What it is |
|---|---|
| `index.html` | **The entire app** — ~3980 lines: CSS (44–~1750), markup (~1750–~1850), JS (~1850–3978) |
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

- **1755 `tracePath`** — draws a cell. Cells are always square now (shape picker and the
  bezier "Custom Shape" editor were removed); it just does `ctx.rect(...)`.
- **1765 `state`** — the single mutable object holding everything. `state.cells[r][c]` is a
  hex color string or `null` for empty. `state.mode` is `'image' | 'live'`; `state.captureMode`
  (Live only) is `'image' | 'video'` — yes, two different things both called "image", be careful.
- **1787 GRID CANVAS** — `cellLayout()` computes square cells centered in the canvas;
  `drawGridToContext()` is the one renderer used by screen, hi-res export and video frames.
  In Live mode this is a **cover** fit (fills the screen, crops overflow — no white margins);
  Breakpoints: `BP_MOBILE = 700`, `BP_TABLET = 1024`.
- **1996 CONTROLS WIRING** — all DOM event binding.
- **~2100 palettes** — `BRAND_PALETTE_ALL`, `PALETTE_PRESETS`, `PALETTE_LABELS`. `PALETTE_PRESETS`
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
- **2248 EXPORT / 2296 EXPORT PREVIEW** — `renderHiRes()`/preview-modal plumbing, still used by
  the panel's Download button (Upload mode) and by Live's Download FAB. Live's shutter/record
  no longer goes through here directly — see GALLERY below. Exports are plain — no title/date/
  credit frame around them (removed).
- **2508 LIVE CAMERA** — getUserMedia (video + audio), per-breakpoint constraints, aspect-ratio
  cycling, `liveLoop()` sampling frames into the grid, MediaRecorder video capture (recorded
  video includes the mic audio track when permission is granted).
  **Zoom** is pinch-to-reveal, not a button: a two-finger pinch on the viewfinder
  (`gridCanvas` touchstart/touchmove/touchend in `wireMobileZoomUI()`) opens a curved
  drag-to-scrub dial (`#mob-zoom-dial`, an SVG arc — geometry constants `ZOOM_DIAL_*`,
  `zoomValueToAngle`/`zoomAngleToValue`/`zoomAnglePoint`) and hides every other floating control
  via `body.zoom-dial-active` while it's open; releasing schedules `closePop()` after a grace
  period so you can keep fine-tuning by dragging the dial directly. There's also a persistent
  `#mob-zoom-presets` row (small quick-tap values, e.g. min/1×/max) above the shutter — keep
  both in sync through `setZoomUIValue()`, which drives the dial, the presets' `.active` state,
  and `applyHardwareZoomIfPossible()` together. Don't reintroduce a plain `<input type=range>`
  or a visible "current zoom" FAB button — both were explicitly removed.
  **0.5× is a separate physical ultra-wide lens, not a digital zoom value** — most hardware's
  `zoom` track capability never goes below 1, so it can't be reached through
  `applyHardwareZoomIfPossible()`. `findUltraWideDeviceId()` looks for a back-camera
  `videoinput` whose label matches `/ultra.?wide/i` (populated by `enumerateDevices()` only
  after permission is granted — iOS Safari and most Android browsers expose it this way, with
  no capability flag to detect it up front) and caches the result on
  `liveState.ultraWideDeviceId`/`ultraWideChecked`. Tapping the `.5×` preset
  (`data-ultra-wide="1"`, injected by `renderZoomPresets()` for the back camera whenever the
  digital range doesn't already reach 0.5 on its own) calls `setUltraWideZoom()`, which swaps
  the entire stream to that deviceId via `stopCamera(); startCamera();` — same full restart
  `flipCamera()` already does, since it's a different physical camera, not a constraint on the
  current one. Moving off 0.5× (another preset, the dial, or a pinch) calls
  `leaveUltraWideIfNeeded()` to restart back onto the normal camera first. `flipCamera()` always
  clears `usingUltraWide` (no ultra-wide selfie lens). Because 0.5 is typically below
  `__liveZoomRange.min`, its active-preset state is set directly via `markUltraWideActive()`,
  not through `setZoomUIValue()` (which clamps into that range and would silently discard it).
  On hardware with no separate ultra-wide input (most laptops, some Android phones), tapping
  `.5×` just falls back to the closest digital zoom the device actually has — never a crash or
  dead end.
  **Capture mode** is one 3-way row (`#mob-capture-mode`: Video / Photo / Upload, each a
  `.mob-mode-label`) that doubles as the app's *only* mode switcher now — tapping "Upload" calls
  `switchToMode('image')`, tapping Video/Photo calls `switchToMode('live')` (if needed) then
  `setCaptureMode()`. `updateModeRowActive()` is what actually paints the `.active` state and is
  called from both `setCaptureMode()` and the end of `switchToMode()` — call it too if you add
  another way to change mode. Swiping left/right on the viewfinder (Live only) also cycles
  Photo↔Video through `setCaptureMode()`, never Upload.
  **Recording feedback**: `#mob-shutter.mode-video` turns the shutter's inner square red the
  moment Video is selected (idle, before you've even tapped it); `#mob-shutter.recording` adds
  an orange ring on top of that and only appears while actually recording. `#mob-rec-timer`
  (top of screen) runs via `startRecTimer()`/`stopRecTimer()`, started/stopped in
  `toggleVideoRecording()` alongside those classes — keep all three in lockstep if you touch
  that function.
- **3419 GALLERY** — in-memory only (cleared on reload, same as everything else — no
  IndexedDB/localStorage). The shutter (`addToGallery`) and the recorder's `onstop` no longer
  call `openExportPreview`/`openVideoExportPreview` directly for Live captures — they push into
  `galleryItems` instead (`addGalleryEntry()` assigns an id + object URL). `#mob-gallery` shows
  the latest capture as a live thumbnail (`updateGalleryFabThumb()`) instead of a generic icon,
  like a phone camera's roll shortcut. Tapping it opens `#gallery-screen`, a full-screen grid —
  **light theme, same as the rest of the app** (white bg, black = selected; don't reintroduce a
  dark theme here, that was tried and explicitly reverted). Tapping a thumbnail's own
  `.gallery-check` circle toggles multi-select (for the bottom bar's batch
  `galleryDeleteBtn`/`galleryDownloadBtn`); tapping anywhere else on the thumbnail instead opens
  `#gallery-viewer`, a full-screen single-item view (`openViewer(index)`) — swipe left/right
  (`viewerStep()`) to move between captures, with its own Delete/Download for just the item
  being viewed. Deleting anywhere must `URL.revokeObjectURL()` — don't just splice the array.
  `openExportPreview`/`openVideoExportPreview` (EXPORT PREVIEW section) are still used elsewhere
  (Upload's Download button) — don't delete them thinking they're dead.
- **3136 / 3234 MOBILE** — drawer panel and camera buttons. `#panel-toggle-bar` is the **top**
  bar now (it used to be the bottom bar) — the panel opens *downward* from beneath it, not
  upward from the bottom; it's a slim `height: 36px` (sized to its 10px label, not the tall
  68px bar it started as) with `#main`'s `top: 36px; bottom: 0`, the panel-open scrim's
  `top: 36px`, and `#mob-rec-timer`'s `top: 46px` all assuming that height — change all four
  together if it's resized again. There is no separate top mode-header anymore
  (`#mob-mode-header` / `.mob-fm-btn` / `#mob-fm-image` / `#mob-fm-live` were removed along with
  it) — Upload/Live switching lives entirely in the Video/Photo/Upload row described above. The
  panel (`#panel.panel-open`) is `z-index: 200`, but **opening it no longer hides the bottom
  controls** (shutter/flip/gallery/mode row) — that hiding was removed once the panel became a
  top sheet and stopped overlapping them; don't reintroduce it. Shutter/flip/gallery/mode-row/
  zoom-presets all sit low, close to the screen's bottom edge (shutter `bottom: 20px`) — flip
  and gallery are in the *same row* as the shutter (not with the mode labels above it), gallery
  on the left, flip on the right. `#mob-gallery` is shown in **both** modes now (40×40, same
  size as flip) — in Upload mode it takes the left slot Download used to occupy. `#mob-download`
  moved to Upload's bottom-right (Download's old spot is Live's flip slot) and shrank to match
  the other row buttons (was 44×44, now 40×40 like everything else); its role also changed —
  in Upload mode it no longer downloads straight to disk, it calls
  `saveUploadResultToGallery()` (built from the shared `buildDownloadCanvas()` helper, split out
  of the old `downloadPixels()`) which pushes the result into the gallery instead, same as a
  Live capture. The panel's own `#dl-pixels` button still calls `downloadPixels()` for a direct
  download. The `.mob-mode-label` row's inactive labels are white-with-shadow by default
  (legible over a busy camera feed) but flip to `var(--muted)` grey via
  `#mob-capture-mode.on-light-bg` whenever `state.mode !== 'live'` (toggled in
  `updateModeRowActive()`) — Upload's backdrop is the plain white canvas, so white-on-white text
  would otherwise disappear.
- **3690 INIT** — defaults to Live mode on load (starts the camera immediately).

There is no Draw (freehand paint) mode — only **Upload** (image) and **Live** (camera). It was
removed; don't reintroduce brush/undo/reference-image code without being asked. There is also no
shape picker, no custom-shape bezier editor, and no grid rotation control — cells are always an
unrotated square. The Upload drop zone (`#upload-zone`) lives inside `#main`, overlaying the
canvas itself (shown only in Upload mode with no photo loaded yet) — not in the side panel.
`#drop-zone` itself is a square (`aspect-ratio: 1/1`, not the old wide dashed rectangle) with a
thin, low-opacity `border: 1px solid rgba(0,0,0,.25)`. Since the drop-zone disappears once an
image is loaded, `#mob-upload-more` (an up-arrow FAB, same size/position as the Live shutter)
is the persistent way back into the file picker — it's always shown in Upload mode regardless
of whether an image is already loaded, and just calls `#file-input`'s native `.click()`, reusing
the same `loadFile()` path as the drop-zone. It's `44×44` (matching `#mob-ratio`, not the
shutter's `58×58` — it shipped at the shutter's size once and was reported as too big) with
`bottom: 27px` so its center lines up with the `29px`-bottom, `40px`-tall flip/gallery/download
row next to it. **Any FAB with a glyph (text content or a
`::before`) must set `align-items: center; justify-content: center` on itself explicitly** —
`display: flex` is set from JS (`updateMobileButtonsForMode()`) but flex's own defaults
(`align-items: stretch`, `justify-content: flex-start`) push an uncentered glyph into a
corner instead of the middle; `#mob-download` shipped without this once, and `#mob-upload-more`
needs it too since it's the same pattern.

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
- **Bump `CACHE` in `sw.js`** (currently `pixel-maker-v62`) **and** `__BUILD`/`__SW_URL`'s `?v=`
  near INIT in `index.html` **together**, on any deploy — all three in lockstep, or returning
  users (Safari especially — it's known to under-invalidate a cached `sw.js` byte-for-byte if
  its URL doesn't change) keep the old app indefinitely regardless of what `CACHE` says.
- **Square corners, no borders, no drop shadows.** Every floating/panel button is
  `border-radius: 0`, `border: none`, and `box-shadow: none` — differentiation (idle/hover/
  selected) comes entirely from background shade, never a stroke or an elevation shadow:
  `--bg #fff` (page) → `--panel #f3f4f6` (idle) → `--surface #e5e7eb` (hover/selected) →
  `--fab-bg rgba(255,255,255,.82)` (Live's floating controls, translucent over the camera
  feed) — except `#panel-toggle-bar` (the top bar), which is always solid `--panel` regardless
  of mode, not translucent, since it reported as "still white" over both backdrops. Don't
  reintroduce `border:`/`box-shadow:` on a button to "define" it — use one of
  those shades instead. The one exception is the shutter's `.recording` ring, which is a real
  `border` (not `box-shadow`) precisely so it isn't a drop shadow. Structural dividers (panel/
  section `border-bottom`) are not "buttons" and keep their borders — **except** `#panel`
  itself in its closed (`max-height:0; overflow:hidden`) mobile state, which must NOT carry a
  `border-bottom`: a border renders even at zero content height, so it showed up as a stray
  line sitting exactly at the bottom edge of the top bar above it (that bug shipped once
  already — don't reintroduce it). `body.mode-upload`
  (toggled in `switchToMode()`) is what swaps `#mob-gallery`/`#mob-download`/
  `#mob-upload-more` and the mode-row labels from Live's translucent look to solid
  `--panel`/`--surface` shades, since Upload's backdrop is the plain white canvas, not a busy
  camera feed, and translucent white on white is invisible.
- **The app's CSS/JS still has three layout code paths** (mobile / tablet / desktop —
  panel behavior, Live preview fill cover vs contain) but **only mobile is reachable** in
  normal use, because of the phone-only redirect above. Don't spend effort fixing
  tablet/desktop-only bugs unless asked; do keep the mobile path working.
- **iOS quirks are deliberate.** The explicit text-color overrides on buttons exist because
  iOS tints them blue; the `-webkit` bits and `isIOSSafari()` branches are load-bearing.
- Hebrew appears in comments and docs. UI strings are English.

## Git

Three remotes were originally set up to point at three separate GitHub repos, but as of
2026-09-17 that's down to two working ones:

- `origin` (`pixelmakegrid.git`) and `pixelmaker` (`pixel-maker.git`) are now **the same
  underlying GitHub repo** — GitHub renamed/moved `pixelmakegrid` to `pixel-maker` and
  transparently redirects the old URL, so pushing to `origin` updates `pixelmaker` too (and
  vice versa) with no extra push needed. `git push` warns "This repository moved" — that's
  expected, not an error.
- `pixelart` (`pixel-art-maker.git`) **returns "Repository not found"** — it's gone from
  GitHub. Don't try to push there until/unless the user re-creates it and says so.

Deployed at `https://shakedkleter92-ux.github.io/pixelmakegrid/` and on Netlify.
Work on `main` unless told otherwise.
