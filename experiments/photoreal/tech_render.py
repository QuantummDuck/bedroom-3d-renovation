"""Technical views of Bedroom_Teak_Navy_v7_layout.blend: plan, cut-away aerials, wall elevations, wide-lens interiors, construction details.
  Blender -b ../teak_navy/Bedroom_Teak_Navy_v7_layout.blend --python tech_render.py -- out=renders/tech [only=T01,T05]"""
import bpy, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import photoreal_common as P
import render_jobs as RJ
from mathutils import Vector

A = dict(a.split('=', 1) for a in sys.argv[sys.argv.index('--') + 1:])
OUT = A['out']; os.makedirs(OUT, exist_ok=True); sc = bpy.context.scene; OBJ = bpy.data.objects
ONLY = set(A['only'].split(',')) if 'only' in A else None
E = P.EYE_STAND
CEIL = ['ARCH_Ceiling', 'ARCH_Crown_Molding', 'ARCH_Cove_Ledge', 'FAN_Body', 'FAN_Blades', 'FAN_Globe', 'LIGHT_Fan_Bulb']
CHAIRS = [o.name for o in OBJ['CHAIR_Gaming_MyMax_MX6'].children_recursive] + ['CHAIR_Gaming_MyMax_MX6', 'STOOL_Body', 'STOOL_Seat', 'STOOL_Seat_Welt']


def ortho(name, loc, rot, scale):
    for o in [o for o in OBJ if o.name == name]: bpy.data.objects.remove(o)
    c = bpy.data.cameras.new(name); c.type = 'ORTHO'; c.ortho_scale = scale; c.clip_start = 0.01; c.clip_end = 40
    o = bpy.data.objects.new(name, c); P.coll('CAM_Photoreal').objects.link(o)
    o.location = Vector(loc) * 0.01; o.rotation_euler = [math.radians(a) for a in rot]; return o


def aerial(name, corner):               # corner: (sx, sy) = the room corner the camera hovers beyond
    cx, cy = 150, 145; d = 330; h = 140 + d * math.tan(math.radians(52))
    return P.cam(name, (cx + corner[0] * d, cy + corner[1] * d, h), (cx, cy, 90), 28, 11.0, level=False)


gm = bpy.data.materials.new('M_Tech_Ground'); gm.use_nodes = True; gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.22, 0.22, 0.23, 1)
gm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.9
gp = bpy.data.meshes.new('TECH_Ground'); gp.from_pydata([(-10, -10, -0.003), (10, -10, -0.003), (10, 10, -0.003), (-10, 10, -0.003)], [], [(0, 1, 2, 3)]); gp.materials.append(gm)
GROUND = bpy.data.objects.new('TECH_Ground', gp); P.coll('CAM_Photoreal').objects.link(GROUND); GROUND.hide_render = True

# id, title, camera, (w, h), scenario, hide-lists, exposure override
SHOTS = [
 ('T01', 'Plan (top view, ceiling removed)', ortho('CAM_T01', (150, 145, 600), (0, 0, 180), 3.5), (1600, 1600), 'overcast_morning', CEIL, -3.6),
 ('T02', 'Cut-away aerial from the door / desk-wall corner', aerial('CAM_T02', (-1, 1)), (1600, 900), 'overcast_morning', CEIL + ['ARCH_Wall_1_Door', 'ARCH_Wall_4'], -3.6),
 ('T03', 'Cut-away aerial from the window / frame-wall corner', aerial('CAM_T03', (1, -1)), (1600, 900), 'overcast_morning', CEIL + ['ARCH_Wall_2_Window', 'ARCH_Wall_3'], -3.6),
 ('T04', 'Cut-away aerial from the bed corner', aerial('CAM_T04', (1, 1)), (1600, 900), 'overcast_morning', CEIL + ['ARCH_Wall_1_Door', 'ARCH_Wall_3'], -3.6),
 ('T05', 'Cut-away aerial from the window / wardrobe corner', aerial('CAM_T05', (-1, -1)), (1600, 900), 'overcast_morning', CEIL + ['ARCH_Wall_2_Window', 'ARCH_Wall_4'], -3.6),
 ('T06', 'Elevation: wall 3 (shelves, table, bed head, plug)', ortho('CAM_T06', (70, 145, 135), (90, 0, -90), 3.2), (1500, 1350), 'overcast_morning', CHAIRS, None),
 ('T07', 'Elevation: wall 4 (wardrobe)', ortho('CAM_T07', (240, 145, 135), (90, 0, 90), 3.2), (1500, 1350), 'overcast_morning', CHAIRS, None),
 ('T08', 'Elevation: wall 2 (window, wardrobe end, table)', ortho('CAM_T08', (150, 190, 135), (90, 0, 180), 3.2), (1500, 1350), 'overcast_morning', CHAIRS, None),
 ('T09', 'Elevation: wall 1 (door, bed)', ortho('CAM_T09', (150, 55, 135), (90, 0, 0), 3.2), (1500, 1350), 'overcast_morning', CHAIRS, None),
 ('T10', 'Wide 14 mm from the table corner', P.cam('CAM_T10', (278, 22, 150), (40, 240, 100), 14, 8.0), (1600, 900), 'overcast_morning', [], None),
 ('T11', 'Wide 14 mm from the bed foot', P.cam('CAM_T11', (95, 256, 150), (270, 40, 120), 14, 8.0), (1600, 900), 'afternoon_sun', [], None),
 ('T12', 'Wide 14 mm from the bed head', P.cam('CAM_T12', (270, 262, 125), (40, 60, 130), 14, 8.0), (1600, 900), 'night_cozy', [], None),
 ('T13', 'Wide 12 mm from the ceiling, looking down', P.cam('CAM_T13', (150, 120, 252), (150, 150, 0), 12, 11.0, level=False), (1600, 900), 'overcast_morning', ['FAN_Body', 'FAN_Blades', 'FAN_Globe'], None),
 ('D01', 'Detail: table leg, glide and rug', P.cam('CAM_D01', (185, 78, 30), (142, 45, 16), 50, 4.0, level=False), (1200, 800), 'overcast_morning', [], None),
 ('D02', 'Detail: cove ledge, crown and LED', P.cam('CAM_D02', (200, 70, 215), (200, 0, 247), 35, 5.6, level=False), (1200, 800), 'night_cozy', [], None),
 ('D03', 'Detail: flush wall plug in the boards', P.cam('CAM_D03', (262, 165, 62), (296, 160.7, 44), 50, 4.0, level=False), (1200, 800), 'overcast_morning', [], None),
 ('D04', 'Detail: cable grommet, table corner', P.cam('CAM_D04', (262, 45, 105), (287, 13, 74), 50, 4.0, level=False), (1200, 800), 'overcast_morning', [], None),
 ('D05', 'Detail: under-table LED and legs', P.cam('CAM_D05', (215, 110, 38), (290, 110, 70), 35, 5.6, level=False), (1200, 800), 'night_cozy', [], None),
 ('D06', 'Detail: bed panel LED and head board', P.cam('CAM_D06', (190, 215, 115), (294, 289, 87), 35, 5.6, level=False), (1200, 800), 'night_cozy', [], None),
 ('D07', 'Detail: wardrobe track, plinth and floor', P.cam('CAM_D07', (125, 45, 22), (63, 40, 8), 35, 5.6, level=False), (1200, 800), 'night_cozy', [], None),
 ('D08', 'Detail: door handle, hinge and trim', P.cam('CAM_D08', (58, 245, 112), (40, 290, 105), 50, 4.0, level=False), (1200, 800), 'overcast_morning', [], None),
 ('D09', 'Detail: shelf bracket, boards and books', P.cam('CAM_D09', (238, 98, 178), (296, 90, 160), 50, 4.0, level=False), (1200, 800), 'night_cozy', [], None),
 ('D10', 'Detail: window louvres and frame', P.cam('CAM_D10', (150, 55, 170), (150, 0, 160), 70, 5.6, level=False), (1200, 800), 'overcast_morning', [], None),
]
if 'spp' in A: sc.cycles.samples = int(A['spp'])
base_hide = {o.name: o.hide_render for o in OBJ}
for sid, title, cam, (w, h), scen, hide, expo in SHOTS:
    if ONLY and sid not in ONLY: continue
    for n, v in base_hide.items():
        if n in OBJ: OBJ[n].hide_render = v
    for n in hide:
        if n in OBJ: OBJ[n].hide_render = True
    GROUND.hide_render = sid not in ('T01', 'T02', 'T03', 'T04', 'T05')      # neutral ground under the cut-away views
    RJ.scenario(scen)
    if expo is not None: sc.view_settings.exposure = sc.view_settings.exposure + expo
    sc.camera = cam; sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = w, h, 100
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_depth = '8'
    sc.render.filepath = os.path.join(OUT, f'{sid}.png'); bpy.ops.render.render(write_still=True); print('RENDERED', sid, title, flush=True)
