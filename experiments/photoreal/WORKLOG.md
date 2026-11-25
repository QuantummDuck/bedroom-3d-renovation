# Photoreal round (night of 2026-10-14 → user back 2026-10-15 12:30)

## User answers (2026-10-14 20:40)
- Location: private (the sun study uses a placeholder site, see sun_study.py; BRT = UTC-3, no DST). Window faces **260°** (compass). High-rise flat.
- Next building ~75 m away, bearing ~216° (44° left of the window normal, seen from inside). Height unknown → assume similar tower.
- Defaults accepted: BOTH rooms (current twin first as realism test vs photos; teak/navy v5 gets ~70% render time), tidy-lived-in staging (notes on wall in twin, both purifiers, no plant), 7 lighting scenarios, bed panel → soft blue, archviz lens style + iPhone-match set, no phone pings.
- Height 167 cm → standing eye 156, seated ~118.
- Floor tile 60 cm (diagonal, confirmed photo 43). Rug 130 x 188 (188 = bed length) → fits exactly between bed (y 95.8) and wardrobe (y 227).
- Laser: same height in every photo (value unknown). Fan: one blade 50 cm; floor → globe bottom 217 cm. Stool seat 66 cm. Crown molding: unknown → from photos.
- Photos 41-50: wall paint close-ups (41, 42), floor tile (43), rug (44), puzzle straight-on (45), shelves/books (46-49), bedspread flat (50). No daylight window photo.
- v5 lighting: keep all v4 groups EXCEPT puzzle backlight (frame back flush), sconce, fairy lights. No pink → bed panel blue.
- Approved: 13 CC0 downloads (done, textures/), quit helpers (Ollama quit; opencode/ChatGPT/Steam/Epson helpers auto-restart via launchd → left alone), caffeinate (running, 16 h).
- Book models (Sketchfab CC-BY / CC-BY-NC, user-downloaded) unpacked in props/books_user/ — credit in README.
- NOT allowed / not needed: deleting Steam games (124 GB free).

## Files
- `photoreal_common.py` — shared upgrades (render/colour settings, materials, photo textures, fan, stool, rug, window exterior, worlds, cameras, scenarios).
- `build_current.py` → `Bedroom_Current_Photoreal.blend` (twin, from Bedroom_Baseline.blend + v4 chair/MacBook).
- `build_v5.py` → `../teak_navy/Bedroom_Teak_Navy_v5.blend`.
- `render_jobs.py` — renders (camera, scenario) jobs.
- `sun_study.py` — solar positions (NOAA algorithm, offline) + diagram.

## Status log
- 21:05 setup done, downloads done, research sources collected.
- 21:40 photo textures done (make_photo_textures.py: puzzle, bedspread, rug, wall_micro, floor_speckle). photoreal_common.py + build_v5.py + render_jobs.py working.
  v5 test renders OK: teak scan, black Poly Haven lamp (head lowered via ctrl_top-position), stool 66 cm w/ tube footrest, fan rebuilt (globe 217),
  rug 130x188, puzzle flush, Echo Dot, ledge+net+plant+next tower outside. Sun 16:00 Oct 15 makes a patch on the wardrobe (PR_02).
  TODO: desk-lamp light position (bulb centroid), bed panel blue weaker, BOOKS from photos 46-49, twin build, photo-match cams for new photos.
- 22:09 FINAL QUEUE LAUNCHED: `nohup python3 run_final.py` (resumable; log renders/final/queue.log; 64 images: 4 heroes at 4K, 8 sun-study
  frames, ~52 at 2560x1440). If it dies: just re-run `python3 run_final.py` from this folder (skips finished images).
  Calibration: twin overcast wall colour matched to photos 06/19 with wb 8500 / tint +12 (lum within 4%).
  Review renders in renders/review_v5, review_cur, check2-4. Thermal throttling: renders slow ~2x after 10 min of load.
- 00:27 queue restarted with faster settings (queue_overrides.json: spp_max 640, thr 0.014; ~7.5 min per 2560x1440). 4K heroes + sun study done.
  Soften: wall relief 0.022, plaster normal 0.10, bedspread crinkle 0.22. New cams PR_08 lying in bed, PR_09 piano stool, PR_10 chair turned.
- 01:05 run_extra.py chained (starts automatically when run_final.py exits): 20 more images. make_compare.py = photo vs render sheet.
- 06:10 main queue at ~55/64 (ETA ~07:30), run_extra chained (ETA ~10:30). Compare_Photo_vs_Render.jpg built (photos 06/08/16/19 vs twin).
  NOTE for the user: photo 16 shows a tall building straight out of the window, but the given neighbour coordinates are 44 deg left of the
  260 deg window direction -> either a different building or the indoor compass reading is off (common: 10-30 deg). Offer to redo sun study.
- 10:54 ALL QUEUES DONE: 84 images (v5 44, current 32, sun 8), 1.6 GB. Sheets + compare rebuilt; twin LED-free scenarios relabelled.
  Round5_Summary.md is the user-facing summary. caffeinate stopped after completion.
- Round 6 (2026-10-19): new layout. layout_v6.py (from v5) -> teak_navy/Bedroom_Teak_Navy_v6_layout.blend; check_layout.py; plan_render.py; renders/layout_v6/.
  Wardrobe wall 4 doors to room, L table walls 3+2 (50 cm gap to wardrobe face), bed in old wardrobe corner (mirrored), shelves wall 3, piano+frame in excluded collection STORAGE_Removed.
- Round 7-9 (2026-10-19): layout_v7.py (table 75, boards to wall 3, plug), layout_v8.py (table to 25 cm gap, aquarium study aq_render.py),
  layout_v9.py from v8 -> Bedroom_Teak_Navy_v9_layout.blend: aquarium in STORAGE_Removed, ONE rolling drawer unit (40x45x71.75, 0.25 cm under the
  table, beside the chair), boards = 25 x 9.52 cm + 0.6 gaps, M_Rodape on skirting+crown+ledge. Colour study: rodape_render.py / make_rodape_sheet.py.
- Round 10 (2026-10-19): layout_v10.py (from v9) -> teak_navy/Bedroom_Teak_Navy_v10_slats.blend: vertical slat wall WALL3_Slat_Wall (72 x 2.7 cm slats,
  1.2 deep, 1.35 gaps, 0.9 felt), shelves in the same wood, M_Ward_Paint (fake user). palettes.py (P1-P7 round 1, R1-R5 round 2, deep_teak wood),
  make_palette_sheet.py, make_finalists.py. Final = R4 Smoked Teal -> teak_navy/Bedroom_v11_Smoked_Teal.blend (+ CAM_F1/F2). Write-up: Colour_Study_Round10.md.
- Round 11 (2026-10-19): navy study navy_palettes.py (N1-N6, M2-M4; NAVY #283548), make_navy_sheet.py, make_navy_finalists.py.
  Final M2 Navy & Camel -> teak_navy/Bedroom_v12_Navy_Camel.blend. Write-up Navy_Study_Round11.md. Renders renders/navy, renders/final_navy.
- Round 12 (2026-10-19): user reverted colours. layout_v10.py original_colours=1 out=... from v9 -> teak_navy/Bedroom_v13_Slats_Original_Colours.blend
  (vertical slats only; every material identical to v9, verified; shelves keep M_Shelf_Wood). Render check renders/v13_Slats_Original_Colours.jpg.
- Round 13 (2026-10-20): layout_v14.py from v13 -> teak_navy/Bedroom_v14_Slats_Split.blend: wall-3 slats vertical for world y<194.2 (table side, 48 slats), horizontal
  for y>=194.2 (bed side, 62 slats 2.7 x 1.2, gap 1.387 so they fill floor-to-crown). Render sheet renders/v14_Slats_Split.jpg.
- Round 14 (2026-10-20): user reverted the split slats; current = v13 (vertical slats everywhere). v14 split file + renders kept for later.
  Real-estate renders: estate_render.py / make_estate_sheets.py -> renders/estate/ (E01-E12, P01 plan + P01_dimensioned, P02-P04 cut-away aerials), renders/Estate_contact_sheet.jpg.
- Round 15 (2026-10-20): layout_v15.py from v13 -> teak_navy/Bedroom_v15_Shelves_Frame.blend: wall-3 shelf unit (+books, LEDs) moved +45 cm along y to the centre of the full wall (y=145, overhangs bed 34 cm);
  wall 1: frame (puzzle) over bed x=200 bottom 105, shelf upper-right 48 cm, shelf lower-left 46 cm (user's sketch, reference/round6?). Renders renders/estate_v15 (16) + Estate_contact_sheet_estate_v15.jpg.
- Round 16 (2026-10-20): layout_v16.py from v15 -> teak_navy/Bedroom_v16_Plants_Panels.blend: wall-1 frame+shelves +20 cm (frame bottom 125); bed panel extended up to touch the frame bottom (z 125, LED halo strip moved up);
  1 cm teak panel on the window wall floor -> window bottom frame (z 97.5), x 63-296; procedural trailing plants (no downloads; Poly Haven/free sites have none):
  Marble Queen pothos (white pot, upper shelf), Peperomia Hope (terracotta pot, lower shelf). Renders renders/estate_v16 (E01-E16, P01-P04) + Estate_contact_sheet_estate_v16.jpg.
- Round 17 (2026-10-20): layout_v17.py from v16 -> teak_navy/Bedroom_v17_Panel_Reverted.blend: bed panel back to top 87.5 (LED halo back), lower shelf + Peperomia 1.8 cm back to the wall. Window panel, frame, upper shelf, plants unchanged. Renders renders/estate_v17.
- Round 18 (2026-10-20): layout_v18.py from v17 (variant=A|B) -> teak_navy/Bedroom_v18A_ShelfUnit_2_shelves.blend and Bedroom_v18B_ShelfUnit_3_shelves.blend: table-top steel-post + dark-wood shelf unit
  (clear 46x22, outer 50x26, z 75-142; A boards top at 119,142; B at 110,126,142) in the window/slat-wall corner, aquarium (45x21x30) back on the table; grommet cap hidden. Renders renders/v18A, v18B; sheets ShelfUnit_A_vs_B_1-3.jpg.
- Round 19 (2026-10-21): layout_v19.py from v18A -> teak_navy/Bedroom_v19_Wall_Shelves.blend: steel posts removed, 5 floating shelves (46x23x2.5, tops z 110/136/162/188/214) on the window-side wall in the corner by the slat wall; aquarium moved back against the panel. Renders renders/v19, sheet Wall_Shelves_v19_sheet.jpg.
