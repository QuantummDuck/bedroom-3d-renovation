"""Round 10, built on Bedroom_Teak_Navy_v9_layout.blend -> ../teak_navy/Bedroom_Teak_Navy_v10_slats.blend
  Blender -b ../teak_navy/Bedroom_Teak_Navy_v9_layout.blend --python layout_v10.py
1. Vertical slat wall on wall 3 (replaces the horizontal boards), proportioned like real acoustic slat panels:
   slats 2.7 cm wide x 1.2 cm deep on 0.9 cm black felt (standard 27 mm / 12 mm / 13 mm-gap panels), 72 slats across the 290 cm wall,
   gaps evened out to 1.35 cm so a full slat sits in each corner; floor (5 mm shadow gap) to the crown molding; slat face stays at
   x = 296 so the shelves, table, bed and plug keep their positions.
2. One wood across the room: the shelf boards take the same wood as the slats, table, wardrobe, bed panel and drawer unit.
3. Paint-ready wardrobe material (M_Ward_Paint) and palette hooks for the colour study (palettes.py)."""
import bpy, bmesh, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import photoreal_common as P

S = 0.01; OBJ = bpy.data.objects; sc = bpy.context.scene
OPT = dict(a.split('=', 1) for a in sys.argv[sys.argv.index('--') + 1:]) if '--' in sys.argv else {}
ORIGINAL = OPT.get('original_colours') == '1'          # 1 = slats only, every colour exactly as in v9 (shelves keep their own wood)
WALL, TOP, Z0 = 290.0, 252.5, 0.5                        # wall length; crown bottom; shadow gap at the floor
SW, SD, FELT, N = 2.7, 1.2, 0.9, 72                      # slat width, slat depth, felt thickness, slat count
FACE_L = 4.0                                             # slat face in the object's local frame (= x 296 in the room)
GAP = (WALL - N * SW) / (N - 1)                          # 1.346 cm

ob = OBJ['STUDY_Wood_Wall_Boards']; rng = random.Random(10)
bm = bmesh.new(); tint = bm.verts.layers.float.new('board_tint'); uv = bm.loops.layers.uv.new('UVMap')


def slab(x0, x1, y0, y1, z0, z1, mi, t, du, dv):
    v = [bm.verts.new((x * S, y * S, z * S)) for x, y, z in [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                                                              (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]]
    for vv in v: vv[tint] = t
    for idx in [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]:
        f = bm.faces.new([v[i] for i in idx]); f.material_index = mi; f.normal_update()
        ax = max(range(3), key=lambda i: abs(f.normal[i]))
        for lp in f.loops:                               # grain runs up the slat (u = height)
            c = lp.vert.co
            lp[uv].uv = (c.z + du, c.y + dv) if ax == 0 else (c.z + du, c.x + dv) if ax == 1 else (c.y + du, c.x + dv)


slab(FACE_L - SD - FELT, FACE_L - SD, 0, WALL, Z0, TOP, 1, 0.5, 0, 0)                      # felt backing
for k in range(N):
    y0 = k * (SW + GAP)
    slab(FACE_L - SD, FACE_L, y0, y0 + SW, Z0, TOP, 0, rng.uniform(0.3, 0.7), rng.uniform(0, 0.9), rng.uniform(0, 0.9))
old = ob.data; me = bpy.data.meshes.new('WALL3_Slats'); bm.to_mesh(me); bm.free()
for m in old.materials: me.materials.append(m)
ob.data = me; bpy.data.meshes.remove(old); ob.name = 'WALL3_Slat_Wall'
for md in ob.modifiers:
    if md.type == 'BEVEL': md.width = 0.0012; md.segments = 2
ob['dim_source'] = 'SPEC'
ob['note'] = (f'Vertical slat wall: {N} slats {SW} x {SD} cm on {FELT} cm black felt, gaps {GAP:.2f} cm (27/12/13 mm acoustic-panel proportions), '
              f'floor to crown, face 4 cm off wall 3')

# one wood across the room: shelves match the slats
if not ORIGINAL: OBJ['SHELF_Boards'].data.materials[0] = bpy.data.materials['M_Boards_teak']

# paint-ready wardrobe finish (used by palettes that paint the wardrobe instead of wood)
wp = bpy.data.materials.get('M_Ward_Paint') or P.material('M_Ward_Paint', '#2F3D52', 0.32, **{'Coat Weight': 0.15, 'Coat Roughness': 0.3})
wp['note'] = 'Wardrobe lacquer (palette colour); assign to WARD_Carcass and the door panels to paint the wardrobe'
wp.use_fake_user = True                                   # keep it in the file even while unassigned

P.cam('CAM_S1_Slats_Detail', (255, 158, 112), (296, 168, 108), 50, 4.0, level=False)     # slats between table and shelves
P.cam('CAM_S2_Slats_Grazing', (280, 250, 120), (296, 120, 150), 35, 5.6, level=False)
P.cam('CAM_F1_Slats_Over_Bed', (238, 248, 128), (296, 232, 132), 50, 4.0, level=False)
P.cam('CAM_F2_Doorway_View', (75, 278, P.EYE_STAND), (230, 70, 105), 20, 8.0)

sc['experiment'] = sc.get('experiment', '') + f' | round 10: vertical slat wall ({N} x {SW} cm slats, {GAP:.2f} cm gaps), one wood throughout'
bpy.context.preferences.filepaths.save_version = 0
out = OPT.get('out', os.path.join(P.ROOT, 'experiments', 'teak_navy', 'Bedroom_Teak_Navy_v10_slats.blend'))
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print('SAVED', out, f'gap {GAP:.3f} pitch {SW + GAP:.3f}')
