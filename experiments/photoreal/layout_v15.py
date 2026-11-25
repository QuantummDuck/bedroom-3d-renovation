"""Round 15: shelves centred on the full wall 3, plus your frame + two staggered shelves on the door wall (wall 1) above the bed's long side.
  Blender -b ../teak_navy/Bedroom_v13_Slats_Original_Colours.blend --python layout_v15.py -> ../teak_navy/Bedroom_v15_Shelves_Frame.blend
1. Wall-3 shelf unit (boards, frames, LED strips, books, objects) moved +45 cm along y: its centre goes from y=100 (middle of the table arm)
   to y=145 (middle of the 290 cm wall), so it now overhangs the bed by 34 cm.
2. Wall 1: frame (puzzle picture 75 x 51.4 cm) centred over the bed at x=200, bottom 105 cm; per your sketch a 48 cm shelf upper-right
   (bottom 8 cm above the frame top, starting 75% across the frame) and a 46 cm shelf lower-left (top 5 cm below the frame bottom,
   starting 29 cm left of the frame), both 15 cm deep, 3 cm thick, in the shelf wood on hidden brackets."""
import bpy, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import photoreal_common as P
from mathutils import Vector, Matrix
S = 0.01; OBJ = bpy.data.objects; MAT = bpy.data.materials
DY = 45.0
mv = ['SHELF_Wall_Shelves', 'LED_Shelf_1', 'LED_Shelf_2', 'LED_Shelf_3', 'LED_Channels_Shelves', 'LED_Diffusers_Shelves'] + [o.name for o in bpy.data.collections['PROPS_Books'].objects if o.parent is None]
bpy.context.view_layer.update()
for n in mv:
    o = OBJ.get(n)
    if o is not None: o.matrix_world = Matrix.Translation(Vector((0, DY, 0)) * S) @ o.matrix_world
bpy.context.view_layer.update()

# ---- wall 1 composition (inner face of wall 1 is y = 290)
Y1 = 290.0; FW, FH, FD, FB = 75.0, 51.4, 2.6, 2.1
fx0, fx1 = 200.0 - FW / 2, 200.0 + FW / 2; fz0 = 105.0; fz1 = fz0 + FH
frame_m = MAT['M_Frame_Black_Satin']; pic_m = MAT['M_Puzzle_Picture']; wood = MAT['M_Shelf_Wood']; steel = MAT['M_Steel_Black']
g = P.Geo(); y0 = Y1 - FD
g.box(fx0, fx1, y0, Y1, fz1 - FB, fz1).box(fx0, fx1, y0, Y1, fz0, fz0 + FB)
g.box(fx0, fx0 + FB, y0, Y1, fz0 + FB, fz1 - FB).box(fx1 - FB, fx1, y0, Y1, fz0 + FB, fz1 - FB)
g.box(fx0 + FB, fx1 - FB, Y1 - 0.6, Y1, fz0 + FB, fz1 - FB)
fo = g.finish('WALL1_Frame', 'DECOR_Loose', [frame_m], bevel=(0.12, 2)); fo['dim_source'] = 'USER'; fo['note'] = 'frame from your sketch, 75 x 51.4 cm, over the bed on wall 1'
import bmesh
bm = bmesh.new(); uv = bm.loops.layers.uv.new('UVMap'); py = Y1 - 0.75
vs = [bm.verts.new(Vector(c) * S) for c in [(fx0 + FB, py, fz0 + FB), (fx1 - FB, py, fz0 + FB), (fx1 - FB, py, fz1 - FB), (fx0 + FB, py, fz1 - FB)]]
f = bm.faces.new(vs)
for lp, (u, v) in zip(f.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]): lp[uv].uv = (u, v)         # viewer faces +y: image left -> right = +x
me = bpy.data.meshes.new('WALL1_Picture'); bm.to_mesh(me); bm.free(); me.materials.append(pic_m)
po = bpy.data.objects.new('WALL1_Picture', me); P.coll('DECOR_Loose').objects.link(po); po['dim_source'] = 'PHOTO'
if po.data.polygons[0].normal.y > 0: po.data.polygons[0].flip() if hasattr(po.data.polygons[0], 'flip') else None


def shelf(name, x0, x1, ztop):
    g = P.Geo(); D, T = 15.0, 3.0
    g.box(x0, x1, Y1 - D, Y1, ztop - T, ztop)
    for bx in (x0 + 6, x1 - 6):                                         # two small hidden-ish steel brackets under the plank
        g.box(bx - 0.5, bx + 0.5, Y1 - 0.8, Y1, ztop - T - 7, ztop - T).box(bx - 0.5, bx + 0.5, Y1 - D + 2, Y1, ztop - T - 0.6, ztop - T)
    o = g.finish(name, 'FURN_Shelves', [wood, steel], bevel=(0.15, 1))
    for p in o.data.polygons: p.material_index = 0
    return o
shelf('WALL1_Shelf_Top', fx0 + 0.75 * FW, fx0 + 0.75 * FW + 48.0, fz1 + 8.0 + 3.0)
shelf('WALL1_Shelf_Bottom', fx0 - 29.0, fx0 - 29.0 + 46.0, fz0 - 5.0)

P.cam('CAM_W1_Frame_Wall', (200, 120, 135), (200, 290, 128), 24, 8.0)
P.cam('CAM_W3_Shelves_Over_Bed', (70, 270, 150), (296, 190, 160), 20, 8.0)
bpy.context.scene['experiment'] = bpy.context.scene.get('experiment', '') + ' | round 15: wall-3 shelves centred on the wall, wall-1 frame + 2 shelves'
bpy.context.preferences.filepaths.save_version = 0
out = os.path.join(P.ROOT, 'experiments', 'teak_navy', 'Bedroom_v15_Shelves_Frame.blend')
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True); print('SAVED', out)
