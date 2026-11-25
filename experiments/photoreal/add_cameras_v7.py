"""Adds 15 more perspectives (CAM_L6..L20) to Bedroom_Teak_Navy_v7_layout.blend (saves in place).
  Blender -b ../teak_navy/Bedroom_Teak_Navy_v7_layout.blend --python add_cameras_v7.py"""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import photoreal_common as P
E = P.EYE_STAND
CAMS = [  # name, location, target, lens, fstop, level
    ('CAM_L6_From_Wardrobe_Gap', (100, 30, E), (150, 285, 100), 24, 8.0, True),
    ('CAM_L7_From_Bed_Foot', (112, 262, 120), (240, 40, 130), 24, 8.0, True),
    ('CAM_L8_Door_To_Bed', (50, 275, E), (294, 240, 60), 24, 8.0, True),
    ('CAM_L9_Lying_On_Bed', (130, 245, 80), (150, 0, 150), 20, 5.6, False),
    ('CAM_L10_Seated_At_Table', (210, 138, 120), (296, 100, 140), 24, 5.6, True),
    ('CAM_L11_Window_Arm_To_Bed', (180, 30, E), (290, 150, 110), 24, 8.0, True),
    ('CAM_L12_Shelves_Detail', (225, 100, 165), (296, 100, 168), 50, 4.0, False),
    ('CAM_L13_Table_Corner_Detail', (200, 90, 110), (285, 20, 80), 35, 4.0, False),
    ('CAM_L14_Wardrobe_Doors', (130, 90, 140), (63, 90, 120), 35, 5.6, True),
    ('CAM_L15_Window_From_Table', (230, 60, 118), (170, 0, 160), 35, 5.6, True),
    ('CAM_L16_Looking_Up_At_Fan', (150, 200, 100), (150, 145, 262), 24, 8.0, False),
    ('CAM_L17_Corner_High_Window', (280, 20, 235), (40, 230, 60), 16, 11.0, False),
    ('CAM_L18_Corner_High_Bed', (285, 275, 225), (100, 60, 60), 16, 11.0, False),
    ('CAM_L19_Low_Over_Rug', (90, 170, 35), (250, 110, 40), 24, 5.6, False),
    ('CAM_L20_Center_To_Door', (200, 150, E), (50, 290, 120), 24, 8.0, True),
]
for name, loc, tgt, lens, fs, lvl in CAMS: P.cam(name, loc, tgt, lens, fs, level=lvl)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_mainfile(compress=True); print('CAMERAS', len(CAMS))
