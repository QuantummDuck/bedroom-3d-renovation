"""
Bedroom reconstruction - generates Bedroom_Baseline.blend from scratch.

Run (headless):
  Blender -b --factory-startup --python build_bedroom.py -- [--out PATH.blend]

All dimensions below are in CENTIMETRES; they are converted to metres for Blender.
World frame: origin = floor at the inner corner of wall 2 (window wall) and wall 4.
  +X runs along wall 2 toward wall 3 (300 cm), +Y runs along wall 4 toward wall 1 (door wall, 290 cm), +Z up.

Every object carries custom properties 'dim_source' and 'note':
  DRAWING  your A4 sketches                         USER   measurements you gave in chat
  PHOTO    recovered from calibrated photos (~+-3 cm) SPEC   manufacturer data
  EST      estimated / assumed (+-5-10 cm) - check these first if something looks off
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix, Euler

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = ARGV[ARGV.index('--out') + 1] if '--out' in ARGV else os.path.join(HERE, 'Bedroom_Baseline.blend')
S = 0.01  # cm -> m

# =============================================================================== DIMENSIONS (cm)
RW, RD, RH = 300.0, 290.0, 270.0          # DRAWING  room inside: walls 1/2 = 300, walls 3/4 = 290, height 270
WALL_T, WALL2_T = 15.0, 20.0              # EST      wall thickness (only visible in the door/window reveals)
BB_H, BB_T = 10.0, 1.5                    # PHOTO    baseboard height (10.4 measured), thickness EST
CROWN = dict(drop=17.5, steps=(13.0, 8.6), out=12.0)   # PHOTO bottom edge at 252.5 and step lines; EST ceiling projection

# Door (wall 1, near wall 4). DRAWING leaf 71.5 x 210; PHOTO trim 7.5 wide (measured 7.4-7.5), corner gap 7.5
DOOR_X0, DOOR_W, DOOR_H, DOOR_T = 15.0, 71.5, 210.0, 3.5
TRIM_W = 7.5
# Window (wall 2). DRAWING outer 151.5 x 121.5, sill 97.5, 54.5 from wall 3, frame 1 cm proud of the wall
WIN_X0, WIN_X1, WIN_Z0, WIN_Z1, WIN_TRIM, WIN_PROUD = 94.0, 245.5, 97.5, 219.0, 4.0, 1.0
# Wardrobe (wall 1 / wall 3 corner). DRAWING 181 x 63 floor-to-ceiling, 25 cm from the door trim
WARD_X0, WARD_D = 119.0, 63.0
WARD_STRIPS = (70.0, 130.5, 195.5)        # PHOTO strip centre heights (photo 19/18 calibration)
WARD_DOOR_Z0, WARD_DOOR_Z1 = 11.4, 261.6  # PHOTO door bottom 11.4; top EST (under the 8 cm top rail)
WARD_HANDLE_Z = (76.9, 125.3)             # PHOTO
# Furniture
BED = dict(x0=110.2, x1=298.2, y0=1.8, y1=95.8, h=53.0)         # USER 188 x 94 x 53; position PHOTO
DESK = dict(d=49.0, l=170.0, h=80.0, t=3.0)                      # USER; along wall 4 from the wall-2 corner
PIANO = dict(yl=225.5, w=129.5, d=38.0, h=14.0, xf=260.5, z0=72.5)  # SPEC Korg SP-250 129.5 x 38 x 14; position PHOTO

# =============================================================================== helpers
def lin(hexstr):
    c = [int(hexstr[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple((v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in c) + (1.0,)


def reset():
    for ob in list(bpy.data.objects): bpy.data.objects.remove(ob)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights, bpy.data.images, bpy.data.textures):
        for d in list(coll):
            try: coll.remove(d)
            except Exception: pass
    for c in list(bpy.data.collections): bpy.data.collections.remove(c)


COLLS = {}
def coll(name, parent=None):
    c = bpy.data.collections.new(name)
    (COLLS[parent] if parent else bpy.context.scene.collection).children.link(c)
    COLLS[name] = c
    return c


def tag(ob, src, note=''):
    ob['dim_source'] = src
    if note: ob['note'] = note


def empty(name, loc, c, rz=0.0, src='', note=''):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type, e.empty_display_size = 'PLAIN_AXES', 0.25
    e.location = Vector(loc) * S
    e.rotation_euler = (0, 0, math.radians(rz))
    COLLS[c].objects.link(e)
    if src: tag(e, src, note)
    return e


class MB:
    """bmesh builder working in centimetres."""
    def __init__(self):
        self.bm = bmesh.new()

    def _faces(self, v, mi):
        for f in [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]:
            self.bm.faces.new([v[i] for i in f]).material_index = mi

    def box(self, x0, x1, y0, y1, z0, z1, mi=0):
        x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
        v = [self.bm.verts.new(p) for p in [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                                             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]]
        self._faces(v, mi)
        return self

    def obox(self, c, ax, ay, az, hx, hy, hz, mi=0):
        """Oriented box: centre c, right-handed unit axes, half sizes."""
        c, ax, ay, az = Vector(c), Vector(ax), Vector(ay), Vector(az)
        v = [self.bm.verts.new(c + sx * hx * ax + sy * hy * ay + sz * hz * az)
             for (sx, sy, sz) in [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]]
        self._faces(v, mi)
        return self

    def beam(self, p0, p1, w, h, mi=0, up=(0, 0, 1)):
        """Rectangular tube from p0 to p1 (w across, h along 'up')."""
        p0, p1 = Vector(p0), Vector(p1)
        a = (p1 - p0).normalized(); u = Vector(up)
        if abs(a.dot(u)) > 0.99: u = Vector((1, 0, 0))
        y = u.cross(a).normalized(); z = a.cross(y)
        return self.obox((p0 + p1) / 2, a, y, z, (p1 - p0).length / 2, w / 2, h / 2, mi)

    def cyl(self, p0, p1, r, segs=24, mi=0, r1=None):
        p0, p1 = Vector(p0), Vector(p1); a = (p1 - p0).normalized()
        u = a.orthogonal().normalized(); w = a.cross(u)
        r1 = r if r1 is None else r1
        b = [self.bm.verts.new(p0 + r * (math.cos(t) * u + math.sin(t) * w)) for t in [2 * math.pi * i / segs for i in range(segs)]]
        t_ = [self.bm.verts.new(p1 + r1 * (math.cos(t) * u + math.sin(t) * w)) for t in [2 * math.pi * i / segs for i in range(segs)]]
        for i in range(segs):
            j = (i + 1) % segs
            self.bm.faces.new([b[i], b[j], t_[j], t_[i]]).material_index = mi
        self.bm.faces.new(b[::-1]).material_index = mi
        self.bm.faces.new(t_).material_index = mi
        return self

    def torus(self, c, axis, R, r, seg=32, seg2=10, mi=0):
        c, a = Vector(c), Vector(axis).normalized(); u = a.orthogonal().normalized(); w = a.cross(u)
        rings = []
        for i in range(seg):
            t = 2 * math.pi * i / seg; d = math.cos(t) * u + math.sin(t) * w
            rings.append([self.bm.verts.new(c + (R + r * math.cos(s)) * d + r * math.sin(s) * a)
                          for s in [2 * math.pi * k / seg2 for k in range(seg2)]])
        for i in range(seg):
            for k in range(seg2):
                q = [rings[i][k], rings[(i + 1) % seg][k], rings[(i + 1) % seg][(k + 1) % seg2], rings[i][(k + 1) % seg2]]
                self.bm.faces.new(q).material_index = mi
        return self

    def loft(self, path, side_n, w_axis, profile, closed=False, mi=0):
        """Sweep a 2D profile (u across, w along w_axis) along a polyline with mitred joints.
        side direction of a segment = side_n x segment_direction."""
        path = [Vector(p) for p in path]; n = len(path); N, W = Vector(side_n), Vector(w_axis)
        nseg = n if closed else n - 1
        sides = [N.cross((path[(i + 1) % n] - path[i]).normalized()) for i in range(nseg)]
        rings = []
        for k in range(n):
            sp = sides[k - 1] if (closed or k > 0) else sides[0]
            sn = sides[k] if k < nseg else sides[-1]
            m = (sp + sn).normalized(); m = m / max(m.dot(sn), 1e-6)
            rings.append([self.bm.verts.new(path[k] + u * m + w * W) for (u, w) in profile])
        npf = len(profile)
        for k in range(nseg):
            r0, r1 = rings[k], rings[(k + 1) % n]
            for j in range(npf):
                j2 = (j + 1) % npf
                self.bm.faces.new([r0[j], r1[j], r1[j2], r0[j2]]).material_index = mi
        if not closed:
            self.bm.faces.new(rings[0]).material_index = mi
            self.bm.faces.new(rings[-1][::-1]).material_index = mi
        return self

    def build(self, name, c, mats, origin=(0, 0, 0), parent=None, src='EST', note='', bevel=None, smooth=False, uv01=None, uv_xy=False):
        bm = self.bm
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        uvl = bm.loops.layers.uv.new('UVMap')
        for f in bm.faces:  # box projection in world metres, u along the face's long side
            ax = max(range(3), key=lambda i: abs(f.normal[i])); a, b = [i for i in range(3) if i != ax]
            co = [l.vert.co for l in f.loops]
            ext = lambda i: max(p[i] for p in co) - min(p[i] for p in co)
            if ext(b) > ext(a): a, b = b, a
            for l in f.loops: l[uvl].uv = (l.vert.co[a] * S, l.vert.co[b] * S)
        if uv_xy:  # flat cloth: one continuous top-down mapping, so printed patterns survive the drape
            for f in bm.faces:
                for l in f.loops: l[uvl].uv = (l.vert.co.x * S, l.vert.co.y * S)
        if uv01:  # explicit 0-1 UVs on faces whose normal matches uv01['normal'] (e.g. a picture)
            n0, ua, va, (u0, u1), (v0, v1) = uv01['normal'], uv01['u'], uv01['v'], uv01['urange'], uv01['vrange']
            for f in bm.faces:
                if f.normal.dot(Vector(n0)) > 0.9:
                    for l in f.loops:
                        l[uvl].uv = ((l.vert.co[ua] - u0) / (u1 - u0), (l.vert.co[va] - v0) / (v1 - v0))
        o = Vector(origin)
        for v in bm.verts: v.co = (v.co - o) * S
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        for m in mats: me.materials.append(MAT[m])
        if smooth:
            for p in me.polygons: p.use_smooth = True
        ob = bpy.data.objects.new(name, me); ob.location = o * S
        COLLS[c].objects.link(ob)
        if parent:
            ob.parent = parent
            ob.matrix_parent_inverse = Matrix.LocRotScale(parent.location, parent.rotation_euler, parent.scale).inverted()
        if bevel:
            md = ob.modifiers.new('Bevel', 'BEVEL'); md.width = bevel[0] * S; md.segments = bevel[1]
            md.limit_method = 'ANGLE'; md.harden_normals = False
        tag(ob, src, note)
        return ob


def grid(mb, x0, x1, y0, y1, z, step, mi=0):
    """Flat quad grid (cm) - the starting sheet for cloth simulations."""
    nx, ny = max(2, round((x1 - x0) / step)), max(2, round((y1 - y0) / step))
    vs = [[mb.bm.verts.new((x0 + (x1 - x0) * i / nx, y0 + (y1 - y0) * j / ny, z)) for i in range(nx + 1)] for j in range(ny + 1)]
    for j in range(ny):
        for i in range(nx): mb.bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i])).material_index = mi
    return mb


def heightfield(mb, xs, ys, top, bottom, mi=0):
    """Closed slab whose top surface follows top(x, y) - for shaped seats. xs/ys are sorted cm coordinates."""
    T = [[mb.bm.verts.new((x, y, top(x, y))) for x in xs] for y in ys]
    Bv = [[mb.bm.verts.new((x, y, bottom)) for x in xs] for y in ys]
    nx, ny = len(xs), len(ys)
    for j in range(ny - 1):
        for i in range(nx - 1):
            mb.bm.faces.new((T[j][i], T[j][i + 1], T[j + 1][i + 1], T[j + 1][i])).material_index = mi
            mb.bm.faces.new((Bv[j][i], Bv[j + 1][i], Bv[j + 1][i + 1], Bv[j][i + 1])).material_index = mi
    ring = [(0, i) for i in range(nx)] + [(j, nx - 1) for j in range(1, ny)] + [(ny - 1, i) for i in range(nx - 2, -1, -1)] + [(j, 0) for j in range(ny - 2, 0, -1)]
    for k in range(len(ring)):
        (j0, i0), (j1, i1) = ring[k], ring[(k + 1) % len(ring)]
        mb.bm.faces.new((T[j0][i0], Bv[j0][i0], Bv[j1][i1], T[j1][i1])).material_index = mi
    return mb


def simulate(cloths, colliders, frames, friction=10.0):
    """Run Blender's cloth solver to rest, then freeze the result into plain meshes (no simulation left in the file)."""
    sc = bpy.context.scene
    for ob in colliders:
        ob.modifiers.new('SimCollision', 'COLLISION'); ob.collision.thickness_outer = 0.003; ob.collision.cloth_friction = friction
    sc.frame_start, sc.frame_end = 1, frames
    for f in range(1, frames + 1): sc.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    for ob in cloths:
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
        old = ob.data; ob.modifiers.clear(); ob.data = me; bpy.data.meshes.remove(old)
    for ob in colliders: ob.modifiers.remove(ob.modifiers['SimCollision'])
    sc.frame_set(1)


def cloth(ob, mass, tension, bending, shear=15.0, quality=6, self_collide=False, pressure=0.0, gravity=1.0):
    md = ob.modifiers.new('Cloth', 'CLOTH'); s = md.settings
    s.quality, s.mass, s.air_damping = quality, mass, 2.0
    s.tension_stiffness = s.compression_stiffness = tension; s.shear_stiffness = shear; s.bending_stiffness = bending
    s.effector_weights.gravity = gravity
    if pressure: s.use_pressure = True; s.uniform_pressure_force = pressure
    cs = md.collision_settings; cs.collision_quality = 4; cs.distance_min = 0.003
    if self_collide: cs.use_self_collision = True; cs.self_distance_min = 0.003
    return md


def box(name, c, mat, x0, x1, y0, y1, z0, z1, **kw):
    kw.setdefault('origin', ((x0 + x1) / 2, (y0 + y1) / 2, min(z0, z1)))
    return MB().box(x0, x1, y0, y1, z0, z1).build(name, c, [mat], **kw)


def update(): bpy.context.view_layer.update()

# =============================================================================== materials
MAT = {}
def principled(name, color, rough=0.5, metal=0.0, **extra):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = lin(color) if isinstance(color, str) else color
    p.inputs['Roughness'].default_value = rough; p.inputs['Metallic'].default_value = metal
    for k, v in extra.items(): p.inputs[k].default_value = v
    m.diffuse_color = p.inputs['Base Color'].default_value  # solid-view colour
    MAT[name] = m
    return m, m.node_tree, p


def N(nt, kind, loc=(0, 0), **props):
    n = nt.nodes.new(kind); n.location = loc
    for k, v in props.items(): setattr(n, k, v)
    return n


def ramp(nt, stops, loc=(0, 0), interp='LINEAR'):
    r = N(nt, 'ShaderNodeValToRGB', loc); cr = r.color_ramp; cr.interpolation = interp
    while len(cr.elements) < len(stops): cr.elements.new(0.5)
    for e, (pos, col) in zip(cr.elements, stops): e.position = pos; e.color = lin(col)
    return r


def wood(name, dark, light, rough=0.45, grain=120.0):
    """Subtle straight-grain laminate: fine streaks along the board's long side + broad tone variation."""
    m, nt, p = principled(name, light, rough)
    L = nt.links; tc = N(nt, 'ShaderNodeTexCoord', (-1000, 0))
    def noise(sx, sy, detail, loc):
        mp = N(nt, 'ShaderNodeMapping', (loc[0] - 180, loc[1])); mp.inputs['Scale'].default_value = (sx, sy, 1.0)
        nz = N(nt, 'ShaderNodeTexNoise', loc); nz.inputs['Scale'].default_value = 1.0; nz.inputs['Detail'].default_value = detail
        nz.inputs['Roughness'].default_value = 0.6
        L.new(tc.outputs['UV'], mp.inputs['Vector']); L.new(mp.outputs['Vector'], nz.inputs['Vector'])
        return nz
    a = noise(2.0, grain, 8.0, (-600, 150)); b = noise(0.6, 10.0, 3.0, (-600, -150))
    ma = N(nt, 'ShaderNodeMath', (-380, 150), operation='MULTIPLY'); ma.inputs[1].default_value = 0.6
    mb_ = N(nt, 'ShaderNodeMath', (-380, -150), operation='MULTIPLY'); mb_.inputs[1].default_value = 0.4
    ad = N(nt, 'ShaderNodeMath', (-220, 0), operation='ADD')
    L.new(a.outputs[0], ma.inputs[0]); L.new(b.outputs[0], mb_.inputs[0]); L.new(ma.outputs[0], ad.inputs[0]); L.new(mb_.outputs[0], ad.inputs[1])
    c1 = ramp(nt, [(0.35, dark), (0.65, light)], (-60, 0))
    L.new(ad.outputs[0], c1.inputs[0]); L.new(c1.outputs['Color'], p.inputs['Base Color'])
    bump = N(nt, 'ShaderNodeBump', (-60, -300)); bump.inputs['Strength'].default_value = 0.03
    L.new(a.outputs[0], bump.inputs['Height']); L.new(bump.outputs['Normal'], p.inputs['Normal'])
    m.diffuse_color = lin(light)
    return m


def build_materials():
    principled('M_Wall_Paint', '#E6E1CF', 0.9)      # warm off-white; albedo calibrated against photos 6/19 (linear light)
    principled('M_Ceiling_Paint', '#EFEEEA', 0.92)
    principled('M_Crown_Plaster', '#F0EFEA', 0.8)
    principled('M_Trim_White', '#F1F1EE', 0.35)
    principled('M_Door_Leaf', '#EFEFEC', 0.32)
    principled('M_Metal_Brushed', '#BDBDBD', 0.32, 1.0)
    principled('M_Chrome', '#E4E4E4', 0.06, 1.0)
    principled('M_Window_Alu_White', '#EEEEEA', 0.33)
    m, nt, p = principled('M_Glass', '#FFFFFF', 0.0, **{'Transmission Weight': 1.0, 'IOR': 1.5, 'Thin Wall': True})
    m.diffuse_color = (0.7, 0.8, 0.85, 0.3)
    # Cycles treats glass as opaque for shadow rays, which would block the daylight; let light-carrying rays pass
    lp = N(nt, 'ShaderNodeLightPath', (-400, 300)); mx = N(nt, 'ShaderNodeMath', (-200, 300), operation='MAXIMUM')
    tr = N(nt, 'ShaderNodeBsdfTransparent', (-200, 100)); ms = N(nt, 'ShaderNodeMixShader', (300, 200))
    nt.links.new(lp.outputs['Is Shadow Ray'], mx.inputs[0]); nt.links.new(lp.outputs['Is Diffuse Ray'], mx.inputs[1])
    nt.links.new(mx.outputs[0], ms.inputs['Fac']); nt.links.new(p.outputs['BSDF'], ms.inputs[1]); nt.links.new(tr.outputs[0], ms.inputs[2])
    nt.links.new(ms.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
    principled('M_Wardrobe_White', '#EDEBE6', 0.45)
    wood('M_Wardrobe_Wood', '#5E4128', '#8A6744', 0.4, 160.0)
    principled('M_Wardrobe_Handle', '#9A9C9F', 0.3, 1.0)
    principled('M_Wardrobe_Track', '#8F9194', 0.4, 1.0)
    wood('M_Desk_Wood', '#7A5432', '#AB7F4F', 0.42)
    principled('M_Desk_White', '#ECEAE5', 0.45)
    wood('M_Headboard_Wood', '#7A5432', '#AB7F4F', 0.42)
    wood('M_Shelf_Wood', '#3F2B1E', '#64472F', 0.45)
    principled('M_Steel_Black', '#161616', 0.5)
    principled('M_Plastic_White', '#EDEDEA', 0.4)
    principled('M_Plastic_Black', '#151515', 0.45)
    principled('M_Plastic_LightGray', '#D9DAD7', 0.4)
    principled('M_Rubber_Black', '#202020', 0.85)
    principled('M_Socket', '#CFCFCB', 0.5)
    principled('M_Fan_Grille', '#6E6E6C', 0.5)
    principled('M_Piano_Black', '#111618', 0.35)
    principled('M_Piano_Silver', '#A9A8A2', 0.3, 0.9)
    principled('M_Piano_Top', '#2B2C2A', 0.45, 0.3)
    principled('M_Piano_Rosewood', '#4A261B', 0.35)
    principled('M_Key_White', '#F2EEE4', 0.22)
    principled('M_Key_Black', '#111111', 0.3)
    principled('M_Chair_Blue', '#23507A', 0.85, **{'Sheen Weight': 0.4})
    principled('M_Chair_Black', '#121214', 0.75, **{'Sheen Weight': 0.15})
    principled('M_Leather_Black', '#141413', 0.5)
    principled('M_Mattress', '#E5E2DA', 0.9)
    principled('M_Frame_Black', '#121212', 0.5)

    # floor: large porcelain tiles laid at 45 deg (grout lines located from photo 19), size EST 60 cm
    m, nt, p = principled('M_Floor_Tile', '#A2A198', 0.12); L = nt.links
    tc = N(nt, 'ShaderNodeTexCoord', (-1300, 0)); sp = N(nt, 'ShaderNodeSeparateXYZ', (-1100, 0))
    L.new(tc.outputs['Object'], sp.inputs[0])
    def lincomb(cx, cy, off, loc):  # (cx*x + cy*y)/sqrt2 - off
        a = N(nt, 'ShaderNodeMath', loc, operation='MULTIPLY'); a.inputs[1].default_value = cx / math.sqrt(2)
        b = N(nt, 'ShaderNodeMath', (loc[0], loc[1] - 150), operation='MULTIPLY'); b.inputs[1].default_value = cy / math.sqrt(2)
        s = N(nt, 'ShaderNodeMath', (loc[0] + 180, loc[1]), operation='ADD')
        o = N(nt, 'ShaderNodeMath', (loc[0] + 360, loc[1]), operation='SUBTRACT'); o.inputs[1].default_value = off
        L.new(sp.outputs['X'], a.inputs[0]); L.new(sp.outputs['Y'], b.inputs[0])
        L.new(a.outputs[0], s.inputs[0]); L.new(b.outputs[0], s.inputs[1]); L.new(s.outputs[0], o.inputs[0])
        return o
    A = lincomb(1, 1, 0.2304, (-900, 200)); B = lincomb(1, -1, 0.1676, (-900, -200))
    cx = N(nt, 'ShaderNodeCombineXYZ', (-400, 0)); L.new(B.outputs[0], cx.inputs['X']); L.new(A.outputs[0], cx.inputs['Y'])
    br = N(nt, 'ShaderNodeTexBrick', (-200, 0), offset=0.0, squash=1.0)
    br.inputs['Scale'].default_value = 1.0; br.inputs['Brick Width'].default_value = 0.6; br.inputs['Row Height'].default_value = 0.6
    br.inputs['Mortar Size'].default_value = 0.0025; br.inputs['Mortar Smooth'].default_value = 0.2
    br.inputs['Color1'].default_value = lin('#A2A198'); br.inputs['Color2'].default_value = lin('#9D9C92')
    br.inputs['Mortar'].default_value = lin('#88877E'); br.inputs['Bias'].default_value = 0.0
    L.new(cx.outputs[0], br.inputs['Vector']); L.new(br.outputs['Color'], p.inputs['Base Color'])
    rr = N(nt, 'ShaderNodeMapRange', (0, -250)); rr.inputs['To Min'].default_value = 0.07; rr.inputs['To Max'].default_value = 0.7   # polished porcelain
    L.new(br.outputs['Factor'], rr.inputs['Value']); L.new(rr.outputs['Result'], p.inputs['Roughness'])
    bump = N(nt, 'ShaderNodeBump', (0, -450)); bump.inputs['Strength'].default_value = 0.3; bump.invert = True
    L.new(br.outputs['Factor'], bump.inputs['Height']); L.new(bump.outputs['Normal'], p.inputs['Normal'])

    # rug: grey abstract / concrete-look
    m, nt, p = principled('M_Rug', '#626369', 0.95); L = nt.links
    tc = N(nt, 'ShaderNodeTexCoord', (-900, 0)); n1 = N(nt, 'ShaderNodeTexNoise', (-650, 100))
    n1.inputs['Scale'].default_value = 14.0; n1.inputs['Detail'].default_value = 12.0; n1.inputs['Roughness'].default_value = 0.7
    L.new(tc.outputs['Object'], n1.inputs['Vector'])
    r = ramp(nt, [(0.32, '#313338'), (0.50, '#626369'), (0.66, '#989AA0')], (-400, 100))
    L.new(n1.outputs[0], r.inputs[0]); L.new(r.outputs['Color'], p.inputs['Base Color'])
    bump = N(nt, 'ShaderNodeBump', (-200, -200)); bump.inputs['Strength'].default_value = 0.2
    n2 = N(nt, 'ShaderNodeTexNoise', (-650, -200)); n2.inputs['Scale'].default_value = 400.0
    L.new(tc.outputs['Object'], n2.inputs['Vector']); L.new(n2.outputs[0], bump.inputs['Height']); L.new(bump.outputs['Normal'], p.inputs['Normal'])

    # bedspread: big triangles (grey / mustard / white), approximating the patchwork in photos 7/10
    m, nt, p = principled('M_Bedspread', '#B9BCC1', 0.9, **{'Sheen Weight': 0.3}); L = nt.links
    tc = N(nt, 'ShaderNodeTexCoord', (-1100, 0)); sc = N(nt, 'ShaderNodeVectorMath', (-900, 0), operation='SCALE')
    sc.inputs['Scale'].default_value = 1 / 0.32; L.new(tc.outputs['UV'], sc.inputs[0])
    fl = N(nt, 'ShaderNodeVectorMath', (-700, 100), operation='FLOOR'); fr = N(nt, 'ShaderNodeVectorMath', (-700, -100), operation='FRACTION')
    L.new(sc.outputs['Vector'], fl.inputs[0]); L.new(sc.outputs['Vector'], fr.inputs[0])
    sf = N(nt, 'ShaderNodeSeparateXYZ', (-500, -100)); L.new(fr.outputs['Vector'], sf.inputs[0])
    gt = N(nt, 'ShaderNodeMath', (-300, -100), operation='GREATER_THAN'); L.new(sf.outputs['X'], gt.inputs[0]); L.new(sf.outputs['Y'], gt.inputs[1])
    sfl = N(nt, 'ShaderNodeSeparateXYZ', (-500, 100)); L.new(fl.outputs['Vector'], sfl.inputs[0])
    cmb = N(nt, 'ShaderNodeCombineXYZ', (-150, 0)); L.new(sfl.outputs['X'], cmb.inputs['X']); L.new(sfl.outputs['Y'], cmb.inputs['Y']); L.new(gt.outputs[0], cmb.inputs['Z'])
    wn = N(nt, 'ShaderNodeTexWhiteNoise', (50, 0), noise_dimensions='3D'); L.new(cmb.outputs[0], wn.inputs['Vector'])
    r = ramp(nt, [(0.0, '#ECEAE4'), (0.3, '#BBBEC3'), (0.5, '#8C9099'), (0.7, '#B8893E'), (0.86, '#5D6470')], (250, 0), 'CONSTANT')
    L.new(wn.outputs['Value'], r.inputs[0])
    # printed details on the light triangles, as on your bedspread (photo 7): black dots on some, fine stripes on others
    g = N(nt, 'ShaderNodeSeparateColor', (250, -250)); L.new(wn.outputs['Color'], g.inputs[0])
    vo = N(nt, 'ShaderNodeTexVoronoi', (250, -450)); vo.inputs['Scale'].default_value = 40.0; vo.inputs['Randomness'].default_value = 0.0
    wv = N(nt, 'ShaderNodeTexWave', (250, -650), wave_type='BANDS', bands_direction='DIAGONAL'); wv.inputs['Scale'].default_value = 25.0
    L.new(tc.outputs['UV'], vo.inputs['Vector']); L.new(tc.outputs['UV'], wv.inputs['Vector'])
    def op(kind, a_, b_, loc):
        n = N(nt, 'ShaderNodeMath', loc, operation=kind)
        for i, v in enumerate((a_, b_)):
            if isinstance(v, (int, float)): n.inputs[i].default_value = v
            else: L.new(v, n.inputs[i])
        return n.outputs[0]
    dots = op('LESS_THAN', vo.outputs['Distance'], 0.2, (450, -450)); lines = op('LESS_THAN', wv.outputs['Factor'], 0.15, (450, -650))
    pick_d = op('LESS_THAN', g.outputs['Green'], 0.3, (450, -250))
    pick_s = op('MULTIPLY', op('GREATER_THAN', g.outputs['Green'], 0.3, (450, -150)), op('LESS_THAN', g.outputs['Green'], 0.5, (450, -50)), (600, -150))
    mask = op('ADD', op('MULTIPLY', pick_d, dots, (650, -400)), op('MULTIPLY', pick_s, lines, (650, -600)), (800, -500))
    bw = N(nt, 'ShaderNodeRGBToBW', (450, 100)); L.new(r.outputs['Color'], bw.inputs[0])
    m_ = op('MULTIPLY', mask, op('GREATER_THAN', bw.outputs[0], 0.45, (600, 100)), (950, -300))
    mx = N(nt, 'ShaderNodeMix', (1100, 0), data_type='RGBA'); sock(mx, 'B_Color').default_value = lin('#22262E')
    L.new(m_, sock(mx, 'Factor_Float')); L.new(r.outputs['Color'], sock(mx, 'A_Color'))
    L.new(next(o for o in mx.outputs if o.identifier == 'Result_Color'), p.inputs['Base Color'])

    # pillows
    m, nt, p = principled('M_Pillow_Dots', '#EEEBE4', 0.85); L = nt.links
    tc = N(nt, 'ShaderNodeTexCoord', (-700, 0)); vo = N(nt, 'ShaderNodeTexVoronoi', (-500, 0)); vo.inputs['Scale'].default_value = 90.0
    vo.inputs['Randomness'].default_value = 0.0
    L.new(tc.outputs['Object'], vo.inputs['Vector'])
    r = ramp(nt, [(0.0, '#4A4E57'), (0.17, '#EEEBE4')], (-250, 0), 'CONSTANT')
    L.new(vo.outputs['Distance'], r.inputs[0]); L.new(r.outputs['Color'], p.inputs['Base Color'])
    principled('M_Pillow_Print', '#DADBDD', 0.85)
    # black-and-white zigzag fleece throw (photo 7): stripes 5 cm apart, bent into 8 cm zigzags
    m, nt, p = principled('M_Throw_Zigzag', '#ECEAE5', 0.92, **{'Sheen Weight': 0.6}); L = nt.links
    tc = N(nt, 'ShaderNodeTexCoord', (-1100, 0)); xyz = N(nt, 'ShaderNodeSeparateXYZ', (-900, 0)); L.new(tc.outputs['Object'], xyz.inputs[0])
    chain = [('MULTIPLY', 12.5), ('FRACT', None), ('SUBTRACT', 0.5), ('ABSOLUTE', None), ('MULTIPLY', 0.06)]
    prev = xyz.outputs['X']
    for i, (op, v) in enumerate(chain):
        n = N(nt, 'ShaderNodeMath', (-700 + 130 * i, 150), operation=op)
        if v is not None: n.inputs[1].default_value = v
        L.new(prev, n.inputs[0]); prev = n.outputs[0]
    ad = N(nt, 'ShaderNodeMath', (0, 0), operation='ADD'); L.new(xyz.outputs['Y'], ad.inputs[0]); L.new(prev, ad.inputs[1])
    st = N(nt, 'ShaderNodeMath', (150, 0), operation='MULTIPLY'); st.inputs[1].default_value = 20.0
    fr = N(nt, 'ShaderNodeMath', (300, 0), operation='FRACT'); gt = N(nt, 'ShaderNodeMath', (450, 0), operation='GREATER_THAN')
    gt.inputs[1].default_value = 0.5
    mx = N(nt, 'ShaderNodeMix', (600, 0), data_type='RGBA'); sock(mx, 'A_Color').default_value = lin('#18181A'); sock(mx, 'B_Color').default_value = lin('#ECEAE5')
    for a, b in [(ad.outputs[0], st.inputs[0]), (st.outputs[0], fr.inputs[0]), (fr.outputs[0], gt.inputs[0]), (gt.outputs[0], sock(mx, 'Factor_Float')),
                 (next(o for o in mx.outputs if o.identifier == 'Result_Color'), p.inputs['Base Color'])]:
        L.new(a, b)

    # puzzle picture (rectified crop of your photo 06)
    m, nt, p = principled('M_Puzzle_Picture', '#20283C', 0.85, **{'Specular IOR Level': 0.3}); L = nt.links
    tex = N(nt, 'ShaderNodeTexImage', (-400, 0))
    path = os.path.join(HERE, 'textures', 'puzzle_from_photo06.png')
    if os.path.exists(path):
        tex.image = bpy.data.images.load(path); tex.image.pack()
        g = N(nt, 'ShaderNodeVectorMath', (-150, 0), operation='MULTIPLY'); g.inputs[1].default_value = (1.29, 1.26, 1.25)  # calibrated under real daylight
        L.new(tex.outputs['Color'], g.inputs[0]); L.new(g.outputs['Vector'], p.inputs['Base Color'])

# =============================================================================== realism layer
# Real scanned surfaces (Poly Haven, CC0) on top of the photo-calibrated colours, plus imperfections.
TEX = os.path.join(HERE, 'textures')
_IMG = {}


def tex_img(nt, asset, kind, vec, loc, color=False):
    path = os.path.join(TEX, asset, f'{asset}_{kind}_2k.jpg')
    if path not in _IMG:
        im = bpy.data.images.load(path); im.colorspace_settings.name = 'sRGB' if color else 'Non-Color'
        im.filepath = '//' + os.path.relpath(path, os.path.dirname(OUT)).replace(os.sep, '/')
        _IMG[path] = im
    n = N(nt, 'ShaderNodeTexImage', loc); n.image = _IMG[path]
    nt.links.new(vec, n.inputs['Vector'])
    return n


def uvmap(nt, size_m, rot=0.0, offset=(0.0, 0.0), loc=(-1500, -400)):
    """UVs are in metres, so scale = 1 / the scan's real-world tile size."""
    tc = N(nt, 'ShaderNodeTexCoord', (loc[0] - 200, loc[1])); mp = N(nt, 'ShaderNodeMapping', loc)
    mp.inputs['Scale'].default_value = (1 / size_m, 1 / size_m, 1.0)
    mp.inputs['Rotation'].default_value = (0.0, 0.0, math.radians(rot))
    mp.inputs['Location'].default_value = (offset[0], offset[1], 0.0)
    nt.links.new(tc.outputs['UV'], mp.inputs['Vector'])
    return mp.outputs['Vector']


def scan_normal(nt, p, asset, vec, strength, loc=(-450, -650)):
    t = tex_img(nt, asset, 'nor_gl', vec, (loc[0] - 300, loc[1]))
    nm = N(nt, 'ShaderNodeNormalMap', loc); nm.inputs['Strength'].default_value = strength
    nt.links.new(t.outputs['Color'], nm.inputs['Color'])
    prev = p.inputs['Normal'].links[0].from_node if p.inputs['Normal'].is_linked else None
    if prev is not None and prev.bl_idname == 'ShaderNodeBump' and not prev.inputs['Normal'].is_linked:
        nt.links.new(nm.outputs['Normal'], prev.inputs['Normal'])      # existing bump stacks on top of the scan
    else:
        nt.links.new(nm.outputs['Normal'], p.inputs['Normal'])


def scan_rough(nt, p, asset, vec, lo, hi, src, loc=(-450, -350)):
    t = tex_img(nt, asset, 'rough', vec, (loc[0] - 300, loc[1]))
    mr = N(nt, 'ShaderNodeMapRange', loc)
    mr.inputs['From Min'].default_value, mr.inputs['From Max'].default_value = src
    mr.inputs['To Min'].default_value, mr.inputs['To Max'].default_value = lo, hi
    nt.links.new(t.outputs['Color'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], p.inputs['Roughness'])


def scan_color(nt, p, asset, vec, gain, loc=(-450, 250)):
    """Scanned colour scaled per channel so its average equals the calibrated colour (gain = target / scan mean)."""
    t = tex_img(nt, asset, 'diff', vec, (loc[0] - 300, loc[1]), color=True)
    g = N(nt, 'ShaderNodeVectorMath', loc, operation='MULTIPLY'); g.inputs[1].default_value = gain
    nt.links.new(t.outputs['Color'], g.inputs[0]); nt.links.new(g.outputs['Vector'], p.inputs['Base Color'])


def bump_noise(nt, p, strength, scale, distance=0.001, loc=(-250, -1550)):
    """Fine procedural relief (orange peel on paint, powder coat). Stacks on any existing normal input."""
    tc = N(nt, 'ShaderNodeTexCoord', (loc[0] - 400, loc[1])); nz = N(nt, 'ShaderNodeTexNoise', (loc[0] - 200, loc[1]))
    nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 3.0
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    b = N(nt, 'ShaderNodeBump', loc); b.inputs['Strength'].default_value = strength; b.inputs['Distance'].default_value = distance
    nt.links.new(nz.outputs['Factor'], b.inputs['Height'])
    if p.inputs['Normal'].is_linked: nt.links.new(p.inputs['Normal'].links[0].from_socket, b.inputs['Normal'])
    nt.links.new(b.outputs['Normal'], p.inputs['Normal'])


def imperfect(nt, p, amp=0.06, scale=5.0, loc=(-250, -1250)):
    """Smudges + micro-roughness: no real surface is evenly glossy (the most-cited photorealism tip)."""
    L = nt.links
    tc = N(nt, 'ShaderNodeTexCoord', (loc[0] - 600, loc[1]))
    big = N(nt, 'ShaderNodeTexNoise', (loc[0] - 400, loc[1])); big.inputs['Scale'].default_value = scale
    big.inputs['Detail'].default_value = 8.0; big.inputs['Roughness'].default_value = 0.65
    fine = N(nt, 'ShaderNodeTexNoise', (loc[0] - 400, loc[1] - 250)); fine.inputs['Scale'].default_value = scale * 15
    fine.inputs['Detail'].default_value = 4.0
    L.new(tc.outputs['Object'], big.inputs['Vector']); L.new(tc.outputs['Object'], fine.inputs['Vector'])
    a = N(nt, 'ShaderNodeMapRange', (loc[0] - 200, loc[1]))
    a.inputs['From Min'].default_value, a.inputs['From Max'].default_value = 0.42, 0.72
    a.inputs['To Min'].default_value, a.inputs['To Max'].default_value = -amp * 0.5, amp
    b = N(nt, 'ShaderNodeMapRange', (loc[0] - 200, loc[1] - 250))
    b.inputs['To Min'].default_value, b.inputs['To Max'].default_value = -amp * 0.4, amp * 0.4
    L.new(big.outputs['Factor'], a.inputs['Value']); L.new(fine.outputs['Factor'], b.inputs['Value'])
    s = N(nt, 'ShaderNodeMath', (loc[0], loc[1]), operation='ADD'); L.new(a.outputs['Result'], s.inputs[0]); L.new(b.outputs['Result'], s.inputs[1])
    r = N(nt, 'ShaderNodeMath', (loc[0] + 180, loc[1]), operation='ADD', use_clamp=True)
    rin = p.inputs['Roughness']
    if rin.is_linked: L.new(rin.links[0].from_socket, r.inputs[0])
    else: r.inputs[0].default_value = rin.default_value
    L.new(s.outputs[0], r.inputs[1]); L.new(r.outputs[0], rin)


def scanned_wood(name, asset, size_m, rot, gain, src, rough=(0.35, 0.55), normal=0.4):
    nt = MAT[name].node_tree
    for n in list(nt.nodes):
        if n.bl_idname not in ('ShaderNodeBsdfPrincipled', 'ShaderNodeOutputMaterial'): nt.nodes.remove(n)
    p = nt.nodes['Principled BSDF']; v = uvmap(nt, size_m, rot)
    scan_color(nt, p, asset, v, gain); scan_rough(nt, p, asset, v, *rough, src=src); scan_normal(nt, p, asset, v, normal)
    imperfect(nt, p, 0.04)


def realism_pass():
    if not os.path.isdir(os.path.join(TEX, 'kitchen_wood')):
        print('scanned textures missing - keeping the procedural materials'); return
    M = lambda n: (MAT[n].node_tree, MAT[n].node_tree.nodes['Principled BSDF'])
    # paint: real roller/plaster micro-texture; the colour lives in the PAINT_COLOR node (colour studies change only that)
    for name, col, rough, nstr in [('M_Wall_Paint', '#E6E1CF', (0.78, 0.93), 0.9), ('M_Ceiling_Paint', '#EFEEEA', (0.85, 0.95), 0.5),
                                   ('M_Crown_Plaster', '#F0EFEA', (0.72, 0.88), 0.3)]:
        nt, p = M(name)
        pc = N(nt, 'ShaderNodeRGB', (-500, 400)); pc.name = pc.label = 'PAINT_COLOR'
        pc.outputs[0].default_value = lin(col); nt.links.new(pc.outputs[0], p.inputs['Base Color'])
        v = uvmap(nt, 3.0)
        scan_rough(nt, p, 'beige_wall_001', v, *rough, src=(0.58, 0.86)); scan_normal(nt, p, 'beige_wall_001', v, nstr)
    # woods: real grain; gains = calibrated mean colour / scan mean colour (linear), grain turned along each board
    scanned_wood('M_Desk_Wood', 'kitchen_wood', 0.9, 90, (2.10, 1.60, 0.98), (0.36, 0.82))
    scanned_wood('M_Headboard_Wood', 'kitchen_wood', 0.9, 90, (2.10, 1.60, 0.98), (0.36, 0.82))
    scanned_wood('M_Wardrobe_Wood', 'kitchen_wood', 0.9, 90, (1.10, 0.84, 0.57), (0.36, 0.82))
    scanned_wood('M_Shelf_Wood', 'dark_wood', 2.0, 0, (0.79, 1.73, 2.32), (0.49, 0.76), (0.4, 0.6))
    # fabrics: weave / pile relief only - their calibrated colours and printed patterns stay
    for name, asset, size, nstr, rough in [('M_Bedspread', 'stretch_poplin', 0.29, 0.6, None), ('M_Pillow_Dots', 'stretch_poplin', 0.29, 0.5, None),
                                           ('M_Pillow_Print', 'stretch_poplin', 0.29, 0.5, None), ('M_Chair_Blue', 'rough_linen', 0.27, 0.8, (0.75, 0.95)),
                                           ('M_Chair_Black', 'rough_linen', 0.27, 0.8, (0.7, 0.9)), ('M_Rug', 'dirty_carpet', 0.6, 1.0, None)]:
        nt, p = M(name); v = uvmap(nt, size)
        scan_normal(nt, p, asset, v, nstr)
        if rough: scan_rough(nt, p, asset, v, *rough, src=(0.6, 0.9))
    nt, p = M('M_Leather_Black'); v = uvmap(nt, 1 / 1.477, offset=(0.625, 0.3))     # keeps the scan's stitched seam off the seat
    scan_normal(nt, p, 'fabric_leather_01', v, 0.8); scan_rough(nt, p, 'fabric_leather_01', v, 0.32, 0.62, src=(0.36, 0.99))
    # glossy and painted surfaces: smudges + micro-roughness; orange peel on paint and powder coat
    for name, amp in [('M_Wardrobe_White', 0.05), ('M_Desk_White', 0.05), ('M_Door_Leaf', 0.05), ('M_Trim_White', 0.05),
                      ('M_Window_Alu_White', 0.04), ('M_Piano_Black', 0.06), ('M_Piano_Top', 0.06), ('M_Plastic_White', 0.05),
                      ('M_Plastic_Black', 0.05), ('M_Plastic_LightGray', 0.05), ('M_Metal_Brushed', 0.05), ('M_Chrome', 0.03),
                      ('M_Key_White', 0.04), ('M_Wardrobe_Handle', 0.04), ('M_Steel_Black', 0.08)]:
        imperfect(*M(name), amp)
    for name, s, sc in [('M_Door_Leaf', 0.02, 500.0), ('M_Trim_White', 0.02, 500.0), ('M_Steel_Black', 0.05, 900.0)]:
        bump_noise(*M(name), s, sc)
    # floor: mottling inside each tile on top of the tile-to-tile shade, plus smudges on the polished glaze
    nt, p = M('M_Floor_Tile'); L = nt.links
    br = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeTexBrick')
    tc = N(nt, 'ShaderNodeTexCoord', (-600, 500)); nz = N(nt, 'ShaderNodeTexNoise', (-400, 500))
    nz.inputs['Scale'].default_value = 4.0; nz.inputs['Detail'].default_value = 10.0; nz.inputs['Roughness'].default_value = 0.6
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    mr = N(nt, 'ShaderNodeMapRange', (-200, 500)); mr.inputs['To Min'].default_value, mr.inputs['To Max'].default_value = 0.94, 1.06
    L.new(nz.outputs['Factor'], mr.inputs['Value'])
    mul = N(nt, 'ShaderNodeVectorMath', (0, 300), operation='SCALE')
    L.new(br.outputs['Color'], mul.inputs[0]); L.new(mr.outputs['Result'], mul.inputs['Scale']); L.new(mul.outputs['Vector'], p.inputs['Base Color'])
    imperfect(nt, p, 0.06, 3.0)
    # every tile sits at its own tiny tilt (<0.2 deg), like a real installation: reflections break at the joints
    tv = br.inputs['Vector'].links[0].from_socket                       # the 45-degree tile coordinates (metres)
    dv = N(nt, 'ShaderNodeVectorMath', (-200, -700), operation='DIVIDE'); dv.inputs[1].default_value = (0.6, 0.6, 1.0)
    fl = N(nt, 'ShaderNodeVectorMath', (0, -650), operation='FLOOR'); fr = N(nt, 'ShaderNodeVectorMath', (0, -800), operation='FRACTION')
    wn = N(nt, 'ShaderNodeTexWhiteNoise', (200, -650), noise_dimensions='3D'); rgb = N(nt, 'ShaderNodeSeparateColor', (400, -650))
    loc = N(nt, 'ShaderNodeSeparateXYZ', (200, -850))
    L.new(tv, dv.inputs[0]); L.new(dv.outputs['Vector'], fl.inputs[0]); L.new(dv.outputs['Vector'], fr.inputs[0])
    L.new(fl.outputs['Vector'], wn.inputs['Vector']); L.new(wn.outputs['Color'], rgb.inputs[0]); L.new(fr.outputs['Vector'], loc.inputs[0])
    terms = []
    for ch, ax, y in (('Red', 'X', -650), ('Green', 'Y', -800)):
        sl = N(nt, 'ShaderNodeMath', (600, y), operation='MULTIPLY_ADD'); sl.inputs[1].default_value = 0.007; sl.inputs[2].default_value = -0.0035
        cen = N(nt, 'ShaderNodeMath', (600, y - 75), operation='SUBTRACT'); cen.inputs[1].default_value = 0.5
        mm = N(nt, 'ShaderNodeMath', (800, y), operation='MULTIPLY')
        L.new(rgb.outputs[ch], sl.inputs[0]); L.new(loc.outputs[ax], cen.inputs[0]); L.new(sl.outputs[0], mm.inputs[0]); L.new(cen.outputs[0], mm.inputs[1])
        terms.append(mm)
    h = N(nt, 'ShaderNodeMath', (1000, -700), operation='ADD'); L.new(terms[0].outputs[0], h.inputs[0]); L.new(terms[1].outputs[0], h.inputs[1])
    hm = N(nt, 'ShaderNodeMath', (1150, -700), operation='MULTIPLY'); hm.inputs[1].default_value = 0.6    # tile units -> metres
    L.new(h.outputs[0], hm.inputs[0])
    tb = N(nt, 'ShaderNodeBump', (1300, -700)); tb.inputs['Strength'].default_value = 1.0; tb.inputs['Distance'].default_value = 1.0
    L.new(hm.outputs[0], tb.inputs['Height'])
    if p.inputs['Normal'].is_linked: L.new(p.inputs['Normal'].links[0].from_socket, tb.inputs['Normal'])
    L.new(tb.outputs['Normal'], p.inputs['Normal'])

# =============================================================================== architecture
def build_architecture():
    c = 'ARCH_Architecture'
    # floor slab under everything (origin at world origin so the tile shader aligns)
    MB().box(-WALL_T, RW + WALL_T, -WALL2_T, RD + WALL_T, -2, 0).build(
        'ARCH_Floor', c, ['M_Floor_Tile'], origin=(0, 0, 0), src='DRAWING', note='Tiles 45 deg; tile size 60x60 EST - measure one tile to confirm')
    box('ARCH_Ceiling', c, 'M_Ceiling_Paint', -WALL_T, RW + WALL_T, -WALL2_T, RD + WALL_T, RH, RH + 2, src='DRAWING')
    walls = {
        'ARCH_Wall_1_Door': (-WALL_T, RW + WALL_T, RD, RD + WALL_T),
        'ARCH_Wall_2_Window': (-WALL_T, RW + WALL_T, -WALL2_T, 0),
        'ARCH_Wall_3': (RW, RW + WALL_T, -WALL2_T, RD + WALL_T),
        'ARCH_Wall_4': (-WALL_T, 0, -WALL2_T, RD + WALL_T),
    }
    W = {}
    for name, (x0, x1, y0, y1) in walls.items():
        W[name] = box(name, c, 'M_Wall_Paint', x0, x1, y0, y1, 0, RH, src='DRAWING',
                      note='Inner faces are the measured room; thickness is EST')
    cut = 'ARCH_Cutters'
    def cutter(name, wall, x0, x1, y0, y1, z0, z1):
        k = box(name, cut, 'M_Wall_Paint', x0, x1, y0, y1, z0, z1, src='DRAWING')
        k.display_type = 'WIRE'; k.hide_render = True
        md = W[wall].modifiers.new('Opening', 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.object = k
        md.solver = 'EXACT'
    cutter('CUT_Door_Opening', 'ARCH_Wall_1_Door', DOOR_X0 - 2, DOOR_X0 + DOOR_W + 2, RD - 5, RD + WALL_T + 5, -1, DOOR_H + 2)
    cutter('CUT_Window_Opening', 'ARCH_Wall_2_Window', WIN_X0 + WIN_TRIM, WIN_X1 - WIN_TRIM, -WALL2_T - 5, 5,
           WIN_Z0 + WIN_TRIM, WIN_Z1 - WIN_TRIM)
    COLLS[cut].hide_render = True

    # baseboards (stop at the door trim and at the wardrobe)
    prof = [(0, 0), (BB_T, 0), (BB_T, BB_H - 1.2), (BB_T - 0.5, BB_H), (0, BB_H)]
    mb = MB()
    mb.loft([(DOOR_X0 - TRIM_W, RD, 0), (0, RD, 0), (0, 0, 0), (RW, 0, 0), (RW, RD - WARD_D, 0)], (0, 0, 1), (0, 0, 1), prof)
    mb.loft([(WARD_X0, RD, 0), (DOOR_X0 + DOOR_W + TRIM_W, RD, 0)], (0, 0, 1), (0, 0, 1), prof)
    mb.build('ARCH_Baseboards', c, ['M_Trim_White'], src='PHOTO', note='height 10.4 measured in photo 19')

    # crown molding (stepped + cove), interrupted by the floor-to-ceiling wardrobe
    d, (s1, s2), out = CROWN['drop'], CROWN['steps'], CROWN['out']
    prof = [(0, d), (1.0, d), (1.0, s1), (2.0, s1), (2.0, s2), (3.2, s2), (3.2, 7.0)]
    prof += [(12 + 8.8 * math.cos(t), 7 + 7 * math.sin(t)) for t in [math.pi + i * (math.pi / 2) / 6 for i in range(1, 7)]]
    prof += [(0, 0)]
    MB().loft([(WARD_X0, RD, RH), (0, RD, RH), (0, 0, RH), (RW, 0, RH), (RW, RD - WARD_D, RH)], (0, 0, 1), (0, 0, -1), prof).build(
        'ARCH_Crown_Molding', c, ['M_Crown_Plaster'], src='PHOTO', note='drop 17.5 and step lines measured (photo 16); projection on ceiling EST')

    # electrical plates (4x2" plates, 7.4 x 11.8)
    e = 'ARCH_Electrical'
    def plate(name, wall_axis, wall_pos, sgn, cu, cz, portrait=True, sockets=0, rockers=0, src='PHOTO'):
        w, h = (7.4, 11.8) if portrait else (11.8, 7.4)
        mb = MB()
        def bx(u0, u1, z0, z1, t0, t1, mi):
            if wall_axis == 'x': mb.box(wall_pos + sgn * t0, wall_pos + sgn * t1, u0, u1, z0, z1, mi)
            else: mb.box(u0, u1, wall_pos + sgn * t0, wall_pos + sgn * t1, z0, z1, mi)
        bx(cu - w / 2, cu + w / 2, cz - h / 2, cz + h / 2, 0, 0.8, 0)
        for i in range(rockers):
            zc = cz - 3.2 + i * 3.2; bx(cu - 1.6, cu + 1.6, zc - 1.1, zc + 1.1, 0.8, 1.2, 0)
        for i in range(sockets):
            zc = cz + (0 if sockets == 1 else (2.6 if i == 0 else -2.6))
            p0 = Vector((wall_pos + sgn * 0.8, cu, zc)) if wall_axis == 'x' else Vector((cu, wall_pos + sgn * 0.8, zc))
            p1 = p0 + (Vector((sgn * 0.15, 0, 0)) if wall_axis == 'x' else Vector((0, sgn * 0.15, 0)))
            mb.cyl(p0, p1, 2.0, 20, 1)
        org = (wall_pos, cu, cz) if wall_axis == 'x' else (cu, wall_pos, cz)
        return mb.build(name, e, ['M_Plastic_White', 'M_Socket'], origin=org, src=src)
    plate('ELEC_Light_Switch_W4', 'x', 0, 1, 200.0, 119.0, rockers=3, src='PHOTO')
    plate('ELEC_Outlet_W4_Desk_A', 'x', 0, 1, 82.8, 132.45, sockets=1, src='PHOTO')
    plate('ELEC_Plate_W4_Desk_B_blank', 'x', 0, 1, 103.9, 132.45, src='PHOTO')
    plate('ELEC_Outlet_W4_Low', 'x', 0, 1, 77.0, 38.5, sockets=2, src='PHOTO')
    plate('ELEC_Outlet_W3_Low', 'x', RW, -1, 170.5, 44.0, sockets=2, src='PHOTO')
    box('ARCH_Curtain_Bracket_old', c, 'M_Plastic_White', 264.5, 267.0, 0, 3.5, 246.7, 252.3, src='PHOTO',
        note='small bracket above the window (photo 16), no rod/curtain present')

# =============================================================================== door
def build_door():
    c = 'DOOR_Door'
    x0, x1 = DOOR_X0, DOOR_X0 + DOOR_W
    MB().loft([(x0, RD, 0), (x0, RD, DOOR_H), (x1, RD, DOOR_H), (x1, RD, 0)], (0, -1, 0), (0, -1, 0),
              [(0, 0), (0, 1.6), (TRIM_W - 1.1, 1.6), (TRIM_W, 0.6), (TRIM_W, 0)]).build(
        'DOOR_Trim', c, ['M_Trim_White'], src='PHOTO', note='7.5 cm casing, outer edges 7.5 / 94 from wall 4')
    mb = MB()
    mb.box(x0 - 2, x0, RD, RD + WALL_T, 0, DOOR_H + 2).box(x1, x1 + 2, RD, RD + WALL_T, 0, DOOR_H + 2)
    mb.box(x0 - 2, x1 + 2, RD, RD + WALL_T, DOOR_H, DOOR_H + 2)
    mb.build('DOOR_Jamb', c, ['M_Trim_White'], src='EST')
    hinge = Vector((x0, RD + 0.5, 0))
    pivot = empty('DOOR_Leaf_Pivot', hinge, c, src='DRAWING',
                  note='Rotate Z NEGATIVE to open the door into the room (about -95 deg max). Hinges on the wall-4 side.')
    leaf = box('DOOR_Leaf', c, 'M_Door_Leaf', x0, x1, RD + 0.5, RD + 0.5 + DOOR_T, 0.5, DOOR_H, origin=tuple(hinge),
               parent=pivot, src='DRAWING', note='71.5 x 210 flat painted leaf', bevel=(0.15, 2))
    hw = MB()
    for zc in (190.0, 107.5, 25.0):  # PHOTO top/middle hinge heights (photo 17); bottom one assumed
        hw.cyl((x0, RD + 0.1, zc - 4.45), (x0, RD + 0.1, zc + 4.45), 0.65, 16)
    hw.build('DOOR_Hinges', c, ['M_Metal_Brushed'], origin=tuple(hinge), parent=pivot, src='PHOTO')
    hx, hz, fy = x1 - 6.0, 105.0, RD + 0.5        # PHOTO lever rosette ~6 cm from the latch edge, ~105 high
    h = MB()
    h.cyl((hx, fy, hz), (hx, fy - 0.9, hz), 2.6, 32)                      # rosette
    h.cyl((hx, fy - 0.9, hz), (hx, fy - 5.0, hz), 0.9, 16)                # neck
    h.cyl((hx + 0.6, fy - 5.0, hz), (hx - 11.5, fy - 5.6, hz), 0.85, 16)  # lever, pointing to the hinge side
    h.cyl((hx, fy, hz - 6.4), (hx, fy - 0.7, hz - 6.4), 2.2, 32)          # key escutcheon
    h.box(hx - 0.25, hx + 0.25, fy - 0.8, fy - 0.6, hz - 7.3, hz - 5.6, 1)  # keyhole
    h.build('DOOR_Handle_Lever', c, ['M_Metal_Brushed', 'M_Plastic_Black'], origin=tuple(hinge), parent=pivot, src='PHOTO', smooth=True)
    return leaf

# =============================================================================== window
def build_window():
    c = 'WIN_Window'
    ix0, ix1, iz0, iz1 = WIN_X0 + WIN_TRIM, WIN_X1 - WIN_TRIM, WIN_Z0 + WIN_TRIM, WIN_Z1 - WIN_TRIM
    MB().loft([(ix0, 0, iz0), (ix0, 0, iz1), (ix1, 0, iz1), (ix1, 0, iz0)], (0, -1, 0), (0, 1, 0),
              [(0, 0), (0, WIN_PROUD), (WIN_TRIM, WIN_PROUD), (WIN_TRIM, 0)], closed=True).build(
        'WIN_Trim', c, ['M_Window_Alu_White'], src='DRAWING', note='151.5 x 121.5 outer, 1 cm proud of the wall, 4 cm face (PHOTO)')
    f = MB(); fw = 2.0
    f.box(ix0, ix1, -11, -1.5, iz1 - fw, iz1).box(ix0, ix1, -11, -1.5, iz0, iz0 + fw)
    f.box(ix0, ix0 + fw, -11, -1.5, iz0, iz1).box(ix1 - fw, ix1, -11, -1.5, iz0, iz1)
    f.build('WIN_Frame', c, ['M_Window_Alu_White'], src='PHOTO')
    # left sash (wall-3 side): fixed-blade louvre panel on the front track
    lx0, lx1, lz0, lz1, y0, y1 = 171.5, 239.5, 104.0, 212.5, -5.0, -2.0
    s = MB()
    s.box(lx1 - 6, lx1, y0, y1, lz0, lz1).box(lx0, lx0 + 5, y0, y1, lz0, lz1)
    s.box(lx0 + 5, lx1 - 6, y0, y1, lz1 - 5, lz1).box(lx0 + 5, lx1 - 6, y0, y1, lz0, lz0 + 6)
    nb, za, zb = 16, lz0 + 6, lz1 - 5
    pitch = (zb - za) / nb; ang = math.radians(40)
    for i in range(nb):
        zc = za + pitch * (i + 0.5)
        s.obox(((lx0 + lx1 - 1) / 2, (y0 + y1) / 2, zc), (1, 0, 0), (0, math.cos(ang), math.sin(ang)),
               (0, -math.sin(ang), math.cos(ang)), (lx1 - lx0 - 11) / 2, 4.2, 0.12)
    s.build('WIN_Sash_Louvre', c, ['M_Window_Alu_White'], src='PHOTO', note='16 fixed blades counted in photo 16')
    # right sash (wall-4 side): glazed, back track
    gx0, gx1, gz0, gz1, y0, y1 = 98.5, 175.0, 104.0, 212.5, -9.0, -6.0
    g = MB()
    g.box(gx0, 103.9, y0, y1, gz0, gz1).box(167.4, gx1, y0, y1, gz0, gz1)
    g.box(103.9, 167.4, y0, y1, 208.3, gz1).box(103.9, 167.4, y0, y1, gz0, 108.4)
    g.build('WIN_Sash_Glazed', c, ['M_Window_Alu_White'], src='PHOTO')
    gl = MB(); gl.box(103.9, 167.4, -7.55, -7.45, 108.4, 208.3)
    gl.build('WIN_Glass', c, ['M_Glass'], src='PHOTO')
    l = MB()
    l.box(235.8, 237.2, -2.0, -0.6, 151.0, 166.0).box(100.1, 101.5, -6.0, -4.6, 151.0, 166.0)
    l.build('WIN_Latches', c, ['M_Window_Alu_White'], src='PHOTO', bevel=(0.3, 2))

# =============================================================================== wardrobe
def build_wardrobe():
    c = 'WARD_Wardrobe'
    x0, x1, yf, yb = WARD_X0, RW, RD - WARD_D, RD
    root = empty('WARD_Wardrobe', ((x0 + x1) / 2, (yf + yb) / 2, 0), c, src='DRAWING', note='181 x 63 x 270, sliding doors')
    t = 1.8
    car = MB()
    car.box(x0, x0 + t, yf, yb, 0, RH).box(x1 - t, x1, yf, yb, 0, RH)          # side panels
    car.box(x0 + t, x1 - t, yf, yf + 2, 262, RH)                                # top rail fascia
    car.box(x0 + t, x1 - t, yf + 2, yb, RH - t, RH).box(x0 + t, x1 - t, yb - 0.6, yb, 0, RH)
    car.box(x0 + t, x1 - t, yf + 1, yb, 0, 9.0)                                 # plinth, 1 cm recessed
    car.build('WARD_Carcass', c, ['M_Wardrobe_White'], parent=root, src='DRAWING', bevel=(0.1, 1))
    MB().box(x0 + t, x1 - t, yf + 0.6, yf + 6.6, 9.0, 11.2).build('WARD_Bottom_Track', c, ['M_Wardrobe_Track'], parent=root, src='PHOTO')
    inner = x1 - x0 - 2 * t; overlap = 4.0; dw = (inner + overlap) / 2
    doors = {'WARD_Door_Left_back': (x0 + t, x0 + t + dw, yf + 3.0), 'WARD_Door_Right_front': (x1 - t - dw, x1 - t, yf + 0.5)}
    z0, z1, sh = WARD_DOOR_Z0, WARD_DOOR_Z1, 2.3
    for name, (dx0, dx1, dy) in doors.items():
        d = MB(); edges = [z0]
        for zc in WARD_STRIPS: edges += [zc - sh / 2, zc + sh / 2]
        edges.append(z1)
        for i in range(len(edges) - 1):
            wood = i % 2 == 1
            d.box(dx0, dx1, dy + (0.15 if wood else 0), dy + 1.8, edges[i], edges[i + 1], 1 if wood else 0)
        d.build(name, c, ['M_Wardrobe_White', 'M_Wardrobe_Wood'], origin=((dx0 + dx1) / 2, dy, z0), parent=root,
                src='PHOTO', note='door width from 181 - 2 side panels + 4 cm overlap; strip heights PHOTO', bevel=(0.08, 1))
        hx = dx0 + 7.0 if 'Left' in name else dx1 - 7.0
        hy = dy - 3.0; za, zb = WARD_HANDLE_Z
        hb = MB()
        hb.cyl((hx, hy, za + 1), (hx, hy, zb - 1), 1.75, 24, 0)
        hb.cyl((hx, hy, za), (hx, hy, za + 1), 1.85, 24, 1).cyl((hx, hy, zb - 1), (hx, hy, zb), 1.85, 24, 1)
        for zz in (za + 3, zb - 3): hb.cyl((hx, hy, zz), (hx, dy, zz), 0.5, 12, 0)
        hb.build(name.replace('Door', 'Handle'), c, ['M_Wardrobe_Handle', 'M_Chrome'], origin=(hx, hy, za), parent=root,
                 src='PHOTO', smooth=True)

# =============================================================================== bed
def build_bed():
    c = 'FURN_Bed'
    b = BED; root = empty('BED_Bed', ((b['x0'] + b['x1']) / 2, (b['y0'] + b['y1']) / 2, 0), c, src='USER', note='188 x 94 x 53')
    base = box('BED_Base', c, 'M_Mattress', b['x0'] + 1, b['x1'] - 1, b['y0'] + 1, b['y1'] - 1, 0, 30, parent=root, src='EST')
    mattress = box('BED_Mattress', c, 'M_Mattress', b['x0'], b['x1'], b['y0'], b['y1'], 30, b['h'], parent=root, src='USER', bevel=(3, 3))
    hb2 = box('BED_Headboard_Wall2', c, 'M_Headboard_Wood', 104.5, RW, 0, 1.8, 46.0, 87.5, parent=root, src='PHOTO',
              note='top at 87.5 (photos 16/6); bottom hidden behind the bed (EST)', bevel=(0.15, 1))
    hb3 = box('BED_Headboard_Wall3', c, 'M_Headboard_Wood', RW - 1.8, RW, 1.8, 95.0, 46.0, 87.5, parent=root, src='PHOTO', bevel=(0.15, 1))
    # bedspread: a 2.5 cm cloth sheet dropped on the mattress; gravity drapes it over the open front and foot (real folds)
    sp = grid(MB(), b['x0'] - 50, b['x1'] - 0.8, b['y0'] + 0.8, b['y1'] + 50, b['h'] + 3.0, 2.5).build(
        'BED_Bedspread', c, ['M_Bedspread'], parent=root, src='PHOTO', note='cloth-simulated drape; pattern approximated', uv_xy=True)
    md = cloth(sp, mass=0.12, tension=150.0, bending=4.0, shear=40.0, quality=10, self_collide=True)   # quilt: barely stretches, folds softly
    tucked = [v.index for v in sp.data.vertices                                                # tucked in along the two walls -
              if (v.co.y * 100 < 7 and v.co.x * 100 >= b['x0']) or (v.co.x * 100 > 292 and v.co.y * 100 <= b['y1'])]  # only over the mattress
    sp.vertex_groups.new(name='Tucked').add(tucked, 1.0, 'REPLACE'); md.settings.vertex_group_mass = 'Tucked'
    # pillows: flat sacks inflated by air pressure without gravity - gives real seams, puffiness and corner pinch
    pillows = []
    for name, mat, z0 in [('BED_Pillow_Upright_Dots', 'M_Pillow_Dots', 300.0), ('BED_Pillow_Lying_Print', 'M_Pillow_Print', 400.0)]:
        mb = MB(); bmesh.ops.create_cube(mb.bm, size=1.0)
        bmesh.ops.subdivide_edges(mb.bm, edges=mb.bm.edges[:], cuts=14, use_grid_fill=True)
        for v in mb.bm.verts: v.co = Vector((150 + v.co.x * 64, 150 + v.co.y * 44, z0 + v.co.z * 3))
        pw = mb.build(name, c, [mat], origin=(150, 150, z0), parent=root, src='PHOTO', smooth=True)
        cloth(pw, mass=0.3, tension=15.0, bending=0.5, quality=5, pressure=1.5, gravity=0.0); pillows.append(pw)
    floor, w2, w3 = (bpy.data.objects[n] for n in ('ARCH_Floor', 'ARCH_Wall_2_Window', 'ARCH_Wall_3'))
    simulate([sp] + pillows, [mattress, base, hb2, hb3, floor, w2, w3], 60)
    for md_kind, kw in [('DISPLACE', {}), ('SOLIDIFY', dict(thickness=0.012, offset=1.0)), ('SUBSURF', dict(levels=1, render_levels=2))]:
        md = sp.modifiers.new(md_kind.title(), md_kind)
        for k, v in kw.items(): setattr(md, k, v)
        if md_kind == 'DISPLACE':
            tex = bpy.data.textures.new('Quilt_Wrinkles', 'CLOUDS'); tex.noise_scale = 0.18; tex.noise_depth = 2
            md.texture = tex; md.strength = 0.010; md.mid_level = 0.0; md.direction = 'Z'   # soft quilt undulations, only upward (never into the mattress)
    for p in sp.data.polygons: p.use_smooth = True
    def rest(ob, rot, at, zmin, ymin=None):
        ob.rotation_euler = [math.radians(a) for a in rot]; ob.location = Vector(at) * S; update()
        pts = [ob.matrix_world @ v.co for v in ob.data.vertices]
        ob.location.z += zmin * S - min(p.z for p in pts)
        if ymin is not None: ob.location.y += ymin * S - min(p.y for p in pts)
    for pw in pillows:
        md = pw.modifiers.new('Smooth', 'SUBSURF'); md.levels = md.render_levels = 1
    rest(pillows[0], (78, 0, 3), (268, 12, 70), b['h'] + 1.0, ymin=2.4)      # standing against the window-wall headboard
    rest(pillows[1], (0, 0, 84), (266, 52, 60), b['h'] + 1.2)                  # lying across the bed
    # folded black-and-white zigzag throw at the foot (photo 7)
    th = MB().box(-29, 29, -20, 20, 0, 5.5).build('BED_Throw_Zigzag', c, ['M_Throw_Zigzag'], parent=root, src='PHOTO',
                                                   note='folded fleece throw, photo 7', bevel=(2.2, 3), smooth=True)
    md = th.modifiers.new('Soft', 'SUBSURF'); md.levels = md.render_levels = 2
    tex = bpy.data.textures.new('Throw_Folds', 'CLOUDS'); tex.noise_scale = 0.06
    md = th.modifiers.new('Folds', 'DISPLACE'); md.texture = tex; md.strength = 0.008
    rest(th, (0, 0, -12), (150, 44, 60), b['h'] + 1.4)

# =============================================================================== desk
def build_desk():
    c = 'FURN_Desk'; d, l, h, t = DESK['d'], DESK['l'], DESK['h'], DESK['t']
    root = empty('DESK_Desk', (d / 2, l / 2, 0), c, src='USER', note='170 x 49 x 80, 3 cm boards; along wall 4 from the window corner')
    w = MB()
    w.box(0, d, 0, l, h - t, h)                 # top
    w.box(0, t, 0, l, h, 99.0)                  # back upstand, top at 99 (PHOTO)
    w.box(0, d - 1, 0, t, 0, h - t).box(0, d - 1, l - t, l, 0, h - t)   # end panels
    w.build('DESK_Wood', c, ['M_Desk_Wood'], parent=root, src='USER', note='upstand height and end panels from photos', bevel=(0.1, 1))
    cy0, cy1 = 121.5, l - t                     # PHOTO cabinet under the door-side end
    MB().box(1, d - 5, cy0, cy1, 0, h - t).build('DESK_Cabinet', c, ['M_Desk_White'], parent=root, src='PHOTO')
    box('DESK_Cabinet_Door', c, 'M_Desk_White', d - 5, d - 3.2, cy0 + 0.3, cy1 - 0.3, 1.0, h - t - 1.5, parent=root,
        src='PHOTO', bevel=(0.1, 1))
    rp = MB(); rx = d - 3.2
    rp.box(rx, rx + 0.3, 126.2, 128.8, 64.5, 67.1)
    rp.torus((rx + 0.55, 127.5, 64.6), (1, 0, 0), 1.35, 0.22, 24, 8)
    rp.build('DESK_Ring_Pull', c, ['M_Metal_Brushed'], parent=root, src='PHOTO', smooth=True)

# =============================================================================== wall shelves (above desk)
def build_shelves():
    c = 'FURN_Shelves'
    root = empty('SHELF_Wall_Shelves', (12.5, 87.5, 140), c, src='PHOTO', note='3 boards on 4 black steel frames (photos 8/14/15)')
    dep = 25.0
    boards = [(4.0, 131.0, 142.0), (4.0, 171.0, 164.5), (4.0, 171.0, 187.5)]   # (y0, y1, z bottom) PHOTO
    b = MB()
    for y0, y1, zb in boards: b.box(0, dep, y0, y1, zb, zb + 2.5)
    b.build('SHELF_Boards', c, ['M_Shelf_Wood'], parent=root, src='PHOTO', note='depth 25 EST', bevel=(0.1, 1))
    f = MB(); tt = 2.0
    for yc, z0, z1 in [(15.0, 140.0, 187.5), (68.0, 140.0, 211.0), (116.0, 140.0, 187.5), (161.0, 140.0, 215.0)]:
        ya, yb = yc - tt / 2, yc + tt / 2
        f.box(0, tt, ya, yb, z0, z1).box(dep - tt, dep, ya, yb, z0, z1)
        for zr in sorted({z0, z1 - tt} | {zb - tt for (_, _, zb) in boards if z0 < zb <= z1}):
            f.box(tt, dep - tt, ya, yb, zr, zr + tt)
    f.build('SHELF_Steel_Frames', c, ['M_Steel_Black'], parent=root, src='PHOTO')

# =============================================================================== piano (Korg SP-250 on X-stand)
def build_piano():
    c = 'FURN_Piano'; P = PIANO
    yl, yr = P['yl'], P['yl'] - P['w']; xf, xb = P['xf'], P['xf'] + P['d']; z0 = P['z0']; zt = z0 + P['h']
    root = empty('PIANO_Korg_SP250', ((xf + xb) / 2, (yl + yr) / 2, 0), c, src='SPEC',
                 note='Korg SP-250: 129.5 x 38 x 14 cm (korg.com); position from photos 6/19')
    cap = 3.65; kl, kr = yl - cap, yr + cap; zk = z0 + 9.5; za = 69.5   # za: top of the stand arms
    body = MB()
    body.box(xf + 0.5, xb, kr, kl, z0, zk - 2.2, 0)                  # key bed / base
    body.box(xf + 14.5, xb, kr, kl, zk - 2.2, zt - 0.2, 0)           # rear housing
    body.box(xf - 0.4, xb, kl, yl, z0, zk + 3.0, 0).box(xf - 0.4, xb, yr, kr, z0, zk + 3.0, 0)   # end blocks
    body.box(xf + 14.5, xb, kr, kl, zt - 0.2, zt, 3)                  # dark metallic top
    for ya, yb, mi in [(187.0, kl, 2), (134.0, 187.0, 1), (kr, 134.0, 2)]:
        body.box(xf + 13.5, xf + 14.5, ya, yb, zk + 1.1, zt, mi)      # fascia behind the keys
    body.build('PIANO_Body', c, ['M_Piano_Black', 'M_Piano_Silver', 'M_Piano_Rosewood', 'M_Piano_Top'], parent=root, src='SPEC', bevel=(0.4, 2))
    wk, bk = MB(), MB(); pitch = (kl - kr) / 52
    names = 'ABCDEFG'
    for i in range(52):
        ya = kl - pitch * (i + 1) + 0.05; yb = kl - pitch * i - 0.05
        wk.box(xf, xf + 14.5, ya, yb, zk - 2.0, zk)
        if i < 51 and names[i % 7] in 'ACDFG':
            yc = kl - pitch * (i + 1)
            bk.box(xf + 5.0, xf + 14.5, yc - 0.6, yc + 0.6, zk, zk + 1.1)
    wk.build('PIANO_Keys_White', c, ['M_Key_White'], parent=root, src='SPEC', note='52 white keys')
    bk.build('PIANO_Keys_Black', c, ['M_Key_Black'], parent=root, src='SPEC', note='36 black keys')
    t = math.radians(12)
    MB().obox((xb - 6.0, 162.0, zt + 7.5), (math.cos(t), 0, -math.sin(t)), (0, 1, 0), (math.sin(t), 0, math.cos(t)), 0.3, 25.0, 8.0).build(
        'PIANO_Music_Rest', c, ['M_Plastic_LightGray'], parent=root, src='PHOTO', bevel=(0.2, 2))
    st = MB(); tw = 2.5
    for ya in (125.0, 195.0):           # PHOTO arm positions (photo 6)
        st.box(xf - 2, xb - 0.5, ya - tw / 2, ya + tw / 2, za - 2.5, za, 0)          # top arms
        st.box(xf + 4, xb - 4, ya - 1.0, ya + 1.0, za, z0, 1)                       # rubber pads / feet of the piano
        st.box(xf - 4, xb - 0.5, ya - tw / 2, ya + tw / 2, 0.8, 3.3, 0)             # feet
        for xx in (xf - 2, xb - 0.5): st.cyl((xx, ya, za - 1.25), (xx + (-1.5 if xx < xf else 1.0), ya, za - 1.25), 1.6, 12, 1)
        for xx in (xf - 4, xb - 0.5): st.cyl((xx, ya, 2.05), (xx + (-1.5 if xx < xf else 1.0), ya, 2.05), 1.6, 12, 1)
    for xx in (xf + 13.0, xf + 21.0):   # double-braced X legs
        st.beam((xx, 125.0, za - 1.25), (xx, 195.0, 2.05), 2.5, 2.5, 0, up=(1, 0, 0))
        st.beam((xx, 195.0, za - 1.25), (xx, 125.0, 2.05), 2.5, 2.5, 0, up=(1, 0, 0))
    st.cyl((xf + 8.0, 160.0, (za - 1.25 + 2.05) / 2), (xf + 11.8, 160.0, (za - 1.25 + 2.05) / 2), 1.8, 16, 1)
    st.build('PIANO_X_Stand', c, ['M_Steel_Black', 'M_Rubber_Black'], parent=root, src='PHOTO',
             note='double-braced X stand; arm spacing from photo 6, geometry EST')
    MB().box(xb - 30, xb - 10, 158.0, 166.0, 0.8, 5.5).build('PIANO_Sustain_Pedal', c, ['M_Plastic_Black'], parent=root,
                                                            src='PHOTO', bevel=(0.8, 2))

# =============================================================================== small furniture & decor
def build_chair():
    c = 'FURN_Chair'
    root = empty('CHAIR_Gaming_MyMax_MX6', (78.0, 48.0, 0), c, rz=-15, src='SPEC',
                 note='MyMax MX6: seat 48, backrest 85, base 70 (spec); placed as in photos 7/15/16, facing into the room')
    def part(name, mats, mb, soft=False, **kw):
        ob = mb.build(name, c, mats, **kw); ob.parent = root; ob.matrix_parent_inverse = Matrix()
        if soft:
            md = ob.modifiers.new('Soften', 'SUBSURF'); md.levels = md.render_levels = 2
            for p in ob.data.polygons: p.use_smooth = True
        return ob
    base = MB(); base.cyl((0, 0, 6), (0, 0, 12), 5.0, 24)
    for k in range(5):
        a = math.radians(90 + 72 * k); d = Vector((math.cos(a), math.sin(a), 0))
        base.beam(d * 4 + Vector((0, 0, 9)), d * 33 + Vector((0, 0, 6.5)), 4.0, 3.5)
        base.cyl(d * 33 + Vector((-2.5 * d.y, 2.5 * d.x, 2.9)), d * 33 + Vector((2.5 * d.y, -2.5 * d.x, 2.9)), 2.9, 16)
    base.cyl((0, 0, 12), (0, 0, 28), 2.6, 20).cyl((0, 0, 28), (0, 0, 40), 2.1, 20)
    part('CHAIR_Base', ['M_Chair_Black'], base, src='SPEC', bevel=(0.5, 2))
    seat = MB()                                                         # bucket seat: blue cushion between raised black bolsters
    seat.box(-27, 27, -25, 27, 40, 44, 1).box(-19, 19, -22, 24, 44, 51, 0).box(-19, 19, 23, 27, 43, 51.5, 1)
    for sx in (-1, 1):
        seat.box(sx * 19, sx * 27, -24, 26, 43, 55.5, 1)
        seat.box(sx * 25.5, sx * 29.5, -8, 2, 44, 64, 1).box(sx * 24.5, sx * 30.5, -14, 12, 64, 67, 1)   # armrests
    part('CHAIR_Seat_Arms', ['M_Chair_Blue', 'M_Chair_Black'], seat, soft=True, src='SPEC', bevel=(1.5, 2))
    # racing backrest, lofted through height profiles: (height, half width, half cushion width, wing depth)
    t = math.radians(12); up = Vector((0, -math.sin(t), math.cos(t))); fw = Vector((0, math.cos(t), math.sin(t))); ax = Vector((1, 0, 0))
    o = Vector((0, -22, 50))
    P = lambda x, d, h: o + ax * x + fw * d + up * h
    rows = [(0, 22, 14, 4), (10, 21, 13.5, 6), (24, 22, 14, 8), (38, 25.5, 15, 10), (52, 26.5, 15.5, 9.5),
            (63, 23.5, 14, 6), (70, 16, 12, 2.5), (80, 15, 11.5, 2), (86, 13.5, 10.5, 1)]
    xs = lambda W, C: [-W, -W + 3.5, -C - 1.5, -C, -C / 2, 0, C / 2, C, C + 1.5, W - 3.5, W]
    ds = lambda d: [d * 0.55, d, 0.6, 1.0, 2.4, 2.0, 2.4, 1.0, 0.6, d, d * 0.55]
    bk = MB(); bm = bk.bm; thick = 8.0
    Fr = [[bm.verts.new(P(x, d, h)) for x, d in zip(xs(W, C), ds(wd))] for h, W, C, wd in rows]
    Bk = [[bm.verts.new(P(x, -thick, h)) for x in xs(W, C)] for h, W, C, wd in rows]
    nc = len(Fr[0])
    for r in range(len(rows) - 1):
        for i in range(nc - 1):
            bm.faces.new((Fr[r][i], Fr[r][i + 1], Fr[r + 1][i + 1], Fr[r + 1][i])).material_index = 0 if 3 <= i < 7 else 1
            bm.faces.new((Bk[r][i], Bk[r + 1][i], Bk[r + 1][i + 1], Bk[r][i + 1])).material_index = 1
        for i, flip in ((0, False), (nc - 1, True)):
            q = (Fr[r][i], Fr[r + 1][i], Bk[r + 1][i], Bk[r][i])
            bm.faces.new(q[::-1] if flip else q).material_index = 1
    for r, flip in ((0, False), (len(rows) - 1, True)):
        for i in range(nc - 1):
            q = (Fr[r][i], Bk[r][i], Bk[r][i + 1], Fr[r][i + 1])
            bm.faces.new(q[::-1] if flip else q).material_index = 1
    for sx in (-1, 1):                                                  # the two harness slots of the MX6 headrest
        bk.obox(P(sx * 9.0, 1.9, 76.5), ax, fw, up, 2.4, 0.6, 3.6, 1)
    part('CHAIR_Backrest', ['M_Chair_Blue', 'M_Chair_Black'], bk, soft=True, src='SPEC', note='racing-seat shape after photo 7')


def build_stool():
    c = 'FURN_Stool'
    root = empty('STOOL_Bar_Stool', (228.0, 166.0, 0), c, src='PHOTO', note='position from photos 6/19; sizes EST')
    s = MB()
    s.cyl((0, 0, 0.8), (0, 0, 2.0), 20.0, 48, 0).cyl((0, 0, 2.0), (0, 0, 4.0), 12.0, 48, 0, r1=4.0)
    s.cyl((0, 0, 4.0), (0, 0, 55.0), 2.5, 24, 0)
    s.torus((0, 0, 27.0), (0, 0, 1), 17.0, 1.0, 48, 10, 0)
    for k in range(3):
        a = math.radians(120 * k); s.cyl((2.5 * math.cos(a), 2.5 * math.sin(a), 27), (16.2 * math.cos(a), 16.2 * math.sin(a), 27), 0.7, 10, 0)
    s.cyl((0, 0, 54.0), (0, 0, 56.5), 9.0, 32, 0)                     # seat plate
    ob = s.build('STOOL_Body', c, ['M_Chrome', 'M_Leather_Black'], src='EST', smooth=True)
    ob.parent = root; ob.matrix_parent_inverse = Matrix()
    def top(x, y):                                                      # saddle: rear lip, slight side rise, rolled front
        return 60.0 + 4.2 * max(0.0, (-y - 6.0) / 12.0) ** 1.6 + 1.2 * (x / 21.0) ** 2 - 0.9 * max(0.0, (y - 11.0) / 7.0) ** 2
    seat = heightfield(MB(), [-21 + 3 * i for i in range(15)], [-18 + 3 * j for j in range(13)], top, 56.0, 0)
    so = seat.build('STOOL_Seat', c, ['M_Leather_Black'], src='EST', note='saddle seat after photos 6/19', bevel=(0.8, 2), smooth=True)
    md = so.modifiers.new('Soft', 'SUBSURF'); md.levels = md.render_levels = 2
    so.parent = root; so.matrix_parent_inverse = Matrix()


def build_decor():
    c = 'DECOR_Loose'
    box('DECOR_Rug', c, 'M_Rug', 98.5, 298.5, 75.0, 225.0, 0, 0.8, src='EST',
        note='assumed 150 x 200; long edge along the wardrobe front (photo 19)', bevel=(0.4, 2))
    pz = MB(); pz.box(RW - 2.5, RW, 80.0, 155.0, 121.3, 172.7, 0)
    pz.build('DECOR_Puzzle_Frame', c, ['M_Puzzle_Picture'], src='PHOTO', note='75 x 51.4 frame on wall 3 (photo 6 calibration)',
             uv01=dict(normal=(-1, 0, 0), u=1, v=2, urange=(155.0, 80.0), vrange=(121.3, 172.7)))
    e = empty('DECOR_Purifier_White', (245.6, 212.1, 0), c, rz=-70.0, src='PHOTO', note='~22x19x38; placement from photos 11/19')
    p = MB(); p.box(-11, 11, -9.5, 9.5, 0.8, 36.0, 0).box(-11, 11, -9.5, 9.5, 36.0, 38.5, 1)
    ob = p.build('DECOR_Purifier_White_Body', c, ['M_Plastic_White', 'M_Plastic_Black'], src='EST', bevel=(1.2, 2))
    ob.parent = e; ob.matrix_parent_inverse = Matrix()
    g = MB(); g.cyl((0, -9.5, 18.0), (0, -9.9, 18.0), 7.0, 40, 0).torus((0, -9.9, 18.0), (0, 1, 0), 4.2, 0.35, 32, 6, 1)
    ob = g.build('DECOR_Purifier_White_Fan', c, ['M_Fan_Grille', 'M_Plastic_White'], src='PHOTO', smooth=True)
    ob.parent = e; ob.matrix_parent_inverse = Matrix()
    q = MB(); q.cyl((288.0, 117.0, 0.8), (288.0, 117.0, 40.0), 10.0, 40, 0).cyl((288.0, 117.0, 40.0), (288.0, 117.0, 40.3), 8.5, 40, 1)
    q.build('DECOR_Purifier_Black_Cylinder', c, ['M_Plastic_Black', 'M_Socket'], src='PHOTO', smooth=True, note='~20 dia x 40 (photo 6)')

# =============================================================================== lived-in props (stand-ins)
def sock(n, ident):
    return next(s for s in n.inputs if s.identifier == ident)


def build_props():
    """Stand-ins for what makes your photos look lived-in: books and objects on the shelves, laptop, lamp, notes.
    Placed loosely after photos 8/14/15/16 (EST). Hide the PROPS_Lived_In collection for the empty room."""
    import random
    c = 'PROPS_Lived_In'; rng = random.Random(7)
    books = ['#7A1F1F', '#1F3A5F', '#2B2B2B', '#E8E3D6', '#C9A227', '#3D5A40', '#8C3B2A', '#4B3F72', '#D96C2C', '#1E6B6B', '#B5B0A1', '#F2F0EA']
    for i, h in enumerate(books): principled(f'M_Book_{i:02d}', h, rng.uniform(0.45, 0.7))
    principled('M_Book_Band_Gold', '#B8933F', 0.35, 0.7); principled('M_Book_Band_Cream', '#E9E4D8', 0.6); principled('M_Book_Band_Black', '#151515', 0.5)
    bm = [f'M_Book_{i:02d}' for i in range(len(books))] + ['M_Book_Band_Gold', 'M_Book_Band_Cream', 'M_Book_Band_Black']
    principled('M_Paper', '#F3F0E8', 0.85); principled('M_Laptop_Alu', '#B7B9BC', 0.3, 1.0); principled('M_Laptop_Keys', '#1C1D20', 0.6)
    principled('M_Slipper_Navy', '#22305A', 0.65)
    principled('M_Laptop_Screen', '#030405', 0.04)      # asleep: black glass that reflects the room
    principled('M_Bottle_Purple', '#3B2A55', 0.25); principled('M_Bottle_Green', '#1E4D33', 0.25); principled('M_Toy_Red', '#A3201B', 0.35)
    # handwritten notes: wobbly ink lines (wave bands ~8 mm apart) in random patches, on cream paper
    m, nt, p = principled('M_Paper_Notes', '#F1EDE2', 0.85); L = nt.links
    tc = N(nt, 'ShaderNodeTexCoord', (-900, 0))
    wv = N(nt, 'ShaderNodeTexWave', (-700, 150), wave_type='BANDS', bands_direction='Z')
    wv.inputs['Scale'].default_value = 39.0; wv.inputs['Distortion'].default_value = 1.5; wv.inputs['Detail'].default_value = 2.0
    ink = ramp(nt, [(0.0, '#3E4552'), (0.04, '#F1EDE2')], (-450, 150))
    nz = N(nt, 'ShaderNodeTexNoise', (-700, -150)); nz.inputs['Scale'].default_value = 25.0
    mk = N(nt, 'ShaderNodeMapRange', (-450, -150)); mk.inputs['From Min'].default_value, mk.inputs['From Max'].default_value = 0.47, 0.53
    mx = N(nt, 'ShaderNodeMix', (-200, 0), data_type='RGBA'); sock(mx, 'A_Color').default_value = lin('#F1EDE2')
    for a, b in [(tc.outputs['Object'], wv.inputs['Vector']), (wv.outputs['Factor'], ink.inputs[0]), (tc.outputs['Object'], nz.inputs['Vector']),
                 (nz.outputs['Factor'], mk.inputs['Value']), (mk.outputs['Result'], sock(mx, 'Factor_Float')),
                 (ink.outputs['Color'], sock(mx, 'B_Color')), (next(o for o in mx.outputs if o.identifier == 'Result_Color'), p.inputs['Base Color'])]:
        L.new(a, b)

    frames = (15.0, 68.0, 116.0, 161.0)                    # steel uprights - books stay clear of them
    def row(mb, y0, y1, z, hmax):
        y = y0
        while True:
            t = rng.uniform(1.3, 3.8)
            if any(abs(y + t / 2 - f) < 2.5 + t / 2 for f in frames): y += 1.0; continue
            if y + t > y1: break
            d = rng.uniform(13.0, 17.0)
            hh = rng.uniform(hmax - 5.0, hmax); mb.box(2.5, 2.5 + d, y, y + t, z, z + hh, rng.randrange(12))
            if rng.random() < 0.6:                                  # printed title band on the spine
                b0 = rng.uniform(0.62, 0.8); mb.box(2.5 + d, 2.53 + d, y + 0.15, y + t - 0.15, z + hh * b0, z + hh * (b0 + rng.uniform(0.05, 0.12)), 12 + rng.randrange(3))
            y += t + rng.uniform(0.0, 0.25)
    def stack(mb, y0, z, n):
        for _ in range(n):
            t = rng.uniform(1.5, 3.5); mb.box(3.0, 3.0 + rng.uniform(13, 16), y0, y0 + rng.uniform(19, 23), z, z + t, rng.randrange(12)); z += t
    mb = MB()
    row(mb, 22, 62, 144.5, 19.0); stack(mb, 72, 144.5, 3); row(mb, 104, 128, 144.5, 19.0)     # bottom shelf (top at 144.5)
    row(mb, 34, 41, 167.0, 19.5); stack(mb, 42, 167.0, 5); row(mb, 92, 150, 167.0, 19.5)       # middle shelf
    row(mb, 120, 150, 190.0, 23.0)                                                              # top shelf
    mb.build('PROP_Books', c, bm, src='EST', note='stand-in books; density and colours after photos 8/14/15', bevel=(0.15, 1))
    o = MB()
    o.cyl((9, 8, 144.5), (9, 8, 155.5), 3.4, 24, 0)                                             # pen tin + pens
    for i in range(6):
        a = i * 1.05; o.cyl((9 + 1.6 * math.cos(a), 8 + 1.6 * math.sin(a), 150), (9 + 2.6 * math.cos(a), 8 + 2.6 * math.sin(a), 163), 0.45, 8, 1 + i % 3)
    for (y, r, h, mi) in [(8.5, 2.8, 19.0, 4), (22.0, 3.0, 17.5, 5), (29.0, 2.4, 16.0, 6)]:      # bottles, middle shelf
        o.cyl((10, y, 167.0), (10, y, 167.0 + h - 3.0), r, 24, mi).cyl((10, y, 167.0 + h - 3.0), (10, y, 167.0 + h), r * 0.4, 16, mi)
    o.box(5, 13, 98, 103, 144.5, 147.5, 7)                                                     # toy car
    o.box(3, 21, 152, 168, 167.0, 181.0, 3).box(3, 21, 75, 108, 190.0, 202.0, 3)              # black boxes / case
    o.box(4, 20, 25, 50, 190.0, 197.0, 8).cyl((12, 31, 197), (12, 31, 205), 3.5, 24, 8).cyl((12, 43, 197), (12, 43, 202), 4.5, 24, 8)  # wooden kit model
    o.build('PROP_Shelf_Objects', c, ['M_Metal_Brushed', 'M_Book_00', 'M_Book_01', 'M_Plastic_Black', 'M_Bottle_Purple', 'M_Bottle_Green',
                                      'M_Plastic_White', 'M_Toy_Red', 'M_Desk_Wood'], src='EST', smooth=True)
    # desk: laptop (open ~107 deg, screen facing you), mouse, white cylinder, papers, clamp lamp
    lp = MB(); lp.box(13, 34.5, 34, 64.4, 80, 81.5, 0)
    lp.box(14.6, 24.6, 35.6, 62.8, 81.5, 81.56, 2).box(26.0, 32.6, 43.6, 54.8, 81.5, 81.53, 0)   # keyboard well, trackpad
    t = math.radians(17); up, nrm = Vector((-math.sin(t), 0, math.cos(t))), Vector((math.cos(t), 0, math.sin(t)))
    hinge = Vector((13.3, 49.2, 81.5))
    lp.obox(hinge + up * 9.75 - nrm * 0.3, (0, 1, 0), up, nrm, 15.2, 9.75, 0.25, 0)
    lp.obox(hinge + up * 10.2 + nrm * 0.0, (0, 1, 0), up, nrm, 14.2, 9.0, 0.04, 1)
    lp.build('PROP_Laptop', c, ['M_Laptop_Alu', 'M_Laptop_Screen', 'M_Laptop_Keys'], src='EST', note='laptop as in photo 8', bevel=(0.3, 2))
    # your blue slides by the wardrobe (photo 19)
    for k, (x, y, rz) in enumerate([(131.0, 206.0, -28.0), (146.0, 213.0, -12.0)]):
        sl = heightfield(MB(), [-13 + 2 * i for i in range(14)], [-5 + 2 * j for j in range(6)], lambda u, v: 1.6 - 0.4 * (u / 13.0) ** 2, 0.2, 0)
        sl.box(-1.0, 7.0, -4.8, 4.8, 1.5, 3.4, 0)                                   # strap over the toes
        so = sl.build(f'PROP_Slipper_{k + 1}', c, ['M_Slipper_Navy'], src='PHOTO', note='slides, photo 19', bevel=(0.6, 2), smooth=True)
        md = so.modifiers.new('Soft', 'SUBSURF'); md.levels = md.render_levels = 2
        so.location = Vector((x, y, 0)) * S; so.rotation_euler = (0, 0, math.radians(rz))
    # cables: piano and air purifier to the low socket on the piano wall
    for name, pts in [('PROP_Cable_Piano', [(296.5, 150, 73), (298.4, 156, 64), (299.1, 163, 52), (299.4, 169, 46), (299.6, 170.5, 44.5)]),
                      ('PROP_Cable_Purifier', [(279, 117, 3), (286, 130, 0.5), (296.5, 150, 0.5), (299.3, 166, 1.5), (299.4, 169.5, 25), (299.6, 170.5, 40.5)])]:
        cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0028; cu.bevel_resolution = 3; cu.use_fill_caps = True
        spl = cu.splines.new('NURBS'); spl.points.add(len(pts) - 1); spl.order_u = 3; spl.use_endpoint_u = True
        for pt, q in zip(spl.points, pts): pt.co = (q[0] * S, q[1] * S, q[2] * S, 1.0)
        cu.materials.append(MAT['M_Rubber_Black']); ob = bpy.data.objects.new(name, cu); COLLS[c].objects.link(ob); tag(ob, 'EST', 'cable')
    d = MB(); d.box(22, 33, 70, 76, 80, 83.5, 0)
    d.cyl((10, 118, 80), (10, 118, 98), 4.5, 32, 1)
    for i, (cx, cy, rz) in enumerate([(31.0, 107.0, 6.0), (34.0, 112.0, -4.0)]):
        a = math.radians(rz); d.obox((cx, cy, 80.03 + 0.02 * i), (math.cos(a), math.sin(a), 0), (-math.sin(a), math.cos(a), 0), (0, 0, 1), 10.5, 14.85, 0.01, 2)
    d.build('PROP_Desk_Items', c, ['M_Plastic_Black', 'M_Plastic_White', 'M_Paper'], src='EST', bevel=(0.4, 2))
    lamp = MB()
    lamp.box(0.5, 5.0, 9.5, 14.5, 95.0, 101.0, 0).cyl((2.8, 12, 101), (2.8, 12, 128), 0.8, 12, 0)
    lamp.cyl((2.8, 12, 128), (20, 26, 124), 0.7, 12, 0).cyl((20, 26, 124), (25.5, 31, 114.5), 1.6, 24, 0, r1=6.0)
    lamp.build('PROP_Desk_Lamp', c, ['M_Steel_Black'], src='EST', note='black clamp lamp, photo 8', smooth=True)
    # footrest under the desk (black frame, wooden slats)
    f = MB(); f.box(12, 42, 66, 68, 0, 12, 0).box(12, 42, 98, 100, 0, 12, 0)
    for i in range(7): f.box(14, 40, 69 + i * 4.1, 71.5 + i * 4.1, 10.5, 12.0, 1)
    f.build('PROP_Footrest', c, ['M_Steel_Black', 'M_Desk_Wood'], src='EST', note='footrest, photo 8', bevel=(0.2, 1))
    # notes on wall 4 above the desk (kept off the two plates) and handwritten sheets on wall 2 by the window
    n = MB(); plates = [(78.0, 87.5, 125.5, 139.5), (99.0, 108.6, 125.5, 139.5)]; k = 0
    for _ in range(80):
        w, h = rng.choice([(7.6, 7.6), (10.5, 14.8), (14.8, 21.0), (10.5, 14.8), (7.6, 7.6)])
        y, z = rng.uniform(4 + w / 2, 112 - w / 2), rng.uniform(101 + h / 2, 141 - h / 2)
        if any(y + w / 2 > a - 1 and y - w / 2 < b + 1 and z + h / 2 > c0 - 1 and z - h / 2 < d0 + 1 for a, b, c0, d0 in plates): continue
        r = math.radians(rng.uniform(-4, 4))
        n.obox((0.06 + 0.004 * k, y, z), (0, math.cos(r), math.sin(r)), (0, -math.sin(r), math.cos(r)), (1, 0, 0), w / 2, h / 2, 0.02, 0)
        k += 1
        if k == 18: break
    n.box(40, 61, 0.05, 0.09, 136, 165.7, 0).box(64, 85, 0.05, 0.09, 133, 162.7, 0)
    n.build('PROP_Wall_Notes', c, ['M_Paper_Notes'], src='EST', note='notes collage, photo 8; sheets by the window, photo 16')


# =============================================================================== lights, world, cameras
CAMS = {   # solved from your photos (pinhole, f in px, rvec = world->camera Rodrigues, C = camera centre in cm)
    6: dict(size=(2000, 1500), f=1502.0, rvec=(1.32846, -1.44024, 1.12975), C=(118.6, 168.2, 140.3)),
    8: dict(size=(2000, 1500), f=1502.0, rvec=(1.44109, 1.68051, -1.12731), C=(178.3, 133.0, 148.5)),
    14: dict(size=(2000, 1500), f=1502.0, rvec=(1.36688, 0.83946, -0.83153), C=(156.1, 116.8, 154.8)),
    15: dict(size=(2000, 1500), f=1502.0, rvec=(0.75417, 1.64807, -1.70977), C=(178.0, 136.2, 157.8)),
    16: dict(size=(2000, 1500), f=1502.0, rvec=(-0.10511, 2.22784, -2.31184), C=(141.8, 192.5, 158.4)),
    17: dict(size=(1500, 2000), f=1502.0, rvec=(1.63254, 0.07879, -0.02927), C=(64.1, 141.0, 150.3)),
    18: dict(size=(1500, 2000), f=1450.4, rvec=(1.59446, 0.00640, -0.00157), C=(127.5, 128.7, 145.7)),
    19: dict(size=(2000, 1500), f=1501.0, rvec=(1.75146, -0.66219, 0.51840), C=(53.3, 89.9, 135.8)),
}


DAYLIGHT = 64.0  # zenith luminance of the CIE overcast sky (fallback); calibrated against your photos 6/8/19 at exposure 0
HDRI = os.path.join(HERE, 'textures', 'hotel_rooftop_balcony', 'hotel_rooftop_balcony_4k.hdr')
HDRI_STRENGTH = 32.0  # calibrated against your photos 6/8/19 at exposure 0 (AgX)
WHITE_BALANCE = (1.06, 1.0, 0.965)  # warms the bluish overcast light the way a camera's white balance would (from photo whites)
HDRI_ROTATION = -18.0  # degrees about Z: puts the panorama's city/sea side outside your window


SUNNY = 1                     # default look: 1 = sunny afternoon, 0 = overcast calibrated to your photos (Scene > Custom Properties > sunny)
SUN_HDRI = os.path.join(HERE, 'textures', 'homecoming_center_rooftop', 'homecoming_center_rooftop_4k.hdr')
SUN_HDRI_ROTATION = -36.0     # puts that panorama's city skyline outside your window
SUN_HDRI_CLAMP = 4.86         # its sun disc is cut above this luminance for lighting rays; the sun lamp carries that energy instead
SUN_SKY_STRENGTH = 8.0        # exposure of the sunny look (+3 stops: a photographer exposing for the room; camera exposure stays 0)
SUN_ELEVATION, SUN_AZIMUTH = 45.0, -105.0   # mid-afternoon sun (you said it comes in in the afternoon; exact bearing EST)
SUN_IRRADIANCE = 4.17 * 0.88  # measured from that HDRI's sun disc; x0.88 for the longer air path of a low afternoon sun


def res(n):
    return next(o for o in n.outputs if o.identifier == 'Result_Color')


def drive(idblock, path, expr):
    """Driver on scene['sunny'] (simple expression - works without enabling Python scripts)."""
    d = idblock.driver_add(path).driver; d.type = 'SCRIPTED'
    v = d.variables.new(); v.name = 'var'; v.type = 'SINGLE_PROP'
    v.targets[0].id_type = 'SCENE'; v.targets[0].id = bpy.context.scene; v.targets[0].data_path = '["sunny"]'
    d.expression = expr


def env_branch(nt, path, rot, loc):
    tc = N(nt, 'ShaderNodeTexCoord', (loc[0] - 400, loc[1])); mp = N(nt, 'ShaderNodeMapping', (loc[0] - 200, loc[1]))
    mp.inputs['Rotation'].default_value = (0.0, 0.0, math.radians(rot)); mp.label = 'Turn the view outside'
    env = N(nt, 'ShaderNodeTexEnvironment', loc); env.image = bpy.data.images.load(path)
    env.image.filepath = '//' + os.path.relpath(path, os.path.dirname(OUT)).replace(os.sep, '/')
    nt.links.new(tc.outputs['Generated'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], env.inputs['Vector'])
    return env.outputs['Color'], tc


def build_world():
    """Two real daylights in one world, switched by scene['sunny']:
    overcast - 360-degree HDR photo of an overcast city (calibrated to your photos);
    sunny    - clear-sky HDR photo of a city skyline; for lighting rays its sun disc is cut (the sun lamp replaces it with
               the measured energy) and its ground is neutralised (its artificial grass would tint your ceiling green)."""
    if not os.path.exists(HDRI):
        return build_cie_sky()
    sc = bpy.context.scene; sc['sunny'] = SUNNY if os.path.exists(SUN_HDRI) else 0
    sc.id_properties_ui('sunny').update(min=0, max=1, description='1 = sunny afternoon, 0 = overcast (calibrated to your photos)')
    w = bpy.data.worlds.new('WORLD_Daylight'); sc.world = w
    w.use_nodes = True; nt = w.node_tree; L = nt.links
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_WORLD': nt.nodes.remove(n)
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_WORLD')
    bg = N(nt, 'ShaderNodeBackground', (1100, 0)); L.new(bg.outputs[0], out.inputs['Surface'])
    oc, _ = env_branch(nt, HDRI, HDRI_ROTATION, (-600, 400))
    ov = N(nt, 'ShaderNodeVectorMath', (-300, 400), operation='MULTIPLY', label='Overcast brightness x white balance')
    ov.inputs[1].default_value = tuple(HDRI_STRENGTH * c for c in WHITE_BALANCE); L.new(oc, ov.inputs[0])
    if not os.path.exists(SUN_HDRI):
        L.new(ov.outputs['Vector'], bg.inputs['Color']); return
    col, tc = env_branch(nt, SUN_HDRI, SUN_HDRI_ROTATION, (-600, -300))
    lum = N(nt, 'ShaderNodeRGBToBW', (-300, -150)); L.new(col, lum.inputs[0])
    mx = N(nt, 'ShaderNodeMath', (-150, -150), operation='MAXIMUM'); mx.inputs[1].default_value = 1e-4
    dv = N(nt, 'ShaderNodeMath', (0, -150), operation='DIVIDE'); dv.inputs[0].default_value = SUN_HDRI_CLAMP
    k = N(nt, 'ShaderNodeMath', (150, -150), operation='MINIMUM'); k.inputs[1].default_value = 1.0
    cl = N(nt, 'ShaderNodeVectorMath', (300, -300), operation='SCALE')
    gl = N(nt, 'ShaderNodeMath', (300, -150), operation='MULTIPLY')
    sep = N(nt, 'ShaderNodeSeparateXYZ', (0, -550)); below = N(nt, 'ShaderNodeMath', (150, -550), operation='LESS_THAN')
    gnd = N(nt, 'ShaderNodeMix', (450, -300), data_type='RGBA')
    lp = N(nt, 'ShaderNodeLightPath', (150, -800)); seen = N(nt, 'ShaderNodeMath', (350, -800), operation='MAXIMUM')
    vw = N(nt, 'ShaderNodeMix', (650, -300), data_type='RGBA')
    ss = N(nt, 'ShaderNodeVectorMath', (850, -300), operation='SCALE', label='Sunny sky brightness')
    ss.inputs['Scale'].default_value = SUN_SKY_STRENGTH
    pick = N(nt, 'ShaderNodeMix', (950, 0), data_type='RGBA'); pick.name = pick.label = 'SUNNY_SWITCH'
    for a, b in [(lum.outputs[0], mx.inputs[0]), (mx.outputs[0], dv.inputs[1]), (dv.outputs[0], k.inputs[0]),
                 (col, cl.inputs[0]), (k.outputs[0], cl.inputs['Scale']), (lum.outputs[0], gl.inputs[0]), (k.outputs[0], gl.inputs[1]),
                 (tc.outputs['Generated'], sep.inputs[0]), (sep.outputs['Z'], below.inputs[0]),
                 (below.outputs[0], sock(gnd, 'Factor_Float')), (cl.outputs['Vector'], sock(gnd, 'A_Color')), (gl.outputs[0], sock(gnd, 'B_Color')),
                 (lp.outputs['Is Camera Ray'], seen.inputs[0]), (lp.outputs['Is Transmission Ray'], seen.inputs[1]),
                 (seen.outputs[0], sock(vw, 'Factor_Float')), (res(gnd), sock(vw, 'A_Color')), (col, sock(vw, 'B_Color')),
                 (res(vw), ss.inputs[0]), (ov.outputs['Vector'], sock(pick, 'A_Color')), (ss.outputs['Vector'], sock(pick, 'B_Color')),
                 (res(pick), bg.inputs['Color'])]:
        L.new(a, b)
    below.inputs[1].default_value = 0.0
    drive(nt, 'nodes["SUNNY_SWITCH"].inputs[0].default_value', 'var')


def build_cie_sky():
    """CIE standard overcast sky: L = Lz (1 + 2 cos(zenith)) / 3 above the horizon, ground (albedo 0.2) below.
    Neutral daylight, so wall colours compare fairly; the window view reads as a bright sky over grey ground."""
    w = bpy.data.worlds.new('WORLD_Overcast_Daylight'); bpy.context.scene.world = w
    w.use_nodes = True; nt = w.node_tree; L = nt.links
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_WORLD': nt.nodes.remove(n)
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_WORLD')
    tc = N(nt, 'ShaderNodeTexCoord', (-1200, 0)); sep = N(nt, 'ShaderNodeSeparateXYZ', (-1000, 0))
    L.new(tc.outputs['Generated'], sep.inputs[0])                     # world 'Generated' = view direction
    up = N(nt, 'ShaderNodeMath', (-800, 150), operation='MAXIMUM'); up.inputs[1].default_value = 0.0
    sky = N(nt, 'ShaderNodeMath', (-600, 150), operation='MULTIPLY_ADD')
    sky.inputs[1].default_value, sky.inputs[2].default_value = 2 / 3, 1 / 3
    above = N(nt, 'ShaderNodeMath', (-800, -150), operation='GREATER_THAN'); above.inputs[1].default_value = 0.0
    g = 0.2 * 7 / 9                                                   # ground: albedo 0.2 x horizontal illuminance 7*pi*Lz/9 / pi
    d = N(nt, 'ShaderNodeMath', (-400, 150), operation='SUBTRACT'); d.inputs[1].default_value = g
    m = N(nt, 'ShaderNodeMath', (-200, 0), operation='MULTIPLY')
    a = N(nt, 'ShaderNodeMath', (0, 0), operation='ADD'); a.inputs[1].default_value = g
    s = N(nt, 'ShaderNodeMath', (200, 0), operation='MULTIPLY'); s.inputs[1].default_value = DAYLIGHT
    s.label = 'Daylight brightness (zenith)'
    bg = N(nt, 'ShaderNodeBackground', (400, 0)); bg.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)
    for x, y in [(sep.outputs['Z'], up.inputs[0]), (up.outputs[0], sky.inputs[0]), (sep.outputs['Z'], above.inputs[0]),
                 (sky.outputs[0], d.inputs[0]), (d.outputs[0], m.inputs[0]), (above.outputs[0], m.inputs[1]),
                 (m.outputs[0], a.inputs[0]), (a.outputs[0], s.inputs[0]), (s.outputs[0], bg.inputs['Strength']),
                 (bg.outputs[0], out.inputs['Surface'])]:
        L.new(x, y)


def level_cam(name, loc, azimuth, lens, shift_y, note, focus=220.0, fstop=4.0):
    """Architectural camera: level (vertical lines stay vertical), framed with lens shift instead of tilt.
    Real depth of field: at 16 mm f/4 focused at 2.2 m, everything from ~1.1 m to infinity is sharp, nearer things soften."""
    cam = bpy.data.cameras.new(name); cam.lens = lens; cam.sensor_fit = 'HORIZONTAL'; cam.sensor_width = 36.0
    cam.shift_y = shift_y; cam.clip_start = 0.05; cam.clip_end = 50
    cam.dof.use_dof = True; cam.dof.focus_distance = focus * S; cam.dof.aperture_fstop = fstop
    ob = bpy.data.objects.new(name, cam); COLLS['CAM_Cameras'].objects.link(ob)
    a = math.radians(azimuth)
    ob.location = Vector(loc) * S; ob.rotation_euler = Vector((math.cos(a), math.sin(a), 0)).to_track_quat('-Z', 'Y').to_euler()
    tag(ob, 'EST', note)
    return ob


def aim_cam(name, loc, target, lens, fstop, note):
    """Photographer's camera aimed at a subject, focused on it (shallow depth of field for detail shots)."""
    cam = bpy.data.cameras.new(name); cam.lens = lens; cam.sensor_fit = 'HORIZONTAL'; cam.sensor_width = 36.0
    cam.clip_start = 0.05; cam.clip_end = 50
    ob = bpy.data.objects.new(name, cam); COLLS['CAM_Cameras'].objects.link(ob)
    v = Vector(target) - Vector(loc); ob.location = Vector(loc) * S; ob.rotation_euler = v.to_track_quat('-Z', 'Y').to_euler()
    cam.dof.use_dof = True; cam.dof.focus_distance = v.length * S; cam.dof.aperture_fstop = fstop
    tag(ob, 'EST', note)
    return ob


def build_lights_world_cams():
    c = 'LIGHT_Lighting'
    build_world()
    lt = bpy.data.lights.new('LIGHT_Window_Portal', 'AREA'); lt.shape = 'RECTANGLE'
    lt.size, lt.size_y = (WIN_X1 - WIN_X0 - 2 * WIN_TRIM) * S, (WIN_Z1 - WIN_Z0 - 2 * WIN_TRIM) * S
    lt.cycles.is_portal = True
    ob = bpy.data.objects.new('LIGHT_Window_Portal', lt); COLLS[c].objects.link(ob)
    ob.location = Vector(((WIN_X0 + WIN_X1) / 2, -14.0, (WIN_Z0 + WIN_Z1) / 2)) * S; ob.rotation_euler = (math.radians(90), 0, 0)
    tag(ob, 'DRAWING', 'Cycles light portal in the window opening (guides sky light; emits nothing itself)')
    if os.path.exists(SUN_HDRI):
        lt = bpy.data.lights.new('LIGHT_Sun_Afternoon', 'SUN'); lt.angle = math.radians(0.53)     # the real sun's disc: crisp shadows, soft edge
        lt.use_temperature = True; lt.temperature = 5000.0                                          # warmer low sun
        e, a = math.radians(SUN_ELEVATION), math.radians(SUN_AZIMUTH)
        d = Vector((math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)))            # toward the sun
        ob = bpy.data.objects.new('LIGHT_Sun_Afternoon', lt); COLLS[c].objects.link(ob)
        ob.location = Vector((150, -250, 300)) * S; ob.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        drive(lt, 'energy', f'var * {SUN_IRRADIANCE * SUN_SKY_STRENGTH:.4f}')
        tag(ob, 'EST', f'afternoon sun, elevation {SUN_ELEVATION:.0f} deg; on only when scene["sunny"] = 1; energy measured from the HDRI sun')

    cc = 'CAM_Cameras'
    for n, d in CAMS.items():
        cam = bpy.data.cameras.new(f'CAM_Photo_{n:02d}'); cam.sensor_fit = 'HORIZONTAL'; cam.sensor_width = 36.0
        cam.lens = d['f'] * 36.0 / d['size'][0]; cam.clip_start = 0.05; cam.clip_end = 50
        r = Vector(d['rvec']); R = Matrix.Rotation(r.length, 3, r.normalized()) if r.length > 1e-9 else Matrix.Identity(3)
        Mr = R.transposed() @ Matrix(((1, 0, 0), (0, -1, 0), (0, 0, -1)))
        ob = bpy.data.objects.new(f'CAM_Photo_{n:02d}', cam); COLLS[cc].objects.link(ob)
        ob.matrix_world = Matrix.Translation(Vector(d['C']) * S) @ Mr.to_4x4()
        ob['photo_size'] = d['size']; tag(ob, 'PHOTO', f'Matched to reference/ref_{n:02d}.jpg - render at {d["size"][0]}x{d["size"][1]}')
        img_path = os.path.join(HERE, 'reference', f'ref_{n:02d}.jpg')
        if os.path.exists(img_path):
            cam.show_background_images = True; bgi = cam.background_images.new()
            bgi.image = bpy.data.images.load(img_path); bgi.alpha = 0.5; bgi.display_depth = 'FRONT'; bgi.frame_method = 'STRETCH'
            bgi.image.filepath = '//' + os.path.relpath(img_path, os.path.dirname(OUT)).replace(os.sep, '/')  # folder stays portable
    def ortho(name, loc, rot, scale, note):
        cam = bpy.data.cameras.new(name); cam.type = 'ORTHO'; cam.ortho_scale = scale; cam.clip_start = 0.01; cam.clip_end = 20
        ob = bpy.data.objects.new(name, cam); COLLS[cc].objects.link(ob)
        ob.location = Vector(loc) * S; ob.rotation_euler = [math.radians(a) for a in rot]; tag(ob, 'DRAWING', note)
    ortho('CAM_Plan_Top', (RW / 2, RD / 2, 600), (0, 0, 0), 3.5, 'Top-down plan; hide ARCH_Ceiling + crown to use')
    ortho('CAM_Elevation_Wall1', (RW / 2, 5.0, RH / 2), (90, 0, 0), 3.7, 'Looks at wall 1 (door/wardrobe)')
    ortho('CAM_Elevation_Wall2', (RW / 2, RD - WARD_D - 8.0, RH / 2), (90, 0, 180), 3.7, 'Looks at wall 2 (window)')
    ortho('CAM_Elevation_Wall3', (2.0, RD / 2, RH / 2), (90, 0, -90), 3.7, 'Looks at wall 3 (piano)')
    ortho('CAM_Elevation_Wall4', (WARD_X0 - 2.0, RD / 2, RH / 2), (90, 0, 90), 3.7, 'Looks at wall 4 (desk)')
    bpy.context.scene.camera = level_cam('CAM_Render_A_From_Door', (40, 245, 150), -62, 16, -0.05,
                                         'Render view: walls 2, 3, 4 (window, piano, desk)')
    level_cam('CAM_Render_B_From_Window', (285, 60, 150), 145, 16, -0.05, 'Render view: walls 1, 4 (door, wardrobe, desk)')
    bpy.context.scene.camera = level_cam('CAM_Hero_1_Room', (46, 238, 122), -57, 18, -0.07,
                                         'Hero: the whole room in afternoon sun, photographer height', focus=270.0, fstop=5.6)
    aim_cam('CAM_Hero_2_Bed_Detail', (160, 160, 95), (250, 45, 60), 35, 2.8, 'Hero: sun on the bedding (detail)')
    aim_cam('CAM_Hero_3_Desk', (165, 170, 128), (22, 70, 92), 24, 4.0, 'Hero: desk corner and shelves')


def render_settings():
    sc = bpy.context.scene; cy = sc.cycles
    sc.unit_settings.system = 'METRIC'; sc.unit_settings.length_unit = 'CENTIMETERS'
    sc.render.engine = 'CYCLES'; cy.device = 'GPU'
    cy.samples = 512; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.01; cy.use_denoising = True
    cy.max_bounces, cy.diffuse_bounces, cy.glossy_bounces, cy.transmission_bounces = 12, 6, 4, 8
    cy.transparent_max_bounces = 8; cy.caustics_reflective = cy.caustics_refractive = False
    cy.sample_clamp_indirect = 10.0                       # kills fireflies from the bright window
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100
    try: sc.view_settings.view_transform = 'AgX'
    except Exception: pass
    sc.view_settings.look = 'None'; sc.view_settings.exposure = 0.0


def build_compositor():
    """Photographic finish, applied to every F12 render: a soft bloom around the bright window, slight lens colour
    fringing toward the edges, a gentle vignette and fine film grain (after denoising). Each node is named FX_*;
    switch the whole thing off in Render Properties > Post Processing > Compositing."""
    sc = bpy.context.scene
    ng = bpy.data.node_groups.new('COMP_Photographic_Finish', 'CompositorNodeTree')
    ng.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    sc.compositing_node_group = ng
    nd, L = ng.nodes, ng.links
    def node(kind, x, y=0, name=None, **inputs):
        n = nd.new(kind); n.location = (x, y)
        if name: n.name = n.label = name
        for k, v in inputs.items(): n.inputs[k].default_value = v
        return n
    rl = node('CompositorNodeRLayers', -1400)
    gl = node('CompositorNodeGlare', -1150, name='FX_Window_Bloom', Type='Bloom', Quality='High', Threshold=2.0, Strength=0.05, Size=0.4)
    ld = node('CompositorNodeLensdist', -900, name='FX_Lens_Fringing', Dispersion=0.006, Fit=True)
    ic = node('CompositorNodeImageCoordinates', -700, -250)
    ln = node('ShaderNodeVectorMath', -500, -250); ln.operation = 'LENGTH'
    vg = node('ShaderNodeMapRange', -300, -250, name='FX_Vignette')
    vg.inputs['From Min'].default_value, vg.inputs['From Max'].default_value = 0.55, 1.35
    vg.inputs['To Min'].default_value, vg.inputs['To Max'].default_value = 1.0, 0.8
    vm = node('ShaderNodeVectorMath', -100); vm.operation = 'SCALE'
    wn = node('ShaderNodeTexWhiteNoise', -300, -500); wn.noise_dimensions = '2D'
    gr = node('ShaderNodeMapRange', -100, -500, name='FX_Film_Grain')
    gr.inputs['To Min'].default_value, gr.inputs['To Max'].default_value = 0.965, 1.035
    gm = node('ShaderNodeVectorMath', 150); gm.operation = 'SCALE'
    out = node('NodeGroupOutput', 400)
    for a, b in [(rl.outputs['Image'], gl.inputs['Image']), (gl.outputs['Image'], ld.inputs['Image']), (ld.outputs['Image'], ic.inputs['Image']),
                 (ic.outputs['Uniform'], ln.inputs[0]), (ln.outputs['Value'], vg.inputs['Value']), (ld.outputs['Image'], vm.inputs[0]),
                 (vg.outputs['Result'], vm.inputs['Scale']), (ic.outputs['Pixel'], wn.inputs['Vector']), (wn.outputs['Value'], gr.inputs['Value']),
                 (vm.outputs['Vector'], gm.inputs[0]), (gr.outputs['Result'], gm.inputs['Scale']), (gm.outputs['Vector'], out.inputs[0])]:
        L.new(a, b)
    sc.render.use_compositing = True


def setup_viewport():
    """Open looking through the overview camera in Material Preview, instead of at the outside of a closed box."""
    lc = bpy.context.view_layer.layer_collection.children['ARCH_Architecture'].children['ARCH_Cutters']
    lc.hide_viewport = True                      # boolean cutters keep working, just not drawn
    for scr in bpy.data.screens:
        for area in scr.areas:
            if area.type != 'VIEW_3D': continue
            sp = area.spaces.active
            sp.shading.type = 'MATERIAL'
            sp.clip_start, sp.clip_end = 0.01, 100.0
            sp.show_object_viewport_camera = sp.show_object_viewport_light = False   # 15 camera gizmos would clutter the room
            sp.overlay.show_floor = sp.overlay.show_axis_x = sp.overlay.show_axis_y = False
            sp.region_3d.view_perspective = 'CAMERA'


README = """BEDROOM BASELINE - read me
==========================
This file is generated by build_bedroom.py (same folder). Treat it as READ-ONLY reference of the real room.
For renovation ideas, copy it into experiments/ and change the copy (or re-run the script to regenerate).

Coordinates: origin = floor at the corner of wall 2 (window) and wall 4 (desk wall).
 +X along wall 2 toward wall 3 (300 cm), +Y along wall 4 toward wall 1 (door wall, 290 cm), +Z up (270 cm).
Every object has custom properties 'dim_source' (DRAWING / USER / PHOTO / SPEC / EST) and often 'note'.
Moving furniture: select the furniture's Empty (e.g. DESK_Desk, PIANO_Korg_SP250) - children follow.
Opening the door: rotate DOOR_Leaf_Pivot around Z with a NEGATIVE angle.
Materials are named M_* and shared per finish (e.g. M_Wall_Paint) - change one to re-paint everything using it.
Photo-matched cameras CAM_Photo_NN show your photo overlaid (camera view, 50% alpha) - quick accuracy check.
Rendering: F12 renders the active camera (CAM_Hero_1_Room) with Cycles at 1920x1080. Enable your GPU once in
 Preferences > System > Cycles Render Devices > Metal. Other cameras: CAM_Hero_2_Bed_Detail, CAM_Hero_3_Desk, CAM_Render_A/B.
Lighting: Scene > Custom Properties > 'sunny': 1 = afternoon sun (clear-sky city HDRI + measured sun lamp, sun angle EST),
 0 = overcast calibrated to your photos. Surfaces use scanned Poly Haven textures (CC0) on the photo-calibrated colours;
 wall colour = the PAINT_COLOR node in M_Wall_Paint. Bedding is cloth-simulated (frozen meshes).
Lens effects (bloom, colour fringing, vignette, grain) live in the compositor (FX_* nodes). Props: collection PROPS_Lived_In.
"""


def main():
    reset()
    for name, parent in [('ARCH_Architecture', None), ('ARCH_Electrical', 'ARCH_Architecture'), ('ARCH_Cutters', 'ARCH_Architecture'),
                         ('DOOR_Door', None), ('WIN_Window', None), ('WARD_Wardrobe', None),
                         ('FURNITURE', None), ('FURN_Bed', 'FURNITURE'), ('FURN_Desk', 'FURNITURE'), ('FURN_Shelves', 'FURNITURE'),
                         ('FURN_Piano', 'FURNITURE'), ('FURN_Chair', 'FURNITURE'), ('FURN_Stool', 'FURNITURE'),
                         ('DECOR_Loose', None), ('PROPS_Lived_In', None), ('LIGHT_Lighting', None), ('CAM_Cameras', None)]:
        coll(name, parent)
    build_materials(); realism_pass(); build_architecture(); update()
    build_door(); build_window(); build_wardrobe(); update()
    build_bed(); build_desk(); build_shelves(); build_piano(); update()
    build_chair(); build_stool(); build_decor(); build_props(); build_lights_world_cams(); render_settings(); build_compositor()
    t = bpy.data.texts.new('README_Bedroom'); t.write(README)
    setup_viewport()
    update()
    bpy.context.preferences.filepaths.save_version = 0  # no .blend1 backups next to the baseline
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
    print('SAVED', OUT, len(bpy.data.objects), 'objects')


main()
