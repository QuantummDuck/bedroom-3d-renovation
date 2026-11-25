"""Teak & navy round 5 (photoreal) on top of Bedroom_Teak_Navy_v4.blend -> ../teak_navy/Bedroom_Teak_Navy_v5.blend
  Blender -b ../teak_navy/Bedroom_Teak_Navy_v4.blend --python build_v5.py
Your round-5 lighting decisions: keep every v4 group EXCEPT the puzzle backlight (frame back flat on the wall),
the reading sconce and the fairy lights; no pink anywhere -> the bed-panel halo is soft blue.
Then the shared photoreal upgrades (photoreal_common.py) and the new camera set."""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import photoreal_common as P
from mathutils import Vector

sc = bpy.context.scene
FRONT = 4.0                                    # the teak boards push the desk/shelves 4 cm off wall 4

# ---------------------------------------------------------------- 1. lighting edits
P.remove('PROP_Sconce', 'PROP_Sconce_Bulb', 'PROP_Sconce_Shade', 'LIGHT_Sconce', 'PROP_Fairy_Wire', 'PROP_Fairy_Beads',
         'LED_Puzzle_Top', 'LED_Puzzle_Bottom', 'LED_Puzzle_Left', 'LED_Puzzle_Right', 'LED_Channels_Puzzle', 'LED_Diffusers_Puzzle')
for key in ('Puzzle', 'Sconce', 'Fairy'):
    for k in (f'{key}_RGB', f'{key}_Brightness'):
        if k in sc: del sc[k]
    m = bpy.data.materials.get(f'M_LED_{key}')
    if m: bpy.data.materials.remove(m)
for n in ('M_Brass_Brushed', 'M_Linen_Shade', 'M_Copper_Wire'):
    m = bpy.data.materials.get(n)
    if m and m.users == 0: bpy.data.materials.remove(m)
BED_BLUE = P.lin('#6E9BFF')                    # soft blue: complementary to the warm amber layers
sc['BedPanel_RGB'] = BED_BLUE
sc['BedPanel_Brightness'] = 0.35               # an accent, not a flood: the navy walls bounce blue back strongly
sc.id_properties_ui('BedPanel_RGB').update(description='Bed panel halo (soft blue)')

# ---------------------------------------------------------------- 2. shared photoreal upgrades
P.render_settings()
P.upgrade_paint(); P.upgrade_floor(); P.upgrade_glass(); P.upgrade_metals()
P.teak_scan(); P.bedspread_photo()
P.rug_photo(); P.puzzle_rebuild()
P.fan_rebuild(); P.stool_rebuild(); P.echo_dot(x=FRONT + 10.0, y=26.0, z=80.0)
P.window_exterior(); P.plant_outside(); P.piano_and_pillows(); P.macbook_screen(True); P.bed_imperfections()
import shelves_books as SB
SB.fix_shelf_heights(); SB.build_books(FRONT); SB.decor_top(FRONT)
P.ensure_worlds()
lamp_col = P.desk_lamp_asset((FRONT + 46.5, 9.0, 80.0), -67.0)

# desk lamp: head lowered to where yours sits (shade ~30 cm above the desk, photos 27/34); warm spot inside the shade
lo_, hi_ = P.desk_lamp_pose((-6.0, 10.0, -30.0))
print('LAMP HEAD bbox cm', tuple(round(c) for c in lo_), tuple(round(c) for c in hi_))
print('LAMP LIGHT', P.desk_lamp_light())
for n in ('PROP_Cable_Lamp', 'PROP_Wall_Notes'):         # notes stay in the current-room twin only
    ob = bpy.data.objects.get(n)
    if ob: ob.hide_render = True
for n in ('PROP_Desk_Lamp_Bulb',):
    ob = bpy.data.objects.get(n)
    if ob: ob.hide_render = True

# ---------------------------------------------------------------- 3. cameras (eye heights for a 167 cm person)
E, Z = P.EYE_STAND, P.EYE_SEAT
P.cam('CAM_PR_01_Door', (52, 262, E), (175, 0, 115), 24, 8.0)
P.cam('CAM_PR_02_Toward_Door', (90, 30, E), (190, 290, 110), 24, 8.0)
P.cam('CAM_PR_03_Bed_Corner', (128, 214, E), (300, 40, 105), 28, 8.0)
P.cam('CAM_PR_04_Desk_Seated', (102, 52, Z), (14, 60, 112), 24, 5.6)
P.cam('CAM_PR_05_From_Bed', (276, 58, 112), (20, 175, 120), 28, 8.0)
P.cam('CAM_PR_06_Piano_Wall', (80, 120, 150), (300, 150, 118), 35, 5.6)
P.cam('CAM_PR_07_Door_Portrait', (52, 262, E), (175, 0, 115), 24, 8.0)
P.cam('CAM_PR_D1_Pillows', (226, 128, 96), (288, 38, 62), 50, 2.8, level=False)
P.cam('CAM_PR_D2_Desk_Lamp', (88, 98, 118), (FRONT + 28, 26, 100), 50, 2.8, level=False)
P.cam('CAM_PR_D3_Books', (92, 60, 172), (FRONT + 4, 45, 182), 35, 4.0, level=False)
P.cam('CAM_PR_D4_Window', (170, 170, 150), (165, 0, 158), 35, 5.6)
P.cam('CAM_PR_D5_Stool_Rug', (176, 132, 92), (228, 172, 44), 50, 2.8, level=False)
P.cam('CAM_PR_D6_Wardrobe_Glow', (196, 150, 58), (222, 227, 12), 35, 4.0, level=False)
P.cam('CAM_PR_08_Lying_In_Bed', (234, 66, 84), (40, 230, 165), 20, 5.6, level=False)      # lying in bed, head by the pillows
P.cam('CAM_PR_09_Piano_Stool', (222, 170, 141), (296, 150, 92), 24, 5.6, level=False)      # sitting at the piano (stool 66 cm)
P.cam('CAM_PR_10_Chair_Turned', (84, 58, 118), (300, 30, 96), 24, 8.0)                      # desk chair turned to the room
for n in ('CAM_PR_02_Window_Side', 'CAM_PR_06_Piano_Corner'): P.remove(n)
sc.camera = bpy.data.objects['CAM_PR_01_Door']

sc['experiment'] = (sc.get('experiment', '') + ' | round 5: photoreal (scanned teak, your bedspread/rug/puzzle/paint from photos, '
                    'real sun for the project site, window 260 deg), no puzzle backlight / sconce / fairy lights, bed panel blue')
bpy.context.preferences.filepaths.save_version = 0
out = os.path.join(P.ROOT, 'experiments', 'teak_navy', 'Bedroom_Teak_Navy_v5.blend')
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print('SAVED', out)
