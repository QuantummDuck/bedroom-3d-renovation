"""
Teak & navy, round 4 - cozy lighting plan, on top of Bedroom_Teak_Navy_v3.blend.
Warm light is the base; every LED group has its own colour and brightness; the desk lamp stays warm white (3000 K).
Lighting layers (each a group in Scene > Custom Properties: <Group>_RGB colour picker + <Group>_Brightness; LED_Master = all):
  Cove      ceiling cove: LED on a slim white ledge just under the crown molding, washing crown + ceiling (base light)
  Shelves   under the back edge of each shelf, washing the teak boards
  Piano     back of the piano, halo on the wall
  BedPanel  top edge of the teak panel around the bed, halo on the navy wall
  Puzzle    behind the puzzle frame (frame on 2 cm stand-offs): halo around it
  Desk      under the back edge of the desk: glow on the boards and floor below
  Wardrobe  wardrobe plinth: glow on the floor in front of it ('floating' wardrobe)
  Fairy     copper-wire micro LEDs in swags above the window
  Sconce    plug-in brass reading sconce with a linen drum shade above the bed head
Saves Bedroom_Teak_Navy_v4.blend; renders into renders_v4/.

  Blender -b Bedroom_Teak_Navy_v3.blend --python teak_navy_v4.py -- [set=test|views|all|none] [spp=..] [scale=..] [expo=..] [cams=..]
"""
import bpy, bmesh, json, math, os, sys
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
OPT = dict(a.split('=', 1) for a in (sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []))
SET = OPT.get('set', 'all'); OUT = os.path.join(HERE, 'renders_v4'); S = 0.01
sc = bpy.context.scene
FRONT = bpy.data.objects['DESK_Desk'].location.x * 100 - 24.5
EXPOSURE = float(OPT.get('expo', -2.0))

# group: label, colour (sRGB hex ~ black-body), brightness scale, physical spec for the shopping list
GROUPS = {
    'Cove':     ('Ceiling cove (base light)', '#FFA957', 10.0, '2700 K'),
    'Shelves':  ('Shelf wall-wash',           '#FFB46B', 30.0, '3000 K'),
    'Piano':    ('Piano halo',                '#FF8912', 70.0, '2000 K amber'),
    'BedPanel': ('Bed panel halo',            '#FF7E86', 45.0, 'dusty rose'),
    'Puzzle':   ('Puzzle backlight',          '#FF6A2B', 35.0, 'sunset orange'),
    'Desk':     ('Under-desk glow',           '#FF932C', 20.0, '2200 K'),
    'Wardrobe': ('Wardrobe plinth glow',      '#FF9D3F', 15.0, '2400 K'),
    'Fairy':    ('Fairy lights',              '#FF8912', 1.0, '2000 K candle'),
    'Sconce':   ('Reading sconce',            '#FF9D3F', 1.0, '2400 K'),
}


def lin(h):
    return tuple((v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)])


def material(name, hexc, rough, metal=0.0, **extra):
    m = bpy.data.materials.get(name)
    if m: bpy.data.materials.remove(m)
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*lin(hexc), 1); p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    for k, v in extra.items(): p.inputs[k].default_value = v
    m.diffuse_color = (*lin(hexc), 1)
    return m


def remove(name):
    ob = bpy.data.objects.get(name)
    if ob: bpy.data.objects.remove(ob)


def drive(idblock, path, expr, props, index=-1):
    """props: list of (variable name, scene property, array index or None)."""
    fc = idblock.driver_add(path, index) if index >= 0 else idblock.driver_add(path)
    d = fc.driver; d.type = 'SCRIPTED'
    for vname, prop, pidx in props:
        v = d.variables.new(); v.name = vname; v.type = 'SINGLE_PROP'; v.targets[0].id_type = 'SCENE'; v.targets[0].id = sc
        v.targets[0].data_path = f'["{prop}"]' + (f'[{pidx}]' if pidx is not None else '')
    d.expression = expr


class Mesh:
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
        return self.prism(((x0 + x1) / 2, (y0 + y1) / 2, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1),
                          [(-(x1 - x0) / 2, -(y1 - y0) / 2), ((x1 - x0) / 2, -(y1 - y0) / 2), ((x1 - x0) / 2, (y1 - y0) / 2),
                           (-(x1 - x0) / 2, (y1 - y0) / 2)], z0, z1, mi)

    def cyl(self, p0, p1, r, n=24, mi=0, caps=True):
        p0, p1 = Vector(p0), Vector(p1); a = (p1 - p0).normalized(); u = a.orthogonal().normalized(); w = a.cross(u)
        return self.prism(p0, u, w, a, [(r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n)) for k in range(n)],
                          0, (p1 - p0).length, mi, caps)

    def sphere(self, c, r, mi=0, seg=8):
        res = bmesh.ops.create_uvsphere(self.bm, u_segments=seg, v_segments=max(4, seg // 2), radius=r * S)
        bmesh.ops.translate(self.bm, verts=res['verts'], vec=Vector(c) * S)
        for f in {f for v in res['verts'] for f in v.link_faces}: f.material_index = mi
        return self

    def finish(self, name, coll, mats, smooth=False, bevel=None):
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces[:])
        uv = self.bm.loops.layers.uv.new('UVMap')
        for f in self.bm.faces:
            ax = max(range(3), key=lambda i: abs(f.normal[i])); a, b = [i for i in range(3) if i != ax]
            for lp in f.loops: lp[uv].uv = (lp.vert.co[a], lp.vert.co[b])
        me = bpy.data.meshes.new(name); self.bm.to_mesh(me); self.bm.free()
        for m in mats: me.materials.append(m if isinstance(m, bpy.types.Material) else bpy.data.materials[m])
        if smooth:
            for p in me.polygons: p.use_smooth = True
        ob = bpy.data.objects.new(name, me); bpy.data.collections[coll].objects.link(ob)
        if bevel:
            md = ob.modifiers.new('Bevel', 'BEVEL'); md.width = bevel[0] * S; md.segments = bevel[1]; md.limit_method = 'ANGLE'
        return ob


def visible_only(ob):
    ob.visible_diffuse = False; ob.visible_shadow = False; ob.visible_transmission = False


# ================================================================ 0. clear the round-3 LED system, add the per-group controls
LC = bpy.data.collections['LIGHT_LED_Strips']
for o in list(LC.objects): bpy.data.objects.remove(o)
for n in ('M_LED_Shelf', 'M_LED_Piano'):
    if n in bpy.data.materials: bpy.data.materials.remove(bpy.data.materials[n])
for k in ('LED_RGB', 'LED_Brightness'):
    if k in sc: del sc[k]
sc['LED_Master'] = 1.0; sc.id_properties_ui('LED_Master').update(min=0.0, max=5.0, description='all LED lighting')
for key, (label, hexc, _, _) in GROUPS.items():
    sc[f'{key}_RGB'] = lin(hexc); sc.id_properties_ui(f'{key}_RGB').update(subtype='COLOR', min=0.0, max=1.0, description=label)
    sc[f'{key}_Brightness'] = 1.0; sc.id_properties_ui(f'{key}_Brightness').update(min=0.0, max=10.0, description=label)
alu = bpy.data.materials['M_Metal_Brushed']
GMAT = {}


def group_material(key, strength):
    """Emissive diffuser / bead material whose colour and strength follow the group's controls."""
    m = material(f'M_LED_{key}', '#F4F4F2', 0.35); nt = m.node_tree; p = nt.nodes['Principled BSDF']
    rgb = nt.nodes.new('ShaderNodeRGB'); rgb.name = rgb.label = 'GROUP_RGB'; rgb.location = (-300, 200)
    nt.links.new(rgb.outputs[0], p.inputs['Emission Color'])
    for i in range(3): drive(nt, 'nodes["GROUP_RGB"].outputs[0].default_value', 'var', [('var', f'{key}_RGB', i)], i)
    drive(nt, f'nodes["Principled BSDF"].inputs[{p.inputs.find("Emission Strength")}].default_value', f'var * m * {strength:.1f}',
          [('var', f'{key}_Brightness', None), ('m', 'LED_Master', None)])
    GMAT[key] = m
    return m


def group_light(key, name, kind, loc, rot, energy, **props):
    lt = bpy.data.lights.new(name, kind)
    for k, v in props.items(): setattr(lt, k, v)
    ob = bpy.data.objects.new(name, lt); LC.objects.link(ob); ob.location = Vector(loc) * S; ob.rotation_euler = rot
    for i in range(3): drive(lt, 'color', 'var', [('var', f'{key}_RGB', i)], i)
    drive(lt, 'energy', f'var * m * {energy:.2f}', [('var', f'{key}_Brightness', None), ('m', 'LED_Master', None)])
    ob['group'] = key; ob['note'] = GROUPS[key][0]
    return ob


def strip(key, name, p0, p1, normal, tilt_dir, tilt_deg, diff_mesh, chan_mesh, width=1.2, spread=130):
    """LED strip in a slim aluminium profile from p0 to p1 (cm), light leaving along `normal` tilted toward `tilt_dir`."""
    p0, p1, n, td = Vector(p0), Vector(p1), Vector(normal).normalized(), Vector(tilt_dir).normalized()
    a = (p1 - p0); L = a.length; a.normalize(); side = n.cross(a).normalized()
    c = (p0 + p1) / 2
    chan_mesh.prism(c, a, side, n, [(-L / 2, -width / 2 - 0.2), (L / 2, -width / 2 - 0.2), (L / 2, width / 2 + 0.2), (-L / 2, width / 2 + 0.2)], -0.7, 0.0)
    diff_mesh.prism(c, a, side, n, [(-L / 2 + 0.1, -width / 2), (L / 2 - 0.1, -width / 2), (L / 2 - 0.1, width / 2), (-L / 2 + 0.1, width / 2)], 0.0, 0.07)
    d = (n * math.cos(math.radians(tilt_deg)) + td * math.sin(math.radians(tilt_deg))).normalized()
    rot = Matrix((side, a, -d)).transposed().to_euler() if abs(side.cross(a).dot(-d)) > 0 else d.to_track_quat('-Z', 'Y').to_euler()
    ob = group_light(key, name, 'AREA', c + n * 0.12, (0, 0, 0), GROUPS[key][2] * L / 100, shape='RECTANGLE',
                     size=width * S, size_y=L * S, spread=math.radians(spread))
    q = (-d).to_track_quat('Z', 'Y')                                  # local -Z along d, local Y along the strip
    up = a - d * a.dot(d)
    ob.rotation_euler = Matrix((up.cross(-d).normalized() * -1, up.normalized(), -d)).transposed().to_euler() if up.length > 1e-6 else q.to_euler()
    return ob


# ================================================================ 1. strips: shelves, piano, cove, bed panel, desk, wardrobe
frames = (15.0, 68.0, 116.0, 161.0)
for key in ('Shelves', 'Piano', 'Cove', 'BedPanel', 'Desk', 'Wardrobe'): group_material(key, GROUPS[key][2] / 0.012)
for key in ('Shelves', 'Piano', 'Cove', 'BedPanel', 'Desk', 'Wardrobe'):
    ch, df = Mesh(), Mesh()
    if key == 'Shelves':
        for n, (y0, y1, zb) in enumerate([(4, 131, 142.0), (4, 171, 164.5), (4, 171, 187.5)]):
            strip(key, f'LED_Shelf_{n + 1}', (FRONT + 3.1, y0 + 0.5, zb), (FRONT + 3.1, y1 - 0.5, zb), (0, 0, -1), (-1, 0, 0), 20, df, ch)
    elif key == 'Piano':
        strip(key, 'LED_Piano_Halo', (297.15, 98.0, 87.2), (297.15, 223.5, 87.2), (0, 0, 1), (1, 0, 0), 40, df, ch, 1.1, 100)
    elif key == 'Cove':
        for n, (p0, p1, nrm) in enumerate([((5, 1.6, 246.0), (300, 1.6, 246.0), (0, 1, 0)), ((298.4, 5, 246.0), (298.4, 227, 246.0), (-1, 0, 0)),
                                           ((FRONT + 1.6, 5, 246.0), (FRONT + 1.6, 288, 246.0), (1, 0, 0)), ((FRONT + 5, 288.4, 246.0), (119, 288.4, 246.0), (0, -1, 0))]):
            strip(key, f'LED_Cove_{n + 1}', p0, p1, (0, 0, 1), nrm, 15, df, ch, 1.2, 120)
    elif key == 'BedPanel':
        strip(key, 'LED_BedPanel_W2', (106.0, 0.9, 87.5), (298.0, 0.9, 87.5), (0, 0, 1), (0, -1, 0), 25, df, ch, 1.1, 110)
        strip(key, 'LED_BedPanel_W3', (299.1, 3.0, 87.5), (299.1, 95.0, 87.5), (0, 0, 1), (1, 0, 0), 25, df, ch, 1.1, 110)
    elif key == 'Desk':
        strip(key, 'LED_Under_Desk', (FRONT + 3.2, 4.0, 77.0), (FRONT + 3.2, 162.0, 77.0), (0, 0, -1), (-1, 0, 0), 25, df, ch, 1.1, 120)
    elif key == 'Wardrobe':
        strip(key, 'LED_Wardrobe_Plinth', (121.0, 227.6, 8.6), (298.0, 227.6, 8.6), (0, -0.5, -1), (0, -1, 0), 10, df, ch, 1.0, 120)
    ch.finish(f'LED_Channels_{key}', 'LIGHT_LED_Strips', [alu])
    visible_only(df.finish(f'LED_Diffusers_{key}', 'LIGHT_LED_Strips', [GMAT[key]]))

# cove ledge (the physical 'sanca'): 5 cm deep plate 24 cm below the ceiling with a 2.5 cm lip that hides the strip
remove('ARCH_Cove_Ledge'); remove('ARCH_Curtain_Bracket_old')                 # the unused curtain bracket would sit on the ledge
lg = Mesh()
lg.box(FRONT, 300, 0, 5, 243, 246).box(FRONT, 300, 4, 5, 246, 248.5)                                   # wall 2
lg.box(295, 300, 5, 227, 243, 246).box(295, 296, 5, 227, 246, 248.5)                                    # wall 3 (to the wardrobe)
lg.box(FRONT, FRONT + 5, 5, 290, 243, 246).box(FRONT + 4, FRONT + 5, 5, 285, 246, 248.5)               # wall 4 (on the boards)
lg.box(FRONT + 5, 119, 285, 290, 243, 246).box(FRONT + 5, 119, 285, 286, 246, 248.5)                  # wall 1 (door side)
lg.finish('ARCH_Cove_Ledge', 'ARCH_Architecture', ['M_Crown_Plaster'], bevel=(0.15, 1))['note'] = 'NEW: LED cove ledge (sanca) 5 x 3 cm, lip 2.5 cm'

# ================================================================ 2. puzzle backlight (frame moved 2 cm off the wall on stand-offs)
pz = bpy.data.objects['DECOR_Puzzle_Frame']
if not pz.get('standoff'): pz.location.x -= 0.02; pz['standoff'] = 1
group_material('Puzzle', GROUPS['Puzzle'][2] / 0.010)
pc, pd = Mesh(), Mesh()                     # 4 strips on the back edges of the frame, aimed out at the wall: soft halo around it
for nm, p0, p1, out in (('Top', (298.3, 83, 169.7), (298.3, 152, 169.7), (0, 0, 1)), ('Bottom', (298.3, 83, 124.3), (298.3, 152, 124.3), (0, 0, -1)),
                        ('Left', (298.3, 83, 125.5), (298.3, 83, 168.5), (0, -1, 0)), ('Right', (298.3, 152, 125.5), (298.3, 152, 168.5), (0, 1, 0))):
    strip('Puzzle', f'LED_Puzzle_{nm}', p0, p1, (1, 0, 0), out, 50, pd, pc, 1.0, 120)
pc.finish('LED_Channels_Puzzle', 'LIGHT_LED_Strips', [alu]); visible_only(pd.finish('LED_Diffusers_Puzzle', 'LIGHT_LED_Strips', [GMAT['Puzzle']]))

# ================================================================ 3. reading sconce above the bed head (wall 3)
for n in ('PROP_Sconce', 'PROP_Sconce_Shade'): remove(n)
brass = material('M_Brass_Brushed', '#C9A15C', 0.3, 1.0)
linen = bpy.data.materials.get('M_Linen_Shade')
if linen: bpy.data.materials.remove(linen)
linen = bpy.data.materials.new('M_Linen_Shade'); linen.use_nodes = True; nt = linen.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
dif = nt.nodes.new('ShaderNodeBsdfDiffuse'); tr = nt.nodes.new('ShaderNodeBsdfTranslucent'); mx = nt.nodes.new('ShaderNodeMixShader')
dif.inputs['Color'].default_value = (*lin('#EDE3D0'), 1); tr.inputs['Color'].default_value = (*lin('#F2DDB8'), 1); mx.inputs['Fac'].default_value = 0.55
nt.links.new(dif.outputs[0], mx.inputs[1]); nt.links.new(tr.outputs[0], mx.inputs[2])
nt.links.new(mx.outputs[0], next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL').inputs['Surface']); linen.diffuse_color = (*lin('#EDE3D0'), 1)
SY, SZ, SX = 46.0, 122.0, 284.0
sm = Mesh()
sm.cyl((299.95, SY, SZ), (298.9, SY, SZ), 5.0, 32)                                           # wall plate
sm.cyl((298.9, SY, SZ), (SX + 1.0, SY, SZ + 1.5), 0.5, 12).cyl((SX + 1.0, SY, SZ + 1.5), (SX, SY, SZ + 1.5), 0.5, 12)   # arm
sm.cyl((SX, SY, SZ + 1.5), (SX, SY, SZ - 2.0), 0.9, 16)                                      # bulb holder
sm.finish('PROP_Sconce', 'PROPS_Lived_In', [brass], smooth=True)['note'] = 'NEW: plug-in brass reading sconce'
sh = Mesh().cyl((SX, SY, SZ - 7.0), (SX, SY, SZ + 6.0), 8.0, 48, 0, caps=False)
so = sh.finish('PROP_Sconce_Shade', 'PROPS_Lived_In', [linen], smooth=True)
md = so.modifiers.new('Thickness', 'SOLIDIFY'); md.thickness = 0.002
group_light('Sconce', 'LIGHT_Sconce', 'POINT', (SX, SY, SZ - 2.8), (0, 0, 0), 7.0, shadow_soft_size=0.02)
bulb = Mesh().sphere((SX, SY, SZ - 3.2), 1.8, 0, 16); group_material('Sconce', 220.0)
visible_only(bulb.finish('PROP_Sconce_Bulb', 'PROPS_Lived_In', [GMAT['Sconce']], smooth=True))

# ================================================================ 4. fairy lights in swags above the window
for n in ('PROP_Fairy_Wire', 'PROP_Fairy_Beads'): remove(n)
pts = []
hooks = [(88.0, 238.0), (142.0, 238.0), (196.0, 238.0), (251.0, 238.0)]
pts += [(88.0, 200.0 + 38.0 * k / 12) for k in range(12)]                                 # left tail hanging down
for (x0, z0), (x1, z1) in zip(hooks, hooks[1:]):
    for k in range(24): t = k / 24; pts.append((x0 + (x1 - x0) * t, z0 - 9.0 * math.sin(math.pi * t)))   # swag, 9 cm sag
pts += [(251.0, 238.0 - 38.0 * k / 12) for k in range(13)]                                # right tail
cu = bpy.data.curves.new('PROP_Fairy_Wire', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0006
sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
for p, (x, z) in zip(sp.points, pts): p.co = (x * S, 1.6 * S, z * S, 1.0)
cu.materials.append(material('M_Copper_Wire', '#B87333', 0.35, 1.0))
bpy.data.collections['PROPS_Lived_In'].objects.link(bpy.data.objects.new('PROP_Fairy_Wire', cu))
beads = Mesh(); acc, last = 0.0, None
for x, z in pts:                                                                          # a micro LED every ~6 cm along the wire
    if last is not None: acc += math.dist((x, z), last)
    if last is None or acc >= 6.0:
        beads.sphere((x, 1.6, z), 0.22, 0, 6); acc = 0.0
    last = (x, z)
group_material('Fairy', 900.0)
fb = beads.finish('PROP_Fairy_Beads', 'PROPS_Lived_In', [GMAT['Fairy']], smooth=True); visible_only(fb)
fb['note'] = 'NEW: copper-wire micro-LED fairy lights (~5 m, warm 2000 K)'

# ================================================================ 5. look, save
sc.view_settings.exposure = EXPOSURE
lamp = bpy.data.lights.get('LIGHT_Desk_Lamp')
if lamp: lamp.temperature = 3000.0
sc['experiment'] = (sc.get('experiment', '') + ' | round 4: cozy layered lighting (cove, shelves, piano, bed panel, puzzle, under-desk, '
                    'wardrobe plinth, fairy lights, reading sconce) - each group its own colour; desk lamp warm white')
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'Bedroom_Teak_Navy_v4.blend'), compress=True)
print('SAVED v4')

# ================================================================ 6. renders (+ numbered call-outs for the plan)
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'METAL'; prefs.get_devices()
for d in prefs.devices: d.use = True
sc.cycles.device = 'GPU'; sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_depth = '8'


def set_layers(on):
    for key in GROUPS: sc[f'{key}_Brightness'] = 1.0 if (on == 'all' or key in on) else 0.0
    sc.update_tag(); bpy.context.view_layer.update()


def shot(cam, path, spp, pct):
    sc.camera = bpy.data.objects[cam]; sc.cycles.samples = spp; sc.render.resolution_percentage = pct
    os.makedirs(os.path.dirname(path), exist_ok=True); sc.render.filepath = path; bpy.ops.render.render(write_still=True)
    print('RENDERED', os.path.relpath(path, OUT), flush=True)


CALLOUT = {'Cove': (150, 1, 247), 'Shelves': (FRONT + 4, 90, 160), 'Piano': (297, 200, 95), 'BedPanel': (200, 1, 93),
           'Puzzle': (297, 150, 168), 'Desk': (FRONT + 4, 120, 70), 'Wardrobe': (210, 227, 6), 'Fairy': (196, 2, 232),
           'Sconce': (284, 46, 128), 'DeskLamp': (30, 41, 104)}


def callouts(cam):
    c = bpy.data.objects[cam]; r = {}
    for k, p in CALLOUT.items():
        v = world_to_camera_view(sc, c, Vector(p) * S)
        if v.z > 0 and 0.02 < v.x < 0.98 and 0.02 < v.y < 0.98: r[k] = (round(v.x, 4), round(1 - v.y, 4))
    return r


VIEWS = ['CAM_Dusk_Wide', 'CAM_Hero_1_Room', 'CAM_Render_B_From_Window', 'CAM_Detail_Wall3', 'CAM_Hero_3_Desk', 'CAM_Detail_Fan']
scale = float(OPT.get('scale', 1.0))
if SET == 'test':
    set_layers('all')
    for cam in OPT.get('cams', ','.join(VIEWS)).split(','):
        shot(cam, os.path.join(OUT, 'test', cam.replace('CAM_', '') + '.png'), int(OPT.get('spp', 48)), round(40 * scale))
if SET in ('all', 'views'):
    set_layers(['Shelves', 'Piano'])                                      # 'before': round-3 lights, now warm
    shot('CAM_Dusk_Wide', os.path.join(OUT, 'compare', 'A_warm_base_only.png'), int(OPT.get('spp', 256)), round(67 * scale))
    set_layers('all')
    shot('CAM_Dusk_Wide', os.path.join(OUT, 'compare', 'B_cozy_layers.png'), int(OPT.get('spp', 256)), round(67 * scale))
    for cam in VIEWS:
        shot(cam, os.path.join(OUT, 'views', cam.replace('CAM_', '') + '.png'), int(OPT.get('vspp', 512)), round(100 * scale))
    os.makedirs(OUT, exist_ok=True)
    json.dump({'groups': {k: dict(label=v[0], hex=v[1], spec=v[3]) for k, v in GROUPS.items()},
               'callouts': {cam: callouts(cam) for cam in VIEWS}}, open(os.path.join(OUT, 'plan.json'), 'w'), indent=1)
