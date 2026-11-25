"""Round 18, from Bedroom_v17_Panel_Reverted.blend. Table-top shelf unit in the window / slat-wall corner + the aquarium back on the table.
  Blender -b ../teak_navy/Bedroom_v17_Panel_Reverted.blend --python layout_v18.py -- variant=A|B
  A = two floors (boards at z 119 and 142), B = three floors (boards at 110, 126, 142): same overall height (75 -> 142), same footprint.
Unit: 2 x 2 cm black steel posts like the table's legs (standing on the table), 2 cm boards in the dark shelf wood, clear inside 46 x 22 cm
(aquarium 45 x 21 x 30), outer 50 x 26, wedged between the slat wall (x 296) and the window frame (x 245.5): 0.5 cm to spare."""
import bpy, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import photoreal_common as P
from mathutils import Vector
S = 0.01; OBJ, MAT = bpy.data.objects, bpy.data.materials
V = dict(a.split('=', 1) for a in sys.argv[sys.argv.index('--') + 1:])['variant']
TABLE, TOP, T = 75.0, 142.0, 2.0
X1 = 296.0; PW = 2.0; INX, INY = 46.0, 22.0
X0 = X1 - INX - 2 * PW                      # 246.0
YA = 1.0; YB = YA + INY + 2 * PW            # 1 .. 27
BOARDS = {'A': [119.0, 142.0], 'B': [110.0, 126.0, 142.0]}[V]
for n in [o.name for o in OBJ if o.name.startswith('TSHELF_')]: P.remove(n)
steel, wood = MAT['M_Steel_Black'], MAT['M_Shelf_Wood']
g = P.Geo()
for px in (X0, X1 - PW):
    for py in (YA, YB - PW): g.box(px, px + PW, py, py + PW, TABLE, TOP)
po = g.finish('TSHELF_Posts', 'FURN_Shelves', [steel], bevel=(0.1, 1)); po['dim_source'] = 'EST'
g = P.Geo()
for top in BOARDS: g.box(X0 + PW, X1 - PW, YA + PW, YB - PW, top - T, top)
bo = g.finish('TSHELF_Boards', 'FURN_Shelves', [wood], bevel=(0.12, 1)); bo['dim_source'] = 'EST'
bo['note'] = f'table-top shelf unit, variant {V}: boards with top surfaces at z={BOARDS}, clear width {INX} x depth {INY} for the 45 x 21 x 30 aquarium'
# aquarium back from storage
aq = [o for o in OBJ if o.name.startswith('AQ_')]
for o in aq:
    for c in list(o.users_collection): c.objects.unlink(o)
    P.coll('FURN_Desk').objects.link(o)
root = OBJ['AQ_Aquarium']; root.location = Vector((X0 + PW + INX / 2, YA + PW + INY / 2, TABLE)) * S; root.rotation_euler = (0, 0, 0)
bpy.context.view_layer.update()
g_ = OBJ.get('DESK_Cable_Grommet')
if g_: g_.hide_render = True                                 # the aquarium sits right on the cable hole
P.cam('CAM_U1_Unit_Front', (262, 118, 112), (271, 14, 112), 35, 5.6)
P.cam('CAM_U2_Unit_Close', (252, 62, 104), (271, 14, 108), 35, 4.0, level=False)
bpy.context.scene['experiment'] = bpy.context.scene.get('experiment', '') + f' | round 18 variant {V}: table-top shelf unit + aquarium'
bpy.context.preferences.filepaths.save_version = 0
out = os.path.join(P.ROOT, 'experiments', 'teak_navy', {'A': 'Bedroom_v18A_ShelfUnit_2_shelves.blend', 'B': 'Bedroom_v18B_ShelfUnit_3_shelves.blend'}[V])
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True); print('SAVED', out)
