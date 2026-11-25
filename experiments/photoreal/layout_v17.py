"""Round 17, from Bedroom_v16_Plants_Panels.blend -> ../teak_navy/Bedroom_v17_Panel_Reverted.blend
Bed panel back to its previous size (top 87.5 cm); its LED strip back on the old top edge; the lower shelf + Peperomia, which sat on the panel's face,
move 1.8 cm back against the wall. Frame, upper shelf, plants and the window-wall panel are unchanged."""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import photoreal_common as P
from mathutils import Vector, Matrix
S = 0.01; OBJ = bpy.data.objects
g = P.Geo(); g.box(100.5, 296.0, 288.2, 290.0, 0, 87.5)
g.finish('BED_Headboard_Wall1', 'FURN_Bed', [bpy.data.materials['M_Boards_teak']], bevel=(0.15, 1))['note'] = 'bed panel, original size (top 87.5 cm)'
bpy.context.view_layer.update()
for n in ('LED_Channels_BedPanel', 'LED_Diffusers_BedPanel', 'LED_BedPanel_W1'):
    o = OBJ[n]; o.matrix_world = Matrix.Translation(Vector((0, 0, 87.5 - 125.0)) * S) @ o.matrix_world
for n in [o.name for o in OBJ if o.name.startswith('PEPEROMIA_')] + ['WALL1_Shelf_Bottom']:
    o = OBJ[n]; o.matrix_world = Matrix.Translation(Vector((0, 1.8, 0)) * S) @ o.matrix_world
bpy.context.preferences.filepaths.save_version = 0
out = os.path.join(P.ROOT, 'experiments', 'teak_navy', 'Bedroom_v17_Panel_Reverted.blend')
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True); print('SAVED', out)
