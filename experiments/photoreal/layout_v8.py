"""Layout round 8 = round 7 with the table extended to a 25 cm gap and a 45 x 21 x 30 aquarium (moves between 4 table spots; see AQ_Aquarium).
Round 7 = round 6 + table 75 high, 75 cm gap to the wardrobe, teak boards moved to wall 3 (bed + shelves wall), new plug.
Built on Bedroom_Teak_Navy_v5.blend -> ../teak_navy/Bedroom_Teak_Navy_v8_layout.blend
  Blender -b ../teak_navy/Bedroom_Teak_Navy_v5.blend --python layout_v6.py
v5 and every older file stay untouched; this only writes the new file.

Plan (from your sketch; top view with the window at the top is the same as the model's top view):
  wardrobe   on wall 4 (desk wall), window corner, long side along the wall, doors facing the room (you face its side when the door opens)
  table      V/L shape: wall 3 from the bed's side edge up to the window corner, then along the window wall to 50 cm short of the wardrobe
  bed        wall 1 / wall 3 corner (where the wardrobe was), head at wall 3
  shelves    wall 3 (the old frame wall), over the table;  puzzle frame and piano removed (kept in a hidden collection, not deleted)
Coordinates in cm: x from wall 4 (0) to wall 3 (300), y from wall 2 / window (0) to wall 1 / door (290)."""
import bpy, bmesh, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import photoreal_common as P
from mathutils import Vector, Matrix

S = 0.01; RW, RD, RH = 300.0, 290.0, 270.0
FRONT = 4.0
FACE = 296.0                                              # boards now on wall 3: their face is at x = 296 (wall 4 is plain navy again)
sc = bpy.context.scene; OBJ = bpy.data.objects


def T(x=0.0, y=0.0, z=0.0): return Matrix.Translation(Vector((x, y, z)) * S)
def about(deg, cx, cy): return T(cx, cy) @ Matrix.Rotation(math.radians(deg), 4, 'Z') @ T(-cx, -cy)
def refresh(): bpy.context.view_layer.update()


def move(names, M):
    """Rigid move of top-level objects (their children follow). names: object names or objects."""
    refresh()
    for n in names:
        o = OBJ.get(n) if isinstance(n, str) else n
        if o is not None: o.matrix_world = M @ o.matrix_world
    refresh()


def delete(*names):
    for n in names:
        o = OBJ.get(n)
        if o: bpy.data.objects.remove(o)


def loft(g, path, side_n, w_axis, profile, mi=0):
    """Mitred sweep of a 2-D profile along a polyline (cm), same maths as build_bedroom.MB.loft (open path)."""
    path = [Vector(p) for p in path]; n = len(path); N, W = Vector(side_n), Vector(w_axis)
    sides = [N.cross((path[i + 1] - path[i]).normalized()) for i in range(n - 1)]
    rings = []
    for k in range(n):
        sp = sides[k - 1] if k > 0 else sides[0]; sn = sides[k] if k < n - 1 else sides[-1]
        m = (sp + sn).normalized(); m = m / max(m.dot(sn), 1e-6)
        rings.append([g.v(path[k] + u * m + w * W) for (u, w) in profile])
    npf = len(profile)
    for k in range(n - 1):
        for j in range(npf):
            j2 = (j + 1) % npf; g.f((rings[k][j], rings[k + 1][j], rings[k + 1][j2], rings[k][j2]), mi)
    g.f(rings[0], mi); g.f(rings[-1][::-1], mi)
    return g


# ------------------------------------------------------------------------------------------ layout constants
WARD_BACK, WARD_D, WARD_L = 0.0, 63.0, 181.0              # wardrobe: back on the bare wall 4, 63 deep, 181 along wall 4 from the window corner
WARD_FRONT = WARD_BACK + WARD_D                           # 63
CLEAR = 25.0                                              # gap between table end and wardrobe (user)
TAB_D, TAB_T, TAB_H = 49.0, 3.0, 75.0
TAB_END_X = WARD_FRONT + CLEAR                            # 138 : window-wall leg stops here
TAB_END_Y = 290.0 - 95.8                                  # 194.2 : wall-3 leg starts where the bed's side ends

# ------------------------------------------------------------------------------------------ 0. storage for what leaves the room
st = bpy.data.collections.get('STORAGE_Removed') or bpy.data.collections.new('STORAGE_Removed')
if st.name not in sc.collection.children: sc.collection.children.link(st)
st['note'] = 'Removed from the layout on purpose (piano, puzzle frame). Not deleted: enable the collection and move them wherever you like.'


def stash(collection_name=None, names=()):
    objs = list(bpy.data.collections[collection_name].objects) if collection_name else [OBJ[n] for n in names if n in OBJ]
    for o in objs:
        for c in list(o.users_collection): c.objects.unlink(o)
        st.objects.link(o)


stash('FURN_Piano'); stash(names=('DECOR_Puzzle_Frame', 'DECOR_Puzzle_Picture'))
bpy.context.view_layer.layer_collection.children['STORAGE_Removed'].exclude = True      # out of the scene (and every render) but still in the file
delete('LED_Piano_Halo', 'LED_Channels_Piano', 'LED_Diffusers_Piano', 'PROP_Cable_Piano', 'PROP_Cable_Purifier')

# ------------------------------------------------------------------------------------------ 1. wardrobe: wall 4, window corner, doors to the room
c0 = (209.5, 258.5); c1 = (WARD_BACK + WARD_D / 2, WARD_L / 2)
M_ward = T(c1[0] - c0[0], c1[1] - c0[1]) @ about(90, *c0)
move(['WARD_Wardrobe', 'LED_Wardrobe_Plinth', 'LED_Channels_Wardrobe', 'LED_Diffusers_Wardrobe'], M_ward)

# ------------------------------------------------------------------------------------------ 2. bed: wall 1 / wall 3 corner (mirror of its old window-wall spot)
M_mirror = T(-4.0, RD) @ Matrix.Diagonal((1, -1, 1, 1))          # mirror to the door wall, 4 cm off wall 3 (boards)
move(['BED_Bed'], M_mirror)
delete('BED_Headboard_Wall2', 'BED_Headboard_Wall3', 'ELEC_Outlet_W3_Low', 'LED_BedPanel_W2', 'LED_BedPanel_W3', 'LED_Channels_BedPanel', 'LED_Diffusers_BedPanel')
tk = bpy.data.materials['M_Boards_teak']
g = P.Geo(); g.box(100.5, FACE, RD - 1.8, RD, 0, 87.5)
P.coll('FURN_Bed'); g.finish('BED_Headboard_Wall1', 'FURN_Bed', [tk], bevel=(0.15, 1))['dim_source'] = 'PHOTO'      # the teak boards on wall 3 are its head panel now

# ------------------------------------------------------------------------------------------ 3. workstation (shelves, desk props, chair) rigidly to wall 3
M_ws = T(-4.0) @ about(180, 152.0, 93.75)                             # x -> 304 - x (board face x=4 -> wall 3), y -> 187.5 - y
ws = ['SHELF_Wall_Shelves', 'LED_Shelf_1', 'LED_Shelf_2', 'LED_Shelf_3', 'LED_Channels_Shelves', 'LED_Diffusers_Shelves',
      'PROP_MacBook_Air_13_M4', 'PROP_MagSafe_Plug', 'PROP_Cable_MagSafe', 'PROP_Desk_Items', 'PROP_Echo_Dot', 'PROP_Footrest',
      'LAMP_PH_Root', 'LIGHT_Desk_Lamp', 'PROP_Cable_Lamp', 'CHAIR_Gaming_MyMax_MX6', 'PROP_Wall_Notes',
      'DESK_Cable_Grommet', 'CUT_Grommet_Hole']
ws += [o.name for o in bpy.data.collections['PROPS_Books'].objects if o.parent is None]
grom = ['DESK_Cable_Grommet', 'CUT_Grommet_Hole']
move([n for n in ws if n not in grom], M_ws)
move(grom, T(274.0, 0, 0))                                  # old corner (13, 13) -> new corner (291, 13): same 9 cm / 13 cm from the two walls

TABLETOP = ['PROP_MacBook_Air_13_M4', 'PROP_MagSafe_Plug', 'PROP_Cable_MagSafe', 'PROP_Desk_Items', 'PROP_Echo_Dot', 'LAMP_PH_Root', 'LIGHT_Desk_Lamp'] + grom
move(TABLETOP, T(0, 0, -5.0))                               # table is 5 cm lower now
move(['STUDY_Wood_Wall_Boards'], about(180, 150.0, 145.0))    # teak boards: wall 4 -> wall 3

# ------------------------------------------------------------------------------------------ 4. the V-shaped (L) table
delete('DESK_Wood', 'DESK_Legs', 'LED_Under_Desk', 'LED_Channels_Desk', 'LED_Diffusers_Desk')
desk = OBJ['DESK_Desk']; desk.location = Vector((FACE, 0, 0)) * S; desk.rotation_euler = (0, 0, 0)
x_in = FACE - TAB_D                                           # 251: inner edge of the wall-3 arm
pts = [(FACE, 0), (FACE, TAB_END_Y), (x_in, TAB_END_Y), (x_in, TAB_D), (TAB_END_X, TAB_D), (TAB_END_X, 0)]
top = P.Geo().prism((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1), pts, TAB_H - TAB_T, TAB_H, 0)
tw = top.finish('DESK_Wood', 'FURN_Desk', [tk], bevel=(0.1, 1))
tw['dim_source'] = 'USER'; tw['note'] = 'L/V table: 49 deep, 3 cm top, 80 high; wall-3 arm 194 long from the bed side, window-wall arm ends 50 cm before the wardrobe'
cut = OBJ['CUT_Grommet_Hole']
if 'Grommet_Hole' not in tw.modifiers:
    bo = tw.modifiers.new('Grommet_Hole', 'BOOLEAN'); bo.operation = 'DIFFERENCE'; bo.object = cut; bo.solver = 'EXACT'
steel, glide = bpy.data.materials['M_Steel_Black'], bpy.data.materials['M_Rubber_Black']
lg_ = P.Geo()
legs = [(FACE - 5, TAB_END_Y - 6.5), (FACE - 45, TAB_END_Y - 6.5),         # free end by the bed: 2 square 3x3 legs, set in 6.5 cm so they clear the bedspread's drape
        (TAB_END_X + 4, 5), (TAB_END_X + 4, 45),                       # free end by the wardrobe: 2 legs
        (FACE - 45, TAB_D - 4)]                                          # one more under the inner corner (the old desk leaned on a wall at both ends)
for xc, yc in legs:
    lg_.box(xc - 1.5, xc + 1.5, yc - 1.5, yc + 1.5, 0.4, TAB_H - TAB_T, 0)
    lg_.cyl((xc, yc, 0.0), (xc, yc, 0.4), 1.1, 24, 1)
lgo = lg_.finish('DESK_Legs', 'FURN_Desk', [steel, glide], bevel=(0.15, 1))
lgo['dim_source'] = 'USER'; lgo['note'] = 'square black steel legs 3 x 3 cm (round-4 choice); the 5th leg under the inner corner is new'
refresh()                                                   # the empty's new matrix must be current before it becomes the parent
for ob in (tw, lgo):
    ob.parent = desk; ob.matrix_parent_inverse = desk.matrix_world.inverted()

# ------------------------------------------------------------------------------------------ 5. stool, rug, slippers, purifiers
refresh()
stool_parts = ['STOOL_Body', 'STOOL_Seat', 'STOOL_Seat_Welt']
move(stool_parts, T(150 - 228, 80 - 166))                    # now beside the window-wall arm of the table
move(['DECOR_Rug'], T(75.0 - 110.2, 55.0 - 96.4))           # 130 x 188 in front of the wardrobe doors, reaching a little under the table
OBJ['PROP_Slipper_1'].location = Vector((98.0, 224.0, 0)) * S
OBJ['PROP_Slipper_2'].location = Vector((101.0, 240.0, 0)) * S
move(['DECOR_Purifier_Black_Cylinder'], T(278 - 288, 120 - 117))      # under the wall-3 arm
OBJ['DECOR_Purifier_White'].location = Vector((160.0, 22.0, 0)) * S   # under the window-wall arm

# ------------------------------------------------------------------------------------------ 6. architecture that depended on the old wardrobe spot
delete('ARCH_Crown_Molding', 'ARCH_Baseboards', 'ARCH_Cove_Ledge', 'LED_Cove_1', 'LED_Cove_2', 'LED_Cove_3', 'LED_Cove_4',
       'LED_Channels_Cove', 'LED_Diffusers_Cove')
BB_H, BB_T, TRIM_W, DOOR_X0, DOOR_W = 10.0, 1.5, 7.5, 15.0, 71.5
prof = [(0, 0), (BB_T, 0), (BB_T, BB_H - 1.2), (BB_T - 0.5, BB_H), (0, BB_H)]
g = P.Geo()
loft(g, [(WARD_FRONT, 0, 0), (RW, 0, 0), (RW, RD, 0), (DOOR_X0 + DOOR_W + TRIM_W, RD, 0)], (0, 0, 1), (0, 0, 1), prof)
loft(g, [(DOOR_X0 - TRIM_W, RD, 0), (0, RD, 0), (0, WARD_L, 0)], (0, 0, 1), (0, 0, 1), prof)
g.finish('ARCH_Baseboards', 'ARCH_Architecture', ['M_Trim_White'])['note'] = 'rebuilt for the new wardrobe spot (stops at the wardrobe, runs the full wall 3 and wall 1)'
d_, (s1, s2) = 17.5, (13.0, 8.6)
cp = [(0, d_), (1.0, d_), (1.0, s1), (2.0, s1), (2.0, s2), (3.2, s2), (3.2, 7.0)]
cp += [(12 + 8.8 * math.cos(t), 7 + 7 * math.sin(t)) for t in [math.pi + i * (math.pi / 2) / 6 for i in range(1, 7)]] + [(0, 0)]
g = P.Geo(); loft(g, [(WARD_FRONT, 0, RH), (RW, 0, RH), (RW, RD, RH), (0, RD, RH), (0, WARD_L, RH)], (0, 0, 1), (0, 0, -1), cp)
g.finish('ARCH_Crown_Molding', 'ARCH_Architecture', ['M_Crown_Plaster'])['note'] = 'rebuilt: interrupted by the wardrobe on walls 2/4, continuous on walls 1 and 3'
lg = P.Geo()
lg.box(WARD_FRONT + 0.5, FACE, 0, 5, 243, 246).box(WARD_FRONT + 0.5, FACE, 4, 5, 246, 248.5)                          # wall 2
lg.box(FACE - 5, FACE, 5, RD, 243, 246).box(FACE - 5, FACE - 4, 5, RD - 5, 246, 248.5)                                # wall 3 (on the boards)
lg.box(5, FACE - 5, RD - 5, RD, 243, 246).box(5, FACE - 5, RD - 5, RD - 4, 246, 248.5)                                # wall 1
lg.box(0, 5, WARD_L + 0.5, RD, 243, 246).box(4, 5, WARD_L + 0.5, RD - 5, 246, 248.5)                                  # wall 4 (bare wall now)
lg.finish('ARCH_Cove_Ledge', 'ARCH_Architecture', ['M_Crown_Plaster'], bevel=(0.15, 1))['note'] = 'LED cove ledge, rebuilt for the new layout'

# ------------------------------------------------------------------------------------------ 7. LED strips that follow the new furniture (same maths as round 4)
GROUPS = {'Cove': 10.0, 'BedPanel': 45.0, 'Desk': 20.0}
LC = bpy.data.collections['LIGHT_LED_Strips']; alu = bpy.data.materials['M_Metal_Brushed']


def drive(idblock, path, expr, props, index=-1):
    fc = idblock.driver_add(path, index) if index >= 0 else idblock.driver_add(path)
    d = fc.driver; d.type = 'SCRIPTED'
    for vname, prop, pidx in props:
        v = d.variables.new(); v.name = vname; v.type = 'SINGLE_PROP'; v.targets[0].id_type = 'SCENE'; v.targets[0].id = sc
        v.targets[0].data_path = f'["{prop}"]' + (f'[{pidx}]' if pidx is not None else '')
    d.expression = expr


def strip(key, name, p0, p1, normal, tilt_dir, tilt_deg, diff, chan, width=1.2, spread=130):
    p0, p1, n, td = Vector(p0), Vector(p1), Vector(normal).normalized(), Vector(tilt_dir).normalized()
    a = p1 - p0; L = a.length; a.normalize(); side = n.cross(a).normalized(); c = (p0 + p1) / 2
    chan.prism(c, a, side, n, [(-L / 2, -width / 2 - 0.2), (L / 2, -width / 2 - 0.2), (L / 2, width / 2 + 0.2), (-L / 2, width / 2 + 0.2)], -0.7, 0.0)
    diff.prism(c, a, side, n, [(-L / 2 + 0.1, -width / 2), (L / 2 - 0.1, -width / 2), (L / 2 - 0.1, width / 2), (-L / 2 + 0.1, width / 2)], 0.0, 0.07)
    d = (n * math.cos(math.radians(tilt_deg)) + td * math.sin(math.radians(tilt_deg))).normalized()
    lt = bpy.data.lights.new(name, 'AREA'); lt.shape = 'RECTANGLE'; lt.size = width * S; lt.size_y = L * S; lt.spread = math.radians(spread)
    ob = bpy.data.objects.new(name, lt); LC.objects.link(ob); ob.location = (c + n * 0.12) * S
    up = a - d * a.dot(d)
    ob.rotation_euler = Matrix((up.cross(-d).normalized() * -1, up.normalized(), -d)).transposed().to_euler() if up.length > 1e-6 else (-d).to_track_quat('Z', 'Y').to_euler()
    for i in range(3): drive(lt, 'color', 'var', [('var', f'{key}_RGB', i)], i)
    drive(lt, 'energy', f'var * m * {GROUPS[key] * L / 100:.2f}', [('var', f'{key}_Brightness', None), ('m', 'LED_Master', None)])
    ob['group'] = key


def group(key, items):
    ch, df = P.Geo(), P.Geo()
    for it in items: strip(key, *it[:6], df, ch, *it[6:])
    ch.finish(f'LED_Channels_{key}', 'LIGHT_LED_Strips', [alu])
    P.visible_only(df.finish(f'LED_Diffusers_{key}', 'LIGHT_LED_Strips', [bpy.data.materials[f'M_LED_{key}']]))


Z = (0, 0, 1)
group('Cove', [('LED_Cove_1', (WARD_FRONT + 3, 1.6, 246.0), (FACE - 0.5, 1.6, 246.0), Z, (0, 1, 0), 15, 1.2, 120),
               ('LED_Cove_2', (FACE - 1.6, 5, 246.0), (FACE - 1.6, RD - 2, 246.0), Z, (-1, 0, 0), 15, 1.2, 120),
               ('LED_Cove_3', (FACE - 8, RD - 1.6, 246.0), (7, RD - 1.6, 246.0), Z, (0, -1, 0), 15, 1.2, 120),
               ('LED_Cove_4', (1.6, RD - 6, 246.0), (1.6, WARD_L + 3, 246.0), Z, (1, 0, 0), 15, 1.2, 120)])
group('BedPanel', [('LED_BedPanel_W1', (102.0, RD - 0.9, 87.5), (FACE - 2, RD - 0.9, 87.5), Z, (0, 1, 0), 25, 1.1, 110)])
group('Desk', [('LED_Under_Desk_W3', (FACE - 3.2, 4.0, TAB_H - TAB_T), (FACE - 3.2, TAB_END_Y - 6, TAB_H - TAB_T), (0, 0, -1), (1, 0, 0), 25, 1.1, 120),
               ('LED_Under_Desk_W2', (FACE - TAB_D - 2, 3.2, TAB_H - TAB_T), (TAB_END_X + 6, 3.2, TAB_H - TAB_T), (0, 0, -1), (0, -1, 0), 25, 1.1, 120)])

move(['PROP_MacBook_Air_13_M4', 'PROP_MagSafe_Plug', 'PROP_Cable_MagSafe'], T(0, -8.0, 0))     # make room for the aquarium at the bed-end corner
move(['PROP_Echo_Dot'], T(0, -52.0, 0))

# the new wall plug: flush in the boards under where the piano stood (piano y 96-225, centre 160.7), black face, two sockets
g = P.Geo(); g.box(FACE - 0.3, FACE, 156.7, 164.7, 40.0, 48.0, 0)
for dz in (-1.9, 1.9): g.cyl((FACE - 0.3, 160.7, 44.0 + dz), (FACE - 0.45, 160.7, 44.0 + dz), 1.7, 20, 1)
pl = g.finish('ELEC_Outlet_W3_Low', 'ARCH_Electrical', ['M_Plastic_Black', 'M_Socket'], bevel=(0.15, 1)); pl['dim_source'] = 'USER'
pl['note'] = 'new flush wall plug through the boards, under the old piano spot (y 160.7, centre 44 cm high)'

# ------------------------------------------------------------------------------------------ 8. cameras for the new layout
E = P.EYE_STAND
P.cam('CAM_L1_Entrance', (45, 283, E), (32, 90, 115), 24, 8.0)                       # door opens: you face the side of the wardrobe
P.cam('CAM_L2_Table_Shelves', (85, 150, E), (300, 70, 125), 24, 8.0)
P.cam('CAM_L3_Bed_Door', (125, 105, E), (175, 290, 85), 24, 8.0)
P.cam('CAM_L5_Overview', (30, 262, 232), (205, 95, 40), 16, 11.0, level=False)      # high corner view of the whole layout
P.cam('CAM_L4_Wardrobe_Gap', (200, 150, E), (70, 20, 120), 24, 8.0)
pc = bpy.data.cameras.new('CAM_Plan_Sketch'); pc.type = 'ORTHO'; pc.ortho_scale = 3.5; pc.clip_start = 0.01; pc.clip_end = 20
po = bpy.data.objects.new('CAM_Plan_Sketch', pc); P.coll('CAM_Photoreal').objects.link(po)
po.location = Vector((RW / 2, RD / 2, 600)) * S; po.rotation_euler = (0, 0, math.pi)      # window at the top, wall 4 at the right: same as your sketch
po['note'] = 'Top-down plan oriented like your sketch (hide ceiling, crown, fan)'


# ------------------------------------------------------------------------------------------ 8b. aquarium 45 x 21 x 30 cm (your sketch) on the table
import random
for n in [o.name for o in OBJ if o.name.startswith('AQ_')]: bpy.data.objects.remove(OBJ[n])
AQ_L, AQ_D, AQ_H, GT, WATER_Z = 45.0, 21.0, 30.0, 0.4, 26.0
glass = bpy.data.materials['M_Glass']
water = glass.copy(); water.name = 'M_Aq_Water'
wb = P.bsdf(water); wb.inputs['IOR'].default_value = 1.333; wb.inputs['Base Color'].default_value = (0.82, 0.95, 1.0, 1.0)
trim = bpy.data.materials['M_Plastic_Black']
gravel = P.material('M_Aq_Gravel', '#2E2A26', 0.8); gn = gravel.node_tree
vo = P.node(gn, 'ShaderNodeTexVoronoi', -700, 0); vo.inputs['Scale'].default_value = 90.0
tcn = P.node(gn, 'ShaderNodeTexCoord', -900, 0); gn.links.new(tcn.outputs['Object'], vo.inputs['Vector'])
rr = P.node(gn, 'ShaderNodeValToRGB', -450, 0); rr.color_ramp.elements[0].color = (0.03, 0.025, 0.02, 1); rr.color_ramp.elements[1].color = (0.30, 0.26, 0.20, 1)
gn.links.new(vo.outputs['Distance'], rr.inputs[0]); gn.links.new(rr.outputs['Color'], P.bsdf(gravel).inputs['Base Color'])
P.add_bump(gn, P.bsdf(gravel), vo.outputs['Distance'], 0.6, 0.002, -300, -400)
rock = P.material('M_Aq_Rock', '#5B5A57', 0.85)
plant = P.material('M_Aq_Plant', '#2F8A3A', 0.5); plant.use_backface_culling = False
fish_m = P.material('M_Aq_Fish', '#F26A1B', 0.35, **{'Coat Weight': 0.4})
root = bpy.data.objects.new('AQ_Aquarium', None); P.coll('FURN_Desk').objects.link(root)
root['note'] = 'Aquarium 45 x 21 x 30 cm (your sketch). Move/rotate this empty to try positions; z=75 is the table top.'
rng = random.Random(8)
def part(name, g, mats, **kw):
    ob = g.finish(name, 'FURN_Desk', mats, **kw); ob.parent = root; ob.matrix_parent_inverse = root.matrix_world.inverted(); return ob
hx, hy = AQ_L / 2, AQ_D / 2
g = P.Geo(); g.box(-hx, hx, -hy, hy, 0, GT)                                                      # bottom pane
g.box(-hx, hx, -hy, -hy + GT, GT, AQ_H).box(-hx, hx, hy - GT, hy, GT, AQ_H)                          # front / back panes
g.box(-hx, -hx + GT, -hy + GT, hy - GT, GT, AQ_H).box(hx - GT, hx, -hy + GT, hy - GT, GT, AQ_H)       # end panes
part('AQ_Glass', g, [glass])
g = P.Geo(); g.box(-hx + GT, hx - GT, -hy + GT, hy - GT, GT, WATER_Z)
part('AQ_Water', g, [water])
g = P.Geo(); g.box(-hx - 0.1, hx + 0.1, -hy - 0.1, hy + 0.1, -0.5, 0.0)                         # black base frame
for sx in (-1, 1): g.box(sx * (hx - 0.6) - 0.6, sx * (hx - 0.6) + 0.6, -hy, hy, AQ_H - 0.1, AQ_H + 0.3)
for sy in (-1, 1): g.box(-hx, hx, sy * (hy - 0.6) - 0.6, sy * (hy - 0.6) + 0.6, AQ_H - 0.1, AQ_H + 0.3)   # top rim
part('AQ_Frame', g, [trim], bevel=(0.1, 1))
# gravel bed with a gentle slope, higher at the back
xs = [-hx + GT + i * (AQ_L - 2 * GT) / 44 for i in range(45)]; ys = [-hy + GT + j * (AQ_D - 2 * GT) / 20 for j in range(21)]
top = lambda x, y: 2.4 + 2.2 * (y + hy) / AQ_D + 0.5 * math.sin(x * 0.45) * math.cos(y * 0.6)
g = P.Geo(); T_ = [[g.v((x, y, top(x, y))) for x in xs] for y in ys]; B_ = [[g.v((x, y, GT)) for x in xs] for y in ys]
for j in range(20):
    for i in range(44):
        g.f((T_[j][i], T_[j][i + 1], T_[j + 1][i + 1], T_[j + 1][i])); g.f((B_[j][i], B_[j + 1][i], B_[j + 1][i + 1], B_[j][i + 1]))
for j in range(20):
    for (i0, i1, flip) in ((0, 0, False), (44, 44, True)):
        pass
part('AQ_Gravel', g, [gravel], smooth=True)
g = P.Geo()
for (x, y, r) in ((-9, 3, 3.6), (-5.5, 5.5, 2.4), (11, 4, 3.0)): g.sphere((x, y, top(x, y) + 0.6), r, 0, 12, rz=r * 0.7)
part('AQ_Rocks', g, [rock], smooth=True)
g = P.Geo()                                                                                      # plants: curved leaf ribbons
for (px_, py_) in ((-17, 6), (-14, 7), (-1, 7.5), (2, 6), (16, 6.5), (18, 4), (-19, 3)):
    for _ in range(3):
        ang = rng.uniform(0, 6.28); hgt = rng.uniform(11, 21); sway = rng.uniform(2.0, 4.5); wd = rng.uniform(0.7, 1.2)
        rows = []
        for k in range(7):
            t = k / 6; cx = px_ + math.cos(ang) * sway * t * t; cy = py_ + math.sin(ang) * sway * t * t * 0.4
            w = wd * (1 - 0.7 * t) * (0.4 + math.sin(math.pi * min(1, t + 0.15)))
            rows.append((g.v((cx - w, cy, top(px_, py_) + hgt * t)), g.v((cx + w, cy, top(px_, py_) + hgt * t))))
        for k in range(6): g.f((rows[k][0], rows[k][1], rows[k + 1][1], rows[k + 1][0]))
part('AQ_Plants', g, [plant], smooth=True)
g = P.Geo()                                                                                      # three small fish
for (x, y, z, a) in ((-6, -1, 16, 0.3), (8, 1, 20, math.pi + 0.2), (14, -2, 12, 0.1)):
    ca, sa = math.cos(a), math.sin(a)
    g.sphere((x, y, z), 1.6, 0, 12, rz=1.3)
    for k in range(3): g.sphere((x - ca * (1.6 + 0.8 * k), y - sa * (1.6 + 0.8 * k), z), 1.0 - 0.18 * k, 0, 8, rz=1.0 - 0.15 * k)
part('AQ_Fish', g, [fish_m], smooth=True)
AQ_SPOTS = {'V1': ((273.0, 11.0), 0), 'V2': ((111.0, 11.0), 0), 'V3': ((111.0, 37.5), 0), 'V4': ((285.0, 171.2), 90)}
(sx_, sy_), rz_ = AQ_SPOTS['V1']
root.location = Vector((sx_, sy_, TAB_H)) * S; root.rotation_euler = (0, 0, math.radians(rz_)); root['spot'] = 'V1'

# ------------------------------------------------------------------------------------------ 9. save
sc['experiment'] = (sc.get('experiment', '') + ' | round 6: new layout (wardrobe on wall 4 facing the room, L-table on walls 3+2 with 50 cm clearance, '
                    'bed in the old wardrobe corner, shelves on wall 3, no piano, no puzzle frame)')
bpy.context.preferences.filepaths.save_version = 0
out = os.path.join(P.ROOT, 'experiments', 'teak_navy', 'Bedroom_Teak_Navy_v8_layout.blend')
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print('SAVED', out)
