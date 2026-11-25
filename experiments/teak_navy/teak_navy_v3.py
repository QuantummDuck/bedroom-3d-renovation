"""
Teak & navy, round 3 (your notes of 14 Oct), on top of Bedroom_Teak_Navy_v2.blend:
  - your picks: wardrobe strips S5 deep navy, desk legs L1 square black steel 3 cm (already in v2)
  - MyMax MX6 chair remodelled after your two photos; your 3-blade ceiling fan added (light OFF)
  - RGB LED strips under the back edge of each shelf (wall wash) and on the back of the piano (halo on the wall)
  - desk lamp: real open shade, glowing bulb and a strong spot light
  - blue hour: sun just set, deep blue sky with a warm glow on the horizon; the room is lit by its own lights
Scene custom properties (Scene > Custom Properties): LED_RGB (colour picker), LED_Brightness, Desk_Lamp.
Saves Bedroom_Teak_Navy_v3.blend; renders into renders_v3/.

  Blender -b Bedroom_Teak_Navy_v2.blend --python teak_navy_v3.py -- [set=test|colors|views|all|none] [spp=..] [scale=..] [expo=..]
"""
import bpy, bmesh, json, math, os, sys
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.normpath(os.path.join(HERE, '..', '..', 'textures'))
OPT = dict(a.split('=', 1) for a in (sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []))
SET = OPT.get('set', 'all')
OUT = os.path.join(HERE, 'renders_v3')
S = 0.01
sc = bpy.context.scene
FRONT = bpy.data.objects['DESK_Desk'].location.x * 100 - 24.5          # boards' depth off the wall (4 cm)

EXPOSURE = float(OPT.get('expo', -2.0))         # night exposure: a camera exposing for the lamps
DUSK_STRENGTH = 0.6                  # blue-hour sky (made by tools/make_dusk_sky.py) - the room's own lights dominate
SHELF_W_PER_M, PIANO_W_PER_M = 40.0, 120.0
DESK_LAMP_W = 60.0
COLORS = [('C1', 'warm_white', 'Warm white', '#FFB46B'), ('C2', 'violet', 'Violet', '#7A2BFF'),
          ('C3', 'ice_blue', 'Ice blue', '#2BC8FF'), ('C4', 'deep_blue', 'Deep blue', '#2945FF'),
          ('C5', 'pink', 'Hot pink', '#FF2BA6'), ('C6', 'red', 'Red', '#FF2A1A')]
DEFAULT_COLOR = OPT.get('color', 'C2')


def lin(h):
    return tuple((v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)])


def lum(c): return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


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


def drive(idblock, path, expr, prop, index=-1, pidx=None):
    fc = idblock.driver_add(path, index) if index >= 0 else idblock.driver_add(path)
    d = fc.driver; d.type = 'SCRIPTED'; v = d.variables.new(); v.name = 'var'; v.type = 'SINGLE_PROP'
    v.targets[0].id_type = 'SCENE'; v.targets[0].id = sc
    v.targets[0].data_path = f'["{prop}"]' + (f'[{pidx}]' if pidx is not None else ''); d.expression = expr


class Mesh:
    """bmesh builder in centimetres (stored in metres); optional per-vertex float attributes."""
    def __init__(self, layers=()):
        self.bm = bmesh.new(); self.layers = {k: self.bm.verts.layers.float.new(k) for k in layers}   # all layers before any vertex

    def v(self, p, **at):
        vv = self.bm.verts.new(Vector(p) * S)
        for k, val in at.items():
            if k not in self.layers: self.layers[k] = self.bm.verts.layers.float.new(k)
            vv[self.layers[k]] = val
        return vv

    def f(self, vs, mi=0):
        f = self.bm.faces.new(vs); f.material_index = mi; return f

    def prism(self, O, A, B, N, pts, t0, t1, mi=0):
        O, A, B, N = map(Vector, (O, A, B, N))
        bot = [self.v(O + A * x + B * y + N * t0) for x, y in pts]; top = [self.v(O + A * x + B * y + N * t1) for x, y in pts]
        self.f(bot[::-1], mi); self.f(top, mi)
        for i in range(len(pts)):
            j = (i + 1) % len(pts); self.f((bot[i], bot[j], top[j], top[i]), mi)
        return self

    def ring(self, O, A, B, N, outer, inner, t0, t1, mi=0):
        O, A, B, N = map(Vector, (O, A, B, N)); n = len(outer)
        L = [[self.v(O + A * x + B * y + N * t) for x, y in pts] for pts in (outer, inner) for t in (t0, t1)]   # o0 o1 i0 i1
        for k in range(n):
            j = (k + 1) % n
            for q in [(L[0][k], L[0][j], L[1][j], L[1][k]), (L[2][k], L[3][k], L[3][j], L[2][j]),
                      (L[1][k], L[1][j], L[3][j], L[3][k]), (L[0][k], L[2][k], L[2][j], L[0][j])]:
                self.f(q, mi)
        return self

    def box(self, x0, x1, y0, y1, z0, z1, mi=0):
        x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
        return self.prism(((x0 + x1) / 2, (y0 + y1) / 2, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1),
                          [(-(x1 - x0) / 2, -(y1 - y0) / 2), ((x1 - x0) / 2, -(y1 - y0) / 2), ((x1 - x0) / 2, (y1 - y0) / 2),
                           (-(x1 - x0) / 2, (y1 - y0) / 2)], z0, z1, mi)

    def cyl(self, p0, p1, r, n=24, mi=0):
        p0, p1 = Vector(p0), Vector(p1); a = (p1 - p0).normalized(); u = a.orthogonal().normalized(); w = a.cross(u)
        return self.prism(p0, u, w, a, [(r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n)) for k in range(n)],
                          0, (p1 - p0).length, mi)

    def revolve(self, O, axis, profile, n=48, mats=None):
        """profile: [(radius, distance along axis)]; radius 0 = pole. mats: material per profile segment."""
        O, a = Vector(O), Vector(axis).normalized(); u = a.orthogonal().normalized(); w = a.cross(u)
        rings = [[self.v(O + a * t)] if r < 1e-6 else
                 [self.v(O + a * t + (u * math.cos(2 * math.pi * k / n) + w * math.sin(2 * math.pi * k / n)) * r) for k in range(n)]
                 for r, t in profile]
        for s in range(len(rings) - 1):
            A_, B_ = rings[s], rings[s + 1]; mi = mats[s] if mats else 0
            if len(A_) == 1 and len(B_) == 1: continue
            for k in range(n):
                j = (k + 1) % n
                if len(A_) == 1: self.f((A_[0], B_[j], B_[k]), mi)
                elif len(B_) == 1: self.f((A_[k], A_[j], B_[0]), mi)
                else: self.f((A_[k], A_[j], B_[j], B_[k]), mi)
        return self

    def grid_solid(self, xs, ys, top, zbot, mat_top, side=1):
        T = [[self.v((x, y, top(x, y))) for x in xs] for y in ys]; Bv = [[self.v((x, y, zbot)) for x in xs] for y in ys]
        nx, ny = len(xs), len(ys)
        for j in range(ny - 1):
            for i in range(nx - 1):
                self.f((T[j][i], T[j][i + 1], T[j + 1][i + 1], T[j + 1][i]), mat_top((xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2))
                self.f((Bv[j][i], Bv[j + 1][i], Bv[j + 1][i + 1], Bv[j][i + 1]), side)
        ring = [(0, i) for i in range(nx)] + [(j, nx - 1) for j in range(1, ny)] + [(ny - 1, i) for i in range(nx - 2, -1, -1)] + \
               [(j, 0) for j in range(ny - 2, 0, -1)]
        for k in range(len(ring)):
            (j0, i0), (j1, i1) = ring[k], ring[(k + 1) % len(ring)]
            self.f((T[j0][i0], Bv[j0][i0], Bv[j1][i1], T[j1][i1]), side)
        return self

    def finish(self, name, coll, mats, parent=None, bevel=None, smooth=False, subsurf=0, recalc=True):
        bm = self.bm
        if recalc: bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        uv = bm.loops.layers.uv.new('UVMap')
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
        if parent: ob.parent = parent; ob.matrix_parent_inverse = Matrix()
        if bevel:
            md = ob.modifiers.new('Bevel', 'BEVEL'); md.width = bevel[0] * S; md.segments = bevel[1]; md.limit_method = 'ANGLE'
        if subsurf:
            md = ob.modifiers.new('Soft', 'SUBSURF'); md.levels = md.render_levels = subsurf
        return ob


def collection(name):
    c = bpy.data.collections.get(name)
    if not c: c = bpy.data.collections.new(name); sc.collection.children.link(c)
    return c


# ================================================================ 1. your picks: navy wardrobe strips (legs L1 are already in v2)
navy = material('M_Strip_navy', '#2F3D52', 0.45)
for n in ('WARD_Door_Left_back', 'WARD_Door_Right_front'):
    bpy.data.objects[n].material_slots[1].material = navy

# ================================================================ 2. MyMax MX6, after your photos
root = bpy.data.objects['CHAIR_Gaming_MyMax_MX6']
for n in ('CHAIR_Seat_Arms', 'CHAIR_Backrest', 'CHAIR_Armrests', 'CHAIR_Logo_MYMAX', 'CHAIR_Logo_MX6', 'CUT_Chair_Slots', 'CHAIR_Slot_Trims'):
    remove(n)
blue, black = bpy.data.materials['M_Chair_Blue'], bpy.data.materials['M_Chair_Black']
blue.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*lin('#1F4E9A'), 1)   # brighter royal blue, as in the photos
quilt = bpy.data.materials.get('M_Chair_Blue_Quilted')
if quilt: bpy.data.materials.remove(quilt)
quilt = blue.copy(); quilt.name = 'M_Chair_Blue_Quilted'; nt = quilt.node_tree; L = nt.links; p = nt.nodes['Principled BSDF']
ah = node(nt, 'ShaderNodeAttribute', -1800, -900, attribute_name='quilt_h'); axn = node(nt, 'ShaderNodeAttribute', -1800, -1150, attribute_name='quilt_x')


def mnode(op, a, b=None, x=0, y=0):
    n = node(nt, 'ShaderNodeMath', x, y, operation=op)
    for i, val in enumerate((a, b)):
        if val is None: continue
        if isinstance(val, (int, float)): n.inputs[i].default_value = val
        else: L.new(val, n.inputs[i])
    return n.outputs[0]


hh = ah.outputs['Fac']; xx = axn.outputs['Fac']
dh = mnode('MULTIPLY', mnode('ABSOLUTE', mnode('SUBTRACT', mnode('FRACT', mnode('ADD', mnode('DIVIDE', mnode('SUBTRACT', hh, 15.3, -1600, -900), 9.5, -1450, -900), 0.5, -1300, -900), -1150, -900), 0.5, -1000, -900), -850, -900), 9.5, -700, -900)
inrange = mnode('MULTIPLY', mnode('GREATER_THAN', hh, 10.5, -1000, -700), mnode('LESS_THAN', hh, 54.0, -1000, -600), -850, -650)
dx = mnode('ABSOLUTE', xx, None, -1600, -1150)
inx = mnode('MULTIPLY', mnode('GREATER_THAN', hh, 6.0, -1450, -1300), mnode('LESS_THAN', hh, 54.0, -1450, -1400), -1300, -1350)
def groove(d, w, x, y):
    mr = node(nt, 'ShaderNodeMapRange', x, y, interpolation_type='SMOOTHSTEP')
    mr.inputs['From Min'].default_value, mr.inputs['From Max'].default_value = 0.0, w
    mr.inputs['To Min'].default_value, mr.inputs['To Max'].default_value = 1.0, 0.0
    L.new(d, mr.inputs['Value']); return mr.outputs['Result']
g = mnode('MAXIMUM', mnode('MULTIPLY', groove(dh, 0.35, -550, -900), inrange, -400, -900),
          mnode('MULTIPLY', groove(dx, 0.3, -1150, -1150), inx, -1000, -1250), -250, -1000)
bump = node(nt, 'ShaderNodeBump', -100, -800, invert=True); bump.inputs['Strength'].default_value = 0.8; bump.inputs['Distance'].default_value = 0.003
L.new(g, bump.inputs['Height'])
if p.inputs['Normal'].is_linked: L.new(p.inputs['Normal'].links[0].from_socket, bump.inputs['Normal'])
L.new(bump.outputs['Normal'], p.inputs['Normal'])
dk = node(nt, 'ShaderNodeVectorMath', -100, 300, operation='SCALE'); dk.inputs[0].default_value = p.inputs['Base Color'].default_value[:3]
L.new(mnode('SUBTRACT', 1.0, mnode('MULTIPLY', g, 0.35, -250, 300), -200, 200), dk.inputs['Scale']); L.new(dk.outputs['Vector'], p.inputs['Base Color'])

t = math.radians(12); UP = Vector((0, -math.sin(t), math.cos(t))); FW = Vector((0, math.cos(t), math.sin(t))); AX = Vector((1, 0, 0))
O = Vector((0, -22, 50))
P = lambda x, d, h: O + AX * x + FW * d + UP * h
ROWS = [(0, 23.0, 14.5, 7.0), (7, 23.5, 14.5, 8.5), (17, 23.5, 14.5, 9.5), (27, 24.0, 14.5, 9.5), (35, 24.0, 14.5, 9.0),
        (41, 26.0, 14.5, 10.0), (48, 28.5, 14.5, 11.0), (54, 28.0, 14.5, 10.0), (58, 25.0, 15.0, 7.0), (61, 21.0, 16.0, 3.5),
        (65, 17.5, 16.5, 1.5), (72, 17.2, 16.5, 1.0), (79, 16.8, 16.3, 0.8), (83, 15.8, 15.3, 0.5), (85.5, 13.5, 13.0, 0.3),
        (86.5, 10.0, 9.5, 0.0)]


def row_pts(h, W, C, dw):
    Ci = min(C, W - 2.5); Si = Ci + min(4.0, 0.6 * (W - 1.5 - Ci)); lb = 2.0 * math.exp(-((h - 22) / 9) ** 2)
    xs = [-W, -(W - 1.5), -Si, -Ci, -Ci / 2, 0, Ci / 2, Ci, Si, W - 1.5, W]
    ds = [dw * 0.55, dw, dw * 0.45, 1.2 + lb * 0.6, 2.4 + lb, 2.0 + lb, 2.4 + lb, 1.2 + lb * 0.6, dw * 0.45, dw, dw * 0.55]
    back = -8.0 + (max(0.0, h - 60) / 26.5) * 2.5
    return xs, ds, [back - 1.2 * (1 - (x / W) ** 2) for x in xs]


def face_mat(j, h):                         # 0 quilted blue centre, 1 black, 2 plain blue
    if j in (3, 4, 5, 6): return 0 if h < 54 else 2
    if j in (2, 7): return 2 if h >= 60 else 1
    return 2 if (h >= 41 or 7 <= h < 27) else 1


bk = Mesh(layers=('quilt_h', 'quilt_x')); Fr, Bk = [], []
for h, W, C, dw in ROWS:
    xs, ds, dbk = row_pts(h, W, C, dw)
    Fr.append([bk.v(P(x, d, h), quilt_h=h, quilt_x=x) for x, d in zip(xs, ds)])
    Bk.append([bk.v(P(x, d, h), quilt_h=-100.0, quilt_x=0.0) for x, d in zip(xs, dbk)])
nc = len(Fr[0])
for r in range(len(ROWS) - 1):
    hm = (ROWS[r][0] + ROWS[r + 1][0]) / 2
    for i in range(nc - 1):
        bk.f((Fr[r][i], Fr[r][i + 1], Fr[r + 1][i + 1], Fr[r + 1][i]), face_mat(i, hm))
        bk.f((Bk[r][i], Bk[r + 1][i], Bk[r + 1][i + 1], Bk[r][i + 1]), 1)
    for i in (0, nc - 1):
        bk.f((Fr[r][i], Fr[r + 1][i], Bk[r + 1][i], Bk[r][i]), 1)
for r in (0, len(ROWS) - 1):
    for i in range(nc - 1): bk.f((Fr[r][i], Bk[r][i], Bk[r][i + 1], Fr[r][i + 1]), 1)
back = bk.finish('CHAIR_Backrest', 'FURN_Chair', [quilt, black, blue], parent=root, smooth=True, subsurf=2)
back['note'] = 'MyMax MX6 backrest after your photos: quilted blue centre, black stripes, blue shoulder wings and lower pads, harness slots'


def trap(top_hw, bot_hw, height, c=0.9):
    """Trapezoid with chamfered corners, points (x, h) about its centre, counter-clockwise."""
    corners = [(-bot_hw, -height / 2), (bot_hw, -height / 2), (top_hw, height / 2), (-top_hw, height / 2)]
    pts = []
    for k in range(4):
        p0, p1, p2 = Vector(corners[k - 1]), Vector(corners[k]), Vector(corners[(k + 1) % 4])
        pts += [tuple(p1 + (p0 - p1).normalized() * c), tuple(p1 + (p2 - p1).normalized() * c)]
    return pts


cut, trims = Mesh(), Mesh()
for sx in (-1, 1):
    cx, ch = sx * 7.6, 61.0
    Oc = P(cx, 0, ch)
    trims.ring(Oc, AX, UP, FW, trap(6.0, 5.0, 12.6), trap(4.5, 3.6, 9.8, 0.7), 1.3, 3.0, 0)
    cut.prism(Oc, AX, UP, FW, trap(4.5, 3.6, 9.8, 0.7), -14.0, 6.0, 0)
co = cut.finish('CUT_Chair_Slots', 'FURN_Chair', ['M_Plastic_Black'], parent=root); co.hide_render = True; co.display_type = 'WIRE'
bo = back.modifiers.new('Harness_Slots', 'BOOLEAN'); bo.operation = 'DIFFERENCE'; bo.object = co; bo.solver = 'EXACT'
bo.material_mode = 'TRANSFER'
trims.finish('CHAIR_Slot_Trims', 'FURN_Chair', ['M_Plastic_Black'], parent=root, bevel=(0.3, 2), smooth=True)

logo = material('M_Chair_Logo', '#E8E8E6', 0.6)
X, Y, Z = -AX, UP, FW                          # text reads left-to-right seen from the front
for name, body, size, cx, ch in (('CHAIR_Logo_MYMAX', 'MYMAX', 2.6, 0.0, 81.0), ('CHAIR_Logo_MX6', 'MX6', 1.6, -4.4, 78.3)):
    cu = bpy.data.curves.new(name, 'FONT'); cu.body = body; cu.size = size * S; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
    cu.extrude = 0.0003; cu.materials.append(logo)
    ob = bpy.data.objects.new(name, cu); bpy.data.collections['FURN_Chair'].objects.link(ob)
    ob.parent = root; ob.matrix_parent_inverse = Matrix()
    ob.matrix_basis = Matrix.Translation(P(cx, 2.85, ch) * S) @ Matrix((X, Y, Z)).transposed().to_4x4()


def seat_top(x, y):
    a = abs(x)
    zc = 50.0 + 1.2 * math.exp(-((y - 17) / 6) ** 2) + 0.8 * max(0.0, (-12 - y) / 12)
    zb = 55.0 + 1.0 * min(1.0, max(0.0, (y + 10) / 22))
    z = zc if a <= 17.5 else zc + 0.4 if a <= 21 else zb if a <= 25.5 else zb - 2.5 * (a - 25.5) / 1.5
    return z - 3.5 * min(1.0, max(0.0, (y - 22) / 5)) ** 2


st = Mesh().grid_solid([-27, -25.5, -21, -17.5, -12, -6, 0, 6, 12, 17.5, 21, 25.5, 27], [-24, -20, -12, -4, 4, 12, 18, 22, 25, 27],
                       seat_top, 44.0, lambda x, y: 2 if abs(x) < 17.5 else 1 if abs(x) < 21 else (2 if y > -14 and abs(x) < 25.5 else 1))
st.box(-26, 26, -24, 25, 40, 44.2, 1)
st.finish('CHAIR_Seat_Arms', 'FURN_Chair', [quilt, black, blue], parent=root, smooth=True, subsurf=2)['note'] = 'MX6 bucket seat'
ar = Mesh()
for sx in (-1, 1):
    ar.box(sx * 27.0, sx * 30.6, -6.5, 2.0, 43.0, 63.5).box(sx * 25.6, sx * 32.0, -14.0, 12.0, 63.5, 66.4)   # armrest post + pad
    ar.cyl((sx * 27.0, -21.0, 49.0), (sx * 28.8, -21.0, 49.0), 6.5, 32)                                     # recline hinge cover
ar.cyl((28.8, -21.0, 49.0), (31.0, -21.0, 49.0), 1.2, 16).box(29.6, 30.8, -20.5, -6.0, 47.6, 49.2)          # recline lever
ar.finish('CHAIR_Armrests', 'FURN_Chair', ['M_Plastic_Black'], parent=root, bevel=(0.6, 3), smooth=True)

# ================================================================ 3. ceiling fan (3 white blades, opal globe) - light OFF
collection('FIXT_Ceiling_Fan')
FX, FY = 150.0, 145.0                       # EST: centre of the ceiling
white_p = material('M_Fan_White', '#F2F1EC', 0.3, **{'Coat Weight': 0.3})
band = material('M_Fan_Band', '#E6DBC4', 0.45)
opal = material('M_Fan_Opal_Glass', '#ECEBE6', 0.15, **{'Coat Weight': 0.8, 'Subsurface Weight': 0.25})
body = Mesh()
body.revolve((FX, FY, 0), (0, 0, 1), [(0, 270), (6.5, 270), (6.5, 268.5), (5.6, 266.6), (4.0, 266.2), (8.0, 265.8), (9.0, 265.0),
                                      (9.3, 263.0), (9.3, 257.5), (8.8, 256.2), (8.4, 255.6), (0, 255.6)])
body.revolve((FX, FY, 0), (0, 0, 1), [(0, 255.6), (8.3, 255.6), (8.45, 255.2), (8.45, 251.8), (8.3, 251.4), (0, 251.4)], mats=[1] * 5)
globe = [(0, 251.4), (8.1, 251.4)] + [(8.4 * max(0.0, 1 - (k / 18) ** 1.7) ** 0.62, 250.4 - 13.9 * k / 18) for k in range(19)]
globe[-1] = (0, globe[-1][1])
body.revolve((FX, FY, 0), (0, 0, 1), globe, mats=[2] * (len(globe) - 1))
body.finish('FAN_Body', 'FIXT_Ceiling_Fan', [white_p, band, opal], smooth=True)['note'] = 'ceiling fan body + light kit (EST sizes); light off'
bl = Mesh(); nu, nv, Lb, r0, zm = 24, 10, 45.0, 6.5, 259.5
for k in range(3):
    th = math.radians(30 + 120 * k); ct, st_ = math.cos(th), math.sin(th)
    top, bot = [], []
    for i in range(nu + 1):
        s = i / nu; r = r0 + s * Lb; gro = math.sin(min(s / 0.72, 1) * math.pi / 2)
        wl, wt = 3.0 + 6.5 * gro, 2.5 + 5.0 * gro
        if s > 0.72:
            e = max(0.12, math.sqrt(max(0.0, 1 - ((s - 0.72) / 0.28) ** 2))); wl *= e; wt *= e
        a = math.radians(13 - 4 * s); rt, rb = [], []
        for j in range(nv + 1):
            q = -wt + (wl + wt) * j / nv; zc = -0.5 * ((2 * j / nv) - 1) ** 2
            qq, zz = q * math.cos(a) - zc * math.sin(a), q * math.sin(a) + zc * math.cos(a)
            wx, wy = FX + r * ct - qq * st_, FY + r * st_ + qq * ct
            rt.append(bl.v((wx, wy, zm + zz + 0.28))); rb.append(bl.v((wx, wy, zm + zz - 0.28)))
        top.append(rt); bot.append(rb)
    for i in range(nu):
        for j in range(nv):
            bl.f((top[i][j], top[i + 1][j], top[i + 1][j + 1], top[i][j + 1])); bl.f((bot[i][j], bot[i][j + 1], bot[i + 1][j + 1], bot[i + 1][j]))
    edge = [(i, 0) for i in range(nu + 1)] + [(nu, j) for j in range(1, nv + 1)] + [(i, nv) for i in range(nu - 1, -1, -1)] + [(0, j) for j in range(nv - 1, 0, -1)]
    for m in range(len(edge)):
        (i0, j0), (i1, j1) = edge[m], edge[(m + 1) % len(edge)]
        bl.f((top[i0][j0], bot[i0][j0], bot[i1][j1], top[i1][j1]))
bl.finish('FAN_Blades', 'FIXT_Ceiling_Fan', [white_p], smooth=True)['note'] = 'three paddle blades, ~102 cm sweep (EST)'

# ================================================================ 4. RGB LED strips (shelves: wall wash; piano: halo)
for k, v, ui in (('LED_RGB', lin(dict((c[0], c[3]) for c in COLORS)[DEFAULT_COLOR]), dict(subtype='COLOR', min=0.0, max=1.0)),
                 ('LED_Brightness', 1.0, dict(min=0.0, max=10.0, description='LED strip brightness')),
                 ('Desk_Lamp', 1.0, dict(min=0.0, max=5.0, description='desk lamp brightness'))):
    sc[k] = v; sc.id_properties_ui(k).update(**ui)
LC = collection('LIGHT_LED_Strips')
for o in list(LC.objects): bpy.data.objects.remove(o)
alu = bpy.data.materials['M_Metal_Brushed']


def led_material(name, k):
    m = bpy.data.materials.get(name)
    if m: bpy.data.materials.remove(m)
    m = material(name, '#F4F4F2', 0.35); nt = m.node_tree; p = nt.nodes['Principled BSDF']
    rgb = node(nt, 'ShaderNodeRGB', -300, 200); rgb.name = rgb.label = 'LED_RGB'
    nt.links.new(rgb.outputs[0], p.inputs['Emission Color'])
    for i in range(3): drive(nt, 'nodes["LED_RGB"].outputs[0].default_value', 'var', 'LED_RGB', i, i)
    drive(nt, f'nodes["Principled BSDF"].inputs[{p.inputs.find("Emission Strength")}].default_value', f'var * {k:.1f}', 'LED_Brightness')
    return m


def strip_light(name, loc, rot, length, w_per_m, width=1.2, spread=130):
    lt = bpy.data.lights.new(name, 'AREA'); lt.shape = 'RECTANGLE'; lt.size, lt.size_y = width * S, length * S
    lt.spread = math.radians(spread)
    ob = bpy.data.objects.new(name, lt); LC.objects.link(ob); ob.location = Vector(loc) * S; ob.rotation_euler = rot
    for i in range(3): drive(lt, 'color', 'var', 'LED_RGB', i, i)
    drive(lt, 'energy', f'var * {w_per_m * length / 100:.2f}', 'LED_Brightness')
    ob['note'] = f'RGB LED strip, {w_per_m:.0f} W/m (Blender units); colour = Scene LED_RGB'
    return ob


def visible_only(ob):
    ob.visible_diffuse = False; ob.visible_shadow = False; ob.visible_transmission = False


shelf_led = led_material('M_LED_Shelf', SHELF_W_PER_M / 0.012)
piano_led = led_material('M_LED_Piano', PIANO_W_PER_M / 0.011)
ch, df = Mesh(), Mesh()
frames = (15.0, 68.0, 116.0, 161.0)
for n, (y0, y1, zb) in enumerate([(4, 131, 142.0), (4, 171, 164.5), (4, 171, 187.5)]):
    cuts = [y0 + 0.5] + [c for f in frames if y0 < f < y1 for c in (f - 1.1, f + 1.1)] + [y1 - 0.5]
    for a, b in zip(cuts[::2], cuts[1::2]):
        ch.box(FRONT + 2.3, FRONT + 3.9, a, b, zb - 0.9, zb, 0); df.box(FRONT + 2.5, FRONT + 3.7, a + 0.1, b - 0.1, zb - 0.97, zb - 0.88, 0)
    strip_light(f'LED_Shelf_{n + 1}', (FRONT + 3.1, (y0 + y1) / 2, zb - 1.0), (0, math.radians(20), 0), y1 - y0 - 1, SHELF_W_PER_M)
ch.box(296.4, 297.9, 98.0, 223.5, 86.5, 87.2, 0); df.box(296.55, 297.75, 98.2, 223.3, 87.2, 87.28, 1)
strip_light('LED_Piano_Halo', (297.15, 160.75, 87.32), (math.pi, math.radians(40), 0), 125.3, PIANO_W_PER_M, 1.1, 100)   # aimed at the wall: halo
ch.finish('LED_Channels', 'LIGHT_LED_Strips', [alu])
visible_only(df.finish('LED_Diffusers', 'LIGHT_LED_Strips', [shelf_led, piano_led]))

# ================================================================ 5. desk lamp: open shade, glowing bulb, strong spot
lamp = bpy.data.objects['PROP_Desk_Lamp']
bm = bmesh.new(); bm.from_mesh(lamp.data); bm.verts.ensure_lookup_table(); seen, isl_all = set(), []
for v0 in bm.verts:
    if v0.index in seen: continue
    stack, isl = [v0], []
    while stack:
        q = stack.pop()
        if q.index in seen: continue
        seen.add(q.index); isl.append(q); stack += [e.other_vert(q) for e in q.link_edges]
    isl_all.append(isl)
target = Vector((22.75, 28.5, 119.25)) * S
shade_isl = min(isl_all, key=lambda isl: (sum((q.co for q in isl), Vector()) / len(isl) - target).length)
if max(q.co.z for q in shade_isl) > 1.10 and len(shade_isl) > 20:
    bmesh.ops.delete(bm, geom=shade_isl, context='VERTS')
bm.to_mesh(lamp.data); bm.free()
for n in ('PROP_Desk_Lamp_Shade', 'PROP_Desk_Lamp_Bulb', 'LIGHT_Desk_Lamp'): remove(n)
apex = Vector((24.0, 36.0, 109.0)); axis = Vector((5.5, 5.0, -9.5)).normalized()
outer = [(0, 0), (2.2, 0), (2.6, 1.0), (3.6, 3.5), (5.0, 7.0), (6.6, 10.5), (7.2, 12.0)]
inner = [(7.08, 12.0), (6.48, 10.6), (4.88, 7.1), (3.48, 3.6), (2.45, 1.15), (2.05, 0.15), (0, 0.15)]
sh = Mesh().revolve(apex, axis, outer + inner, n=48, mats=[0] * (len(outer) - 1) + [0] + [1] * (len(inner) - 1))
sh.cyl(apex + axis * 0.5, apex + axis * 3.2, 1.4, 20, 2)
sh.finish('PROP_Desk_Lamp_Shade', 'PROPS_Lived_In', ['M_Steel_Black', material('M_Lamp_Inner', '#E9E6DF', 0.55), 'M_Plastic_Black'],
          smooth=True, recalc=False)
bulb = material('M_Lamp_Bulb', '#FFF4E0', 0.2, **{'Emission Color': (1.0, 0.72, 0.42, 1.0)})
drive(bulb.node_tree, f'nodes["Principled BSDF"].inputs[{bulb.node_tree.nodes["Principled BSDF"].inputs.find("Emission Strength")}].default_value',
      'var * 600.0', 'Desk_Lamp')
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=2.3 * S)
bmesh.ops.translate(bm, verts=bm.verts[:], vec=(apex + axis * 5.6) * S)
me = bpy.data.meshes.new('PROP_Desk_Lamp_Bulb'); bm.to_mesh(me); bm.free(); me.materials.append(bulb)
for pl in me.polygons: pl.use_smooth = True
bo_ = bpy.data.objects.new('PROP_Desk_Lamp_Bulb', me); bpy.data.collections['PROPS_Lived_In'].objects.link(bo_); visible_only(bo_)
lt = bpy.data.lights.new('LIGHT_Desk_Lamp', 'SPOT'); lt.spot_size = math.radians(115); lt.spot_blend = 0.35
lt.shadow_soft_size = 2.3 * S; lt.use_temperature = True; lt.temperature = 3000.0
drive(lt, 'energy', f'var * {DESK_LAMP_W:.1f}', 'Desk_Lamp')
lo = bpy.data.objects.new('LIGHT_Desk_Lamp', lt); bpy.data.collections['LIGHT_Lighting'].objects.link(lo)
lo.location = (apex + axis * 5.6) * S; lo.rotation_euler = axis.to_track_quat('-Z', 'Y').to_euler()
lo['note'] = 'desk lamp, warm 3000 K spot; brightness = Scene Desk_Lamp'

# ================================================================ 6. blue hour
old = sc.world; old.use_fake_user = True                  # daylight world kept in the file (World selector)
w = bpy.data.worlds.get('WORLD_Dusk') or bpy.data.worlds.new('WORLD_Dusk'); w.use_nodes = True; wn = w.node_tree
for n_ in list(wn.nodes):
    if n_.type != 'OUTPUT_WORLD': wn.nodes.remove(n_)
outn = next(n_ for n_ in wn.nodes if n_.type == 'OUTPUT_WORLD')
tc = node(wn, 'ShaderNodeTexCoord', -800, 0); mp = node(wn, 'ShaderNodeMapping', -600, 0); mp.label = 'Turn the view outside'
mp.inputs['Rotation'].default_value = (0, 0, math.radians(-36.0))
env = node(wn, 'ShaderNodeTexEnvironment', -350, 0)
path = os.path.join(TEX, 'dusk_from_homecoming_center_rooftop.exr'); env.image = bpy.data.images.load(path, check_existing=True)
env.image.filepath = bpy.path.relpath(path)
bg = node(wn, 'ShaderNodeBackground', 0, 0); bg.label = 'Dusk sky brightness'; bg.inputs['Strength'].default_value = DUSK_STRENGTH
for a, b in [(tc.outputs['Generated'], mp.inputs['Vector']), (mp.outputs['Vector'], env.inputs['Vector']),
             (env.outputs['Color'], bg.inputs['Color']), (bg.outputs[0], outn.inputs['Surface'])]:
    wn.links.new(a, b)
sc.world = w; sc['sunny'] = 0; sc.update_tag(); bpy.context.view_layer.update()      # afternoon sun lamp off
sc.view_settings.exposure = EXPOSURE
gl = sc.compositing_node_group.nodes.get('FX_Window_Bloom')
if gl: gl.inputs['Threshold'].default_value = 1.5; gl.inputs['Strength'].default_value = 0.12; gl.inputs['Size'].default_value = 0.5

# ================================================================ 7. cameras
def level_cam(name, loc, az, lens, shift_y, focus, fstop):
    remove(name); cam = bpy.data.cameras.new(name); cam.lens = lens; cam.sensor_width = 36; cam.sensor_fit = 'HORIZONTAL'
    cam.shift_y = shift_y; cam.clip_start = 0.03; cam.clip_end = 50; cam.dof.use_dof = True; cam.dof.focus_distance = focus * S
    cam.dof.aperture_fstop = fstop; ob = bpy.data.objects.new(name, cam); bpy.data.collections['CAM_Cameras'].objects.link(ob)
    a = math.radians(az); ob.location = Vector(loc) * S
    ob.rotation_euler = Vector((math.cos(a), math.sin(a), 0)).to_track_quat('-Z', 'Y').to_euler(); return ob


def aim(name, loc, target, lens, fstop):
    remove(name); cam = bpy.data.cameras.new(name); cam.lens = lens; cam.sensor_width = 36; cam.sensor_fit = 'HORIZONTAL'
    cam.clip_start = 0.03; cam.clip_end = 50; ob = bpy.data.objects.new(name, cam); bpy.data.collections['CAM_Cameras'].objects.link(ob)
    v = Vector(target) - Vector(loc); ob.location = Vector(loc) * S; ob.rotation_euler = v.to_track_quat('-Z', 'Y').to_euler()
    cam.dof.use_dof = True; cam.dof.focus_distance = v.length * S; cam.dof.aperture_fstop = fstop; return ob


level_cam('CAM_Dusk_Wide', (45, 225, 145), -52, 14, 0.04, 230, 5.6)
aim('CAM_Detail_Fan', (60, 240, 128), (185, 100, 234), 18, 5.6)
cf = root.matrix_world.to_3x3() @ Vector((0, 1, 0)); cr = root.matrix_world.translation * 100
aim('CAM_Detail_Chair', tuple(cr + cf * 125 + Vector((0, 0, 112))), tuple(root.matrix_world @ (Vector((0, -18, 82)) * S) * 100), 30, 2.8)
sc.camera = bpy.data.objects['CAM_Dusk_Wide']
sc['experiment'] = (sc.get('experiment', '') + ' | round 3: navy wardrobe strips + square black legs, MX6 chair remodelled, ceiling fan (off), '
                    'RGB LED strips on shelves and piano, strong desk lamp, blue hour')
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'Bedroom_Teak_Navy_v3.blend'), compress=True)
print('SAVED v3')

# ================================================================ 8. renders
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'METAL'; prefs.get_devices()
for d in prefs.devices: d.use = True
sc.cycles.device = 'GPU'; sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_depth = '8'


def set_color(code):
    c = dict((x[0], x[3]) for x in COLORS)[code]; rgb = lin(c)
    sc['LED_RGB'] = rgb; sc['LED_Brightness'] = max(0.9, min(3.0, (0.5 / max(lum(rgb), 1e-3)) ** 0.7))   # similar perceived brightness
    sc.update_tag(); bpy.context.view_layer.update()


def shot(cam, path, spp, pct):
    sc.camera = bpy.data.objects[cam]; sc.cycles.samples = spp; sc.render.resolution_percentage = pct
    os.makedirs(os.path.dirname(path), exist_ok=True); sc.render.filepath = path; bpy.ops.render.render(write_still=True)
    print('RENDERED', os.path.relpath(path, OUT), flush=True)


VIEWS = ['CAM_Dusk_Wide', 'CAM_Render_B_From_Window', 'CAM_Detail_Wall3', 'CAM_Hero_3_Desk', 'CAM_Detail_Fan', 'CAM_Detail_Chair']
scale = float(OPT.get('scale', 1.0))
if SET == 'test':
    set_color(DEFAULT_COLOR)
    for cam in OPT.get('cams', ','.join(VIEWS)).split(','):
        shot(cam, os.path.join(OUT, 'test', cam.replace('CAM_', '') + '.png'), int(OPT.get('spp', 48)), round(40 * scale))
if SET in ('all', 'colors'):
    for code, slug, label, hexc in COLORS:
        set_color(code); shot('CAM_Dusk_Wide', os.path.join(OUT, 'colors', f'{code}_{slug}.png'), int(OPT.get('spp', 256)), round(67 * scale))
if SET in ('all', 'views'):
    set_color(DEFAULT_COLOR)
    for cam in VIEWS:
        shot(cam, os.path.join(OUT, 'views', cam.replace('CAM_', '') + '.png'), int(OPT.get('vspp', 512)), round(100 * scale))
if SET in ('all', 'colors', 'views'):
    os.makedirs(OUT, exist_ok=True)
    json.dump({'colors': [dict(code=c, slug=s, label=l, hex=h) for c, s, l, h in COLORS], 'default': DEFAULT_COLOR},
              open(os.path.join(OUT, 'options.json'), 'w'), indent=1)
