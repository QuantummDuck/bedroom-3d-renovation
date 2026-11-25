"""Layout round 9, built on Bedroom_Teak_Navy_v8_layout.blend -> ../teak_navy/Bedroom_Teak_Navy_v9_layout.blend
  Blender -b ../teak_navy/Bedroom_Teak_Navy_v8_layout.blend --python layout_v9.py
- aquarium taken out of the room (kept in the hidden STORAGE_Removed collection)
- 1 rolling drawer unit (user changed from 4 to 1) (3 drawers, round knobs, twin-wheel casters) under the table, tops 0.25 cm under the table top
- teak boards on wall 3 standardised: 25 equal boards of 9.52 cm with 0.6 cm black gaps (floor to crown, no cut boards)
- skirting + crown molding + cove ledge share one material, M_Rodape, so their colour can be changed in one place
Coordinates in cm (x from wall 4 to wall 3, y from the window wall to the door wall)."""
import bpy, bmesh, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import photoreal_common as P
from mathutils import Vector, Matrix

S = 0.01; sc = bpy.context.scene; OBJ = bpy.data.objects
FACE, TAB_TOP_UNDERSIDE = 296.0, 72.0                    # board face on wall 3; table top is 72-75 cm
CLEAR_TOP = 0.25                                          # drawer top -> table underside


def T(x=0.0, y=0.0, z=0.0): return Matrix.Translation(Vector((x, y, z)) * S)
def move(names, M):
    bpy.context.view_layer.update()
    for n in names:
        o = OBJ.get(n)
        if o is not None: o.matrix_world = M @ o.matrix_world
    bpy.context.view_layer.update()


# ------------------------------------------------------------------ 1. aquarium out of the room (not deleted)
st = bpy.data.collections['STORAGE_Removed']
for o in [o for o in OBJ if o.name.startswith('AQ_')]:
    for c in list(o.users_collection): c.objects.unlink(o)
    st.objects.link(o)
move(['PROP_MacBook_Air_13_M4', 'PROP_MagSafe_Plug', 'PROP_Cable_MagSafe'], T(0, 8.0, 0))   # back to where they were before the aquarium
move(['PROP_Echo_Dot'], T(0, 52.0, 0))

# ------------------------------------------------------------------ 2. standardised teak boards (rebuilt in the object's own local frame)
BACK, FELT, BT, WALL, TOP, GAP, NB = 1.6, 0.4, 2.0, 290.0, 252.5, 0.6, 25
BW = (TOP - (NB - 1) * GAP) / NB                         # 9.524 cm
ob = OBJ['STUDY_Wood_Wall_Boards']; rng = random.Random(9)
bm = bmesh.new(); tint = bm.verts.layers.float.new('board_tint'); uv = bm.loops.layers.uv.new('UVMap')
def bbox(x0, x1, y0, y1, z0, z1, mi, t, du, dv):
    v = [bm.verts.new((x * S, y * S, z * S)) for x, y, z in [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                                                              (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]]
    for vv in v: vv[tint] = t
    for idx in [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]:
        f = bm.faces.new([v[i] for i in idx]); f.material_index = mi; f.normal_update()
        ax = max(range(3), key=lambda i: abs(f.normal[i]))
        for lp in f.loops:                               # grain along the board (y), as before
            c = lp.vert.co
            lp[uv].uv = (c.y + du, c.z + dv) if ax == 0 else (c.z + du, c.x + dv) if ax == 1 else (c.y + du, c.x + dv)
bbox(BACK, BACK + FELT, 0, WALL, 0, TOP, 1, 0.5, 0, 0)                                  # black backing
for k in range(NB):
    z0 = k * (BW + GAP)
    bbox(BACK + FELT, BACK + FELT + BT, 0, WALL, z0, z0 + BW, 0, rng.random(), rng.uniform(0, 0.9), rng.uniform(0, 0.9))
old = ob.data; me = bpy.data.meshes.new('STUDY_Wood_Wall_Boards'); bm.to_mesh(me); bm.free()
for m in old.materials: me.materials.append(m)
ob.data = me; bpy.data.meshes.remove(old)
ob['note'] = f'{NB} equal horizontal teak boards {BW:.2f} cm + {GAP} cm black gaps, floor to crown (standardised in round 9)'

# ------------------------------------------------------------------ 3. make room under the table
move(['PROP_Footrest'], T(0, 4.0, 0))                                        # clear of the corner drawer unit
move(['DECOR_Purifier_Black_Cylinder'], T(285 - 278, 172 - 120))              # deep under the table at the bed end
pw = OBJ['DECOR_Purifier_White']; pw.location = Vector((11.0, 195.0, 0)) * S; pw.rotation_euler = (0, 0, math.radians(90))   # by the wardrobe end, grille to the room

# ------------------------------------------------------------------ 4. one rolling drawer unit (sketch: 3 drawers, round knobs, wheels)
UW, UD, UH = 40.0, 45.0, TAB_TOP_UNDERSIDE - CLEAR_TOP     # 40 wide, 45 deep, 71.75 tall incl. casters
CH, PT = 6.5, 1.8                                          # caster height, panel thickness
teak, knob_m = bpy.data.materials['M_Boards_teak'], bpy.data.materials['M_Steel_Black']
caster_m, wheel_m = bpy.data.materials['M_Plastic_Black'], bpy.data.materials['M_Rubber_Black']


def unit(name, seed):
    r = random.Random(seed); g = P.Geo(); hx, hy = UW / 2, UD / 2; z0, z1 = CH, UH
    g.box(-hx, -hx + PT, -hy, hy, z0, z1).box(hx - PT, hx, -hy, hy, z0, z1)              # sides
    g.box(-hx + PT, hx - PT, -hy, hy, z1 - PT, z1).box(-hx + PT, hx - PT, -hy, hy, z0, z0 + PT)   # top, bottom
    g.box(-hx + PT, hx - PT, -hy, -hy + 0.6, z0 + PT, z1 - PT)                             # back
    inner0, inner1, rail = z0 + PT, z1 - PT, 1.2
    bays = (inner1 - inner0 - 2 * rail) * 0.25
    heights = [bays * 2, bays, bays]                                                      # bottom (big), middle, top
    z = inner0
    for i, h in enumerate(heights):
        g.box(-hx + PT + 0.3, hx - PT - 0.3, hy - 2.0, hy - 0.2, z + 0.3, z + h - 0.3)    # drawer front, inset in the frame
        kz = z + h / 2 if i else z + h * 0.62
        g.cyl((0, hy - 0.2, kz), (0, hy + 0.9, kz), 0.6, 16, 1).cyl((0, hy + 0.9, kz), (0, hy + 2.4, kz), 1.6, 24, 1)   # round knob
        z += h
        if i < 2: g.box(-hx + PT, hx - PT, hy - 1.8, hy, z, z + rail); z += rail          # rail between drawers
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):                                   # twin-wheel casters
        cx, cy = sx * (hx - 4.5), sy * (hy - 4.5); yaw = math.radians(r.uniform(-40, 40) + (0 if r.random() < 0.6 else 90))
        ux, uy = math.cos(yaw), math.sin(yaw)                                             # wheel axle direction
        fx, fy = -uy, ux                                                                   # trailing direction
        g.box(cx - 2.2, cx + 2.2, cy - 2.2, cy + 2.2, z0 - 0.3, z0, 2)                    # mounting plate
        g.cyl((cx, cy, z0 - 0.3), (cx, cy, 4.7), 1.3, 20, 2)                              # swivel
        ax, ay = cx + fx * 1.4, cy + fy * 1.4; R = 2.4
        for side in (-1, 1):
            p0 = Vector((ax + ux * side * 0.4, ay + uy * side * 0.4, R)); p1 = Vector((ax + ux * side * 1.9, ay + uy * side * 1.9, R))
            g.cyl(p0, p1, R, 24, 3)                                                       # wheel
        g.cyl((ax - ux * 0.45, ay - uy * 0.45, R), (ax + ux * 0.45, ay + uy * 0.45, R), 2.0, 24, 2)   # hub cover between the wheels
    o = g.finish(name, 'FURN_Desk', [teak, knob_m, caster_m, wheel_m], bevel=(0.12, 1))
    o['dim_source'] = 'EST'; o['note'] = f'rolling drawer unit {UW:.0f} x {UD:.0f} x {UH:.2f} cm incl. casters; top {CLEAR_TOP} cm under the table'
    return o


SPOTS = [('DRAWER_Unit', (273.0, 68.0), 90)]          # one unit (user): under the corner of the table, beside the chair, front to the chair
for i, (name, (x, y), rz) in enumerate(SPOTS):
    o = unit(name, 90 + i); o.location = Vector((x, y, 0)) * S; o.rotation_euler = (0, 0, math.radians(rz))

# ------------------------------------------------------------------ 5. one material for the 'rodape': skirting + crown molding + cove ledge
rod = bpy.data.materials.get('M_Rodape') or bpy.data.materials['M_Trim_White'].copy()
rod.name = 'M_Rodape'; P.bsdf(rod).inputs['Base Color'].default_value = (*P.lin('#F0EFEA'), 1)
for n in ('ARCH_Baseboards', 'ARCH_Crown_Molding', 'ARCH_Cove_Ledge'):
    me_ = OBJ[n].data; me_.materials.clear(); me_.materials.append(rod)
rod['note'] = 'Skirting, crown molding and cove ledge colour (rodape). Change Base Color here.'

# ------------------------------------------------------------------ 6. cameras for this round
E = P.EYE_STAND
P.cam('CAM_R1_Wide_Table_Corner', (278, 22, 150), (40, 240, 100), 14, 8.0)
P.cam('CAM_R3_Skirting_Door_Corner', (95, 186, 45), (5, 252, 8), 24, 5.6, level=False)
P.cam('CAM_R4_Crown_Corner', (130, 150, 200), (0, 260, 255), 24, 5.6, level=False)
P.cam('CAM_DR1_Drawers_Wide', (165, 150, 125), (262, 62, 35), 24, 8.0, level=False)
P.cam('CAM_DR2_Drawer_Front', (212, 92, 20), (250, 70, 9), 35, 4.0, level=False)       # low: front, knobs and casters
P.cam('CAM_DR3_Corner_Unit', (200, 72, 48), (262, 68, 32), 35, 4.0, level=False)

sc['experiment'] = (sc.get('experiment', '') + ' | round 9: aquarium stored, 1 rolling drawer unit under the table, standardised 9.5 cm boards, '
                    'rodape (skirting + crown + ledge) material M_Rodape')
bpy.context.preferences.filepaths.save_version = 0
out = os.path.join(P.ROOT, 'experiments', 'teak_navy', 'Bedroom_Teak_Navy_v9_layout.blend')
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print('SAVED', out, 'board width', round(BW, 3))
