"""
H8-N made real: horizontal teak boards on the desk/shelf wall and deep navy walls (from the wood-wall study), plus:
the white plates on the board wall removed (the wiring goes through the boards), the wardrobe's white surfaces in the same
teak, the white cabinet under the desk removed, and the bed's headboard panels in the same teak.
Realistic look: afternoon sun, depth of field, lens effects. Saves Bedroom_Teak_Navy.blend and renders each camera.

  Blender -b ../wood_wall/Bedroom_WoodWall_H_08_teak_deep_navy.blend --python teak_navy.py -- [spp=512] [scale=1.0] [cams=A,B]
"""
import bpy, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OPT = dict(a.split('=', 1) for a in (sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []))
SPP, SCALE = int(OPT.get('spp', 512)), float(OPT.get('scale', 1.0))
CAMS = OPT.get('cams', 'CAM_Study_Wood_Wall,CAM_Render_B_From_Window,CAM_Hero_1_Room,CAM_Hero_2_Bed_Detail,CAM_Hero_3_Desk').split(',')
sc = bpy.context.scene
teak = bpy.data.materials['M_Boards_teak']

for n in ['ELEC_Light_Switch_W4', 'ELEC_Outlet_W4_Desk_A', 'ELEC_Plate_W4_Desk_B_blank', 'ELEC_Outlet_W4_Low',
          'DESK_Cabinet', 'DESK_Cabinet_Door', 'DESK_Ring_Pull']:
    ob = bpy.data.objects.get(n)
    if ob: bpy.data.objects.remove(ob)

for name, tint in [('WARD_Carcass', 0.5), ('WARD_Door_Left_back', 0.35), ('WARD_Door_Right_front', 0.65),
                   ('BED_Headboard_Wall2', 0.45), ('BED_Headboard_Wall3', 0.6)]:     # tint: each piece its own +-10% tone
    ob = bpy.data.objects[name]
    for s in ob.material_slots:
        if s.material and s.material.name in ('M_Wardrobe_White', 'M_Headboard_Wood'): s.material = teak
    me = ob.data
    if 'board_tint' not in me.attributes: me.attributes.new('board_tint', 'FLOAT', 'POINT')
    me.attributes['board_tint'].data.foreach_set('value', [tint] * len(me.vertices))

# realistic look again (the study file was saved in the quick preview look)
sc['sunny'] = 1; sc.update_tag(); bpy.context.view_layer.update()
sc.render.use_compositing = True
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100
sc.cycles.samples = SPP
sc.view_settings.exposure = 1.25        # navy + teak absorb far more light than your current walls: expose like a photographer would
cam = bpy.data.objects['CAM_Study_Wood_Wall'].data
cam.dof.use_dof = True; cam.dof.focus_distance = 2.9; cam.dof.aperture_fstop = 5.6
sc.camera = bpy.data.objects['CAM_Study_Wood_Wall']
sc['experiment'] = ('H8-N final: horizontal teak boards (mixed 6/9/12 cm, 0.6 cm gaps), deep navy walls #2F3D52, '
                    'teak desk without back board or cabinet, teak wardrobe and headboards, no plates on the board wall')
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'Bedroom_Teak_Navy.blend'), compress=True)

prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'METAL'; prefs.get_devices()
for d in prefs.devices: d.use = True
sc.cycles.device = 'GPU'; sc.render.resolution_percentage = round(100 * SCALE)
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_depth = '8'
os.makedirs(os.path.join(HERE, 'renders'), exist_ok=True)
for n in CAMS:
    sc.camera = bpy.data.objects[n]
    sc.render.filepath = os.path.join(HERE, 'renders', n.replace('CAM_', '') + '.png')
    bpy.ops.render.render(write_still=True)
    print('RENDERED', n, flush=True)
