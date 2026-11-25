"""
Wall-colour study. Opens the (read-only) baseline, recolours M_Wall_Paint, renders both render cameras with Cycles,
measures light levels in linear light and saves one editable .blend per colour next to this script.

  Blender -b ../../Bedroom_Baseline.blend --python wall_colors.py -- [resolution %] [samples]
"""
import bpy, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
PCT = int(ARGS[0]) if ARGS else 67
SPP = int(ARGS[1]) if len(ARGS) > 1 else 256

COLORS = [  # (file-safe name, label, sRGB hex) - matte finish, walls only (ceiling, trim and crown stay white)
    ('01_current_warm_off_white', 'Current warm off-white', '#E6E1CF'),
    ('02_crisp_white', 'Crisp white', '#F4F3EF'),
    ('03_greige', 'Greige', '#CBC3B6'),
    ('04_warm_sand', 'Warm sand', '#D9C4A3'),
    ('05_sage_green', 'Sage green', '#A8B59D'),
    ('06_dusty_blue', 'Dusty blue', '#9EB1C2'),
    ('07_terracotta', 'Terracotta', '#C98463'),
    ('08_deep_navy', 'Deep navy', '#2F3D52'),
]
VIEWS = {  # camera: {region: (x0, x1, y0, y1) as fractions of the frame, y from the top} - white, non-wall surfaces = light meters
    'CAM_Render_A_From_Door': {'ceiling': (0.40, 0.70, 0.03, 0.12), 'bedspread': (0.33, 0.48, 0.66, 0.74)},
    'CAM_Render_B_From_Window': {'wardrobe': (0.66, 0.94, 0.33, 0.62), 'desk_top': (0.14, 0.38, 0.60, 0.65)},
}


def lin(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c]


def region_lum(path, box):
    img = bpy.data.images.load(path); w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1]       # flip: row 0 = top
    bpy.data.images.remove(img)
    x0, x1, y0, y1 = int(box[0] * w), int(box[1] * w), int(box[2] * h), int(box[3] * h)
    r = px[y0:y1, x0:x1, :3]
    return float(np.median(r @ np.array([0.2126, 0.7152, 0.0722])))


sc = bpy.context.scene
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'METAL'; prefs.get_devices()
for d in prefs.devices: d.use = True
ORIG = (sc.render.resolution_percentage, sc.cycles.samples)          # saved files keep full quality for F12
sc.cycles.device = 'GPU'; sc.cycles.samples = SPP; sc.render.resolution_percentage = PCT
if 'sunny' in sc:                       # fair colour comparison: the overcast light calibrated to your photos, no sun patches
    sc['sunny'] = 0; sc.update_tag(); bpy.context.view_layer.update()   # re-evaluate the drivers that switch the light (tested)
sc.render.resolution_x, sc.render.resolution_y = 1920, 1440          # the 4:3 frame these light-meter regions were set on
mat = bpy.data.materials['M_Wall_Paint']; bsdf = mat.node_tree.nodes['Principled BSDF']
paint = mat.node_tree.nodes.get('PAINT_COLOR')   # realism layer keeps the wall colour here (scanned paint texture on top)
os.makedirs(os.path.join(HERE, 'renders'), exist_ok=True)
stats = {}
for slug, label, hexc in COLORS:
    rgb = lin(hexc)
    (paint.outputs[0] if paint else bsdf.inputs['Base Color']).default_value = (*rgb, 1.0); mat.diffuse_color = (*rgb, 1.0)
    sc['experiment'] = f'Wall colour: {label} {hexc}'
    stats[slug] = {'label': label, 'hex': hexc, 'lrv': round(100 * (0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]), 1)}
    for cam, regions in VIEWS.items():
        sc.camera = bpy.data.objects[cam]
        base = os.path.join(HERE, 'renders', f'{slug}_{cam[11]}')                # ..._A / ..._B
        sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = base + '.png'
        bpy.ops.render.render(write_still=True)
        sc.render.image_settings.file_format = 'OPEN_EXR'                     # scene-linear copy for measuring light
        bpy.data.images['Render Result'].save_render(base + '.exr', scene=sc)
        sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_depth = '8'
        for k, box in regions.items():
            stats[slug][k] = region_lum(base + '.exr', box)
        os.remove(base + '.exr')
        print('RENDERED', slug, cam, flush=True)
    sc.camera = bpy.data.objects['CAM_Render_A_From_Door']
    bpy.context.preferences.filepaths.save_version = 0
    sc.render.resolution_percentage, sc.cycles.samples = ORIG
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, f'Bedroom_Wall_{slug}.blend'), copy=True, compress=True)
    sc.render.resolution_percentage, sc.cycles.samples = PCT, SPP
ref = stats[COLORS[0][0]]
for s in stats.values():   # light reaching white surfaces, relative to your current walls
    s['light_vs_current_pct'] = round(100 * np.mean([s[k] / ref[k] for k in ('ceiling', 'bedspread', 'wardrobe', 'desk_top')]))
json.dump(stats, open(os.path.join(HERE, 'renders', 'stats.json'), 'w'), indent=1)
print('STATS', json.dumps({k: (v['lrv'], v['light_vs_current_pct']) for k, v in stats.items()}))
