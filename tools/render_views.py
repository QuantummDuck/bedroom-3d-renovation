"""Render named cameras headless.
  Blender -b FILE.blend --python tools/render_views.py -- OUTDIR CAM1,CAM2 [SCALE=1.0] [SAMPLES=file default]
Photo-matched cameras render at their photo's size, plan/elevation cameras hide ceiling/furniture as needed,
other cameras use the file's resolution. Uses the Mac's GPU (Metal)."""
import bpy, os, sys
a = sys.argv[sys.argv.index('--') + 1:]
out, names = a[0], a[1].split(',')
scale = float(a[2]) if len(a) > 2 else 1.0
sc = bpy.context.scene
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'METAL'; prefs.get_devices()
for d in prefs.devices: d.use = True
sc.cycles.device = 'GPU'
if len(a) > 3: sc.cycles.samples = int(a[3])
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_depth = '8'
W, H = sc.render.resolution_x, sc.render.resolution_y
for n in names:
    cam = bpy.data.objects[n]; sc.camera = cam; hidden = []
    if n.startswith('CAM_Plan'):
        hidden = [bpy.data.objects['ARCH_Ceiling'], bpy.data.objects['ARCH_Crown_Molding']]; w, h = 1050, 1050
    elif n.startswith('CAM_Elev'):
        hidden = [o for cn in ('FURNITURE', 'DECOR_Loose', 'PROPS_Lived_In') if cn in bpy.data.collections
                  for o in bpy.data.collections[cn].all_objects]; w, h = 1110, 833
    elif 'photo_size' in cam:
        w, h = cam['photo_size']
    else:
        w, h = W, H
    for o in hidden: o.hide_render = True
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = int(w * scale), int(h * scale), 100
    sc.render.filepath = os.path.join(out, n + '.png')
    bpy.ops.render.render(write_still=True)
    for o in hidden: o.hide_render = False
    print('RENDERED', n, flush=True)
