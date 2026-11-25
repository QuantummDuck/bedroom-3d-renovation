"""Top-down plan of a layout file, oriented like the user's sketch (window top, wall 4 right).
  Blender -b FILE.blend --python plan_render.py -- out=PATH.png"""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import photoreal_common as P
A = dict(a.split('=', 1) for a in sys.argv[sys.argv.index('--') + 1:])
sc = bpy.context.scene
for n in ('ARCH_Ceiling', 'ARCH_Crown_Molding', 'ARCH_Cove_Ledge', 'FAN_Body', 'FAN_Blades', 'FAN_Globe', 'LIGHT_Fan_Bulb'):
    o = bpy.data.objects.get(n)
    if o: o.hide_render = True
P.render_settings(); P.ensure_worlds(); P.set_world('WORLD_Daylight', sunny=0); P.set_sun(None)
sc.view_settings.exposure = float(A.get("expo", 0.4)); P.white_balance(8500, 12.0)
sc.camera = bpy.data.objects['CAM_Plan_Sketch']
sc.render.resolution_x = sc.render.resolution_y = 1200; sc.cycles.samples = 96
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_depth = '8'; sc.render.filepath = A['out']
bpy.ops.render.render(write_still=True); print('PLAN', A['out'])
