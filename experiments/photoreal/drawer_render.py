"""Drawer units + new boards, fast renders.  Blender -b ../teak_navy/Bedroom_Teak_Navy_v9_layout.blend --python drawer_render.py -- out=renders/drawers"""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_jobs as RJ
A = dict(a.split('=', 1) for a in sys.argv[sys.argv.index('--') + 1:]); OUT = A['out']; os.makedirs(OUT, exist_ok=True); sc = bpy.context.scene
for scen in ('overcast_morning', 'night_cozy'):
    for cam in ('CAM_DR1_Drawers_Wide', 'CAM_DR2_Drawer_Front', 'CAM_DR3_Corner_Unit', 'CAM_L2_Table_Shelves', 'CAM_L18_Corner_High_Bed'):
        RJ.scenario(scen); sc.cycles.samples = 32; sc.camera = bpy.data.objects[cam]
        sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 960, 540, 100
        sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 90
        sc.render.filepath = os.path.join(OUT, f'{cam[4:]}__{scen}.jpg'); bpy.ops.render.render(write_still=True); print('RENDERED', cam, scen, flush=True)
