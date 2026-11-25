> **Using this repo for marketing videos or edits? Start with [MARKETING_VIDEO_HANDOFF.md](MARKETING_VIDEO_HANDOFF.md).**

# Bedroom 3D: baseline reconstruction

A to-scale Blender model of your bedroom, built from your two A4 sketches, 17 photos and the measurements you gave in chat.

## Files

| Path | What it is |
|---|---|
| `Bedroom_Baseline.blend` | **The reference model of the room as it is.** It's read-only, so it can't be overwritten by accident. |
| `build_bedroom.py` | Script that generates the baseline from scratch. Every dimension is a named value at the top. |
| `verify_baseline.py` | Checks that the room, door, window and wardrobe, plus the bed, desk and piano you measured, still have their exact sizes. Works on any experiment file. |
| `experiments/` | Renovation versions. They are copies of the baseline and never edit it. |
| `experiments/wall_colors/` | Wall-colour study: one editable `.blend` per colour, the renders, and the comparison sheets `renders/compare_view_A.jpg` and `renders/compare_view_B.jpg`. It always renders in the overcast light calibrated to your photos (`sunny` = 0), so colours compare fairly without sun patches. |
| `experiments/wood_wall/` | Wood-wall study: vertical boards over the whole shelf/desk wall (10 woods and layouts) with the other walls dusty blue or deep navy. The desk is in the same wood with its back board removed, and the desk, shelves, props and sockets sit on the boards. It has vertical boards (`renders/`, `Bedroom_WoodWall_*.blend`) and horizontal boards (`renders_horizontal/`, `Bedroom_WoodWall_H_*.blend`), 40 quick previews in all, and **`Wood_Wall_Options.pdf`** comparing every option by code (for example H3-N is horizontal boards, wood 3, deep navy walls). Rebuild it with `python3 make_pdf.py`, or re-render with `wood_wall.py -- orient=horizontal`. |
| `experiments/teak_navy/` | Your pick, **H8-N**: horizontal teak boards (mixed 6/9/12 cm) on the shelf/desk wall and deep navy walls. The white plates on the board wall are removed (the wiring goes through the boards). The wardrobe's white surfaces and the bed's headboard panels are teak too. The desk is teak, without its back board or the white cabinet. `Bedroom_Teak_Navy.blend` is editable and has the realistic look, with exposure +1.25 for the darker room. `renders/` holds five views. Round 2 (`teak_navy_v2.py` → `Bedroom_Teak_Navy_v2.blend`, `renders_v2/`) adds: the teak panel running the whole piano wall to the wardrobe and down to the floor; stacked pillows; no music rest; a flat-woven cream/charcoal rug like your photo; a MacBook Air 13" M4 to scale; a cable grommet in the window-side desk corner (the lamp moved 10 cm to sit beside it); no mouse or papers. It also has option sheets for the wardrobe strip colour (S1–S6) and the desk's door-side metal legs (L1–L4). Round 3 (`teak_navy_v3.py` → `Bedroom_Teak_Navy_v3.blend`, `renders_v3/`) adds: your picks (navy wardrobe strips S5, square black legs L1); the MyMax MX6 remodelled after your photos (quilted blue centre, black stripes, blue wings, harness slots, logo); your 3-blade ceiling fan (size and position EST, light off); RGB LED strips under each shelf and a halo strip on the back of the piano; a strong desk lamp; and blue hour (sky made by `tools/make_dusk_sky.py`). Scene custom properties: **LED_RGB** (colour picker), **LED_Brightness** and **Desk_Lamp**. The daylight world is still in the file (World selector). Round 4 (`teak_navy_v4.py` → `Bedroom_Teak_Navy_v4.blend`, `renders_v4/`) is the cozy lighting plan. It has warm base light and nine light groups (ceiling cove, shelves, piano, bed panel, puzzle backlight, under-desk, wardrobe plinth, fairy lights, reading sconce). Each group has its own **<Group>_RGB** colour and **<Group>_Brightness** in Scene > Custom Properties, plus **LED_Master** for all of them; the desk lamp stays warm white. **`Cozy_Room_Changes.md`** lists every physical change (lighting, plus the earlier renovation choices). |
| `experiments/photoreal/` | **Round 5, the photoreal pass.** It has a digital twin of your room as it is today (`Bedroom_Current_Photoreal.blend`) and the teak/navy design rebuilt with the same realism (`experiments/teak_navy/Bedroom_Teak_Navy_v5.blend`). What's new:<br>• Cameras at your eye height (156 cm standing, 118 cm seated) with 24–35 mm lenses, held level.<br>• Your own bedspread, rug, puzzle, wall paint, floor, 45 book spines, notes and MacBook screen, taken from your photos.<br>• Scanned teak and oak, fingerprints and dust on the glass and chrome, crinkles in the bedding.<br>• The real sun for your address and window (260°), shown in `Sun_Path_Diagram.png`.<br>• 8 lighting scenarios in `render_jobs.py`.<br>Final renders are in `renders/final/` (sheets: `renders/Sheet_*.jpg`). How studios do it, with sources: `Archviz_Research.md`. Live log: `WORKLOG.md`. Rebuild: `build_current.py` / `build_v5.py`; render: `run_final.py`. |
| `reference/` | Your photos (`ref_NN.jpg`) and the two sketches, turned upright. |
| `textures/` | The puzzle texture, taken from photo 06 with the perspective corrected and the colours calibrated. Also the scanned Poly Haven textures and the daylight HDR photo (all CC0), one folder per asset. |
| `renders/` | Plan, wall elevations, an overview, and photo-vs-model comparisons. |
| `tools/` | The small camera-calibration helpers used to measure from the photos. |

**Regenerate the baseline** (needed only if a measurement changes):

```bash
"$HOME/Library/Application Support/Steam/steamapps/common/Blender/Blender.app/Contents/MacOS/Blender" -b --factory-startup --python build_bedroom.py
```

The baseline is read-only, so first run `chmod u+w Bedroom_Baseline.blend`.

**Check any file:**

```bash
"$HOME/Library/Application Support/Steam/steamapps/common/Blender/Blender.app/Contents/MacOS/Blender" -b experiments/SOME_IDEA.blend --python verify_baseline.py
```

## Inside the .blend

- **Coordinates are in centimetres** (the scene unit is cm).
  - The origin is the floor at the corner of wall 2 (window) and wall 4 (desk wall).
  - **+X** runs along the window wall toward wall 3 (300 cm).
  - **+Y** runs along the desk wall toward the door wall (290 cm).
  - **+Z** points up to the ceiling (270 cm).
- **Collections:**
  - `ARCH_Architecture`: walls, floor, ceiling, crown molding, baseboards and electrical plates.
  - `DOOR_Door`, `WIN_Window` and `WARD_Wardrobe`: the three fixed elements.
  - `FURNITURE`: bed, desk, shelves, piano, chair and stool.
  - `DECOR_Loose`: rug, puzzle and the two air purifiers.
  - `LIGHT_Lighting` and `CAM_Cameras`.
- **Moving furniture:** each piece hangs off an Empty, for example `DESK_Desk`, `PIANO_Korg_SP250` or `BED_Bed`. Move or rotate the Empty and the whole piece follows.
- **Opening the door:** rotate `DOOR_Leaf_Pivot` around Z by a negative angle. The door swings into the room, hinged on the wall-4 side.
- **Materials** are shared and named by finish, for example `M_Wall_Paint`, `M_Floor_Tile`, `M_Wardrobe_White`, `M_Wardrobe_Wood` and `M_Desk_Wood`. Changing one of them re-finishes every object that uses it.
- **Where each dimension came from:** every object has a custom property `dim_source` (see the provenance key below). Many also have a `note`.
- **Photo-matched cameras:** `CAM_Photo_06`, `08`, `14` to `19` were solved from your photos.
  - In camera view they show your photo over the model at 50% opacity.
  - Render them at the resolution given in each camera's `note` to get a frame that lines up with the photo.
- **Lighting:** two real daylights, switched with one setting. In Scene Properties → Custom Properties, set **sunny** to 1 (default) or 0.
  - **Sunny afternoon (1):** a clear-sky 360° HDR photo of a city skyline (`homecoming_center_rooftop`, Poly Haven, CC0) provides the sky light and the view outside. A separate sun light sends mid-afternoon sun (45° up) through your window.
    - The sun light's strength was measured from the photo's own sun: on a horizontal surface, direct sun gives about 10 times the sky's light, as on a real clear day.
    - The photo's sun disc is removed from the lighting so it isn't counted twice.
    - Its artificial-grass ground is turned grey for lighting, so it doesn't tint your ceiling green.
    - Its brightness is set like a photographer exposing for the room (+3 stops), so sun patches glow without blowing out.
    - The sun's direction (`SUN_ELEVATION` and `SUN_AZIMUTH` in the script) is an estimate. Tell me which way your window faces and I'll set it exactly.
  - **Overcast (0):** the 360° photo of an overcast city from a high balcony (`hotel_rooftop_balcony`). Brightness and every material colour were calibrated against photos 06, 08 and 19 to within about 5–10%. Use it for fair colour comparisons.
  - Both use a Cycles light portal in the window, and the window glass lets daylight through.
  - If the HDR files are missing, the build falls back to a physically modelled overcast sky (CIE standard).
- **Materials:** real scanned textures (Poly Haven, CC0) sit on top of the calibrated colours:
  - Paint texture on the walls, ceiling and crown molding (`beige_wall_001`).
  - Oak grain on the desk, headboard and wardrobe strips (`kitchen_wood`); dark wood on the shelves (`dark_wood`).
  - Cotton weave on the bedspread and pillows (`stretch_poplin`), linen weave on the chair (`rough_linen`), leather on the stool (`fabric_leather_01`) and pile on the rug (`dirty_carpet`).
  - The wall colour sits in the **PAINT_COLOR** node of `M_Wall_Paint`, so recolouring the walls is still a single edit.
  - Glossy surfaces get smudges and uneven gloss; painted wood and black metal get a fine textured finish; floor tiles get colour variation within each tile.
- **Fabric:** the bedspread is cloth-simulated. It's pinned along the two walls, drapes over the open front and the foot of the bed, and touches the floor at the corner. The pillows are fabric sacks inflated with air pressure.
  - The simulation runs during the build and is frozen into normal meshes, so nothing re-simulates when you open the file.
  - Also added: your black-and-white zigzag throw (photo 7), the printed dots and stripes on the bedspread, your blue slides by the wardrobe (photo 19), and the piano and purifier cables.
- **Furniture shapes:** the MyMax chair is lofted into a racing-seat backrest (wrapping wings, headrest with the two harness slots) on a bucket seat. The stool has a saddle seat.
- **Cameras and lens:** all render cameras have real depth of field.
  - `CAM_Hero_1_Room` (the default) is the whole room from 1.22 m: 18 mm, f/5.6.
  - `CAM_Hero_2_Bed_Detail` is sun on the bedding: 35 mm, f/2.8.
  - `CAM_Hero_3_Desk` is the desk corner and shelves: 24 mm, f/4.
  - `CAM_Render_A_From_Door` and `CAM_Render_B_From_Window` are the earlier wide views.
  - The compositor adds a soft glow around the window, slight colour fringing at the edges, gentle darkening toward the corners and fine film grain (the `FX_*` nodes).
  - To turn these effects off: Render Properties → Post Processing → Compositing.
- **Props:** books and objects on the shelves, the laptop, mouse, papers, desk lamp, white device, footrest, and the handwritten notes above the desk and by the window.
  - They're stand-ins placed loosely after your photos 8, 14, 15 and 16. Hide the `PROPS_Lived_In` collection to see the empty room.

## Rendering it yourself

1. **Use the GPU (one-time setup):** in Blender, go to Preferences → System → Cycles Render Devices and choose **Metal**. Without this, Cycles falls back to the CPU and is several times slower.
2. **Render:** press **F12** (Render → Render Image). That renders the active camera, `CAM_Hero_1_Room`, with Cycles at 1920 × 1080: up to 512 samples, adaptive, with denoising. Expect about 3–5 minutes per view on your M4 GPU.
3. **Other view:** select another camera in the Outliner (`CAM_Hero_2_Bed_Detail`, `CAM_Hero_3_Desk`, `CAM_Render_A/B`, or any `CAM_Photo_NN`), choose View → Cameras → Set Active Object as Camera, then press F12.
   - Headless from Terminal instead: `tools/render_views.py` renders any list of cameras. Its first lines show how.
4. **Save:** in the render window, choose Image → Save As.
5. **Live preview:** set the viewport to **Rendered** shading (top-right buttons) to see the same lighting while you move around. It is noisier, but updates live.

## Provenance key: where each number comes from

| Tag | Meaning | Typical accuracy |
|---|---|---|
| `DRAWING` | Your A4 sketches | As measured |
| `USER` | Measurements you gave in chat | As measured |
| `SPEC` | Manufacturer data (Korg SP-250: 129.5 × 38 × 14 cm; MyMax MX6 seat and backrest heights) | As published |
| `PHOTO` | Recovered from your photos using cameras solved from the known dimensions | about ±1 to 3 cm |
| `EST` | My estimate | ±5 to 10 cm. Check these first if something looks off. |

### Key values

- **Room:** 300 × 290 × 270 (DRAWING).
- **Door:**
  - Leaf 71.5 × 210 (DRAWING).
  - Trim 7.5 cm wide (PHOTO: 7.4 to 7.5 measured).
  - The trim starts 7.5 cm from the wall-4 corner (derived: 300 − 181 − 25 − 71.5 − 2 × 7.5; photo 17 shows about 7).
  - Hinges at about 190 and 107.5 cm, and the lever at about 105 cm (PHOTO). A third hinge at about 25 cm is EST; it's out of frame in the photos.
- **Window:**
  - 151.5 × 121.5, sill at 97.5, 54.5 cm from wall 3, frame 1 cm proud of the wall (DRAWING).
  - Louvre panel (16 blades) on the wall-3 side; glazed panel on the wall-4 side (PHOTO).
- **Wardrobe:**
  - 181 × 63 × 270, 25 cm from the door trim (DRAWING; photo 18 confirms the 25 cm).
  - Wood strips centred at 70.0, 130.5 and 195.5 cm (PHOTO, ±1).
  - Handles from 76.9 to 125.3 cm; doors start 11.4 cm above the floor (PHOTO).
- **Bed:** 188 × 94 × 53 (USER), in the wall-2/wall-3 corner. Headboard panels on both walls, top at 87.5 (PHOTO).
- **Desk:**
  - 170 × 49 × 80 with 3 cm boards, against wall 4 from the window corner (USER).
  - Back upstand to 99 cm; white cabinet under the door end (PHOTO).
- **Wall shelves:** three boards with bottoms at 142, 164.5 and 187.5 cm, on four black frames (PHOTO). The 25 cm depth is EST.
- **Piano:**
  - Korg SP-250, 129.5 × 38 × 14 (SPEC).
  - About 1.5 cm from wall 3, keys at about 82 cm high, on a double-braced X stand (PHOTO).
- **Crown molding:** drops 17.5 cm down the wall (PHOTO). How far it reaches across the ceiling (12 cm) is EST.
- **Baseboard:** 10 cm (PHOTO).
- **Electrical:**
  - Light switch centred 200 cm along wall 4, 119 cm high (PHOTO).
  - Desk-wall plates at 132 cm high; two low sockets at about 38 to 44 cm (PHOTO).

## How I resolved inconsistencies

- **Window wall adds up to 300.5:** 54.5 + 151.5 + 94.5 = 300.5. I kept 54.5 to wall 3, so the wall-4 side is 94.0.
- **Door handle side:** the sketches draw it on the left, the photos on the right. The model follows the photos, with hinges on the wall-4 side and the lever on the wardrobe side.
- **Where the 25 cm is measured from:** it's from the door trim. That makes the space between the trim and the wall-4 corner 7.5 cm, which matches photo 17.

## Uncertain or not modelled

These are estimates or simplifications, listed with the ones most likely to matter first.

1. **Floor tiles:** 60 × 60 cm (you confirmed), laid at 45°.
2. **Rug:** 130 × 188 cm (you confirmed). From round 5 it sits between the bed and the wardrobe.
3. **Crown molding:** how far it reaches across the ceiling is assumed. Wall thickness only shows in the door and window openings and is also assumed.
4. **Movable items:** the bed, chair, stool and purifiers are placed from the photos to about ±3 to 5 cm. The chair and stool are simplified shapes.
5. **Colours:** they are calibrated from your phone photos, whose white balance varies from shot to shot. If you know the wall paint's name or code, I can use the exact colour.
6. **Props are stand-ins:** the books, laptop, lamp and notes are simple shapes placed loosely after your photos, not measured.
   - Not modelled: the LEGO models and figures, the backpack, clothes and bottles on the floor, and the inside of the wardrobe (no photos show it).
7. **The view outside** is a real city photo, but not your city. It shows what a high-floor overcast view looks like through your window.

## Credits

All scanned textures and the HDR photo come from [Poly Haven](https://polyhaven.com) and are CC0 (public domain):
- `beige_wall_001` (Dimitrios Savva, Rico Cilliers)
- `kitchen_wood` and `fabric_leather_01` (Rob Tuytel)
- `dark_wood` (Dario Barresi, Dimitrios Savva, Rico Cilliers)
- `stretch_poplin` and `rough_linen` (colormass, Rico Cilliers)
- `dirty_carpet` (Rohit Seervi)
- `hotel_rooftop_balcony` (Dimitrios Savva, Jarod Guest)
- `homecoming_center_rooftop` (Dario Barresi)

`ceiling_interior` was downloaded but isn't used: its swirl stucco doesn't match your smooth ceiling.

Round 5 assets (CC0):
- Used, from [Poly Haven](https://polyhaven.com): `teak_veneer`, `oak_veneer_01`, `cotton_jersey`, `desk_lamp_arm_01`, `potted_plant_02`.
- Downloaded but not used (your own photos matched better): `white_oak_veneer`, `white_stucco`, `plastered_wall_04`, `wool_boucle`, `throw_pillows_01`.
- [ambientCG](https://ambientcg.com): `Fingerprints002`, `SurfaceImperfections003`, `SurfaceImperfections015`.
- Book models you downloaded from Sketchfab (CC-BY / CC-BY-NC) are unpacked in `props/books_user/` but not used. Your real spines, cut from your photos, are more faithful.

Round 6 layout (`experiments/teak_navy/Bedroom_Teak_Navy_v6_layout.blend`, built by `experiments/photoreal/layout_v6.py` from v5; renders in `experiments/photoreal/renders/layout_v6/`): wardrobe on wall 4 with its doors facing the room, V/L-shaped table along walls 3 and 2 (50 cm gap to the wardrobe), bed in the old wardrobe corner, shelves on wall 3, piano and puzzle frame removed into the hidden collection `STORAGE_Removed` (not deleted). Your sketch is in `reference/round6/`.

Round 9 (`experiments/teak_navy/Bedroom_Teak_Navy_v9_layout.blend`, built by `experiments/photoreal/layout_v9.py` from v8): one rolling drawer unit under the table (top 0.25 cm below the table), 25 equal 9.5 cm teak boards on the shelf/bed wall, aquarium stored in `STORAGE_Removed`. The skirting, crown molding and cove ledge share one material, `M_Rodape`: change its Base Color to recolour them all. Colour study: `experiments/photoreal/renders/Rodape_colours_1.jpg` and `_2.jpg`.

Round 10: vertical slat wall (72 slats 2.7 cm, 1.35 cm gaps) and a colour study. Final: `experiments/teak_navy/Bedroom_v11_Smoked_Teal.blend` (smoked teal #36433F drenched, deep oiled teak wood). Reasoning, finalists and paint list: `experiments/photoreal/Colour_Study_Round10.md`; renders: `experiments/photoreal/renders/Final_Smoked_Teal.jpg`, `Palettes_finalists.jpg`, `Palettes_round1_*.jpg`, `Palettes_round2_*.jpg`.

Round 11: navy variations. Final: `experiments/teak_navy/Bedroom_v12_Navy_Camel.blend` (navy #283548 walls/trim/door, camel #9E8467 wardrobe with navy strips, deep teak slats). Write-up: `experiments/photoreal/Navy_Study_Round11.md`; sheets `renders/Navy_round1_*.jpg`, `Navy_round2.jpg`, `Navy_finalists.jpg`, `Final_Navy_Camel.jpg`.

Round 12 (current): `experiments/teak_navy/Bedroom_v13_Slats_Original_Colours.blend` = the round-9 room with only the vertical slat wall added; all colours as before the colour studies (navy walls, teak wardrobe with navy strips, original teak, dark shelf wood). The colour-study files v11/v12 are kept.

Round 13 (current): `experiments/teak_navy/Bedroom_v14_Slats_Split.blend`: slat wall vertical on the table side, horizontal on the bed side, split at the table/bed line (194.2 cm from the window wall). Colours as in v13.

Round 14: current model is `Bedroom_v13_Slats_Original_Colours.blend` (vertical slats on the whole wall again); the split-slat version `Bedroom_v14_Slats_Split.blend` is kept for later. Real-estate style renders in `experiments/photoreal/renders/estate/` (`E01`-`E12`, plan with dimensions, cut-away aerials).

Round 15 (current): `experiments/teak_navy/Bedroom_v15_Shelves_Frame.blend`: wall-3 shelves centred on the full wall, wall 1 gets the frame + two staggered shelves (sketch in `reference/round6/`). Renders: `experiments/photoreal/renders/estate_v15/`.

Round 16: `experiments/teak_navy/Bedroom_v16_Plants_Panels.blend`: frame and shelves raised 20 cm, bed panel up to the frame, teak panel on the window wall up to the window frame, procedural Marble Queen pothos and Peperomia Hope hanging from the wall-1 shelves. Renders: `experiments/photoreal/renders/estate_v16/`.

Round 17: `experiments/teak_navy/Bedroom_v17_Panel_Reverted.blend` = v16 with the bed panel back to its previous 87.5 cm height; window-wall panel, raised frame/shelves and plants kept.

Round 18: `Bedroom_v18A_ShelfUnit_2_shelves.blend` / `Bedroom_v18B_ShelfUnit_3_shelves.blend` = v17 + a table-top shelf unit and the aquarium in the window/slat-wall corner (same height 75-142 cm, 2 or 3 shelves). Renders in `experiments/photoreal/renders/v18A|v18B`, comparison sheets `ShelfUnit_A_vs_B_*.jpg`.

Round 19 (current): `Bedroom_v19_Wall_Shelves.blend`: the table-top unit's steel posts removed; five floating shelves fixed to the window-side wall (tops 110-214 cm) with the aquarium on the table beneath. Renders in `experiments/photoreal/renders/v19`.

Fabrication drawings (from v19): `experiments/schematic/Fabrication_Drawings_v19.pdf`, 9 A3 sheets.
- Contents: general arrangement, slat wall, L-desk, window wall + floating shelves, door wall, drawer unit, cove ledge + wardrobe, cut list + sheet nesting, and a presentation render (`Presentation_Render_v19.jpg`).
- Sources: `spec.py` holds the views and dimension anchors; `render_views.py` (Blender, Eevee + Freestyle) writes `views/*.png` + json; `build_sheets.py` builds the HTML and Chrome prints it to PDF.
- Rebuild: `"$B" -b experiments/teak_navy/Bedroom_v19_Wall_Shelves.blend --python experiments/schematic/render_views.py`, then `python3 experiments/schematic/build_sheets.py`.

Interactive planner: `experiments/room_planner/` (published at https://claude.ai/artifact/VjrTw2iosa16iaso8d8Reo).
- `export_room.py` turns v19 into `room.glb` (136 flat-coloured items) and `room.glb.txt` (the base64 copy the page loads).
- `index.html` is the three.js app.
- Re-export after model changes: `"$B" -b experiments/teak_navy/Bedroom_v19_Wall_Shelves.blend --python experiments/room_planner/export_room.py`, then base64 the GLB into `room.glb.txt` (see the build note in index.html).
- To run it locally: `python3 -m http.server --directory experiments/room_planner`.
