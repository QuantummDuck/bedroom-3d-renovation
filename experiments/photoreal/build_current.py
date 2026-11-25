"""Current room, photoreal twin (round 5): Bedroom_Baseline.blend + the same photoreal upgrades as v5, your real books,
notes, fairy lights, stool, fan and lamp, the round-3 MyMax chair and the MacBook Air -> Bedroom_Current_Photoreal.blend
  Blender -b ../../Bedroom_Baseline.blend --python build_current.py"""
import bpy, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import photoreal_common as P
import shelves_books as SB
from mathutils import Vector

sc = bpy.context.scene
V4 = os.path.join(P.ROOT, 'experiments', 'teak_navy', 'Bedroom_Teak_Navy_v4.blend')

# ---------------------------------------------------------------- 1. better chair + MacBook from the earlier rounds (renovation-neutral)
for ob in [o for o in bpy.data.objects if o.name.startswith('CHAIR_')] + [bpy.data.objects.get('PROP_Laptop')]:
    if ob: bpy.data.objects.remove(ob)
want = ['CHAIR_Gaming_MyMax_MX6', 'CHAIR_Armrests', 'CHAIR_Backrest', 'CHAIR_Base', 'CHAIR_Logo_MX6', 'CHAIR_Logo_MYMAX', 'CHAIR_Seat_Arms',
        'CHAIR_Slot_Trims', 'CUT_Chair_Slots', 'PROP_MacBook_Air_13_M4', 'PROP_MagSafe_Plug', 'PROP_Cable_MagSafe']
with bpy.data.libraries.load(V4, link=False) as (src, dst):
    dst.objects = [n for n in want if n in src.objects]
for ob in dst.objects:
    target = 'FURN_Chair' if ob.name.startswith(('CHAIR_', 'CUT_Chair')) else 'PROPS_Lived_In'
    P.coll(target).objects.link(ob)
    if ob.name.startswith('CUT_'): ob.hide_render = True; ob.hide_viewport = True
bpy.data.objects['CHAIR_Gaming_MyMax_MX6'].location.x = 0.78          # your chair's spot in the current room (photos 7/15/16)
for n in ('PROP_MacBook_Air_13_M4', 'PROP_MagSafe_Plug', 'PROP_Cable_MagSafe'):
    o = bpy.data.objects.get(n)
    if o: o.location.x -= 0.04                                         # v4 desk sat 4 cm forward on the teak boards

# ---------------------------------------------------------------- 2. shared photoreal upgrades
P.render_settings()
P.upgrade_paint(); P.upgrade_floor(); P.upgrade_glass(); P.upgrade_metals()
P.oak_scan(); P.bedspread_photo()
P.rug_photo(); P.puzzle_rebuild()
P.fan_rebuild(); P.stool_rebuild(); P.echo_dot(x=9.0, y=26.0, z=80.0)
P.window_exterior(); P.plant_outside(); P.piano_and_pillows(); P.macbook_screen(True); P.bed_imperfections()
P.ensure_worlds()
SB.fix_shelf_heights(); SB.build_books(0.0); SB.decor_top(0.0); SB.shelf_fairy_lights(0.0)
P.desk_lamp_asset((46.5, 9.0, 80.0), -67.0)
lo_, hi_ = P.desk_lamp_pose((-6.0, 10.0, -30.0))
for n in ('PROP_Desk_Lamp', 'PROP_Desk_Lamp_Shade', 'PROP_Desk_Lamp_Bulb'):
    o = bpy.data.objects.get(n)
    if o: o.hide_render = True
lt = bpy.data.lights.new('LIGHT_Desk_Lamp', 'SPOT'); lt.spot_size = 1.9; lt.spot_blend = 0.4; lt.shadow_soft_size = 0.02
lt.use_temperature = True; lt.temperature = 3000.0; lt.energy = 0.0
lo = bpy.data.objects.new('LIGHT_Desk_Lamp', lt); P.coll('LIGHT_Lighting').objects.link(lo)
lo.location = Vector(((lo_.x + hi_.x) / 2, (lo_.y + hi_.y) / 2, lo_.z + 4.0)) * P.S
print('LAMP LIGHT', P.desk_lamp_light())

# ---------------------------------------------------------------- 3. twin-only details
# your handwritten notes (crops of photos 27/34/47/48) on the existing note sheets
notes = sorted(f for f in os.listdir(os.path.join(P.TEX, 'notes')) if f.endswith('.png'))
wn = bpy.data.objects.get('PROP_Wall_Notes')
if wn:
    me = wn.data; me.materials.clear()
    for f in notes:
        m = P.material(f'M_Note_{f[:-4]}', '#EEE9DC', 0.85); nt = m.node_tree; p = P.bsdf(m)
        t = P.tex(nt, os.path.join(P.TEX, 'notes', f), None, -400, 200); nt.links.new(t.outputs['Color'], p.inputs['Base Color'])
        me.materials.append(m)
    # each sheet: its own material + 0-1 UVs on its wall-facing side
    import bmesh
    bm = bmesh.new(); bm.from_mesh(me); uv = bm.loops.layers.uv.verify(); bm.faces.ensure_lookup_table()
    islands, seen = [], set()
    for f in bm.faces:
        if f.index in seen: continue
        stack, isl = [f], []
        while stack:
            q = stack.pop()
            if q.index in seen: continue
            seen.add(q.index); isl.append(q)
            for e in q.edges:
                for g in e.link_faces:
                    if g.index not in seen: stack.append(g)
        islands.append(isl)
    big = {'curse_discipline.png', 'break_you.png'}
    for k, isl in enumerate(islands):
        vs = {v for f in isl for v in f.verts}; c = sum((v.co for v in vs), Vector()) / len(vs)
        on_w2 = c.y < 0.02
        name = ('curse_discipline.png' if c.x < 0.62 else 'break_you.png') if on_w2 else [n for n in notes if n not in big][k % (len(notes) - 2)]
        mi = notes.index(name)
        ax = (0, 2) if on_w2 else (1, 2)
        lo3 = [min(v.co[a] for v in vs) for a in ax]; hi3 = [max(v.co[a] for v in vs) for a in ax]
        for f in isl:
            f.material_index = mi
            for l in f.loops:
                u = (l.vert.co[ax[0]] - lo3[0]) / max(hi3[0] - lo3[0], 1e-6); w = (l.vert.co[ax[1]] - lo3[1]) / max(hi3[1] - lo3[1], 1e-6)
                l[uv].uv = (1 - u if on_w2 else u, w)      # wall 2 is seen facing -y: its right-hand side is -x
    bm.to_mesh(me); bm.free()

import random
rng = random.Random(15); g = P.Geo(); plates = [(78.0, 87.5, 125.5, 139.5), (99.0, 108.6, 125.5, 139.5)]; placed = 0
small = [n for n in notes if n not in ('curse_discipline.png', 'break_you.png')]
for _ in range(400):
    w, h = rng.choice([(7.6, 7.6), (10.5, 14.8), (14.8, 10.5), (10.0, 10.0), (14.8, 21.0)])
    y, z = rng.uniform(3 + w / 2, 114 - w / 2), rng.uniform(100.5 + h / 2, 140.5 - h / 2)
    if any(y + w / 2 > a - 0.5 and y - w / 2 < b + 0.5 and z + h / 2 > c0 - 0.5 and z - h / 2 < d0 + 0.5 for a, b, c0, d0 in plates): continue
    r = math.radians(rng.uniform(-3, 3)); x0 = 0.12 + 0.012 * placed
    g.obox((x0, y, z), (0, math.cos(r), math.sin(r)), (0, -math.sin(r), math.cos(r)), (1, 0, 0), w / 2, h / 2, 0.01, notes.index(small[placed % len(small)]))
    placed += 1
    if placed >= 42: break
nob = g.finish('PROP_Wall_Notes_Collage', 'PROPS_Lived_In', [bpy.data.materials[f'M_Note_{n[:-4]}'] for n in notes])
for p_ in nob.data.polygons:                       # 0-1 UVs per sheet on its room-facing side
    vs = [nob.data.vertices[i].co for i in p_.vertices]
    ys_ = [v.y for v in vs]; zs_ = [v.z for v in vs]
    for li in p_.loop_indices:
        co = nob.data.vertices[nob.data.loops[li].vertex_index].co
        nob.data.uv_layers[0].data[li].uv = ((co.y - min(ys_)) / max(max(ys_) - min(ys_), 1e-6), (co.z - min(zs_)) / max(max(zs_) - min(zs_), 1e-6))

# socket on wall 2 at the foot of the bed with your white charger (photos 34/35)
g = P.Geo(); g.box(88.0, 99.8, 0.0, 0.8, 34.5, 42.0, 0)
for yz in ((91.0, 38.2), (96.8, 38.2)): g.cyl((yz[0], 0.8, yz[1]), (yz[0], 0.95, yz[1]), 2.0, 20, 1)
g.box(95.0, 98.6, 0.9, 4.6, 36.4, 40.0, 0)                          # USB-C charger brick
g.finish('ELEC_Outlet_W2_Bed', 'ARCH_Electrical', ['M_Plastic_White', 'M_Socket'], bevel=(0.25, 2))['dim_source'] = 'PHOTO'
cu = bpy.data.curves.new('PROP_Cable_Charger', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0022; cu.bevel_resolution = 3
sp = cu.splines.new('NURBS'); pts = [(96.8, 4.6, 37.0), (97.5, 6.0, 25.0), (98.0, 7.5, 2.0), (90.0, 14.0, 0.25), (70.0, 40.0, 0.25), (52.0, 60.0, 0.25), (49.5, 64.0, 30.0), (40.0, 60.0, 80.2)]
sp.points.add(len(pts) - 1); sp.order_u = 3; sp.use_endpoint_u = True
for pt, q in zip(sp.points, pts): pt.co = (q[0] * P.S, q[1] * P.S, q[2] * P.S, 1.0)
cu.materials.append(P.material('M_Cable_White', '#EDEDEA', 0.4)); P.coll('PROPS_Lived_In').objects.link(bpy.data.objects.new('PROP_Cable_Charger', cu))

# ---------------------------------------------------------------- 4. cameras: same human eye heights as v5 + your photo spots
E, Z = P.EYE_STAND, P.EYE_SEAT
P.cam('CAM_PR_01_Door', (52, 262, E), (175, 0, 115), 24, 8.0)
P.cam('CAM_PR_02_Toward_Door', (90, 30, E), (190, 290, 110), 24, 8.0)
P.cam('CAM_PR_03_Bed_Corner', (128, 214, E), (300, 40, 105), 28, 8.0)
P.cam('CAM_PR_04_Desk_Seated', (98, 52, Z), (10, 60, 112), 24, 5.6)
P.cam('CAM_PR_05_From_Bed', (276, 58, 112), (20, 175, 120), 28, 8.0)
P.cam('CAM_PR_06_Piano_Wall', (80, 120, 150), (300, 150, 118), 35, 5.6)
P.cam('CAM_PR_D3_Books', (92, 60, 172), (4, 45, 182), 35, 4.0, level=False)
P.cam('CAM_PR_D2_Desk_Lamp', (84, 98, 118), (24, 26, 100), 50, 2.8, level=False)
P.cam('CAM_PR_D4_Window', (170, 170, 150), (165, 0, 158), 35, 5.6)
P.cam('CAM_PR_08_Lying_In_Bed', (234, 66, 84), (40, 230, 165), 20, 5.6, level=False)      # lying in bed, head by the pillows
P.cam('CAM_PR_09_Piano_Stool', (222, 170, 141), (296, 150, 92), 24, 5.6, level=False)      # sitting at the piano (stool 66 cm)
P.cam('CAM_PR_10_Chair_Turned', (84, 58, 118), (300, 30, 96), 24, 8.0)                      # desk chair turned to the room
P.cam('CAM_Sun_Study', (62, 12, 262), (205, 200, 25), 16, 11.0, level=False)       # analysis view from the window corner: where the sun lands
sc.camera = bpy.data.objects['CAM_PR_01_Door']

sc['experiment'] = 'round 5: photoreal digital twin of the current room (as photographed), for realism checks against your photos'
bpy.context.preferences.filepaths.save_version = 0
out = os.path.join(P.HERE, 'Bedroom_Current_Photoreal.blend')
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print('SAVED', out)
