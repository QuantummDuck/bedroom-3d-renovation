"""Aquarium position study on Bedroom_Teak_Navy_v8_layout.blend: V1..V4 x views x two times.
  Blender -b ../teak_navy/Bedroom_Teak_Navy_v8_layout.blend --python aq_render.py -- out=renders/aq [spp=64]"""
import bpy, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import photoreal_common as P
import render_jobs as RJ
from mathutils import Vector
A = dict(a.split('=', 1) for a in sys.argv[sys.argv.index('--') + 1:])
OUT = A['out']; os.makedirs(OUT, exist_ok=True); sc = bpy.context.scene; OBJ = bpy.data.objects
sc.cycles.samples = int(A.get('spp', 64))
SPOTS = {'V1': ((273.0, 11.0), 0), 'V2': ((111.0, 11.0), 0), 'V3': ((111.0, 37.5), 0), 'V4': ((285.0, 171.2), 90)}
CEIL = ['ARCH_Ceiling', 'ARCH_Crown_Molding', 'ARCH_Cove_Ledge', 'FAN_Body', 'FAN_Blades', 'FAN_Globe', 'LIGHT_Fan_Bulb']
pc = bpy.data.cameras.new('CAM_AQ_Plan'); pc.type = 'ORTHO'; pc.ortho_scale = 3.5; pc.clip_start = 0.01; pc.clip_end = 20
po = bpy.data.objects.new('CAM_AQ_Plan', pc); sc.collection.objects.link(po); po.location = Vector((150, 145, 600)) * 0.01; po.rotation_euler = (0, 0, math.pi)
VIEWS = ['CAM_L2_Table_Shelves', 'CAM_L4_Wardrobe_Gap', 'CAM_L11_Window_Arm_To_Bed', 'CAM_L18_Corner_High_Bed']
for v, ((x, y), rz) in SPOTS.items():
    r = OBJ['AQ_Aquarium']; r.location = Vector((x, y, 75.0)) * 0.01; r.rotation_euler = (0, 0, math.radians(rz)); bpy.context.view_layer.update()
    for scen in ('overcast_morning', 'night_cozy'):
        RJ.scenario(scen)
        for cn in VIEWS:
            for n in CEIL: OBJ[n].hide_render = False
            sc.camera = OBJ[cn]; sc.render.resolution_x, sc.render.resolution_y = 1280, 720
            sc.render.filepath = os.path.join(OUT, f'{v}__{cn[4:]}__{scen}.png'); bpy.ops.render.render(write_still=True); print('RENDERED', v, cn, scen, flush=True)
    RJ.scenario('overcast_morning'); sc.view_settings.exposure -= 3.6
    for n in CEIL: OBJ[n].hide_render = True
    sc.camera = po; sc.render.resolution_x = sc.render.resolution_y = 1000
    sc.render.filepath = os.path.join(OUT, f'{v}__plan.png'); bpy.ops.render.render(write_still=True); print('RENDERED', v, 'plan', flush=True)
