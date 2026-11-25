"""Real-estate style renders of Bedroom_v13_Slats_Original_Colours.blend: wide level corner shots, wall elevations, plan and cut-away aerials.
  Blender -b ../teak_navy/Bedroom_v13_Slats_Original_Colours.blend --python estate_render.py -- out=renders/estate [only=E01,E02] [spp=128]"""
import bpy, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import photoreal_common as P
import render_jobs as RJ
from mathutils import Vector
A = dict(a.split('=', 1) for a in sys.argv[sys.argv.index('--') + 1:])
OUT = A['out']; os.makedirs(OUT, exist_ok=True); sc = bpy.context.scene; OBJ = bpy.data.objects
ONLY = set(A['only'].split(',')) if 'only' in A else None
CEIL = ['ARCH_Ceiling', 'ARCH_Crown_Molding', 'ARCH_Cove_Ledge', 'FAN_Body', 'FAN_Blades', 'FAN_Globe', 'LIGHT_Fan_Bulb']
H = 135.0                                                  # chest height, as real-estate photographers shoot
def ortho(name, loc, rot, scale):
    for o in [o for o in OBJ if o.name == name]: bpy.data.objects.remove(o)
    c = bpy.data.cameras.new(name); c.type = 'ORTHO'; c.ortho_scale = scale; c.clip_start = 0.01; c.clip_end = 40
    o = bpy.data.objects.new(name, c); P.coll('CAM_Photoreal').objects.link(o); o.location = Vector(loc) * 0.01; o.rotation_euler = [math.radians(a) for a in rot]; return o
def aerial(name, corner):
    cx, cy, d = 150, 145, 330; h = 140 + d * math.tan(math.radians(52))
    return P.cam(name, (cx + corner[0] * d, cy + corner[1] * d, h), (cx, cy, 90), 28, 11.0, level=False)
gm = bpy.data.materials.new('M_Estate_Ground'); gm.use_nodes = True; gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.22, 0.22, 0.23, 1)
gp = bpy.data.meshes.new('ESTATE_Ground'); gp.from_pydata([(-10, -10, -0.003), (10, -10, -0.003), (10, 10, -0.003), (-10, 10, -0.003)], [], [(0, 1, 2, 3)]); gp.materials.append(gm)
GROUND = bpy.data.objects.new('ESTATE_Ground', gp); P.coll('CAM_Photoreal').objects.link(GROUND); GROUND.hide_render = True
CH = [o.name for o in OBJ['CHAIR_Gaming_MyMax_MX6'].children_recursive] + ['CHAIR_Gaming_MyMax_MX6']
# id, title, camera, size, scenario, hide, exposure offset
S = [
 ('E01', 'Corner view: door corner to the window / slat-wall corner', P.cam('CAM_E01', (98, 285, 150), (292, 6, 100), 15, 8.0), (1920, 1080), 'afternoon_sun', [], 0),
 ('E02', 'Corner view: window corner to the bed corner', P.cam('CAM_E02', (84, 9, H), (290, 283, 70), 15, 8.0), (1920, 1080), 'afternoon_sun', [], 0),
 ('E03', 'Corner view: from the bed corner across the room', P.cam('CAM_E03', (292, 250, 140), (12, 12, 105), 15, 8.0), (1920, 1080), 'afternoon_sun', [], 0),
 ('E04', 'High view: from above the window wall, looking across the room', P.cam('CAM_E04', (228, 12, 212), (45, 272, 75), 15, 8.0), (1920, 1080), 'afternoon_sun', [], 0),
 ('E05', 'Entrance: standing in the doorway', P.cam('CAM_E05', (96, 284, H), (270, 20, 100), 18, 8.0), (1920, 1080), 'afternoon_sun', [], 0),
 ('E06', 'Wall 3: slat wall, shelves and table, straight on', P.cam('CAM_E06', (78, 150, H), (296, 135, 130), 20, 8.0), (1920, 1080), 'afternoon_sun', ['CHAIR'], 0),
 ('E07', 'Wall 2: window wall, straight on', P.cam('CAM_E07', (150, 280, H), (150, 0, 125), 18, 8.0), (1920, 1080), 'afternoon_sun', [], 0),
 ('E08', 'Wall 4: wardrobe, straight on', P.cam('CAM_E08', (284, 146, H), (0, 146, 135), 18, 8.0), (1920, 1080), 'afternoon_sun', ['CHAIR'], 0),
 ('E09', 'Wall 1: door and bed, straight on', P.cam('CAM_E09', (150, 8, H), (150, 290, 120), 18, 8.0), (1920, 1080), 'afternoon_sun', ['CHAIR'], 0),
 ('E10', 'Wide 12 mm from the middle of the room, looking at the bed and door', P.cam('CAM_E10', (175, 120, 140), (160, 290, 100), 12, 8.0), (1920, 1080), 'afternoon_sun', [], 0),
 ('E11', 'Twilight: door corner', P.cam('CAM_E11', (98, 285, 150), (292, 6, 100), 15, 8.0), (1920, 1080), 'blue_hour', [], 0),
 ('E12', 'Twilight: window corner', P.cam('CAM_E12', (84, 9, H), (290, 283, 70), 15, 8.0), (1920, 1080), 'blue_hour', [], 0),
 ('P01', 'Plan, ceiling removed', ortho('CAM_P01', (150, 145, 600), (0, 0, 180), 3.5), (1600, 1600), 'overcast_morning', CEIL, -3.6),
 ('P02', 'Cut-away aerial from the door / wardrobe corner', aerial('CAM_P02', (-1, 1)), (1920, 1080), 'overcast_morning', CEIL + ['ARCH_Wall_1_Door', 'ARCH_Wall_4'], -3.6),
 ('P03', 'Cut-away aerial from the window / slat-wall corner', aerial('CAM_P03', (1, -1)), (1920, 1080), 'overcast_morning', CEIL + ['ARCH_Wall_2_Window', 'ARCH_Wall_3'], -3.6),
 ('P04', 'Cut-away aerial from the bed corner', aerial('CAM_P04', (1, 1)), (1920, 1080), 'overcast_morning', CEIL + ['ARCH_Wall_1_Door', 'ARCH_Wall_3'], -3.6),
]
for sid_, title_, cn_, hide_ in (('E13', 'Wall 1: frame, raised shelves and trailing plants', 'CAM_W1_Frame_Wall', ['CHAIR']),
                                 ('E15', 'Window wall: teak panel up to the window frame', 'CAM_W2_Window_Panel', [])):
    if cn_ in OBJ: S.append((sid_, title_, OBJ[cn_], (1920, 1080), 'afternoon_sun', hide_, 0))
S.append(('E17', 'Table-top shelf unit with the aquarium, front', P.cam('CAM_E17', (236, 215, 145), (271, 14, 145), 28, 8.0), (1920, 1080), 'afternoon_sun', ['CHAIR'], 0))
S.append(('E18', 'Table-top shelf unit, from the side', P.cam('CAM_E18', (215, 90, 150), (271, 14, 140), 24, 8.0, level=False), (1920, 1080), 'afternoon_sun', ['CHAIR'], 0))
S.append(('E14', 'Close: Marble Queen pothos on the upper shelf', P.cam('CAM_E14', (210, 215, 178), (254, 288, 166), 28, 5.6, level=False), (1920, 1080), 'afternoon_sun', ['CHAIR'], 0))
S.append(('E16', 'Close: Peperomia Hope on the lower shelf', P.cam('CAM_E16', (150, 210, 118), (146, 288, 100), 28, 5.6, level=False), (1920, 1080), 'afternoon_sun', ['CHAIR'], 0))
if 'spp' in A: sc.cycles.samples = int(A['spp'])
base = {o.name: o.hide_render for o in OBJ}
for sid, title, cam, (w, h), scen, hide, expo in S:
    if ONLY and sid not in ONLY: continue
    for n, v in base.items():
        if n in OBJ: OBJ[n].hide_render = v
    for n in (CH if 'CHAIR' in hide else []) + [x for x in hide if x != 'CHAIR']:
        if n in OBJ: OBJ[n].hide_render = True
    GROUND.hide_render = not sid.startswith('P')
    RJ.scenario(scen); sc.view_settings.exposure += expo + (0.4 if not sid.startswith('P') else 0)
    sc.camera = cam; sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = w, h, 100
    sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 93
    sc.render.filepath = os.path.join(OUT, f'{sid}.jpg'); bpy.ops.render.render(write_still=True); print('RENDERED', sid, title, flush=True)
