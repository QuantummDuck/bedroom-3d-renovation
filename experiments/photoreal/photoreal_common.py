"""Photoreal upgrades shared by the current-room twin and the teak/navy design (round 5).
Imported by build_current.py / build_v5.py / render_jobs.py inside Blender. Units: cm in code, metres in Blender.

What professional interior renders do, applied here (sources in Archviz_Research.md):
- cameras at eye height (yours: 156 standing / 118 seated), level with lens shift (vertical lines stay vertical),
  24-35 mm for rooms, 50 mm for details; real depth of field; exposure + white balance like a photographer
- scanned PBR materials at real-world scale, colours inside measured albedo ranges, roughness never uniform
- imperfections: paint relief, specks, smudges, fingerprints, dust, tile lippage, bevelled edges
- light from real sources only: physically placed sun for your location, sky/HDRI through the window, practical lamps
"""
import bpy, bmesh, json, math, os, random
from datetime import datetime
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TEX = os.path.join(ROOT, 'textures'); PH = os.path.join(TEX, 'photo')
S = 0.01; RW, RD, RH = 300.0, 290.0, 270.0
EYE_STAND, EYE_SEAT = 156.0, 118.0           # user 167 cm tall
sc = bpy.context.scene


# ============================================================================ helpers
def lin(h):
    return tuple((v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)])


def node(nt, kind, x=0, y=0, **kw):
    n = nt.nodes.new(kind); n.location = (x, y)
    for k, v in kw.items(): setattr(n, k, v)
    return n


def sock(n, ident, out=False):
    return next(s for s in (n.outputs if out else n.inputs) if s.identifier == ident)


def image(path, color=True):
    im = bpy.data.images.load(path, check_existing=True)
    im.colorspace_settings.name = 'sRGB' if color else 'Non-Color'
    try: im.filepath = bpy.path.relpath(path)
    except ValueError: pass
    return im


def tex(nt, path, vec, x, y, color=True, interp='Linear'):
    t = node(nt, 'ShaderNodeTexImage', x, y); t.image = image(path, color); t.interpolation = interp
    if vec is not None: nt.links.new(vec, t.inputs['Vector'])
    return t


def bsdf(m):
    return next(n for n in m.node_tree.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')


def material(name, hexc, rough, metal=0.0, **extra):
    m = bpy.data.materials.get(name)
    if m: bpy.data.materials.remove(m)
    m = bpy.data.materials.new(name); m.use_nodes = True; p = bsdf(m)
    col = (*lin(hexc), 1.0) if isinstance(hexc, str) else hexc
    p.inputs['Base Color'].default_value = col; p.inputs['Roughness'].default_value = rough; p.inputs['Metallic'].default_value = metal
    for k, v in extra.items(): p.inputs[k].default_value = v
    m.diffuse_color = col
    return m


def coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name)
        (bpy.data.collections[parent] if parent else sc.collection).children.link(c)
    return c


def remove(*names):
    for n in names:
        ob = bpy.data.objects.get(n)
        if ob: bpy.data.objects.remove(ob)


def uv_vec(nt, size_m, rot=0.0, x=-1700, y=0, coord='UV', loc=(0.0, 0.0), size_v=None):
    tc = node(nt, 'ShaderNodeTexCoord', x - 200, y); mp = node(nt, 'ShaderNodeMapping', x, y)
    mp.inputs['Scale'].default_value = (1 / size_m, 1 / (size_v or size_m), 1 / size_m)
    mp.inputs['Rotation'].default_value = (0, 0, math.radians(rot)); mp.inputs['Location'].default_value = (*loc, 0)
    nt.links.new(tc.outputs[coord], mp.inputs['Vector'])
    return mp.outputs['Vector']


def stack_normal(nt, p, normal_out):
    """Put a new normal (bump/normal-map output) under whatever already feeds the BSDF normal."""
    if p.inputs['Normal'].is_linked:
        prev = p.inputs['Normal'].links[0].from_node
        if prev.bl_idname == 'ShaderNodeBump' and not prev.inputs['Normal'].is_linked:
            nt.links.new(normal_out, prev.inputs['Normal']); return
    nt.links.new(normal_out, p.inputs['Normal'])


def add_bump(nt, p, height, strength, distance, x=-300, y=-900):
    b = node(nt, 'ShaderNodeBump', x, y); b.inputs['Strength'].default_value = strength; b.inputs['Distance'].default_value = distance
    nt.links.new(height, b.inputs['Height'])
    if p.inputs['Normal'].is_linked: nt.links.new(p.inputs['Normal'].links[0].from_socket, b.inputs['Normal'])
    nt.links.new(b.outputs['Normal'], p.inputs['Normal'])
    return b


def add_rough(nt, p, mask, amount, x=-200, y=-500):
    """roughness += mask * amount (clamped)."""
    mul = node(nt, 'ShaderNodeMath', x - 160, y, operation='MULTIPLY'); mul.inputs[1].default_value = amount
    nt.links.new(mask, mul.inputs[0])
    ad = node(nt, 'ShaderNodeMath', x, y, operation='ADD', use_clamp=True)
    r = p.inputs['Roughness']
    if r.is_linked: nt.links.new(r.links[0].from_socket, ad.inputs[0])
    else: ad.inputs[0].default_value = r.default_value
    nt.links.new(mul.outputs[0], ad.inputs[1]); nt.links.new(ad.outputs[0], r)
    return ad


def mul_color(nt, p, factor, x=-200, y=300):
    """Base colour *= factor (scalar socket)."""
    vm = node(nt, 'ShaderNodeVectorMath', x, y, operation='SCALE')
    bc = p.inputs['Base Color']
    if bc.is_linked: nt.links.new(bc.links[0].from_socket, vm.inputs[0])
    else: vm.inputs[0].default_value = bc.default_value[:3]
    nt.links.new(factor, vm.inputs['Scale']); nt.links.new(vm.outputs['Vector'], bc)
    return vm


def maprange(nt, val, a, b, c, d, x, y):
    mr = node(nt, 'ShaderNodeMapRange', x, y)
    mr.inputs['From Min'].default_value, mr.inputs['From Max'].default_value = a, b
    mr.inputs['To Min'].default_value, mr.inputs['To Max'].default_value = c, d
    nt.links.new(val, mr.inputs['Value'])
    return mr.outputs['Result']


class Geo:
    """bmesh builder in cm."""
    def __init__(self): self.bm = bmesh.new()

    def v(self, p): return self.bm.verts.new(Vector(p) * S)

    def f(self, vs, mi=0):
        f = self.bm.faces.new(vs); f.material_index = mi; return f

    def prism(self, O, A, B, N, pts, t0, t1, mi=0, caps=True):
        O, A, B, N = map(Vector, (O, A, B, N))
        bot = [self.v(O + A * x + B * y + N * t0) for x, y in pts]; top = [self.v(O + A * x + B * y + N * t1) for x, y in pts]
        if caps: self.f(bot[::-1], mi); self.f(top, mi)
        for i in range(len(pts)):
            j = (i + 1) % len(pts); self.f((bot[i], bot[j], top[j], top[i]), mi)
        return self

    def box(self, x0, x1, y0, y1, z0, z1, mi=0):
        x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
        hx, hy = (x1 - x0) / 2, (y1 - y0) / 2
        return self.prism(((x0 + x1) / 2, (y0 + y1) / 2, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1),
                          [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)], z0, z1, mi)

    def obox(self, c, ax, ay, az, hx, hy, hz, mi=0):
        """Oriented box: centre c (cm), unit axes, half sizes (cm)."""
        c, ax, ay, az = Vector(c), Vector(ax), Vector(ay), Vector(az)
        v = [self.v(c + sx * hx * ax + sy * hy * ay + sz * hz * az) for sx, sy, sz in
             [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]]
        for f in [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]: self.f([v[i] for i in f], mi)
        return self

    def cyl(self, p0, p1, r, n=24, mi=0, caps=True, r1=None):
        p0, p1 = Vector(p0), Vector(p1); a = (p1 - p0).normalized(); u = a.orthogonal().normalized(); w = a.cross(u)
        r1 = r if r1 is None else r1
        b = [self.v(p0 + r * (math.cos(t) * u + math.sin(t) * w)) for t in [2 * math.pi * k / n for k in range(n)]]
        t_ = [self.v(p1 + r1 * (math.cos(t) * u + math.sin(t) * w)) for t in [2 * math.pi * k / n for k in range(n)]]
        for k in range(n):
            j = (k + 1) % n; self.f((b[k], b[j], t_[j], t_[k]), mi)
        if caps: self.f(b[::-1], mi); self.f(t_, mi)
        return self

    def revolve(self, c, prof, n=48, mi=0):
        """Profile [(r, z)] revolved about the vertical axis through c (x, y)."""
        rings = []
        for r, z in prof:
            if r < 1e-6: rings.append([self.v((c[0], c[1], z))] * n)
            else: rings.append([self.v((c[0] + r * math.cos(2 * math.pi * k / n), c[1] + r * math.sin(2 * math.pi * k / n), z)) for k in range(n)])
        for i in range(len(prof) - 1):
            a, b = rings[i], rings[i + 1]
            for k in range(n):
                j = (k + 1) % n; q = [a[k], a[j], b[j], b[k]]
                q = [v for idx, v in enumerate(q) if v not in q[:idx]]
                if len(q) >= 3: self.f(q, mi if isinstance(mi, int) else mi[i])
        return self

    def tube(self, pts, r, n=12, closed=False, mi=0):
        """Circle swept along a polyline (parallel-transport frames) - one continuous tube, no beads."""
        P_ = [Vector(p) for p in pts]; m = len(P_)
        tang = [((P_[(i + 1) % m] if closed or i < m - 1 else P_[i]) - (P_[i - 1] if closed or i > 0 else P_[i])).normalized() for i in range(m)]
        u = tang[0].orthogonal().normalized(); rings = []
        for i in range(m):
            if i: u = (u - tang[i] * u.dot(tang[i])).normalized()
            w = tang[i].cross(u)
            rings.append([self.v(P_[i] + r * (math.cos(2 * math.pi * k / n) * u + math.sin(2 * math.pi * k / n) * w)) for k in range(n)])
        for i in range(m if closed else m - 1):
            a, b = rings[i], rings[(i + 1) % m]
            for k in range(n):
                self.f((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]), mi)
        if not closed: self.f(rings[0][::-1], mi); self.f(rings[-1], mi)
        return self

    def sphere(self, c, r, mi=0, seg=24, rz=None):
        res = bmesh.ops.create_uvsphere(self.bm, u_segments=seg, v_segments=max(6, seg // 2), radius=r * S)
        if rz: bmesh.ops.scale(self.bm, vec=(1, 1, rz / r), verts=res['verts'])
        bmesh.ops.translate(self.bm, verts=res['verts'], vec=Vector(c) * S)
        for f in {f for v in res['verts'] for f in v.link_faces}: f.material_index = mi
        return self

    def finish(self, name, collection, mats, smooth=False, bevel=None, subsurf=0, origin=None, uv_m=True):
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces[:])
        uv = self.bm.loops.layers.uv.new('UVMap')
        for f in self.bm.faces:          # box projection in metres, u along the face's longer side
            ax = max(range(3), key=lambda i: abs(f.normal[i])); a, b = [i for i in range(3) if i != ax]
            co = [l.vert.co for l in f.loops]
            if max(p[b] for p in co) - min(p[b] for p in co) > max(p[a] for p in co) - min(p[a] for p in co): a, b = b, a
            for lp in f.loops: lp[uv].uv = (lp.vert.co[a], lp.vert.co[b])
        if origin is not None:
            o = Vector(origin) * S
            for v in self.bm.verts: v.co -= o
        remove(name)
        me = bpy.data.meshes.new(name); self.bm.to_mesh(me); self.bm.free()
        for m in mats: me.materials.append(m if isinstance(m, bpy.types.Material) else bpy.data.materials[m])
        if smooth:
            for p in me.polygons: p.use_smooth = True
        ob = bpy.data.objects.new(name, me); coll(collection).objects.link(ob)
        if origin is not None: ob.location = Vector(origin) * S
        if bevel:
            md = ob.modifiers.new('Bevel', 'BEVEL'); md.width = bevel[0] * S; md.segments = bevel[1]; md.limit_method = 'ANGLE'
            md.harden_normals = False
        if subsurf:
            md = ob.modifiers.new('Subsurf', 'SUBSURF'); md.levels = md.render_levels = subsurf
        return ob


def visible_only(ob):
    ob.visible_diffuse = False; ob.visible_shadow = False; ob.visible_transmission = False


# ============================================================================ render + colour
def render_settings(samples=1024):
    cy = sc.cycles
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'METAL'; prefs.get_devices()
    for d in prefs.devices: d.use = True
    sc.render.engine = 'CYCLES'; cy.device = 'GPU'
    cy.samples = samples; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.008; cy.adaptive_min_samples = 64
    cy.use_denoising = True; cy.denoising_quality = 'HIGH'; cy.denoising_prefilter = 'ACCURATE'; cy.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    cy.use_light_tree = True
    cy.max_bounces, cy.diffuse_bounces, cy.glossy_bounces, cy.transmission_bounces = 16, 6, 6, 12
    cy.transparent_max_bounces = 32; cy.volume_bounces = 0
    cy.caustics_reflective = cy.caustics_refractive = False; cy.blur_glossy = 0.5
    cy.sample_clamp_direct = 0.0; cy.sample_clamp_indirect = 8.0
    sc.render.use_persistent_data = True
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_depth = '16'
    vs = sc.view_settings; vs.view_transform = 'AgX'
    for look in ('AgX - Medium High Contrast', 'Medium High Contrast', 'AgX - Base Contrast'):
        try: vs.look = look; break
        except TypeError: continue
    gl = sc.compositing_node_group.nodes.get('FX_Window_Bloom') if sc.compositing_node_group else None
    if gl: gl.inputs['Threshold'].default_value = 1.2; gl.inputs['Strength'].default_value = 0.08; gl.inputs['Size'].default_value = 0.45
    ld = sc.compositing_node_group.nodes.get('FX_Lens_Fringing') if sc.compositing_node_group else None
    if ld:
        ld.inputs['Dispersion'].default_value = 0.004
        try: ld.inputs['Distortion'].default_value = -0.008        # mild barrel, like a real wide-angle lens
        except KeyError: pass
    gr = sc.compositing_node_group.nodes.get('FX_Film_Grain') if sc.compositing_node_group else None
    if gr: gr.inputs['To Min'].default_value, gr.inputs['To Max'].default_value = 0.975, 1.025


def white_balance(kelvin=None, tint=0.0):
    vs = sc.view_settings
    if kelvin is None: vs.use_white_balance = False; return
    vs.use_white_balance = True; vs.white_balance_temperature = kelvin; vs.white_balance_tint = tint


# ============================================================================ materials
def upgrade_paint():
    """Your wall photo's roller texture as relief + tiny tone variation, dark specks and floor-level grime."""
    for name, strength in (('M_Wall_Paint', 0.022), ('M_Ceiling_Paint', 0.015), ('M_Crown_Plaster', 0.015)):
        m = bpy.data.materials.get(name)
        if not m or m.get('pr5'): continue
        nt = m.node_tree; p = bsdf(m); L = nt.links
        for n in nt.nodes:                      # the earlier plaster scan read as stucco; your wall (photos 41/42) is smooth latex
            if n.bl_idname == 'ShaderNodeNormalMap': n.inputs['Strength'].default_value = min(n.inputs['Strength'].default_value, 0.10)
        v = uv_vec(nt, 0.30, x=-2100, y=-1200)
        t = tex(nt, os.path.join(PH, 'wall_micro.png'), v, -1800, -1200, color=False)
        add_bump(nt, p, t.outputs['Color'], strength, 0.0004, -500, -1200)
        rough = maprange(nt, t.outputs['Color'], 0.3, 0.7, 0.04, -0.04, -1400, -1450)
        add_rough(nt, p, rough, 1.0, -300, -1450)
        pos = node(nt, 'ShaderNodeNewGeometry', -2100, 700)
        nz = node(nt, 'ShaderNodeTexNoise', -1800, 700); nz.inputs['Scale'].default_value = 1.4; nz.inputs['Detail'].default_value = 4.0
        L.new(pos.outputs['Position'], nz.inputs['Vector'])
        tone = maprange(nt, nz.outputs['Factor'], 0.35, 0.65, 0.985, 1.015, -1600, 700)
        sep = node(nt, 'ShaderNodeSeparateXYZ', -1800, 450); L.new(pos.outputs['Position'], sep.inputs[0])
        grime = maprange(nt, sep.outputs['Z'], 0.0, 0.30, 0.955, 1.0, -1600, 450)
        vo = node(nt, 'ShaderNodeTexVoronoi', -1800, 200); vo.inputs['Scale'].default_value = 9.0
        L.new(pos.outputs['Position'], vo.inputs['Vector'])
        wn = node(nt, 'ShaderNodeTexWhiteNoise', -1600, 50, noise_dimensions='3D'); L.new(vo.outputs['Position'], wn.inputs['Vector'])
        spot = maprange(nt, vo.outputs['Distance'], 0.0, 0.0035, 1.0, 0.0, -1600, 200)          # ~1-3 mm dots
        pick = node(nt, 'ShaderNodeMath', -1400, 120, operation='GREATER_THAN'); pick.inputs[1].default_value = 0.88
        L.new(wn.outputs['Value'], pick.inputs[0])
        sp = node(nt, 'ShaderNodeMath', -1250, 160, operation='MULTIPLY'); L.new(spot, sp.inputs[0]); L.new(pick.outputs[0], sp.inputs[1])
        speck = maprange(nt, sp.outputs[0], 0.0, 1.0, 1.0, 0.55, -1100, 160)
        f = tone
        for g in (grime, speck):
            mm = node(nt, 'ShaderNodeMath', -900, 500, operation='MULTIPLY'); L.new(f, mm.inputs[0]); L.new(g, mm.inputs[1]); f = mm.outputs[0]
        mul_color(nt, p, f, -400, 450)
        m['pr5'] = 1


def upgrade_floor():
    """Polished porcelain: speckle from your floor photo, near-mirror gloss broken by smudges (photo 43)."""
    m = bpy.data.materials.get('M_Floor_Tile')
    if not m or m.get('pr5'): return
    nt = m.node_tree; p = bsdf(m); L = nt.links
    for n in nt.nodes:            # glossier base: polished porcelain reads 0.03-0.06
        if n.bl_idname == 'ShaderNodeMapRange' and abs(n.inputs['To Min'].default_value - 0.07) < 1e-4:
            n.inputs['To Min'].default_value = 0.035
    v = uv_vec(nt, 0.18, x=-2200, y=900, coord='Object')
    t = tex(nt, os.path.join(PH, 'floor_speckle.png'), v, -1900, 900, color=False)
    mul_color(nt, p, maprange(nt, t.outputs['Color'], 0.3, 0.7, 0.965, 1.035, -1600, 900), -300, 700)
    v2 = uv_vec(nt, 1.6, rot=17, x=-2200, y=-1700, coord='Object')
    sm = tex(nt, os.path.join(TEX, 'SurfaceImperfections003', 'SurfaceImperfections003_2K-JPG_Opacity.jpg'), v2, -1900, -1700, color=False)
    add_rough(nt, p, maprange(nt, sm.outputs['Color'], 0.05, 0.6, 0.0, 1.0, -1600, -1700), 0.16, -250, -1650)
    m['pr5'] = 1


def upgrade_glass():
    """Real 5 mm pane, slight green edge tint, fingerprints and dust; still passes daylight to diffuse/shadow rays."""
    g = bpy.data.objects.get('WIN_Glass')
    if g and not g.get('pr5'):
        ys = sorted({round(v.co.y, 5) for v in g.data.vertices})
        if len(ys) == 2:
            mid = (ys[0] + ys[1]) / 2
            for v in g.data.vertices: v.co.y = mid + (0.0025 if v.co.y > mid else -0.0025)
        g['pr5'] = 1
    m = bpy.data.materials.get('M_Glass')
    if not m or m.get('pr5'): return
    nt = m.node_tree; p = bsdf(m)
    p.inputs['IOR'].default_value = 1.52; p.inputs['Thin Wall'].default_value = False
    p.inputs['Base Color'].default_value = (0.955, 0.985, 0.97, 1.0)
    v = uv_vec(nt, 0.45, rot=8, x=-1700, y=-600)
    fp = tex(nt, os.path.join(TEX, 'Fingerprints002', 'Fingerprints002_2K-JPG_Roughness.jpg'), v, -1400, -600, color=False)
    v2 = uv_vec(nt, 1.2, rot=-23, x=-1700, y=-900)
    du = tex(nt, os.path.join(TEX, 'SurfaceImperfections015', 'SurfaceImperfections015_2K-JPG_Opacity.jpg'), v2, -1400, -900, color=False)
    p.inputs['Roughness'].default_value = 0.0
    add_rough(nt, p, maprange(nt, fp.outputs['Color'], 0.0, 0.4, 0.0, 1.0, -1100, -600), 0.10, -500, -600)
    add_rough(nt, p, maprange(nt, du.outputs['Color'], 0.2, 0.9, 0.0, 1.0, -1100, -900), 0.05, -300, -800)
    m['pr5'] = 1


def upgrade_metals():
    for name, amt in (('M_Chrome', 0.12), ('M_Laptop_Alu', 0.06), ('M_MBA_Silver', 0.06), ('M_Wardrobe_Handle', 0.08)):
        m = bpy.data.materials.get(name)
        if not m or m.get('pr5'): continue
        nt = m.node_tree; p = bsdf(m)
        v = uv_vec(nt, 0.25, rot=31, x=-1700, y=-1900)
        fp = tex(nt, os.path.join(TEX, 'Fingerprints002', 'Fingerprints002_2K-JPG_Opacity.jpg'), v, -1400, -1900, color=False)
        add_rough(nt, p, maprange(nt, fp.outputs['Color'], 0.05, 0.6, 0.0, 1.0, -1100, -1900), amt, -200, -1900)
        m['pr5'] = 1
    m = bpy.data.materials.get('M_Metal_Brushed')
    if m: bsdf(m).inputs['Anisotropic'].default_value = 0.5


def swap_wood(name, asset, res, size_m, rot, gain, rough_src):
    """Replace the scan images in a wood material (keeps its node layout / per-board tint)."""
    m = bpy.data.materials.get(name)
    if not m: return
    nt = m.node_tree
    for n in nt.nodes:
        if n.bl_idname == 'ShaderNodeTexImage' and n.image:
            for kind in ('diff', 'rough', 'nor_gl'):
                if f'_{kind}_' in os.path.basename(n.image.filepath):
                    n.image = image(os.path.join(TEX, asset, f'{asset}_{kind}_{res}.jpg'), color=(kind == 'diff')); n.interpolation = 'Cubic'
        elif n.bl_idname == 'ShaderNodeMapping':
            n.inputs['Scale'].default_value = (1 / size_m, 1 / size_m, 1.0); n.inputs['Rotation'].default_value = (0, 0, math.radians(rot))
        elif n.bl_idname == 'ShaderNodeVectorMath' and n.operation == 'MULTIPLY' and not n.inputs[1].is_linked:
            n.inputs[1].default_value = gain
        elif n.bl_idname == 'ShaderNodeMapRange' and n.inputs['Value'].is_linked and \
                n.inputs['Value'].links[0].from_node.bl_idname == 'ShaderNodeTexImage' and \
                '_rough_' in os.path.basename(n.inputs['Value'].links[0].from_node.image.filepath):
            n.inputs['From Min'].default_value, n.inputs['From Max'].default_value = rough_src
    m['pr5_wood'] = asset


def teak_scan():
    """H8-N boards (+ wardrobe/headboard/desk): real teak veneer scan (Poly Haven, 1 m tile), graded to the chosen colour."""
    tgt = lin('#9A6A3E'); mean = (0.4337, 0.2247, 0.0953)
    swap_wood('M_Boards_teak', 'teak_veneer', '4k', 1.0, 0, tuple(a / b for a, b in zip(tgt, mean)), (0.55, 0.76))


def oak_scan():
    """Current room: light oak melamine (desk, headboards, wardrobe strips) -> oak veneer scan (1.83 m tile)."""
    mean = (0.36, 0.2117, 0.0989)
    for name, tgt in (('M_Desk_Wood', (0.354, 0.189, 0.0722)), ('M_Headboard_Wood', (0.354, 0.189, 0.0722)),
                      ('M_Wardrobe_Wood', (0.185, 0.099, 0.042))):
        swap_wood(name, 'oak_veneer_01', '2k', 1.83, 90, tuple(a / b for a, b in zip(tgt, mean)), (0.30, 0.76))


def bedspread_photo():
    """Your bedspread (photo 50): de-lit, flattened print on the cloth's top-down UVs (x 60-300 cm, y 0-150 cm)."""
    m = bpy.data.materials.get('M_Bedspread')
    if not m or m.get('pr5'): return
    nt = m.node_tree; p = bsdf(m)
    tc = node(nt, 'ShaderNodeTexCoord', -2000, 900); mp = node(nt, 'ShaderNodeMapping', -1800, 900)
    mp.inputs['Scale'].default_value = (1 / 2.4, 1 / 1.5, 1); mp.inputs['Location'].default_value = (-0.25, 0, 0)
    nt.links.new(tc.outputs['UV'], mp.inputs['Vector'])
    t = tex(nt, os.path.join(PH, 'bedspread.png'), mp.outputs['Vector'], -1550, 900, interp='Cubic')
    nt.links.new(t.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.82; p.inputs['Sheen Weight'].default_value = 0.35
    m['pr5'] = 1


def rug_photo(x0=110.2, x1=298.2, y0=96.4, y1=226.4):
    """Your rug: 130 x 188 between the bed and the wardrobe; pattern from photo 44, pile from a carpet scan."""
    remove('DECOR_Rug')
    g = Geo(); g.box(x0, x1, y0, y1, 0.02, 0.9)
    ob = g.finish('DECOR_Rug', 'DECOR_Loose', [], bevel=(0.35, 3), smooth=False)
    ob['dim_source'] = 'USER'; ob['note'] = '130 x 188 cm (user); fits between bed and wardrobe'
    m = material('M_Rug', '#7A7A7C', 0.95, **{'Sheen Weight': 0.5}); nt = m.node_tree; p = bsdf(m)
    v = uv_vec(nt, 0.94, x=-1700, y=300, size_v=0.48)
    t = tex(nt, os.path.join(PH, 'rug.png'), v, -1400, 300, color=False)
    rp = node(nt, 'ShaderNodeValToRGB', -1100, 300); cr = rp.color_ramp
    cr.elements[0].position, cr.elements[0].color = 0.18, (*[c * 0.92 for c in lin('#3A3B40')], 1)
    cr.elements[1].position, cr.elements[1].color = 0.85, (*[c * 0.92 for c in lin('#D2CDC2')], 1)
    nt.links.new(t.outputs['Color'], rp.inputs[0]); nt.links.new(rp.outputs['Color'], p.inputs['Base Color'])
    v2 = uv_vec(nt, 0.6, x=-1700, y=-500)
    nm_t = tex(nt, os.path.join(TEX, 'dirty_carpet', 'dirty_carpet_nor_gl_2k.jpg'), v2, -1400, -500, color=False)
    nm = node(nt, 'ShaderNodeNormalMap', -1100, -500); nm.inputs['Strength'].default_value = 0.9
    nt.links.new(nm_t.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], p.inputs['Normal'])
    add_bump(nt, p, t.outputs['Color'], 0.25, 0.001, -500, -700)          # light yarn sits a hair proud of the dark
    ob.data.materials.append(m)
    return ob


def puzzle_rebuild():
    """Frame 75 x 51.4 (2.1 cm black face, 2.6 deep) flat on wall 3; picture from your straight-on photo 45."""
    remove('DECOR_Puzzle_Frame', 'DECOR_Puzzle_Picture')
    y0, y1, z0, z1, fw, dp = 80.0, 155.0, 121.3, 172.7, 2.1, 2.6
    fr = material('M_Frame_Black_Satin', '#141414', 0.42)
    g = Geo(); xf = RW - dp
    g.box(xf, RW, y0, y1, z1 - fw, z1).box(xf, RW, y0, y1, z0, z0 + fw)
    g.box(xf, RW, y0, y0 + fw, z0 + fw, z1 - fw).box(xf, RW, y1 - fw, y1, z0 + fw, z1 - fw)
    g.box(RW - 0.6, RW, y0 + fw, y1 - fw, z0 + fw, z1 - fw)                                    # backing board
    g.finish('DECOR_Puzzle_Frame', 'DECOR_Loose', [fr], bevel=(0.12, 2))['dim_source'] = 'PHOTO'
    m = material('M_Puzzle_Picture', '#20283C', 0.38, **{'Coat Weight': 0.25, 'Coat Roughness': 0.25}); nt = m.node_tree; p = bsdf(m)
    t = tex(nt, os.path.join(PH, 'puzzle.png'), None, -500, 200, interp='Cubic'); nt.links.new(t.outputs['Color'], p.inputs['Base Color'])
    bm = bmesh.new(); uv = bm.loops.layers.uv.new('UVMap'); xp = RW - 0.75
    vs = [bm.verts.new(Vector(c) * S) for c in [(xp, y1 - fw, z0 + fw), (xp, y0 + fw, z0 + fw), (xp, y0 + fw, z1 - fw), (xp, y1 - fw, z1 - fw)]]
    f = bm.faces.new(vs)
    for lp, (u, w) in zip(f.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]): lp[uv].uv = (u, w)
    me = bpy.data.meshes.new('DECOR_Puzzle_Picture'); bm.to_mesh(me); bm.free(); me.materials.append(m)
    ob = bpy.data.objects.new('DECOR_Puzzle_Picture', me); coll('DECOR_Loose').objects.link(ob); ob['dim_source'] = 'PHOTO'
    return ob


# ============================================================================ fixtures & props
FAN_C = (150.0, 145.0)


def fan_rebuild():
    """Your fan (photos 28/40): ball canopy, short rod, white motor housing, 3 oval 50 cm blades with a raised rim,
    egg-shaped frosted globe whose bottom is 217 cm above the floor (user)."""
    remove('FAN_Body', 'FAN_Blades', 'FAN_Globe', 'LIGHT_Fan_Bulb')
    coll('FIXT_Ceiling_Fan')
    cx, cy = FAN_C
    white = material('M_Fan_White', '#F1F0EB', 0.28, **{'Coat Weight': 0.2})
    opal = bpy.data.materials.get('M_Fan_Opal')
    if not opal:
        opal = bpy.data.materials.new('M_Fan_Opal'); opal.use_nodes = True; nt = opal.node_tree
        for n in list(nt.nodes):
            if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
        o = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
        p = node(nt, 'ShaderNodeBsdfPrincipled', -300, 300); p.inputs['Base Color'].default_value = (*lin('#EEEDE8'), 1)
        p.inputs['Roughness'].default_value = 0.25; p.inputs['Coat Weight'].default_value = 0.6
        tr = node(nt, 'ShaderNodeBsdfTranslucent', -300, 0); tr.inputs['Color'].default_value = (*lin('#F3EFE6'), 1)
        mx = node(nt, 'ShaderNodeMixShader', 0, 200); mx.inputs['Fac'].default_value = 0.45
        em = node(nt, 'ShaderNodeEmission', 0, -100); em.name = em.label = 'FAN_GLOW'
        em.inputs['Color'].default_value = (1.0, 0.78, 0.55, 1); em.inputs['Strength'].default_value = 0.0
        ad = node(nt, 'ShaderNodeAddShader', 200, 100)
        nt.links.new(p.outputs[0], mx.inputs[1]); nt.links.new(tr.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], ad.inputs[0]); nt.links.new(em.outputs[0], ad.inputs[1]); nt.links.new(ad.outputs[0], o.inputs['Surface'])
        opal.diffuse_color = (*lin('#EEEDE8'), 1)
    body = Geo()
    ball = [(0, RH), (3.2, RH), (4.6, 269.2), (5.3, 267.4), (5.3, 265.6), (4.5, 263.8), (3.0, 262.6), (1.3, 262.2), (1.15, 262.2)]
    rod = [(1.15, 262.2), (1.15, 247.4)]
    housing = [(1.15, 247.4), (6.5, 247.2), (8.6, 246.4), (9.4, 245.0), (9.6, 242.0), (9.4, 238.8), (8.9, 237.8), (8.4, 237.6),
               (8.4, 235.4), (7.9, 235.0), (0, 235.0)]
    body.revolve((cx, cy), ball + rod[1:] + housing[1:], n=48)
    body.finish('FAN_Body', 'FIXT_Ceiling_Fan', [white], smooth=True)['note'] = 'fan body after photos 28/40 (canopy ball, rod, housing)'
    gl = Geo()
    prof = [(0, 235.0), (7.6, 235.0)] + [(7.9 * math.sin(math.acos(max(-1.0, min(1.0, 1 - 2 * k / 20)))) ** 0.9 if 0 < k < 20 else (7.6 if k == 0 else 0),
                                          235.0 - 18.0 * (k / 20) ** 1.12) for k in range(21)]
    prof = [prof[0]] + [q for q in prof[1:] if q[0] > 0.05 or q is prof[-1]]
    prof[-1] = (0, 217.0)
    gl.revolve((cx, cy), prof, n=48)
    gob = gl.finish('FAN_Globe', 'FIXT_Ceiling_Fan', [opal], smooth=True); gob.visible_shadow = False
    gob['note'] = 'frosted egg globe; bottom 217 cm (user)'
    # blades: oval paddles, 50 cm long from the housing, 12 deg pitch, thin with a raised rim; origin on the fan axis for spinning
    bl = Geo(); nu, nv, Lb, r0, zm = 30, 12, 50.0, 8.6, 241.6
    for k in range(3):
        th = math.radians(20 + 120 * k); ct, st = math.cos(th), math.sin(th)
        top, bot = [], []
        for i in range(nu + 1):
            s = i / nu; r = r0 + s * Lb
            wmax = 7.6; shape = math.sin(math.pi * min(1.0, 0.18 + 0.82 * s) ) ** 0.55 if s < 0.97 else 0.05
            half = 1.6 + (wmax - 1.6) * math.sin(min(s / 0.62, 1.0) * math.pi / 2)
            if s > 0.62: half *= math.sqrt(max(0.02, 1 - ((s - 0.62) / 0.38) ** 2))
            a = math.radians(12 - 3 * s); rt, rb = [], []
            for j in range(nv + 1):
                q = -half + 2 * half * j / nv
                rim = 0.28 if j in (0, nv) or i == nu else 0.0                      # raised rim at the edge
                zc = -0.25 * (q / max(half, 1e-3)) ** 2 + rim
                qq, zz = q * math.cos(a) - zc * math.sin(a), q * math.sin(a) + zc * math.cos(a)
                wx, wy = cx + r * ct - qq * st, cy + r * st + qq * ct
                rt.append(bl.v((wx, wy, zm + zz + 0.22))); rb.append(bl.v((wx, wy, zm + zz - 0.22)))
            top.append(rt); bot.append(rb)
        for i in range(nu):
            for j in range(nv):
                bl.f((top[i][j], top[i + 1][j], top[i + 1][j + 1], top[i][j + 1])); bl.f((bot[i][j], bot[i][j + 1], bot[i + 1][j + 1], bot[i + 1][j]))
        edge = [(i, 0) for i in range(nu + 1)] + [(nu, j) for j in range(1, nv + 1)] + [(i, nv) for i in range(nu - 1, -1, -1)] + [(0, j) for j in range(nv - 1, 0, -1)]
        for e in range(len(edge)):
            (i0, j0), (i1, j1) = edge[e], edge[(e + 1) % len(edge)]
            bl.f((top[i0][j0], bot[i0][j0], bot[i1][j1], top[i1][j1]))
        # bracket from the housing to the blade root
        bl.box(cx + (r0 - 1.0) * ct - 1.4 * st - 0.0, cx + (r0 + 3.0) * ct + 1.4 * st, cy + (r0 - 1.0) * st - 1.4 * ct, cy + (r0 + 3.0) * st + 1.4 * ct, zm - 0.6, zm + 0.6)
    bo = bl.finish('FAN_Blades', 'FIXT_Ceiling_Fan', [white], smooth=True, origin=(cx, cy, zm))
    bo['note'] = '3 oval blades, 50 cm each (user), raised rim; rotate about Z to spin'
    lt = bpy.data.lights.new('LIGHT_Fan_Bulb', 'POINT'); lt.shadow_soft_size = 0.035; lt.use_temperature = True; lt.temperature = 2900.0
    lt.energy = 0.0; lo = bpy.data.objects.new('LIGHT_Fan_Bulb', lt); coll('FIXT_Ceiling_Fan').objects.link(lo)
    lo.location = Vector((cx, cy, 226.0)) * S; lo['note'] = 'fan light (2700-3000 K LED bulb in the globe); scenario sets the power'
    return bo


def fan_spin(on, deg_per_frame=55.0):
    bo = bpy.data.objects.get('FAN_Blades')
    if not bo: return
    bo.animation_data_clear(); bo.rotation_euler = (0, 0, 0)
    sc.render.use_motion_blur = bool(on)
    if on:      # linear spin centred on frame 1, shutter = 1 frame: blades sweep ~55 deg like a 1/15 s phone exposure
        prefs = bpy.context.preferences.edit; old = prefs.keyframe_new_interpolation_type; prefs.keyframe_new_interpolation_type = 'LINEAR'
        for f in (0, 1, 2):
            bo.rotation_euler = (0, 0, math.radians(deg_per_frame * (f - 1))); bo.keyframe_insert('rotation_euler', index=2, frame=f)
        prefs.keyframe_new_interpolation_type = old
        sc.render.motion_blur_shutter = 1.0; bo.cycles.motion_steps = 7
    sc.frame_set(1)


def stool_rebuild(cx=228.0, cy=166.0):
    """Saddle bar stool (photo 26): seat top 66 cm (user), chrome dish base, gas column with lever, teardrop footrest."""
    for n in ('STOOL_Body', 'STOOL_Seat', 'STOOL_Footrest'): remove(n)
    chrome = bpy.data.materials.get('M_Chrome') or material('M_Chrome', '#E4E4E4', 0.05, 1.0)
    leather = bpy.data.materials.get('M_Leather_Black') or material('M_Leather_Black', '#141413', 0.5)
    g = Geo()
    g.revolve((cx, cy), [(0, 0.3), (20.0, 0.3), (20.0, 0.9), (17.5, 1.6), (10.0, 2.6), (5.0, 3.3), (3.0, 3.6), (0, 3.6)], n=64)   # dish base
    g.cyl((cx, cy, 3.5), (cx, cy, 38.0), 2.7, 32)                       # lower sleeve
    g.cyl((cx, cy, 38.0), (cx, cy, 60.5), 2.2, 32)                      # gas column
    g.cyl((cx, cy, 60.0), (cx, cy, 62.5), 9.0, 40)                      # seat plate
    g.cyl((cx + 2.0, cy, 61.3), (cx + 15.0, cy, 56.5), 0.55, 12)         # height lever
    g.cyl((cx + 15.0, cy, 56.5), (cx + 15.6, cy, 51.0), 0.6, 12)
    # teardrop footrest: loop of chrome tube in front of the column at ~31 cm, clamped to the sleeve
    zr, pts = 31.0, []
    for k in range(64):            # teardrop in plan: round end in front, pointed end at the clamp on the column
        t = 2 * math.pi * k / 64; back = max(0.0, -math.cos(t))
        pts.append((cx + 17.0 + 12.0 * math.cos(t) - 4.0 * back ** 2, cy + 11.0 * math.sin(t) * (1 - 0.5 * back ** 1.5), zr))
    g.tube(pts, 0.8, 14, closed=True)
    g.cyl((cx + 2.7, cy, zr), (cx - 0.5, cy, zr), 1.4, 16)               # clamp
    ob = g.finish('STOOL_Body', 'FURN_Stool', [chrome], smooth=True); ob['dim_source'] = 'USER'
    ob['note'] = 'seat top 66 cm (user); base, column, lever and footrest after photo 26'

    def bottom(x, y):         # the pad bends down at the front with the top surface (photo 26)
        return 62.5 - 2.2 * max(0.0, (y - 8.0) / 10.0) ** 2 + 1.2 * max(0.0, (-y - 8) / 10)
    def top(x, y):            # saddle: high rear lip, scooped middle, rolled-down front; ~2.8 cm pad
        back = 5.0 * max(0.0, (-y - 5.0) / 13.0) ** 1.8
        side = 0.9 * (x / 21.0) ** 2
        return bottom(x, y) + 2.8 + back + side
    xs = [-21 + 1.5 * i for i in range(29)]; ys = [-18 + 1.5 * j for j in range(25)]
    s = Geo(); T = [[s.v((cx + x, cy + y, top(x, y))) for x in xs] for y in ys]; Bv = [[s.v((cx + x, cy + y, bottom(x, y))) for x in xs] for y in ys]
    nx, ny = len(xs), len(ys)
    for j in range(ny - 1):
        for i in range(nx - 1):
            s.f((T[j][i], T[j][i + 1], T[j + 1][i + 1], T[j + 1][i])); s.f((Bv[j][i], Bv[j + 1][i], Bv[j + 1][i + 1], Bv[j][i + 1]))
    ring = [(0, i) for i in range(nx)] + [(j, nx - 1) for j in range(1, ny)] + [(ny - 1, i) for i in range(nx - 2, -1, -1)] + [(j, 0) for j in range(ny - 2, 0, -1)]
    for k in range(len(ring)):
        (j0, i0), (j1, i1) = ring[k], ring[(k + 1) % len(ring)]; s.f((T[j0][i0], Bv[j0][i0], Bv[j1][i1], T[j1][i1]))
    so = s.finish('STOOL_Seat', 'FURN_Stool', [leather], smooth=True, bevel=(0.9, 3), subsurf=1)
    # top at 66: the saddle's lowest sitting point
    so['note'] = 'black leather saddle seat with stitched edge, top 66 cm (user)'
    # stitched welt: thin raised line 1 cm inside the edge (top surface)
    w = Geo(); ptsw = []
    for k in range(len(ring)):
        j, i = ring[k]; x, y = xs[i], ys[j]; x *= 0.95; y *= 0.95; ptsw.append((cx + x, cy + y, top(x, y) + 0.12))
    w.tube(ptsw, 0.14, 6, closed=True)
    wo = w.finish('STOOL_Seat_Welt', 'FURN_Stool', [material('M_Leather_Stitch', '#3A3A38', 0.6)], smooth=True)
    return ob


def echo_dot(x=11.0, y=24.0, z=80.0):
    """Amazon Echo Dot (photos 27/36): 10 cm fabric sphere, flat base."""
    remove('PROP_Echo_Dot')
    fab = material('M_Echo_Fabric', '#2A2B2E', 0.9, **{'Sheen Weight': 0.6})
    nt = fab.node_tree; p = bsdf(fab)
    v = uv_vec(nt, 0.12, x=-1500, y=-400, coord='Object')
    t = tex(nt, os.path.join(TEX, 'rough_linen', 'rough_linen_nor_gl_2k.jpg'), v, -1200, -400, color=False)
    nm = node(nt, 'ShaderNodeNormalMap', -900, -400); nm.inputs['Strength'].default_value = 1.2
    nt.links.new(t.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], p.inputs['Normal'])
    g = Geo(); r = 5.0; prof = []
    for k in range(25):
        a = -math.pi / 2 + math.pi * k / 24; zz = r * math.sin(a); rr = r * math.cos(a)
        if zz < -r + 1.1: continue
        prof.append((rr, z + r - 1.1 + zz))
    prof = [(0, z)] + prof + [(0, z + 2 * r - 1.1)]
    g.revolve((x, y), prof, n=48)
    ob = g.finish('PROP_Echo_Dot', 'PROPS_Lived_In', [fab], smooth=True); ob['dim_source'] = 'SPEC'; ob['note'] = 'Echo Dot 4th gen, 100 x 89 mm'
    return ob


def desk_lamp_asset(clamp_xyz, yaw_deg):
    """Poly Haven 'desk_lamp_arm_01' (CC0): clamp swing-arm lamp like yours, re-finished in black. Replaces the stand-in."""
    for n in ('PROP_Desk_Lamp', 'PROP_Desk_Lamp_Shade', 'PROP_Desk_Lamp_Bulb'):
        ob = bpy.data.objects.get(n)
        if ob: ob.hide_render = True; ob.hide_viewport = True
    if bpy.data.collections.get('PROP_Desk_Lamp_PH'): return bpy.data.collections['PROP_Desk_Lamp_PH']
    path = os.path.join(TEX, 'desk_lamp_arm_01', 'desk_lamp_arm_01_2k.blend')
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects]
    c = coll('PROP_Desk_Lamp_PH', 'PROPS_Lived_In') if bpy.data.collections.get('PROPS_Lived_In') else coll('PROP_Desk_Lamp_PH')
    root = bpy.data.objects.new('LAMP_PH_Root', None); c.objects.link(root)
    for ob in dst.objects:
        if ob is None: continue
        c.objects.link(ob)
        if ob.name.startswith('wdg_'): ob.hide_render = True; ob.hide_viewport = True
        if ob.parent is None: ob.parent = root
    root.location = Vector(clamp_xyz) * S; root.rotation_euler = (0, 0, math.radians(yaw_deg))
    for n in ('geo_middle_wire', 'geo_top_wire', 'cur_middle_wire', 'cur_top_wire'):   # hooked wires break when re-parented
        o = bpy.data.objects.get(n)
        if o: o.hide_render = True; o.hide_viewport = True
    # black satin powder coat instead of the orange paint: saturated (painted) texels go black and non-metallic,
    # grey bare metal (springs, screws) keeps its look; the bulb area of the head gets a controllable warm glow
    for m in {s_.material for ob in dst.objects if ob and ob.type == 'MESH' for s_ in ob.material_slots if s_.material}:
        if not m.name.startswith('desk_lamp_arm_01') or m.get('pr5'): continue
        nt_ = m.node_tree; p = bsdf(m)
        dif = p.inputs['Base Color'].links[0].from_socket
        hsv = node(nt_, 'ShaderNodeSeparateColor', -300, 650); hsv.mode = 'HSV'; nt_.links.new(dif, hsv.inputs['Color'])
        paint = maprange(nt_, hsv.outputs['Green'], 0.28, 0.5, 0.0, 1.0, -100, 650)
        mx = node(nt_, 'ShaderNodeMix', 100, 500, data_type='RGBA'); nt_.links.new(paint, sock(mx, 'Factor_Float'))
        nt_.links.new(dif, sock(mx, 'A_Color')); sock(mx, 'B_Color').default_value = (0.018, 0.018, 0.019, 1)
        nt_.links.new(sock(mx, 'Result_Color', True), p.inputs['Base Color'])
        for inp, val in (('Metallic', 0.0), ('Roughness', 0.42)):
            src_ = p.inputs[inp].links[0].from_socket
            mm = node(nt_, 'ShaderNodeMix', 100, 200 if inp == 'Metallic' else 0, data_type='FLOAT')
            nt_.links.new(paint, sock(mm, 'Factor_Float')); nt_.links.new(src_, sock(mm, 'A_Float')); sock(mm, 'B_Float').default_value = val
            nt_.links.new(sock(mm, 'Result_Float', True), p.inputs[inp])
        if p.inputs['Emission Strength'].is_linked:          # the head's bulb mask
            g_ = node(nt_, 'ShaderNodeMath', 100, -300, operation='MULTIPLY'); g_.name = g_.label = 'LAMP_GLOW'; g_.inputs[1].default_value = 0.0
            nt_.links.new(p.inputs['Emission Strength'].links[0].from_socket, g_.inputs[0]); nt_.links.new(g_.outputs[0], p.inputs['Emission Strength'])
            p.inputs['Emission Color'].default_value = (1.0, 0.74, 0.45, 1)
        m['pr5'] = 1
    return c


# ============================================================================ outside the window
def window_exterior():
    """Outside: a white concrete ledge with your potted plant, the safety net, the floor-above slab, and the next tower
    (bearing 216 deg, ~75 m, user coordinates; its height is assumed similar to yours)."""
    c = 'EXT_Outside'; coll(c)
    for n in ('EXT_Ledge', 'EXT_Slab_Above', 'EXT_Net', 'EXT_Next_Tower'): remove(n)
    conc = material('M_Ext_Concrete', '#D9D6CF', 0.85)
    g = Geo(); g.box(80, 260, -82, -20, 84, 92)
    g.box(80, 82, -82, -20, 92, 320).box(258, 260, -82, -20, 92, 320)          # side cheeks of the niche
    g.finish('EXT_Ledge', c, [conc], bevel=(0.3, 1))['dim_source'] = 'EST'
    Geo().box(80, 260, -82, -20, 320, 335).finish('EXT_Slab_Above', c, [conc])['dim_source'] = 'EST'   # next floor's planter box
    # safety net: white nylon, ~5 cm diamond mesh, 2.5 mm strands (procedural, mostly transparent)
    net = bpy.data.materials.get('M_Safety_Net')
    if not net:
        net = bpy.data.materials.new('M_Safety_Net'); net.use_nodes = True; nt = net.node_tree; p = bsdf(net)
        p.inputs['Base Color'].default_value = (*lin('#E8E6E0'), 1); p.inputs['Roughness'].default_value = 0.6
        o = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
        tc = node(nt, 'ShaderNodeTexCoord', -1200, 0); sep = node(nt, 'ShaderNodeSeparateXYZ', -1000, 0); nt.links.new(tc.outputs['Object'], sep.inputs[0])
        masks = []
        for k, (a, b) in enumerate(((1, 1), (1, -1))):
            m1 = node(nt, 'ShaderNodeMath', -800, 200 - 250 * k, operation='MULTIPLY'); m1.inputs[1].default_value = a * 14.14
            m2 = node(nt, 'ShaderNodeMath', -800, 100 - 250 * k, operation='MULTIPLY'); m2.inputs[1].default_value = b * 14.14
            nt.links.new(sep.outputs['X'], m1.inputs[0]); nt.links.new(sep.outputs['Z'], m2.inputs[0])
            ad = node(nt, 'ShaderNodeMath', -620, 150 - 250 * k, operation='ADD'); nt.links.new(m1.outputs[0], ad.inputs[0]); nt.links.new(m2.outputs[0], ad.inputs[1])
            fr = node(nt, 'ShaderNodeMath', -460, 150 - 250 * k, operation='FRACT'); nt.links.new(ad.outputs[0], fr.inputs[0])
            lt_ = node(nt, 'ShaderNodeMath', -300, 150 - 250 * k, operation='LESS_THAN'); lt_.inputs[1].default_value = 0.05
            nt.links.new(fr.outputs[0], lt_.inputs[0]); masks.append(lt_)
        mx_ = node(nt, 'ShaderNodeMath', -150, 50, operation='MAXIMUM'); nt.links.new(masks[0].outputs[0], mx_.inputs[0]); nt.links.new(masks[1].outputs[0], mx_.inputs[1])
        trn = node(nt, 'ShaderNodeBsdfTransparent', -150, -150); ms = node(nt, 'ShaderNodeMixShader', 100, 0)
        nt.links.new(mx_.outputs[0], ms.inputs['Fac']); nt.links.new(trn.outputs[0], ms.inputs[1]); nt.links.new(p.outputs[0], ms.inputs[2])
        nt.links.new(ms.outputs[0], o.inputs['Surface'])
    bm = bmesh.new(); vs = [bm.verts.new(Vector(q) * S) for q in [(82, -80, 92), (258, -80, 92), (258, -80, 270), (82, -80, 270)]]
    bm.faces.new(vs); me = bpy.data.meshes.new('EXT_Net'); bm.to_mesh(me); bm.free(); me.materials.append(net)
    ob = bpy.data.objects.new('EXT_Net', me); coll(c).objects.link(ob); ob['dim_source'] = 'PHOTO'
    # the next tower: 25 x 15 m, ground 55 m below the floor (high-rise flat), roof ~9 m above it
    d = Vector((math.cos(math.radians(170 - 216.0)), math.sin(math.radians(170 - 216.0)), 0)); ctr = d * 7500.0
    tw = Geo(); n_ = Vector((-d.y, d.x, 0)); hw, hd = 1250.0, 750.0
    pts = [(-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd)]
    tw.prism((ctr.x, ctr.y, 0), n_, -d, (0, 0, 1), pts, -5500.0, 900.0)
    to = tw.finish('EXT_Next_Tower', c, [tower_material()]); to['dim_source'] = 'USER/EST'
    to['note'] = 'next tower at the user\'s coordinates (~75 m, bearing 216 deg); size/height EST'
    return ob


def tower_material():
    m = bpy.data.materials.get('M_Tower_Facade')
    if m: return m
    m = material('M_Tower_Facade', '#CFCBC2', 0.7); nt = m.node_tree; p = bsdf(m); L = nt.links
    geo = node(nt, 'ShaderNodeNewGeometry', -1500, 0)
    # windows: 1.4 m wide every 3.5 m along the facade, 1.5 m tall every 2.9 m floor; local facade coordinate from position
    sep = node(nt, 'ShaderNodeSeparateXYZ', -1300, 0); L.new(geo.outputs['Position'], sep.inputs[0])
    hor = node(nt, 'ShaderNodeMath', -1100, 100, operation='ADD'); L.new(sep.outputs['X'], hor.inputs[0]); L.new(sep.outputs['Y'], hor.inputs[1])
    def cell(val, period, width, x, y):
        a = node(nt, 'ShaderNodeMath', x, y, operation='DIVIDE'); a.inputs[1].default_value = period; L.new(val, a.inputs[0])
        f = node(nt, 'ShaderNodeMath', x + 150, y, operation='FRACT'); L.new(a.outputs[0], f.inputs[0])
        l = node(nt, 'ShaderNodeMath', x + 300, y, operation='LESS_THAN'); l.inputs[1].default_value = width / period; L.new(f.outputs[0], l.inputs[0])
        fl = node(nt, 'ShaderNodeMath', x + 150, y - 120, operation='FLOOR'); L.new(a.outputs[0], fl.inputs[0])
        return l.outputs[0], fl.outputs[0]
    wx, ix = cell(hor.outputs[0], 3.5, 1.4, -900, 200); wz, iz = cell(sep.outputs['Z'], 2.9, 1.5, -900, -100)
    win = node(nt, 'ShaderNodeMath', -450, 100, operation='MULTIPLY'); L.new(wx, win.inputs[0]); L.new(wz, win.inputs[1])
    cid = node(nt, 'ShaderNodeCombineXYZ', -450, -150); L.new(ix, cid.inputs['X']); L.new(iz, cid.inputs['Y'])
    rnd = node(nt, 'ShaderNodeTexWhiteNoise', -300, -150, noise_dimensions='3D'); L.new(cid.outputs[0], rnd.inputs['Vector'])
    lit = node(nt, 'ShaderNodeMath', -150, -150, operation='LESS_THAN'); lit.inputs[1].default_value = 0.38; L.new(rnd.outputs['Value'], lit.inputs[0])
    nite = node(nt, 'ShaderNodeValue', -300, -350); nite.name = nite.label = 'NIGHT'; nite.outputs[0].default_value = 0.0
    e1 = node(nt, 'ShaderNodeMath', 0, -150, operation='MULTIPLY'); L.new(win.outputs[0], e1.inputs[0]); L.new(lit.outputs[0], e1.inputs[1])
    e2 = node(nt, 'ShaderNodeMath', 150, -150, operation='MULTIPLY'); L.new(e1.outputs[0], e2.inputs[0]); L.new(nite.outputs[0], e2.inputs[1])
    warm = node(nt, 'ShaderNodeMix', 150, -400, data_type='RGBA'); sock(warm, 'A_Color').default_value = (1.0, 0.62, 0.32, 1); sock(warm, 'B_Color').default_value = (0.75, 0.85, 1.0, 1)
    L.new(rnd.outputs['Color'], sock(warm, 'Factor_Float'))
    L.new(sock(warm, 'Result_Color', True), p.inputs['Emission Color']); L.new(e2.outputs[0], p.inputs['Emission Strength'])
    col = node(nt, 'ShaderNodeMix', 0, 300, data_type='RGBA'); sock(col, 'A_Color').default_value = (*lin('#CFCBC2'), 1); sock(col, 'B_Color').default_value = (*lin('#2A3036'), 1)
    L.new(win.outputs[0], sock(col, 'Factor_Float')); L.new(sock(col, 'Result_Color', True), p.inputs['Base Color'])
    rr = node(nt, 'ShaderNodeMapRange', 0, 0); rr.inputs['To Min'].default_value, rr.inputs['To Max'].default_value = 0.75, 0.08
    L.new(win.outputs[0], rr.inputs['Value']); L.new(rr.outputs['Result'], p.inputs['Roughness'])
    return m


def plant_outside(x=150.0, y=-48.0, z=92.0, height=62.0):
    """Stand-in for your tomato plant in a black pot on the ledge (Poly Haven potted_plant_02, CC0, re-potted in black)."""
    if bpy.data.collections.get('EXT_Plant'): return
    path = os.path.join(TEX, 'potted_plant_02', 'potted_plant_02_2k.blend')
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects]
    c = coll('EXT_Plant', 'EXT_Outside'); root = bpy.data.objects.new('EXT_Plant_Root', None); c.objects.link(root)
    for ob in dst.objects:
        c.objects.link(ob); ob.parent = root
    k = height / 84.1; root.scale = (k * 0.8, k * 0.8, k); root.location = Vector((x, y, z)) * S
    pot = bpy.data.materials.get('potted_plant_02_pot')
    if pot:
        p = bsdf(pot)
        if p.inputs['Base Color'].is_linked:
            hsv = node(pot.node_tree, 'ShaderNodeHueSaturation', -200, 400); hsv.inputs['Saturation'].default_value = 0.0; hsv.inputs['Value'].default_value = 0.12
            pot.node_tree.links.new(p.inputs['Base Color'].links[0].from_socket, hsv.inputs['Color']); pot.node_tree.links.new(hsv.outputs['Color'], p.inputs['Base Color'])


# ============================================================================ sky, sun, worlds
SUN = json.load(open(os.path.join(HERE, 'sun_positions.json')))


def sun_at(day, hhmm):
    for r in SUN['days'][day]['samples']:
        if r['time'] == hhmm: return r
    raise KeyError(hhmm)


def ensure_worlds():
    """WORLD_Daylight (existing: overcast / sunny HDRIs), WORLD_Dusk (blue hour EXR), WORLD_Night (same sky, ~1/30)."""
    if not bpy.data.worlds.get('WORLD_Dusk') or not bpy.data.worlds.get('WORLD_Night'):
        for name, strength in (('WORLD_Dusk', 0.6), ('WORLD_Night', 0.02)):
            if bpy.data.worlds.get(name): continue
            w = bpy.data.worlds.new(name); w.use_nodes = True; nt = w.node_tree
            for n in list(nt.nodes):
                if n.type != 'OUTPUT_WORLD': nt.nodes.remove(n)
            out = next(n for n in nt.nodes if n.type == 'OUTPUT_WORLD')
            tc = node(nt, 'ShaderNodeTexCoord', -800, 0); mp = node(nt, 'ShaderNodeMapping', -600, 0); mp.inputs['Rotation'].default_value = (0, 0, math.radians(-36.0))
            env = node(nt, 'ShaderNodeTexEnvironment', -350, 0); env.image = image(os.path.join(TEX, 'dusk_from_homecoming_center_rooftop.exr'))
            bg = node(nt, 'ShaderNodeBackground', 0, 0); bg.inputs['Strength'].default_value = strength; bg.name = bg.label = 'SKY_STRENGTH'
            for a, b in [(tc.outputs['Generated'], mp.inputs['Vector']), (mp.outputs['Vector'], env.inputs['Vector']),
                         (env.outputs['Color'], bg.inputs['Color']), (bg.outputs[0], out.inputs['Surface'])]:
                nt.links.new(a, b)
            w.use_fake_user = True
    w = bpy.data.worlds.get('WORLD_Daylight')
    if w:
        w.use_fake_user = True; nt = w.node_tree
        if not nt.nodes.get('SKY_TINT'):
            ss = next((n for n in nt.nodes if n.label == 'Sunny sky brightness'), None)
            if ss:
                tint = node(nt, 'ShaderNodeVectorMath', ss.location.x + 80, ss.location.y - 200, operation='MULTIPLY'); tint.name = tint.label = 'SKY_TINT'
                tint.inputs[1].default_value = (1, 1, 1)
                dst = [l.to_socket for l in ss.outputs['Vector'].links]
                nt.links.new(ss.outputs['Vector'], tint.inputs[0])
                for d_ in dst: nt.links.new(tint.outputs['Vector'], d_)
    sun = bpy.data.objects.get('LIGHT_Sun_Afternoon')
    if sun and sun.data.animation_data: sun.data.animation_data_clear()


def set_sun(day=None, hhmm=None, kelvin=5200.0, strength=29.4):
    """Physically placed sun for your location (sun_study.py) or off."""
    ob = bpy.data.objects.get('LIGHT_Sun_Afternoon')
    if not ob: return
    if day is None: ob.data.energy = 0.0; ob.hide_render = True; return
    r = sun_at(day, hhmm); d = Vector(r['vec'])
    ob.hide_render = False; ob.data.energy = strength; ob.data.use_temperature = True; ob.data.temperature = kelvin
    ob.data.angle = math.radians(0.53)
    ob.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    return r


def set_world(name, sunny=0, sky_scale=1.0, tint=(1, 1, 1), strength=None):
    w = bpy.data.worlds[name]; sc.world = w
    if name == 'WORLD_Daylight':
        sc['sunny'] = sunny; nt = w.node_tree
        ss = next((n for n in nt.nodes if n.label == 'Sunny sky brightness'), None)
        if ss: ss.inputs['Scale'].default_value = 8.0 * sky_scale
        t = nt.nodes.get('SKY_TINT')
        if t: t.inputs[1].default_value = tint
        for fc in (nt.animation_data.drivers if nt.animation_data else []):
            fc.driver.expression = fc.driver.expression          # touch -> re-evaluate
    elif strength is not None:
        bg = next(n for n in w.node_tree.nodes if n.bl_idname == 'ShaderNodeBackground')
        bg.inputs['Strength'].default_value = strength
    sc.update_tag(); bpy.context.view_layer.update()


def set_tower_night(v):
    m = bpy.data.materials.get('M_Tower_Facade')
    if m: m.node_tree.nodes['NIGHT'].outputs[0].default_value = v


# ============================================================================ cameras
def cam(name, loc, target, lens, fstop=8.0, level=True, shift=None, focus=None):
    """level=True: architectural camera (no tilt; framing via shift so verticals stay vertical)."""
    remove(name); c = bpy.data.cameras.new(name); c.lens = lens; c.sensor_width = 36.0; c.sensor_fit = 'HORIZONTAL'
    c.clip_start = 0.03; c.clip_end = 300.0
    ob = bpy.data.objects.new(name, c); coll('CAM_Photoreal', 'CAM_Cameras' if bpy.data.collections.get('CAM_Cameras') else None).objects.link(ob)
    L, T = Vector(loc), Vector(target); ob.location = L * S
    v = T - L
    if level:
        h = Vector((v.x, v.y, 0)).normalized(); ob.rotation_euler = h.to_track_quat('-Z', 'Y').to_euler()
        if shift is None:            # shift so the target sits where a tilted camera would have put it
            dist = Vector((v.x, v.y)).length; fov_h = 2 * math.atan(18.0 / lens)
            shift = (v.z / dist) / (2 * math.tan(fov_h / 2))
        c.shift_y = shift
    else:
        ob.rotation_euler = v.to_track_quat('-Z', 'Y').to_euler()
    c.dof.use_dof = True; c.dof.aperture_fstop = fstop; c.dof.focus_distance = (focus if focus else v.length) * S
    ob['eye_cm'] = loc[2]
    return ob


def desk_lamp_pose(head_delta_cm=(0.0, 0.0, 0.0)):
    """Move the Poly Haven lamp's head IK control (world-space delta, cm) and return the head's world bbox (cm)."""
    rig = bpy.data.objects.get('rig_lamp')
    if rig and any(head_delta_cm):
        pb = rig.pose.bones.get('ctrl_top-position')
        if pb:
            d = rig.matrix_world.to_3x3().inverted() @ (Vector(head_delta_cm) * S)
            pb.matrix = Matrix.Translation(d) @ pb.matrix
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get(); head = bpy.data.objects.get('geo_lamp-head')
    e = head.evaluated_get(dg); me = e.to_mesh(); pts = [head.matrix_world @ v.co for v in me.vertices]; e.to_mesh_clear()
    lo = Vector([min(p[i] for p in pts) for i in range(3)]) / S; hi = Vector([max(p[i] for p in pts) for i in range(3)]) / S
    return lo, hi


def piano_and_pillows():
    m = bpy.data.materials.get('M_Piano_Top')
    if m:
        p = bsdf(m); p.inputs['Base Color'].default_value = (*lin('#B9B7B0'), 1); p.inputs['Metallic'].default_value = 0.75
        p.inputs['Roughness'].default_value = 0.32
    m = bpy.data.materials.get('M_Pillow_Print')
    if m and not m.get('pr5'):
        nt = m.node_tree; p = bsdf(m)
        tc = node(nt, 'ShaderNodeTexCoord', -1700, 300); mp = node(nt, 'ShaderNodeMapping', -1500, 300)
        mp.inputs['Scale'].default_value = (1 / 2.4, 1 / 1.5, 1); mp.inputs['Location'].default_value = (0.1, 0.2, 0)
        nt.links.new(tc.outputs['UV'], mp.inputs['Vector'])
        t = tex(nt, os.path.join(PH, 'bedspread.png'), mp.outputs['Vector'], -1250, 300); nt.links.new(t.outputs['Color'], p.inputs['Base Color'])
        p.inputs['Sheen Weight'].default_value = 0.35; m['pr5'] = 1


def desk_lamp_light(light_name='LIGHT_Desk_Lamp', energy=40.0):
    """Spot from the lamp's real bulb (faces of the 'light' material on the head), aimed out of the shade mouth."""
    head = bpy.data.objects.get('geo_lamp-head'); piv = bpy.data.objects.get('geo_top-pivot'); lt = bpy.data.objects.get(light_name)
    if not (head and piv and lt): return
    dg = bpy.context.evaluated_depsgraph_get()
    e = head.evaluated_get(dg); me = e.to_mesh()
    li = next((i for i, s_ in enumerate(head.material_slots) if s_.material and 'light' in s_.material.name), 1)
    pts = [head.matrix_world @ me.vertices[v].co for p_ in me.polygons if p_.material_index == li for v in p_.vertices]
    allp = [head.matrix_world @ v.co for v in me.vertices]; e.to_mesh_clear()
    bulb = sum(pts, Vector()) / max(len(pts), 1) if pts else sum(allp, Vector()) / len(allp)
    ep = piv.evaluated_get(dg); m2 = ep.to_mesh(); pc = sum((piv.matrix_world @ v.co for v in m2.vertices), Vector()) / len(m2.vertices); ep.to_mesh_clear()
    d = (Vector((bulb.x - 0.04, bulb.y + 0.06, 0.80)) - bulb).normalized()     # down onto the desk, like your lamp (photos 27/34)
    lt.location = bulb + d * 0.01; lt.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    if lt.data.animation_data: lt.data.animation_data_clear()
    lt.data.energy = energy; lt.data.spot_size = math.radians(100); lt.data.spot_blend = 0.5; lt.data.shadow_soft_size = 0.015
    return bulb, d


def macbook_screen(on=True):
    """Lit MacBook screen with your actual screen from photo 08 (code editor, dark theme): emissive, under glossy glass."""
    o = bpy.data.objects.get('PROP_MacBook_Air_13_M4')
    m = bpy.data.materials.get('M_MBA_Screen_Glass')
    if not (o and m): return
    me = o.data; si = next(i for i, s_ in enumerate(o.material_slots) if s_.material == m)
    faces = [p for p in me.polygons if p.material_index == si]
    big = max(faces, key=lambda p: p.area); n = big.normal
    # screen plane axes: u along the hinge (world y), v up the lid
    vs = [me.vertices[i].co for p in faces if p.normal.dot(n) > 0.95 for i in p.vertices]
    if not vs: return
    U = Vector((0, 1, 0)); Vv = n.cross(U).normalized()
    if Vv.z < 0: Vv = -Vv
    us = [v.dot(U) for v in vs]; ws = [v.dot(Vv) for v in vs]
    uv = me.uv_layers[0].data
    for p in faces:
        if p.normal.dot(n) <= 0.95: continue
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            u = (co.dot(U) - min(us)) / (max(us) - min(us)); w = (co.dot(Vv) - min(ws)) / (max(ws) - min(ws))
            uv[li].uv = (1 - u, w)          # seen from the user's side (-x), +y runs right-to-left
    nt = m.node_tree; p = bsdf(m)
    if not nt.nodes.get('SCREEN_IMG'):
        t = tex(nt, os.path.join(PH, 'macbook_screen.png'), None, -600, 200); t.name = 'SCREEN_IMG'
        # 6% bezel border is black glass
        tc = node(nt, 'ShaderNodeTexCoord', -1100, 0); sep = node(nt, 'ShaderNodeSeparateXYZ', -900, 0); nt.links.new(tc.outputs['UV'], sep.inputs[0])
        mp = node(nt, 'ShaderNodeMapping', -800, 300); mp.inputs['Location'].default_value = (-0.035, -0.045, 0); mp.inputs['Scale'].default_value = (1 / 0.93, 1 / 0.91, 1)
        nt.links.new(tc.outputs['UV'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], t.inputs['Vector']); t.extension = 'CLIP'
        p.inputs['Base Color'].default_value = (0.004, 0.004, 0.005, 1); p.inputs['Roughness'].default_value = 0.03
        nt.links.new(t.outputs['Color'], p.inputs['Emission Color'])
        v = node(nt, 'ShaderNodeValue', -600, -200); v.name = v.label = 'SCREEN_ON'; v.outputs[0].default_value = 1.0
        nt.links.new(v.outputs[0], p.inputs['Emission Strength'])
    nt.nodes['SCREEN_ON'].outputs[0].default_value = 4.0 if on else 0.0


def bed_imperfections():
    """Your bed as it really looks (photos 32/35/50): crinkled microfibre bedspread (fine creases + quilting dips),
    grey jersey fitted sheet on the mattress sides, a slight dip where you sleep."""
    m = bpy.data.materials.get('M_Bedspread')
    if m and not m.get('pr5_crinkle'):
        nt = m.node_tree; p = bsdf(m); L = nt.links
        tc = node(nt, 'ShaderNodeTexCoord', -2300, -1400)
        # creases: distance-to-edge of a stretched, distorted Voronoi = sharp fold lines a few cm apart
        mp = node(nt, 'ShaderNodeMapping', -2100, -1400); mp.inputs['Scale'].default_value = (1.0, 2.2, 1.0)
        L.new(tc.outputs['UV'], mp.inputs['Vector'])
        nz = node(nt, 'ShaderNodeTexNoise', -1900, -1600); nz.inputs['Scale'].default_value = 6.0; nz.inputs['Detail'].default_value = 3.0
        L.new(mp.outputs['Vector'], nz.inputs['Vector'])
        mix = node(nt, 'ShaderNodeMix', -1700, -1400, data_type='VECTOR'); sock(mix, 'Factor_Float').default_value = 0.08
        L.new(mp.outputs['Vector'], sock(mix, 'A_Vector')); L.new(nz.outputs['Color'], sock(mix, 'B_Vector'))
        vo = node(nt, 'ShaderNodeTexVoronoi', -1500, -1400); vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs['Scale'].default_value = 22.0
        L.new(sock(mix, 'Result_Vector', True), vo.inputs['Vector'])
        crease = maprange(nt, vo.outputs['Distance'], 0.0, 0.06, 0.0, 1.0, -1300, -1400)
        # quilting: wavy stitch channels ~35 cm apart across the bed (photo 50)
        sep = node(nt, 'ShaderNodeSeparateXYZ', -1900, -1900); L.new(tc.outputs['UV'], sep.inputs[0])
        wv = node(nt, 'ShaderNodeTexWave', -1700, -1900, wave_type='BANDS', bands_direction='X', wave_profile='SAW')
        wv.inputs['Scale'].default_value = 2.85; wv.inputs['Distortion'].default_value = 1.2; wv.inputs['Detail Scale'].default_value = 0.6
        L.new(tc.outputs['UV'], wv.inputs['Vector'])
        quilt = maprange(nt, wv.outputs['Factor'], 0.0, 0.08, 0.0, 1.0, -1500, -1900)
        h = node(nt, 'ShaderNodeMath', -1100, -1600, operation='MULTIPLY'); L.new(crease, h.inputs[0]); L.new(quilt, h.inputs[1])
        add_bump(nt, p, h.outputs[0], 0.22, 0.004, -600, -1600)
        add_rough(nt, p, maprange(nt, crease, 0, 1, 0.08, 0.0, -1100, -1850), 1.0, -400, -1850)   # folds catch a little sheen
        m['pr5_crinkle'] = 1
    mt = bpy.data.materials.get('M_Mattress')
    if mt and not mt.get('pr5'):
        nt = mt.node_tree; p = bsdf(mt)
        p.inputs['Base Color'].default_value = (*lin('#8E9196'), 1); p.inputs['Roughness'].default_value = 0.9
        p.inputs['Sheen Weight'].default_value = 0.4
        v = uv_vec(nt, 0.26, x=-1500, y=-400)
        t = tex(nt, os.path.join(TEX, 'cotton_jersey', 'cotton_jersey_nor_gl_2k.jpg'), v, -1200, -400, color=False)
        nm = node(nt, 'ShaderNodeNormalMap', -900, -400); nm.inputs['Strength'].default_value = 0.8
        nt.links.new(t.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], p.inputs['Normal'])
        mt['pr5'] = 1
    # where you sleep: the bedspread sits ~1.5 cm lower in a soft dip (hip area), as on a used mattress
    sp = bpy.data.objects.get('BED_Bedspread')
    if sp and not sp.get('pr5_dip'):
        mw = sp.matrix_world; inv = mw.inverted()
        for v in sp.data.vertices:
            w = mw @ v.co; x, y = w.x / S, w.y / S
            if 110 < x < 298 and 0 < y < 96 and w.z / S > 50:
                d = math.exp(-((x - 215) / 38) ** 2 - ((y - 50) / 26) ** 2)
                w.z -= 1.5 * d * S; v.co = inv @ w
        sp.data.update(); sp['pr5_dip'] = 1
