"""
Teak & navy, round 2 (your notes of 14 Oct), applied on top of Bedroom_Teak_Navy.blend:
  - teak panel around the bed runs the whole piano wall up to the wardrobe, and both panels go down to the floor
  - pillows stacked, music rest off the piano, mouse and papers off the desk
  - rug rebuilt as a flat-woven cream/charcoal jacquard like your photo
  - MacBook Air 13" M4 to scale (30.41 x 21.5 x 1.13 cm, Apple), cable grommet in the window-side corner of the desk
  - option sets: wardrobe strip colours (S1-S6) and two thin metal legs for the desk's door-side end (L1-L4)
Saves Bedroom_Teak_Navy_v2.blend (defaults S1 + L1) and renders into renders_v2/.

  Blender -b Bedroom_Teak_Navy.blend --python teak_navy_v2.py -- [set=all|strips|legs|views] [spp=256] [vspp=512] [scale=1]
"""
import bpy, bmesh, json, math, os, sys
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OPT = dict(a.split('=', 1) for a in (sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []))
SET, SPP, VSPP, SCALE = OPT.get('set', 'all'), int(OPT.get('spp', 256)), int(OPT.get('vspp', 512)), float(OPT.get('scale', 1))
OUT = os.path.join(HERE, 'renders_v2')
S = 0.01
sc = bpy.context.scene
FRONT = bpy.data.objects['DESK_Desk'].location.x * 100 - 24.5     # how far the boards pushed the desk off the wall (cm)
STRIPS = [('oak', 'Oak (as now)', None), ('black', 'Matte black', ('#151515', 0.5, 0.0)),
          ('brass', 'Brushed brass', ('#C9A15C', 0.3, 1.0)), ('steel', 'Brushed steel', ('#B5B7BA', 0.28, 1.0)),
          ('navy', 'Deep navy (like the walls)', ('#2F3D52', 0.45, 0.0)), ('white', 'Warm white', ('#ECEAE4', 0.4, 0.0))]
LEGS = [('square_black', 'Square black steel, 3 cm'), ('round_black', 'Round black steel, 2.5 cm'),
        ('round_brass', 'Round brushed brass, 2.5 cm'), ('hairpin_black', 'Black hairpin legs')]


def lin(h):
    return tuple((v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)])


def material(name, hexc, rough, metal=0.0, **extra):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*lin(hexc), 1); p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    for k, v in extra.items(): p.inputs[k].default_value = v
    m.diffuse_color = (*lin(hexc), 1)
    return m


def node(nt, kind, x, y, **kw):
    n = nt.nodes.new(kind); n.location = (x, y)
    for k, v in kw.items(): setattr(n, k, v)
    return n


def sock(n, ident, out=False):
    return next(s for s in (n.outputs if out else n.inputs) if s.identifier == ident)


def remove(name):
    ob = bpy.data.objects.get(name)
    if ob: bpy.data.objects.remove(ob)


class Mesh:
    """bmesh builder, world space, centimetres in, metres out; box-projected UVs in metres (u along the long side)."""
    def __init__(self): self.bm = bmesh.new()

    def v(self, p): return self.bm.verts.new(Vector(p) * S)

    def prism(self, O, A, B, N, pts, t0, t1, mi=0):
        O, A, B, N = map(Vector, (O, A, B, N))
        bot = [self.v(O + A * x + B * y + N * t0) for x, y in pts]; top = [self.v(O + A * x + B * y + N * t1) for x, y in pts]
        self.bm.faces.new(bot[::-1]).material_index = mi; self.bm.faces.new(top).material_index = mi
        for i in range(len(pts)):
            j = (i + 1) % len(pts); self.bm.faces.new((bot[i], bot[j], top[j], top[i])).material_index = mi
        return self

    def box(self, x0, x1, y0, y1, z0, z1, mi=0):
        return self.prism(((x0 + x1) / 2, (y0 + y1) / 2, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1),
                          [(-(x1 - x0) / 2, -(y1 - y0) / 2), ((x1 - x0) / 2, -(y1 - y0) / 2), ((x1 - x0) / 2, (y1 - y0) / 2),
                           (-(x1 - x0) / 2, (y1 - y0) / 2)], z0, z1, mi)

    def cyl(self, p0, p1, r, n=24, mi=0):
        p0, p1 = Vector(p0), Vector(p1); a = (p1 - p0).normalized(); u = a.orthogonal().normalized(); w = a.cross(u)
        return self.prism(p0, u, w, a, [(r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n)) for k in range(n)],
                          0, (p1 - p0).length, mi)

    def finish(self, name, coll, mats, tint=None, bevel=None, smooth=False):
        bm = self.bm; bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        uv = bm.loops.layers.uv.new('UVMap')
        if tint is not None:
            t = bm.verts.layers.float.new('board_tint')
            for vv in bm.verts: vv[t] = tint
        for f in bm.faces:
            ax = max(range(3), key=lambda i: abs(f.normal[i])); a, b = [i for i in range(3) if i != ax]
            co = [lp.vert.co for lp in f.loops]
            if max(c[b] for c in co) - min(c[b] for c in co) > max(c[a] for c in co) - min(c[a] for c in co): a, b = b, a
            for lp in f.loops: lp[uv].uv = (lp.vert.co[a], lp.vert.co[b])
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        for m in mats: me.materials.append(m if isinstance(m, bpy.types.Material) else bpy.data.materials[m])
        if smooth:
            for p in me.polygons: p.use_smooth = True
        ob = bpy.data.objects.new(name, me); bpy.data.collections[coll].objects.link(ob)
        if bevel:
            md = ob.modifiers.new('Bevel', 'BEVEL'); md.width = bevel * S; md.segments = 2; md.limit_method = 'ANGLE'
        return ob


def rrect(w, d, r, n=6):
    pts = []
    for cx, cy, a0 in [(w / 2 - r, d / 2 - r, 0), (-w / 2 + r, d / 2 - r, 90), (-w / 2 + r, -d / 2 + r, 180), (w / 2 - r, -d / 2 + r, 270)]:
        pts += [(cx + r * math.cos(math.radians(a0 + 90 * k / n)), cy + r * math.sin(math.radians(a0 + 90 * k / n))) for k in range(n + 1)]
    return pts


def curve(name, pts, radius, mat, coll='PROPS_Lived_In'):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = radius * S; cu.bevel_resolution = 3
    cu.use_fill_caps = True
    sp = cu.splines.new('NURBS'); sp.points.add(len(pts) - 1); sp.order_u = 3; sp.use_endpoint_u = True
    for pt, q in zip(sp.points, pts): pt.co = (q[0] * S, q[1] * S, q[2] * S, 1.0)
    cu.materials.append(mat); ob = bpy.data.objects.new(name, cu); bpy.data.collections[coll].objects.link(ob)
    return ob


def world_verts(ob):
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get(); ev = ob.evaluated_get(dg); me = ev.to_mesh()
    pts = [ev.matrix_world @ v.co * 100 for v in me.vertices]; ev.to_mesh_clear()
    return pts


teak = bpy.data.materials['M_Boards_teak']

# ---------------------------------------------------------------- 1. teak panel around the bed: whole piano wall, down to the floor
remove('BED_Headboard_Wall2'); remove('BED_Headboard_Wall3')
Mesh().box(104.5, 300, 0, 1.8, 0, 87.5).finish('BED_Headboard_Wall2', 'FURN_Bed', [teak], tint=0.45, bevel=0.15)
Mesh().box(298.2, 300, 1.8, 227.0, 0, 87.5).finish('BED_Headboard_Wall3', 'FURN_Bed', [teak], tint=0.6, bevel=0.15)   # up to the wardrobe
bpy.data.objects['PIANO_Korg_SP250'].location.x -= 0.005             # piano back clears the new panel
for n in ('ELEC_Outlet_W3_Low', 'PROP_Cable_Piano', 'PROP_Cable_Purifier'):   # piano socket comes out through the panel
    bpy.data.objects[n].location.x -= 0.018

# ---------------------------------------------------------------- 2. pillows stacked, music rest off, mouse + papers off
low, up = bpy.data.objects['BED_Pillow_Lying_Print'], bpy.data.objects['BED_Pillow_Upright_Dots']
up.rotation_euler = (math.radians(1.5), math.radians(-2.0), math.radians(94)); up.location = (2.675, 0.49, 0.9)
lz = max(p.z for p in world_verts(low)); uz = min(p.z for p in world_verts(up))
up.location.z += (lz - 2.5 - uz) * S                                   # rests on the lower pillow, sinking 2.5 cm into it
remove('PIANO_Music_Rest')
items = bpy.data.objects['PROP_Desk_Items']; bm = bmesh.new(); bm.from_mesh(items.data)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in (0, 2)], context='FACES')   # 0 mouse, 2 papers; keeps the white device
bm.to_mesh(items.data); bm.free()

# ---------------------------------------------------------------- 3. rug: flat-woven jacquard, cream and charcoal threads in cloudy patches
m = bpy.data.materials['M_Rug']; nt = m.node_tree; L = nt.links
for n in list(nt.nodes):
    if n.type not in ('BSDF_PRINCIPLED', 'OUTPUT_MATERIAL'): nt.nodes.remove(n)
p = nt.nodes['Principled BSDF']
tc = node(nt, 'ShaderNodeTexCoord', -1700, 0)
cell = node(nt, 'ShaderNodeVectorMath', -1500, 200, operation='MULTIPLY'); cell.inputs[1].default_value = (1 / 0.0055, 1 / 0.0022, 1.0)
fl = node(nt, 'ShaderNodeVectorMath', -1300, 250, operation='FLOOR'); fr = node(nt, 'ShaderNodeVectorMath', -1300, 50, operation='FRACTION')
wn = node(nt, 'ShaderNodeTexWhiteNoise', -1100, 250, noise_dimensions='3D'); rgb = node(nt, 'ShaderNodeSeparateColor', -900, 250)
c1 = node(nt, 'ShaderNodeTexNoise', -1300, -250); c1.inputs['Scale'].default_value = 4.5; c1.inputs['Detail'].default_value = 8.0
c1.inputs['Roughness'].default_value = 0.6; c1.inputs['Distortion'].default_value = 0.6
c2 = node(nt, 'ShaderNodeTexNoise', -1300, -500); c2.inputs['Scale'].default_value = 16.0; c2.inputs['Detail'].default_value = 3.0
mix = node(nt, 'ShaderNodeMath', -1100, -350, operation='MULTIPLY_ADD'); mix.inputs[1].default_value = 0.75
m2 = node(nt, 'ShaderNodeMath', -1100, -550, operation='MULTIPLY'); m2.inputs[1].default_value = 0.25
thr = node(nt, 'ShaderNodeMapRange', -900, -400)
thr.inputs['From Min'].default_value, thr.inputs['From Max'].default_value = 0.40, 0.60      # cloudy patches: mostly dark or mostly cream
thr.inputs['To Min'].default_value, thr.inputs['To Max'].default_value = 0.02, 0.98
dark = node(nt, 'ShaderNodeMath', -700, 0, operation='LESS_THAN')
grey = node(nt, 'ShaderNodeMath', -700, 200, operation='LESS_THAN'); grey.inputs[1].default_value = 0.12
mxa = node(nt, 'ShaderNodeMix', -500, 100, data_type='RGBA'); sock(mxa, 'A_Color').default_value = (*lin('#DCD6CA'), 1)
sock(mxa, 'B_Color').default_value = (*lin('#232325'), 1)
mxb = node(nt, 'ShaderNodeMix', -300, 100, data_type='RGBA'); sock(mxb, 'B_Color').default_value = (*lin('#77777A'), 1)
fy = node(nt, 'ShaderNodeSeparateXYZ', -1100, 50); rid = node(nt, 'ShaderNodeMath', -900, 50, operation='PINGPONG')
rid.inputs[1].default_value = 0.5
bump = node(nt, 'ShaderNodeBump', -300, -250); bump.inputs['Strength'].default_value = 0.35; bump.inputs['Distance'].default_value = 0.0008
for a, b in [(tc.outputs['Object'], cell.inputs[0]), (cell.outputs['Vector'], fl.inputs[0]), (cell.outputs['Vector'], fr.inputs[0]),
             (fl.outputs['Vector'], wn.inputs['Vector']), (wn.outputs['Color'], rgb.inputs[0]),
             (tc.outputs['Object'], c1.inputs['Vector']), (tc.outputs['Object'], c2.inputs['Vector']),
             (c1.outputs['Factor'], mix.inputs[0]), (c2.outputs['Factor'], m2.inputs[0]), (m2.outputs[0], mix.inputs[2]),
             (mix.outputs[0], thr.inputs['Value']), (rgb.outputs['Red'], dark.inputs[0]), (thr.outputs['Result'], dark.inputs[1]),
             (rgb.outputs['Green'], grey.inputs[0]), (dark.outputs[0], sock(mxa, 'Factor_Float')),
             (sock(mxa, 'Result_Color', True), sock(mxb, 'A_Color')), (grey.outputs[0], sock(mxb, 'Factor_Float')),
             (sock(mxb, 'Result_Color', True), p.inputs['Base Color']),
             (fr.outputs['Vector'], fy.inputs[0]), (fy.outputs['Y'], rid.inputs[0]), (rid.outputs[0], bump.inputs['Height']),
             (bump.outputs['Normal'], p.inputs['Normal'])]:
    L.new(a, b)
p.inputs['Roughness'].default_value = 0.93; p.inputs['Sheen Weight'].default_value = 0.35; p.inputs['Sheen Roughness'].default_value = 0.5
m.diffuse_color = (*lin('#77777A'), 1)
rug = bpy.data.objects['DECOR_Rug']; rug.scale.z = 0.7; rug['note'] = 'flat-woven jacquard after your photo; size 150 x 200 still EST'

# ---------------------------------------------------------------- 4. MacBook Air 13" M4 (silver), lid open ~108 degrees
remove('PROP_Laptop')
alu = material('M_MBA_Silver', '#C6C8CB', 0.36, 1.0); keys = material('M_MBA_Keys', '#1A1A1C', 0.55)
well = material('M_MBA_Well', '#0C0C0D', 0.6); glass = material('M_MBA_Screen_Glass', '#020203', 0.035)
pad = material('M_MBA_Trackpad', '#C3C5C8', 0.22, 0.6); dark = material('M_MBA_Dark', '#2A2A2C', 0.45, 0.4)
bx0, bx1, by0, by1 = 13 + FRONT, 13 + FRONT + 21.5, 34.0, 34.0 + 30.41     # back (hinge) edge toward the wall, user at +x
cx, cy, z0, BASE, LID = (bx0 + bx1) / 2, (by0 + by1) / 2, 80.06, 0.72, 0.41
mb = Mesh()
mb.prism((cx, cy, 0), (0, 1, 0), (1, 0, 0), (0, 0, 1), rrect(30.41, 21.5, 1.0), z0, z0 + BASE, 0)            # base
top = z0 + BASE
for fx in (bx0 + 2.2, bx1 - 2.2):                                                                              # rubber feet
    for fy_ in (by0 + 2.4, by1 - 2.4): mb.cyl((fx, fy_, z0), (fx, fy_, z0 - 0.06), 0.65, 16, 5)
kx0 = bx0 + 1.0; mb.box(kx0, kx0 + 10.9, cy - 13.85, cy + 13.85, top, top + 0.012, 2)                       # keyboard well
u = 27.5 / 14.5; gap = 0.22
rows = [(0.95, [14.5 / 14] * 14), (1.6, [1] * 13 + [1.5]), (1.6, [1.5] + [1] * 13), (1.6, [1.75] + [1] * 11 + [1.75]),
        (1.6, [2.25] + [1] * 10 + [2.25]), (1.6, [1, 1, 1, 1.25, 5, 1.25, 1, 1, 'ud', 1])]   # back to front; left (-y) to right
x = kx0 + 0.15
for depth, widths in rows:
    y = cy - 13.75
    for w in widths:
        ww = 1 if w == 'ud' else w
        if w == 'ud':                                                    # up/down arrows: half height, stacked
            h = (depth - gap) / 2
            mb.box(x, x + h, y + gap / 2, y + ww * u - gap / 2, top + 0.012, top + 0.07, 1)
            mb.box(x + h + gap, x + depth, y + gap / 2, y + ww * u - gap / 2, top + 0.012, top + 0.07, 1)
        else:
            mb.box(x, x + depth, y + gap / 2, y + ww * u - gap / 2, top + 0.012, top + 0.07, 1)
        y += ww * u
    x += depth + 0.25
tx1 = bx1 - 0.8; tx0 = tx1 - 8.0                                                                               # trackpad (12 x 8 cm, EST)
mb.prism(((tx0 + tx1) / 2, cy, 0), (0, 1, 0), (1, 0, 0), (0, 0, 1), rrect(12.12, 8.12, 0.45), top, top + 0.004, 4)
mb.prism(((tx0 + tx1) / 2, cy, 0), (0, 1, 0), (1, 0, 0), (0, 0, 1), rrect(12.0, 8.0, 0.4), top + 0.004, top + 0.009, 3)
hinge = Vector((bx0 + 0.45, cy, top - 0.15))
mb.cyl(hinge + Vector((0, -12.5, 0)), hinge + Vector((0, 12.5, 0)), 0.42, 20, 4)                               # hinge
t = math.radians(18); U = Vector((-math.sin(t), 0, math.cos(t))); NN = Vector((math.cos(t), 0, math.sin(t)))   # lid tilted 18 deg back
lc = hinge + U * 10.6
mb.prism(lc, (0, 1, 0), U, NN, rrect(30.41, 21.2, 1.0), -LID, 0.0, 0)                                          # lid
mb.prism(lc + U * 0.05, (0, 1, 0), U, NN, rrect(29.7, 20.5, 0.75), 0.0, 0.025, 6)                              # black glass + bezel
ob = mb.finish('PROP_MacBook_Air_13_M4', 'PROPS_Lived_In', [alu, keys, well, pad, dark, 'M_Rubber_Black', glass], smooth=False)
ob['dim_source'] = 'SPEC'; ob['note'] = 'MacBook Air 13" M4: 30.41 x 21.5 x 1.13 cm, 13.6" display (Apple); trackpad size EST'
md = ob.modifiers.new('Bevel', 'BEVEL'); md.width = 0.0004; md.segments = 1; md.limit_method = 'ANGLE'

# ---------------------------------------------------------------- 5. cable grommet in the desk's window-side corner + cables
gx, gy = FRONT + 9, 13.0
remove('CUT_Grommet_Hole')
cut = Mesh().cyl((gx, gy, 75), (gx, gy, 82), 3.0, 40).finish('CUT_Grommet_Hole', 'FURN_Desk', ['M_Steel_Black'])
cut.display_type = 'WIRE'; cut.hide_render = True
desk = bpy.data.objects['DESK_Wood']
if 'Grommet_Hole' not in desk.modifiers:
    bo = desk.modifiers.new('Grommet_Hole', 'BOOLEAN'); bo.operation = 'DIFFERENCE'; bo.object = cut; bo.solver = 'EXACT'
    try: desk.modifiers.move(len(desk.modifiers) - 1, 0)
    except Exception: pass
cap = material('M_Grommet_Brown', '#4E3B2E', 0.42)
a0 = math.degrees(math.acos(1.55 / 2.95))
dcut = [(2.95 * math.cos(math.radians(a)), 2.95 * math.sin(math.radians(a))) for a in [a0 + (360 - 2 * a0) * k / 40 for k in range(41)]]
ring = [(3.4 * math.cos(2 * math.pi * k / 48), 3.4 * math.sin(2 * math.pi * k / 48)) for k in range(48)]
g = Mesh()
g.prism((gx, gy, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1), dcut, 79.8, 80.18, 0)                                    # insert with the D opening (toward you)
gb = g.bm                                                                                                       # flange: annulus 2.95-3.4 cm
outer = [g.v((gx + x_, gy + y_, z)) for z in (80.0, 80.22) for x_, y_ in ring]
inner = [g.v((gx + x_ * 2.95 / 3.4, gy + y_ * 2.95 / 3.4, z)) for z in (80.0, 80.22) for x_, y_ in ring]
n = len(ring)
for k in range(n):
    j = (k + 1) % n
    for quad in [(outer[n + k], outer[n + j], inner[n + j], inner[n + k]), (outer[k], inner[k], inner[j], outer[j]),
                 (outer[k], outer[j], outer[n + j], outer[n + k]), (inner[k], inner[n + k], inner[n + j], inner[j])]:
        gb.faces.new(quad).material_index = 0
remove('DESK_Cable_Grommet')
g.finish('DESK_Cable_Grommet', 'FURN_Desk', [cap], smooth=False)['note'] = 'cable grommet, 6 cm hole, after your photo'
for n_ in ('PROP_Cable_MagSafe', 'PROP_Cable_Lamp', 'PROP_MagSafe_Plug'): remove(n_)
lx = FRONT + 5.0
bpy.data.objects['PROP_Desk_Lamp'].location.y += 0.10            # lamp beside the grommet, not on top of it (as in your photo)
curve('PROP_Cable_MagSafe', [(gx + 2.3, gy + 0.2, 76.0), (gx + 2.4, gy + 0.4, 80.3), (gx + 3.2, gy + 2.5, 80.45), (gx + 4.6, gy + 9.0, 80.25),
                             (bx0 + 2.0, 29.5, 80.25), (bx0 + 2.4, 33.0, 80.4), (bx0 + 2.5, by0 - 0.9, 80.42)],
      0.2, material('M_Cable_Braided_Silver', '#DAD8D2', 0.75))
Mesh().box(bx0 + 1.75, bx0 + 3.25, by0 - 0.95, by0, 80.2, 80.64).finish('PROP_MagSafe_Plug', 'PROPS_Lived_In', [alu], bevel=0.15)
curve('PROP_Cable_Lamp', [(lx, 21.0, 80.4), (gx + 0.5, 18.5, 80.35), (gx + 2.0, gy + 1.5, 80.3),
                          (gx + 2.3, gy + 0.3, 79.0), (gx + 2.2, gy + 0.2, 76.0)], 0.18, bpy.data.materials['M_Rubber_Black'])

# ---------------------------------------------------------------- 6. option sets
strip_mats = {s: (bpy.data.materials['M_Wardrobe_Wood'] if spec is None else material(f'M_Strip_{s}', spec[0], spec[1], spec[2]))
              for s, _, spec in STRIPS}


def set_strips(slug):
    for n_ in ('WARD_Door_Left_back', 'WARD_Door_Right_front'):
        bpy.data.objects[n_].material_slots[1].material = strip_mats[slug]


dw = desk.data; bm = bmesh.new(); bm.from_mesh(dw); bm.verts.ensure_lookup_table(); seen, isl_all = set(), []
for v0 in bm.verts:                                                        # remove the door-side end panel (only once)
    if v0.index in seen: continue
    stack, isl = [v0], []
    while stack:
        q = stack.pop()
        if q.index in seen: continue
        seen.add(q.index); isl.append(q); stack += [e.other_vert(q) for e in q.link_edges]
    isl_all.append(isl)
panel = [q for isl in isl_all if min(q.co.y for q in isl) > 1.6 and max(q.co.z for q in isl) < 0.775 for q in isl]
if panel: bmesh.ops.delete(bm, geom=panel, context='VERTS')
bm.to_mesh(dw); bm.free()
brass = material('M_Brass_Brushed', '#C9A15C', 0.3, 1.0); steel = bpy.data.materials['M_Steel_Black']; glide = bpy.data.materials['M_Rubber_Black']


def set_legs(slug):
    remove('DESK_Legs'); mb = Mesh(); yl = 170 - 4.0; top_z = 77.0
    if slug == 'hairpin_black':
        for xc in (FRONT + 9, FRONT + 49 - 9):
            mb.box(xc - 5, xc + 5, yl - 4, yl + 4, top_z - 0.5, top_z, 0)                        # mounting plate
            for sx in (-1, 1):
                mb.cyl((xc + sx * 6.0, yl, top_z - 0.5), (xc + sx * 0.9, yl, 1.6), 0.55, 14, 0)   # two rods converging...
            mb.cyl((xc - 0.9, yl, 1.6), (xc + 0.9, yl, 1.6), 0.55, 14, 0)                        # ...joined by the U at the floor
            for sx in (-1, 1): mb.cyl((xc + sx * 0.9, yl, 1.6), (xc + sx * 0.9, yl, 0.4), 0.55, 14, 0)
        return mb.finish('DESK_Legs', 'FURN_Desk', [steel], smooth=True)
    for xc in (FRONT + 5, FRONT + 49 - 4):
        if slug == 'square_black': mb.box(xc - 1.5, xc + 1.5, yl - 1.5, yl + 1.5, 0.4, top_z, 0)
        else: mb.cyl((xc, yl, 0.4), (xc, yl, top_z), 1.25, 32, 0)
        mb.cyl((xc, yl, 0.0), (xc, yl, 0.4), 1.1, 24, 1)                                         # floor glide
    return mb.finish('DESK_Legs', 'FURN_Desk', [brass if slug == 'round_brass' else steel, glide], bevel=0.15, smooth=slug != 'square_black')


def aim(name, loc, target, lens, fstop):
    remove(name); cam = bpy.data.cameras.new(name); cam.lens = lens; cam.sensor_width = 36; cam.sensor_fit = 'HORIZONTAL'
    cam.clip_start = 0.03; cam.clip_end = 50; ob = bpy.data.objects.new(name, cam); bpy.data.collections['CAM_Cameras'].objects.link(ob)
    v = Vector(target) - Vector(loc); ob.location = Vector(loc) * S; ob.rotation_euler = v.to_track_quat('-Z', 'Y').to_euler()
    cam.dof.use_dof = True; cam.dof.focus_distance = v.length * S; cam.dof.aperture_fstop = fstop
    return ob


aim('CAM_Detail_Desk_Legs', (165, 210, 112), (FRONT + 26, 150, 55), 24, 4.0)
aim('CAM_Detail_Laptop', (92, 70, 118), (FRONT + 16, 43.5, 80), 32, 2.8)
aim('CAM_Detail_Rug', (118, 212, 128), (200, 150, 0), 24, 4.0)
w3 = aim('CAM_Detail_Wall3', (45, 140, 140), (300, 140, 140), 17, 5.6); w3.data.shift_y = -0.06; w3.data.dof.focus_distance = 2.3
set_strips('oak'); set_legs('square_black')
sc['experiment'] = (sc.get('experiment', '') + ' | round 2: teak panel along the whole piano wall and to the floor, pillows stacked, '
                    'no music rest, woven rug, MacBook Air 13 M4, cable grommet, no mouse/papers, strips S1 oak, legs L1 square black')
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'Bedroom_Teak_Navy_v2.blend'), compress=True)

# ---------------------------------------------------------------- 7. renders
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'METAL'; prefs.get_devices()
for d in prefs.devices: d.use = True
sc.cycles.device = 'GPU'; sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_depth = '8'


def shot(cam, path, spp, pct):
    sc.camera = bpy.data.objects[cam]; sc.cycles.samples = spp; sc.render.resolution_percentage = pct
    os.makedirs(os.path.dirname(path), exist_ok=True); sc.render.filepath = path; bpy.ops.render.render(write_still=True)
    print('RENDERED', os.path.relpath(path, OUT), flush=True)


opt_pct = round(66.67 * SCALE)
if SET in ('all', 'strips'):
    for k, (s, label, _) in enumerate(STRIPS, 1):
        set_strips(s); shot('CAM_Render_B_From_Window', os.path.join(OUT, 'strips', f'S{k}_{s}.png'), SPP, opt_pct)
    set_strips('oak')
if SET in ('all', 'legs'):
    for k, (s, label) in enumerate(LEGS, 1):
        set_legs(s); shot('CAM_Detail_Desk_Legs', os.path.join(OUT, 'legs', f'L{k}_{s}.png'), SPP, opt_pct)
    set_legs('square_black')
if SET in ('all', 'views'):
    for cam in ('CAM_Hero_1_Room', 'CAM_Detail_Wall3', 'CAM_Detail_Laptop', 'CAM_Detail_Rug'):
        shot(cam, os.path.join(OUT, 'views', cam.replace('CAM_', '') + '.png'), VSPP, round(100 * SCALE))
json.dump({'strips': [dict(code=f'S{k}', slug=s, label=l) for k, (s, l, _) in enumerate(STRIPS, 1)],
           'legs': [dict(code=f'L{k}', slug=s, label=l) for k, (s, l) in enumerate(LEGS, 1)]},
          open(os.path.join(OUT, 'options.json'), 'w'), indent=1)
