"""
Checks that the fixed parts of the room still match your measurements.
Run on the baseline or on any experiment file:
  Blender -b SOME_FILE.blend --python verify_baseline.py
Exits with an error listing every dimension that drifted by more than 2 mm.
"""
import bpy, sys
from mathutils import Vector

TOL = 0.2  # cm


def bbox(name):
    ob = bpy.data.objects[name]
    dg = bpy.context.evaluated_depsgraph_get(); ev = ob.evaluated_get(dg)
    pts = [ev.matrix_world @ Vector(c) for c in ev.bound_box]
    lo = [min(p[i] for p in pts) * 100 for i in range(3)]; hi = [max(p[i] for p in pts) * 100 for i in range(3)]
    return lo, hi


def faces(name, axis, value):
    """True if the evaluated mesh has a face lying in the plane coord[axis] == value (cm)."""
    ob = bpy.data.objects[name]; dg = bpy.context.evaluated_depsgraph_get(); me = ob.evaluated_get(dg).to_mesh()
    M = ob.matrix_world; hit = False
    for p in me.polygons:
        vs = [(M @ me.vertices[i].co)[axis] * 100 for i in p.vertices]
        if max(vs) - min(vs) < 0.01 and abs(vs[0] - value) < TOL: hit = True; break
    ob.evaluated_get(dg).to_mesh_clear()
    return hit


CHECKS = []
def check(label, got, want):
    CHECKS.append((label, got, want, abs(got - want) <= TOL))


# room (drawing): inner faces of the walls
check('wall 2 inner face  Y', bbox('ARCH_Wall_2_Window')[1][1], 0.0)
check('wall 1 inner face  Y', bbox('ARCH_Wall_1_Door')[0][1], 290.0)
check('wall 4 inner face  X', bbox('ARCH_Wall_4')[1][0], 0.0)
check('wall 3 inner face  X', bbox('ARCH_Wall_3')[0][0], 300.0)
check('ceiling height     Z', bbox('ARCH_Ceiling')[0][2], 270.0)
# door (drawing 71.5 x 210, trim 7.5, 25 cm to the wardrobe)
lo, hi = bbox('DOOR_Leaf')
check('door leaf width', hi[0] - lo[0], 71.5); check('door leaf top Z', hi[2], 210.0)
lo, hi = bbox('DOOR_Trim')
check('door trim outer left X', lo[0], 7.5); check('door trim outer right X', hi[0], 94.0)
# window (drawing 151.5 x 121.5, sill 97.5, 54.5 from wall 3, 1 cm proud)
lo, hi = bbox('WIN_Trim')
check('window width', hi[0] - lo[0], 151.5); check('window height', hi[2] - lo[2], 121.5)
check('window bottom Z', lo[2], 97.5); check('window to wall 3', 300.0 - hi[0], 54.5); check('window proud of wall', hi[1], 1.0)
# wardrobe (drawing 181 x 63 x 270, 25 cm from the door trim)
lo, hi = bbox('WARD_Carcass')
check('wardrobe width', hi[0] - lo[0], 181.0); check('wardrobe depth', hi[1] - lo[1], 63.0); check('wardrobe height', hi[2] - lo[2], 270.0)
check('door trim -> wardrobe gap', lo[0] - bbox('DOOR_Trim')[1][0], 25.0)
# furniture you measured
lo, hi = bbox('BED_Mattress')
check('bed length', hi[0] - lo[0], 188.0); check('bed width', hi[1] - lo[1], 94.0); check('bed height', hi[2], 53.0)
lo, hi = bbox('DESK_Wood')
check('desk length', hi[1] - lo[1], 170.0); check('desk depth', hi[0] - lo[0], 49.0)
check('desk top height (face at Z=80)', 80.0 if faces('DESK_Wood', 2, 80.0) else -1.0, 80.0)
lo, hi = bbox('PIANO_Body')
check('piano width (Korg 129.5)', hi[1] - lo[1], 129.5)
check('piano depth (Korg 38)', hi[0] - bbox('PIANO_Keys_White')[0][0], 38.0)

bad = [c for c in CHECKS if not c[3]]
for label, got, want, ok in CHECKS:
    print(f"{'OK ' if ok else 'BAD'}  {label:28s} {got:8.2f}  (expected {want})")
print(f"{len(CHECKS) - len(bad)}/{len(CHECKS)} checks passed")
if bad:
    sys.exit(1)
