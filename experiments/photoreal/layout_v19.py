"""Round 19, from Bedroom_v18A_ShelfUnit_2_shelves.blend -> ../teak_navy/Bedroom_v19_Wall_Shelves.blend
Steel posts removed. Floating shelves (dark shelf wood, 2.5 cm thick, hidden fixings) fixed to the window-side wall in the corner next to the slat wall,
stacked up to just under the top of the window frame: boards with top surfaces at z = 110, 136, 162, 188, 214 (aquarium on the table below the first board).
Board 46 wide (x 248-294, centred on the aquarium) x 23 deep from the wall (y 0-23). The aquarium moved back against the panel (y 1 -> 22)."""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import photoreal_common as P
from mathutils import Vector
S = 0.01; OBJ, MAT = bpy.data.objects, bpy.data.materials
for n in ('TSHELF_Posts', 'TSHELF_Boards'): P.remove(n)
TOPS = [110.0, 136.0, 162.0, 188.0, 214.0]; T = 2.5
g = P.Geo()
for top in TOPS: g.box(248.0, 294.0, 0.0, 23.0, top - T, top)
bo = g.finish('TSHELF_Boards', 'FURN_Shelves', [MAT['M_Shelf_Wood']], bevel=(0.15, 1)); bo['dim_source'] = 'EST'
bo['note'] = f'floating wall shelves on the window-side wall, top surfaces at z={TOPS}, 46 x 23 cm'
OBJ['AQ_Aquarium'].location = Vector((271.0, 11.5, 75.0)) * S
bpy.context.view_layer.update()
bpy.context.scene['experiment'] = bpy.context.scene.get('experiment', '') + ' | round 19: posts removed, 5 floating wall shelves'
bpy.context.preferences.filepaths.save_version = 0
out = os.path.join(P.ROOT, 'experiments', 'teak_navy', 'Bedroom_v19_Wall_Shelves.blend')
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True); print('SAVED', out)
