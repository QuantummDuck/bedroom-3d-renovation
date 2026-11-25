# Bedroom 3D: handoff for marketing videos

> For Claude Code agents: read this file first. Repo: https://github.com/QuantummDuck/bedroom-3d-renovation

This is a handoff for another Claude session. The goal is to turn this project into marketing videos for real-estate agents, furniture makers, renovation companies and similar clients. It covers:
- where everything lives
- how each part works
- what to edit to change the look
- three practical ways to produce video
- what must not leave the owner's Mac

Written 2026-11-25; updated the same day when the project moved to GitHub.

---

## 1. What this project is

It is a measured 3-D replica of the owner's real bedroom (3.00 × 2.90 × 2.70 m), plus a full renovation designed on top of it. The renovation includes:
- a vertical teak slat wall
- an L-shaped desk on steel legs
- floating shelves
- teak wall panels
- a cove ledge
- a rolling drawer unit
- a re-faced wardrobe

Everything was built in Blender with Python scripts, so every change can be reproduced.

There are three outputs, and each one is a different video source:

| Output | Look | Speed | Best for |
|---|---|---|---|
| **Web planner** (three.js) | cartoon / isometric dollhouse with outlines | real time | "drag the furniture" demos, quick social clips, before/after layout changes |
| **Blender photoreal** (Cycles) | photographic, real sun, LED lighting scenarios | about 6–11 min per 2560×1440 frame on the M4 Air | hero stills, slow pans of a few seconds, day-to-night stills |
| **Blender CAD look** (Eevee + Freestyle) | flat colours with black outlines, like Fusion or Onshape | about 1–3 s per frame | assembly or exploded animations, "from drawing to room" pieces |

Plus a 9-sheet A3 fabrication drawing set (PDF) that can appear in a video as graphics.

---

## 2. Where everything is, and how to get started

**This project lives on GitHub: https://github.com/QuantummDuck/bedroom-3d-renovation** (public).

```bash
gh repo clone QuantummDuck/bedroom-3d-renovation && cd bedroom-3d-renovation     # about 570 MB
```

The owner's original copy is in iCloud Drive (`Bedroom 3D`), with the full 3 GB of old renders and private reference photos. The repo is a cleaned, lean copy. All paths in this document are relative to the repo root.

**What is in the repo:**

| Folder / file | Contents |
|---|---|
| `experiments/teak_navy/` | every design version as a `.blend`, v2 to v19. **`Bedroom_v19_Wall_Shelves.blend` is current.** |
| `experiments/photoreal/` | render scripts (`render_jobs.py`, `estate_render.py`, `photoreal_common.py`, `layout_vNN.py`, palettes), `WORKLOG.md`, research notes, and `Bedroom_Current_Photoreal.blend` (the room as it is today) |
| `experiments/room_planner/` | the web planner: `index.html`, `room.glb`, `room.glb.txt`, `export_room.py` |
| `experiments/schematic/` | CAD-look renders, the A3 drawing set (`Fabrication_Drawings_v19.pdf`), `Presentation_Render_v19.jpg`, sheet builders |
| `experiments/wall_colors/` | scripts for the early wall-colour study (the study `.blend` files are not in the repo; regenerate them with `wall_colors.py`) |
| `textures/` | CC0 textures and HDRIs used by the materials |
| `Bedroom_Baseline.blend`, `build_bedroom.py`, `verify_baseline.py`, `README.md` | the measured baseline model and its documentation |
| `showcase/` | a few finished sheets and renders (estate contact sheet, wall-shelves sheet, CAD render, desk drawing) to see the look without running anything |

**What was deliberately left out, and what that means:**

| Left out | Effect |
|---|---|
| Old renders (3 GB), study `.blend` folders `wall_colors/` and `wood_wall/` | the scripts regenerate them |
| `reference/` (photos of the real room) | the photo-matched cameras and the photo-versus-render comparison scripts need it; skip those |
| `textures/photo/`, `textures/books/`, `textures/notes/`, `textures/puzzle_from_photo06.png` | derived from private photos and copyrighted covers. The book spines, wall notes and the puzzle picture render as flat or missing textures. Images that point at them show up as missing images in Blender and render pink/black; hide or recolour those objects (the `BOOK_*` and `DEC_*` items). |
| `props/books_user/` | third-party book models of unclear licence |
| The owner's real coordinates | `sun_study.py` now uses a Sao Paulo placeholder, and `sun_positions.json` was regenerated for it. Set `BEDROOM_LAT`, `BEDROOM_LON` and `BEDROOM_TZ` to change the site. |

**Image paths are relative** (`//../../textures/...`), so the `.blend` files open correctly from any clone as long as the folder layout is kept.

### 2.1 Run the planner without Blender

```bash
python3 -m http.server 8765 --directory experiments/room_planner      # then open http://127.0.0.1:8765/
```

The same planner is also published as a private Claude artifact (owner's account only): https://claude.ai/artifact/VjrTw2iosa16iaso8d8Reo

### 2.2 What you need installed

- **Blender 5.2.x** for the photoreal and CAD pipelines and the planner export. On the owner's Mac it is the Steam install; elsewhere, download it from blender.org.
- **Python 3**, **ImageMagick 7** (`magick`), **ffmpeg** and, for the drawing sheets, **Google Chrome**.
- **Node + Playwright or Puppeteer** for the planner video recorder (section 4.4).

---

## 3. Coordinates and naming

The model works in centimetres; Blender stores metres. The origin is the floor corner where wall 2 meets wall 4.

| Axis | Runs from → to |
|---|---|
| x | wall 4 (wardrobe) 0 → wall 3 (slat wall) 300 |
| y | wall 2 (window) 0 → wall 1 (door) 290 |
| z | floor 0 → ceiling 270 |

The walls:

| Wall | What's on it |
|---|---|
| 1 | door, bed panel, puzzle frame, two shelves |
| 2 | window, teak panel, 5 floating shelves, aquarium |
| 3 | 72-slat teak wall, shelf unit |
| 4 | wardrobe |

Object names are prefixed by group:

| Prefix | Group |
|---|---|
| `ARCH_` | architecture |
| `WALL3_`, `WIN_`, `DOOR_` | the slat wall, window and door |
| `WARD_` | wardrobe |
| `BED_`, `DESK_`, `DRAWER_` | bed, desk, drawer unit |
| `TSHELF_`, `SHELF_`, `WALL1_` | the various shelves |
| `CHAIR_`, `STOOL_` | seating |
| `AQ_` | aquarium |
| `PROP_`, `DEC_`, `BOOK_` | small props, decor, books |
| `POTHOS_`, `PEPEROMIA_` | plants |
| `FAN_` | ceiling fan |
| `LED_` | LED strips |
| `CAM_` | cameras |
| `STORAGE_Removed` (collection) | items taken out of the room: piano, old puzzle frame |

Versions are kept as separate files and are **never overwritten or deleted**; this is a standing rule from the owner. Each round is a script that opens the previous `.blend` and saves the next one:
- the scripts are `experiments/photoreal/layout_vNN.py`
- the outputs are `experiments/teak_navy/Bedroom_vNN_*.blend`
- **v19 is current**

---

## 4. The web planner (`experiments/room_planner/`)

### 4.1 Files

| File | Role |
|---|---|
| `index.html` | the whole app: one file, three.js 0.160 from jsDelivr via an import map, no build step |
| `room.glb` | 136 catalog items, flat colours, about 4.3 MB |
| `room.glb.txt` | the same GLB as base64 text. Artifact hosting will not serve `.glb`, so the page loads it with `fetch()`, then `atob`, then `GLTFLoader.parse`. |
| `export_room.py` | Blender script that builds `room.glb` from v19 |

To run it locally:

```bash
python3 -m http.server 8765 --directory "<project>/experiments/room_planner"
```

Then open `http://127.0.0.1:8765/`.

### 4.2 How it works

**Export (`export_room.py`):**
- Every object in v19 is grouped into catalog items through the `GROUPS` table: key, label, category, name prefixes.
- Each item is merged into one mesh, with its origin at the item's floor-centre.
- Heavy meshes are decimated to `MAX_TRIS = 7000`.
- Materials are replaced with flat colours (`OVERRIDE` table, otherwise the image average or base colour).
- glTF extras carry `label`, `cat`, `locked`, `stored`, `wall`.
- Skirting, crown molding and the cove ledge are split per wall; the floating shelves are split per board.

**App (`index.html`):**
- `registerItem()` wraps each item, turns its materials into `MeshToonMaterial` (cartoon shading) and gives it an id.
- `classify()` decides on every move whether an item is wall-mounted or on the ceiling. That drives the cutaway: walls facing the camera hide together with what hangs on them, and tall furniture near a hidden wall turns see-through (`setGhost`).
- `renderFrame()` draws three passes:
  1. the colour pass into `rtColor`
  2. an id + normal + depth pass into `rtInfo`
  3. a composite shader (`comp`) that draws outlines wherever the object id, depth or normal changes, then the transform gizmo on top
- Layout state:
  - format: `{v:1, items:{id:{p:[x,y,z], r, v, c:{material:hex}}}, copies:[...]}`
  - units are three.js metres: x = distance from wall 4, z = −distance from the window wall, y = height
  - autosaved to `localStorage`; the "Copy layout" / "Paste layout" buttons move it as text
  - hidden items are stored separately (key `bedroomPlanner.v19.hidden`)

### 4.3 Where to change the visuals

All of these are in `index.html`:

| Want | Edit |
|---|---|
| Background colour or gradient | CSS tokens `--stage-a`, `--stage-b` (light and dark blocks at the top of `<style>`). For video, set one fixed background and drop the dark-mode blocks. |
| Cartoon shading strength | `TOON_RAMP`: three grey steps (`150, 210, 255`). Lower the first value for harder shadows; use more steps for softer ones. |
| Outline colour and width | uniforms `ink` (`0x221e1b`), `selInk` (selection blue) and `thick` (set in `resize()` from the pixel ratio) |
| Outline sensitivity | in the `comp` fragment shader: depth threshold `0.035 + 0.01*abs(z0)`; crease threshold `dot(...) < 0.72`, with line weight `0.55` for creases |
| Lighting | `HemisphereLight` (sky/ground colours, 1.55), `sun` (`DirectionalLight` 1.9, soft shadows, 2048 map), `fill` light |
| Base slab under the room | `slab` (`BoxGeometry` + toon material `0x3a3c40`); `ground` is the shadow catcher, opacity 0.16 |
| Starting camera | `START = { az, pol, dist }`; orthographic framing comes from `s` in `resize()` |
| Isometric or perspective | the `perspBtn` handler switches between `ortho` and `persp` (FOV 32) |
| Object colours | per item in the UI, or with layout JSON `c:{"<material name>": "#hex"}` |
| Swap or add models | add a `GROUPS` entry in `export_room.py`, re-export, rebuild `room.glb.txt` (section 4.5) |

### 4.4 Making video from the planner

The app runs in real time, but for clean video, step it **frame by frame** instead of screen-recording:

1. **Make a recording build**, a copy such as `record.html`, not the published `index.html`:
   - `new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true })`
   - hide the UI: `#catalog, #inspector, #viewbar, #mobtabs, #toast { display:none }`
   - fix the canvas size (for example 1920×1080 or 1080×1920 for Reels) and set `renderer.setPixelRatio(1)`
   - remove `renderer.setAnimationLoop(...)` and expose the internals, for example `window.planner = { THREE, camera, controls, items, renderFrame, updateVisibility, setGhost, select, restore, snapshot }` at the end of the module script. Everything else lives inside the module scope.
2. **Drive it from Playwright or Puppeteer:**
   - for each frame t, set the camera (spherical orbit around `controls.target`), item positions, colours and visibility
   - call `planner.updateVisibility(); planner.renderFrame()`
   - grab `canvas.toDataURL('image/png')` and write `frame_00001.png` and onwards
3. **Encode:**

   ```bash
   ffmpeg -framerate 30 -i frame_%05d.png -c:v libx264 -pix_fmt yuv420p -crf 16 out.mp4
   ```

**Shots that suit this look:**
- slow 360° orbit of the cutaway; the cutaway updates itself as the camera passes each wall
- **build-up**: start with every item hidden, then reveal furniture one by one with a small drop or scale-in (animate `node.position.y` and `node.scale`)
- **before/after layout**: tween each item's `p` and `r` between two layout JSONs
- **recolour sweep**: tween material colours across palettes
- top-down plan to iso camera move (`animateTo()` already eases between views)

For composition (titles, captions, logos, music), feed the frames or MP4 into Remotion or HyperFrames. The `video-producer`, `gsap-animation` and `brag` skills cover this.

### 4.5 Updating the model behind the planner

Run these on a machine with Blender 5.x:

```bash
B="<path to Blender>"   # on the Mac: ~/Library/Application Support/Steam/steamapps/common/Blender/Blender.app/Contents/MacOS/Blender
"$B" -b experiments/teak_navy/Bedroom_v19_Wall_Shelves.blend --python experiments/room_planner/export_room.py
python3 -c "import base64;open('experiments/room_planner/room.glb.txt','w').write(base64.b64encode(open('experiments/room_planner/room.glb','rb').read()).decode())"
```

To republish the live page, publish `index.html` with the Artifact tool using `url: https://claude.ai/artifact/VjrTw2iosa16iaso8d8Reo` and `files: {"room.glb.txt": ...}`. Do this only with the owner's go-ahead; a new artifact is safer for a marketing variant.

---

## 5. Blender pipelines (`experiments/photoreal/`, `experiments/schematic/`)

**Blender:**
- version 5.2.2, headless CLI only: `"$B" -b FILE.blend --python SCRIPT.py -- key=value ...`
- on the Mac it is the Steam install at the path above
- in the cloud, download the Linux build from blender.org

**Portability gotchas:**
- macOS paths are hard-coded:
  - the Steam Blender path in `run_final.py`
  - `/System/Library/Fonts/Supplemental/Arial.ttf` in the sheet scripts
  - Google Chrome in `schematic/build_sheets.py`
- ImageMagick 7 needs an explicit `-font` path

**Render speed:**
- Cycles on Metal (M4 Air): about 6 min (v5) to 11 min (twin) per 2560×1440 frame at 640 samples. That's fine for stills and too slow for long animations.
- For motion, use **Eevee**, or Cycles at about 64 samples with denoising and short shots.

### 5.1 Photoreal stills: `render_jobs.py` + `photoreal_common.py`

```bash
"$B" -b ../teak_navy/Bedroom_v19_Wall_Shelves.blend --python render_jobs.py -- out=renders/x cams=CAM_E01,CAM_E06 scen=afternoon_sun,blue_hour w=1920 h=1080 spp=256
```

**Lighting scenarios** are defined in the `SCEN` dict:
- daylight: `overcast_morning`, `afternoon_sun`, `late_sun`, `golden_hour`
- dusk and night: `blue_hour`, `night_cozy`, `night_work`, `night_everyday`

Each scenario sets the world (daylight, dusk or night sky), the sun position by date and time, LED group brightness, the desk lamp and fan, exposure and white balance.

**LED groups** are Scene properties `<Group>_RGB`, `<Group>_Brightness` and `LED_Master`, for these groups: Cove, Shelves, BedPanel, Desk, Wardrobe and Piano. They drive both the lights and the emissive materials.

**Real-estate cameras** come from `estate_render.py`:
- E01–E18: corner views at chest height (135 cm), straight-on wall elevations, twilight shots, close-ups of the plants and shelves
- P01–P04: plan and cut-away aerials

```bash
"$B" -b ../teak_navy/Bedroom_v19_Wall_Shelves.blend --python estate_render.py -- out=renders/estate_v19 only=E01,E06 spp=128
```

Contact sheets with dimensions: `make_estate_sheets.py` (set `ESTATE_DIR`).

**Palettes:**
- `palettes.py` and `navy_palettes.py` recolour walls, trim, wardrobe and wood in one call, with `save=<KEY> path=OUT.blend`
- the reasoning behind each palette is in `Colour_Study_Round10.md` and `Navy_Study_Round11.md`
- the owner **reverted** the colour studies: v19 uses the original navy/teak colours with the vertical slats. Treat the palettes as variations for video, not the chosen design.

**Before/after:**
- `Bedroom_Current_Photoreal.blend` is the room as it is today, a photo-matched twin; v19 is the renovation
- the camera names match across files (for example `CAM_PR_01_Door`), so the same shot renders in both
- `make_before_after_pdf.py`, `make_compare.py` and `make_ab_sheet.py` build side-by-side sheets

**Making it move:**
1. Add a camera, keyframe `location` and `rotation` (or use a Follow Path constraint).
2. Set `scene.frame_start` and `scene.frame_end`, and `render.fps`.
3. Render a PNG sequence:

   ```bash
   "$B" -b FILE.blend --python setup_shot.py -a
   ```

   `setup_shot.py` is your own script that adds the keyframes and output path.
4. Animate `scene['<Group>_Brightness']` or the sun for day-to-night timelapses (8 scenarios exist as presets to interpolate between).
5. `photoreal_common.cam(name, loc, target, lens, fstop, level=True)` makes level, archviz-style cameras.

### 5.2 CAD / "Onshape-style" look: `experiments/schematic/`

| File | Role |
|---|---|
| `spec.py` | every view: camera (ortho or perspective, scale), visible objects, dimension anchors in cm; colours per material category (`COLORS`, `MATCOL`) |
| `render_views.py` | flat materials + Eevee + Freestyle outlines on a transparent background → `views/*.png` + projected annotation JSON |
| `build_sheets.py` | A3 SVG/HTML sheets (title block, dimensions, cut list, sheet nesting) → Chrome headless → `Fabrication_Drawings_v19.pdf` |

The `hero` view in `spec.py` is a full-room presentation render (`Presentation_Render_v19.jpg`).

**For video:**
- reuse `render_views.py`'s scene setup (materials, world, sun, Freestyle) with an animated camera, about 2 s per frame
- an **exploded / assembly** animation fits this look: keyframe each part from an offset position into place
- a drawing sheet cross-fading into a photoreal render is a strong "from plan to reality" shot

---

## 6. Ideas for marketing videos

| Concept | Source |
|---|---|
| "Your room, redesigned": photo of the current room → twin render → renovated render, matching camera | twin + v19, `render_jobs.py` |
| Day-to-night: same shot through sun, golden hour, blue hour and night with the LEDs | `SCEN` presets, Eevee for motion |
| Dollhouse orbit with furniture dropping in one by one | web planner recording build |
| Layout A vs B: furniture glides between two arrangements | planner layout JSON tween |
| Palette carousel: same room in 4–6 colour schemes | `palettes.py` / `navy_palettes.py`, or planner recolour |
| From drawing to room: fabrication sheet → CAD render → photoreal | `schematic/` + `render_jobs.py` |
| Product spotlight for a furniture company (slat wall, floating shelves, desk) | close cameras E14/E16/E17, CAD part drawings |
| Interactive demo screen-capture ("plan your room yourself") | the published planner |

---

## 7. Before anything is published (required)

**Private data:**
- The repo is public. The owner's real coordinates and the real-room reference photos were removed on purpose. Keep it that way: never add `reference/`, `textures/photo/` or the original location, and never send the owner's real location to any web service. The owner was explicitly promised this.
- The room is a real bedroom. Present it as a "sample project" without personal details.

**Rights:**
- **Book spines** (`BOOK_*`) were textured from photos of real copyrighted covers. Those textures are not in the repo. Keep it that way: hide the books (the "Books" category in the planner) or use plain colours.
- **Brand items:** MyMax MX6 chair (logo), MacBook, Echo Dot, Monster can, Funko, LEGO / McLaren / Ferrari models. Hide them or make them generic in commercial videos.
- `props/books_user/` (third-party book packs, some possibly CC-BY-NC) is not in the repo. Don't add it without confirming the licence.
- Textures and HDRIs from Poly Haven and ambientCG are **CC0**, fine for commercial use.

**Owner preferences to respect:**
- Never delete or overwrite earlier versions; new work goes into new files.
- No pink in the visuals.
- The owner has a blue MyMax MX6 chair.
- The owner likes being shown results as rendered images or sheets.

**Actions that need the owner's go-ahead:** pushing to this public repo, publishing or sharing artifacts, downloading anything, and anything posted publicly. No `LICENSE` file has been chosen yet; ask before adding one.

---

## 8. Further reading inside the project

| File | Contents |
|---|---|
| `README.md` | baseline reconstruction, file list, where every measurement came from, history of rounds 1–19 |
| `experiments/photoreal/WORKLOG.md` | dated log of every round |
| `experiments/photoreal/Archviz_Research.md` | camera, lens, material and lighting rules used for the photoreal renders |
| `experiments/teak_navy/Cozy_Room_Changes.md` | checklist of every physical change in the cozy-lighting round |
| `experiments/schematic/Fabrication_Drawings_v19.pdf` | dimensioned parts, cut list, materials |
