"""Renders every drawing view of spec.py in a flat CAD look (Eevee + Freestyle outlines, no shadows, transparent background)
and projects the annotation anchors to paper millimetres -> views/<name>.png + views/<name>.json.
  Blender -b experiments/teak_navy/Bedroom_v19_Wall_Shelves.blend --python experiments/schematic/render_views.py -- [only=t_plan,t_iso] [lw=2.0]
Nothing is saved back to the .blend."""
import bpy, json, math, os, sys
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import spec as S
A = dict(a.split('=', 1) for a in sys.argv[sys.argv.index('--') + 1:]) if '--' in sys.argv else {}
OUT = os.path.join(HERE, 'views'); os.makedirs(OUT, exist_ok=True)
sc, O = bpy.context.scene, bpy.data.objects
M = 0.01   # cm -> m


def lin(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return [(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4) for x in c] + [1]


FLAT = {}
for k, h in S.COLORS.items():
    m = bpy.data.materials.new('CAD_' + k); m.use_nodes = True; p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = lin(h); p.inputs['Roughness'].default_value = 0.75; p.inputs['Specular IOR Level'].default_value = 0.2
    FLAT[k] = m
for o in O:   # recolour: new parts by material category, context objects grey
    if o.type != 'MESH': continue
    for s in o.material_slots:
        if o.name in S.GHOST: s.material = FLAT[S.GHOST[o.name]]
        elif s.material: s.material = FLAT[S.MATCOL.get(s.material.name, 'teak')]

w = bpy.data.worlds.new('CADworld'); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (1, 1, 1, 1); bg.inputs[1].default_value = 0.9
for o in O:
    if o.type == 'LIGHT': o.hide_render = True
lt = bpy.data.lights.new('CADsun', 'SUN'); lt.energy = 2.2; lt.use_shadow = False
lo = bpy.data.objects.new('CADsun', lt); sc.collection.objects.link(lo); lo.rotation_euler = (math.radians(50), 0, math.radians(30))
sc.render.engine = 'BLENDER_EEVEE'
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'; sc.view_settings.exposure = -0.6
sc.render.film_transparent = True; sc.render.use_compositing = False; sc.render.resolution_percentage = 100
sc.render.use_freestyle = True; sc.render.line_thickness_mode = 'ABSOLUTE'; sc.render.line_thickness = float(A.get('lw', 2.0))
fs = bpy.context.view_layer.freestyle_settings; ls = fs.linesets[0] if fs.linesets else fs.linesets.new('L')
ls.select_silhouette = ls.select_border = ls.select_crease = True; fs.crease_angle = math.radians(140)
ls.linestyle.color = (0.08, 0.08, 0.09)
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'

cd = bpy.data.cameras.new('CADcam'); cam = bpy.data.objects.new('CADcam', cd); sc.collection.objects.link(cam); sc.camera = cam
cd.clip_start, cd.clip_end = 0.05, 40


def setup(v):
    bw, bh = v['box']; px = S.PX_PER_MM
    sc.render.resolution_x, sc.render.resolution_y = round(bw * px), round(bh * px)
    cd.sensor_fit = 'HORIZONTAL'
    if v['cam'] == 'ortho':
        f, u = Vector(v['fwd']), Vector(v['up']); r = f.cross(u)
        cd.type = 'ORTHO'; cd.ortho_scale = bw * v['scale'] / 1000
        cam.matrix_world = Matrix.Translation(Vector(v['center']) * M - f * 8) @ Matrix((r, u, -f)).transposed().to_4x4()
    else:
        cd.type = 'PERSP'; cd.lens = v['lens']; cd.sensor_width = 36
        loc, tgt = Vector(v['loc']) * M, Vector(v['target']) * M
        cam.matrix_world = Matrix.Translation(loc) @ (tgt - loc).to_track_quat('-Z', 'Y').to_matrix().to_4x4()
    lt.use_shadow = bool(v.get('shadow')); lt.angle = math.radians(8)
    for o in O:
        if o.type in ('MESH', 'CURVE', 'FONT'): o.hide_render = o.name not in v['objs']
    bpy.context.view_layer.update()


def mm(p, v):   # 3-D point (cm) -> paper mm inside the view box (origin top-left)
    c = world_to_camera_view(sc, cam, Vector(p) * M)
    return [round(c.x * v['box'][0], 2), round((1 - c.y) * v['box'][1], 2)]


def project(v):
    out = []
    for a in v.get('ann', []):
        k = a['kind']
        if k == 'dim':
            pa, pb = Vector(a['a']), Vector(a['b']); off = Vector(a['off'])
            out.append(dict(kind='dim', a=mm(pa, v), b=mm(pb, v), a2=mm(pa + off, v), b2=mm(pb + off, v), text=a['text']))
        elif k in ('note', 'bal'):
            out.append(dict(a, p=mm(a['p'], v)))
        elif k == 'box':
            lo, hi = a['lo'], a['hi']; z = lo[2]
            out.append(dict(kind='box', pts=[mm(q, v) for q in ((lo[0], lo[1], z), (hi[0], lo[1], z), (hi[0], hi[1], z), (lo[0], hi[1], z))], label=a['label']))
    return out


for name, v in S.VIEWS.items():
    if 'only' in A and name not in A['only'].split(','): continue
    setup(v); sc.render.filepath = os.path.join(OUT, name + '.png'); bpy.ops.render.render(write_still=True)
    json.dump(dict(box=v['box'], ann=project(v)), open(os.path.join(OUT, name + '.json'), 'w'))
    print('VIEW', name, flush=True)
