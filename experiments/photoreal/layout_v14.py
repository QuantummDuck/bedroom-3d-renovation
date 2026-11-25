"""Round 13: slat wall split at the table/bed line -> ../teak_navy/Bedroom_v14_Slats_Split.blend (from Bedroom_v13_Slats_Original_Colours.blend)
  Blender -b ../teak_navy/Bedroom_v13_Slats_Original_Colours.blend --python layout_v14.py
Wall 3 (world y 0..290): y < 194.2 (table side) keeps the VERTICAL slats; y >= 194.2 (bed side) gets HORIZONTAL slats of identical size
(2.7 wide, 1.2 deep, ~1.35 gap, same felt). 194.2 = where the table's wall-3 arm ends and the bed's side edge starts."""
import bpy, bmesh, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import photoreal_common as P
S = 0.01; OBJ = bpy.data.objects
SPLIT = 194.2                                          # world y of the dividing line
WALL, TOP, Z0, SW, SD, FELT, FACE_L = 290.0, 252.5, 0.5, 2.7, 1.2, 0.9, 4.0
N = 72; PITCH = (WALL - SW) / (N - 1) + SW - (WALL - N * SW) / (N - 1) + (WALL - N * SW) / (N - 1)   # placeholder, recomputed below
GAPV = (WALL - N * SW) / (N - 1); PV = SW + GAPV      # vertical pitch 4.046 (as before)
NH = 62; GAPH = ((TOP - Z0) - NH * SW) / (NH - 1)     # horizontal: 62 slats fill floor-to-crown exactly (gap ~1.39 vs 1.35)
ob = OBJ['WALL3_Slat_Wall']; rng = random.Random(14)
bm = bmesh.new(); tint = bm.verts.layers.float.new('board_tint'); uv = bm.loops.layers.uv.new('UVMap')


def slab(x0, x1, y0, y1, z0, z1, mi, t, du, dv, along_y):
    v = [bm.verts.new((x * S, y * S, z * S)) for x, y, z in [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]]
    for vv in v: vv[tint] = t
    for idx in [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]:
        f = bm.faces.new([v[i] for i in idx]); f.material_index = mi; f.normal_update()
        ax = max(range(3), key=lambda i: abs(f.normal[i]))
        for lp in f.loops:                              # grain along the slat's length
            c = lp.vert.co
            if along_y: lp[uv].uv = (c.y + du, c.z + dv) if ax == 0 else (c.y + du, c.x + dv) if ax == 1 else (c.y + du, c.x + dv)
            else: lp[uv].uv = (c.z + du, c.y + dv) if ax == 0 else (c.z + du, c.x + dv) if ax == 1 else (c.y + du, c.x + dv)


LY = lambda wy: WALL - wy                               # object-local y = 290 - world y
slab(FACE_L - SD - FELT, FACE_L - SD, 0, WALL, Z0, TOP, 1, 0.5, 0, 0, False)                  # felt, whole wall
for j in range(N):                                      # vertical slats on the table side (world lattice unchanged)
    wy0 = j * PV
    if wy0 + SW > SPLIT - 0.01: break
    slab(FACE_L - SD, FACE_L, LY(wy0 + SW), LY(wy0), Z0, TOP, 0, rng.uniform(0.3, 0.7), rng.uniform(0, 0.9), rng.uniform(0, 0.9), False)
for k in range(NH):                                     # horizontal slats on the bed side
    z0 = Z0 + k * (SW + GAPH)
    slab(FACE_L - SD, FACE_L, 0, LY(SPLIT), z0, z0 + SW, 0, rng.uniform(0.3, 0.7), rng.uniform(0, 0.9), rng.uniform(0, 0.9), True)
old = ob.data; me = bpy.data.meshes.new('WALL3_Slats'); bm.to_mesh(me); bm.free()
for m in old.materials: me.materials.append(m)
ob.data = me; bpy.data.meshes.remove(old)
ob['note'] = (f'Slat wall split at world y={SPLIT} (table/bed line): vertical slats on the table side, horizontal on the bed side; '
              f'slats {SW} x {SD} cm, gaps {GAPV:.2f} (vertical) / {GAPH:.2f} (horizontal), on {FELT} cm felt')
P.cam('CAM_T1_Transition', (220, 130, 130), (296, 194, 115), 35, 5.6, level=False)
P.cam('CAM_T2_Bed_Side_Slats', (200, 250, 140), (296, 240, 120), 35, 5.6, level=False)
P.cam('CAM_T3_Whole_Wall', (60, 150, 135), (296, 145, 130), 24, 8.0)
bpy.context.preferences.filepaths.save_version = 0
out = os.path.join(P.ROOT, 'experiments', 'teak_navy', 'Bedroom_v14_Slats_Split.blend')
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print('SAVED', out, f'vertical gap {GAPV:.3f}, horizontal gap {GAPH:.3f}, vertical slats up to y={max(j for j in range(N) if j*PV+SW<=SPLIT)*PV+SW:.1f}')
