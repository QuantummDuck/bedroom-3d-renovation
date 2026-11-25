# Round 5: the photoreal room, what was done overnight

**84 final images** (finished 10:54):
- 44 of the teak & navy design
- 32 of your room as it is today, 4 of them from the exact spots of your photos
- 8 sun-study frames

They take 1.6 GB: each is a 16-bit PNG plus a JPG.

## Where to look first
1. `renders/Compare_Photo_vs_Render.jpg`: your photos 06, 08, 16 and 19 next to the digital twin rendered from the same camera. This is the honest realism test.
2. `renders/Sheet_Teak_Navy.jpg` and `renders/Sheet_Current_Room.jpg`: every final render, labelled.
3. `renders/Sheet_Lighting_Teak_Navy.jpg` and `renders/Sheet_Lighting_Current_Room.jpg`: the same view in all 8 lightings.
4. `renders/Sheet_Sun_Study.jpg` and `Sun_Path_Diagram.png`: where the sun lands, hour by hour, for your coordinates and window.
5. `renders/final/`: the full-resolution images.
   - Folders: `v5/` (teak & navy), `current/` (your room today), `sun/`.
   - The 4 hero shots are 3840 × 2160; the rest are 2560 × 1440.
   - Each image is a 16-bit PNG plus a JPG.
6. `Archviz_Research.md`: how professional interior renders are made (cameras, render settings, materials, simulation), with sources, and how each point was applied here.

## The two rooms
- **`Bedroom_Current_Photoreal.blend`:** your room as it is today, built from the baseline.
  - Your bedspread, rug, puzzle, wall paint, floor, books, notes and MacBook screen come from your photos.
  - Also new: your fan, stool and lamp; the socket and charger at the foot of the bed; the plant, safety net and next tower outside.
- **`../teak_navy/Bedroom_Teak_Navy_v5.blend`:** the teak and navy design, with the same realism.
  - The puzzle backlight, sconce and fairy lights are removed.
  - The bed-panel light is a soft blue accent instead of pink.
  - `Cozy_Room_Changes.md` is updated to match.

## Lighting scenarios (`render_jobs.py`)

| Name | What it is |
|---|---|
| overcast_morning | Soft daylight. White balance and exposure were matched to your photos 06 and 19: wall colour within about 3%, brightness within about 4%. |
| afternoon_sun | Real sun for 15 Oct at 16:00 (28° high, from 273°) |
| late_sun | 17:00 (15° high): the sun patch climbs the wardrobe |
| golden_hour | 17:40 (about 5° high): warm light, the plant's shadow on the wardrobe, LEDs low |
| blue_hour | Dusk sky with all the LED layers on |
| night_cozy | All the cozy LED layers, the desk lamp and the screen |
| night_work | Desk lamp, shelves and a little cove light |
| night_everyday | Fan light on, with the blades spinning (motion blur) |

## Cameras
- **Room views, `CAM_PR_01` to `07`:** at your eye height (156 cm standing, 118 cm seated), with 24–35 mm lenses.
  - The camera is held level and framed with lens shift, so vertical lines stay straight, as architectural photographers shoot.
- **Human-eye views:**
  - `CAM_PR_08` lying in bed
  - `CAM_PR_09` sitting at the piano
  - `CAM_PR_10` desk chair turned to the room
- **Details:** `CAM_PR_D1` to `D6`, with 35–50 mm lenses and shallow focus.
- **Analysis view:** `CAM_Sun_Study`.

## Downloaded assets
- **Used:** teak and oak veneer scans, the jersey fabric (fitted sheet), fingerprint/smudge/dust maps (glass, chrome, floor), the swing-arm desk lamp, and the potted plant outside.
- **Downloaded but not used:** white oak, white stucco, smooth plaster, bouclé and the throw-pillow model. Your own close-up photos of the wall, floor, bedspread and rug matched your room better than any scan.

## Honest notes
- **Laser-level photos:** I didn't re-survey the walls and angles from the laser lines.
  - The room's 26 existing dimension checks still pass, and nothing in the new photos contradicted them.
  - The one measurement the new photos corrected is the **shelf spacing** (26.5 cm apart, not 23).
  - I used the photos mainly for detail: stool, fan, lamp, books, notes, socket and charger, bedspread, rug, puzzle, paint and floor.
- **Window direction vs the next building:** photo 16 shows a tall building straight out of your window. The coordinates you gave for the next building put it 44° to the left of the 260° window direction.
  - Either it's a different building, or the compass reading is off. Phone compasses indoors are often 10–30° off near concrete and steel.
  - If you re-check the bearing (outdoors, or from a map), I can redo the sun study in a few minutes.
  - **What a 230° window would change:** the sun would first reach the glass at 12:40 instead of 12:00. At 16:00 it would come in at a 43° slant instead of 13°, so the late patches would land toward the piano wall instead of on the wardrobe.
- **Outside the window:** the ledge, the "niche" sides and the overhang above (the next floor's planter) are estimates.
  - They decide when the high midday sun is blocked. In the winter frame (21 Jun, 15:00) they block the sun entirely; a flush facade would let some in.
- **Tidy staging:** the backpack, bottle, mouse and loose papers aren't modelled. The tomato plant is a similar plant from a scan library.
- **Paint texture:** it comes from your close-up photo. Under grazing LED light (blue hour, close views) it shows the same roller texture a real painted wall shows under LED strips.
- **Book models:** the models you downloaded weren't used. I modelled 45 of your actual books from your shelf photos instead, so the spines are really yours.

## Rebuild / re-render
- **Rebuild both files** (from the baseline and from v4):

```bash
cd "~/Documents/Bedroom 3D/experiments/photoreal"
B="$HOME/Library/Application Support/Steam/steamapps/common/Blender/Blender.app/Contents/MacOS/Blender"
"$B" -b ../../Bedroom_Baseline.blend --python build_current.py
"$B" -b ../teak_navy/Bedroom_Teak_Navy_v4.blend --python build_v5.py
```

- **Render any camera in any scenario:**

```bash
"$B" -b ../teak_navy/Bedroom_Teak_Navy_v5.blend --python render_jobs.py -- out=renders/mine cams=CAM_PR_01_Door scen=golden_hour w=2560 h=1440 spp=640
```

- **Sun at any time:** `scen=sun@2026-10-15@16:30`. The times available are the ones in `sun_positions.json`: every 5 minutes, 06:00–19:00, on 4 dates.
- **Re-run the overnight queues:** `python3 run_final.py` and `python3 run_extra.py`. They skip images that already exist. Then `python3 make_sheets.py` and `python3 make_compare.py`.
