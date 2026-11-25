"""Layout checks for Bedroom_Teak_Navy_v6_layout.blend: positions, the 50 cm clearance and overlaps (cm)."""
import bpy
from mathutils import Vector
dg = bpy.context.evaluated_depsgraph_get()
def bb(*names):
    pts = []
    for n in names:
        o = bpy.data.objects[n]; e = o.evaluated_get(dg); me = e.to_mesh(); pts += [o.matrix_world @ v.co for v in me.vertices]; e.to_mesh_clear()
    return [round(min(p[i] for p in pts) * 100, 1) for i in range(3)], [round(max(p[i] for p in pts) * 100, 1) for i in range(3)]
def kids(root): return [c.name for c in bpy.data.objects[root].children_recursive if c.type == 'MESH' and not c.hide_render]
W = bb(*[n for n in kids('WARD_Wardrobe') if n.startswith('WARD_')]); print('wardrobe incl. handles', W)
WC = bb('WARD_Carcass'); print('wardrobe carcass', WC)
M = bb('BED_Mattress'); print('mattress', M)
Tp = bb('DESK_Wood'); print('table top', Tp)
print('bed side edge y', M[0][1], '| table arm starts y', Tp[1][1])
print('clearance table end -> wardrobe door face:', round(Tp[0][0] - WC[1][0], 1), 'cm (to the handle tips:', round(Tp[0][0] - W[1][0], 1), ')')
print('wall-3 arm end vs bed side edge (should be 0):', round(M[0][1] - Tp[1][1], 1))
def overlap(a, b): return all(a[0][i] < b[1][i] - 0.05 and b[0][i] < a[1][i] - 0.05 for i in range(3))
items = {'wardrobe': W, 'mattress': M, 'table top': Tp, 'rug(floor)': bb('DECOR_Rug'), 'chair base': bb('CHAIR_Base'), 'stool': bb('STOOL_Body'),
         'purifier black': bb('DECOR_Purifier_Black_Cylinder'), 'purifier white': bb('DECOR_Purifier_White_Body'),
         'shelves': bb('SHELF_Boards'), 'door leaf': bb('DOOR_Leaf')}
names = list(items)
for i, a in enumerate(names):
    for b in names[i + 1:]:
        if overlap(items[a], items[b]): print('OVERLAP', a, 'x', b, items[a], items[b])
print('shelves', items['shelves'], '| stool', items['stool'], '| chair', items['chair base'])
for n in ('BED_Headboard_Wall1', 'BED_Headboard_Wall3', 'ARCH_Crown_Molding', 'ARCH_Cove_Ledge', 'ARCH_Baseboards'):
    o = bpy.data.objects.get(n); print(n, bb(n) if o else None, [c.name for c in o.users_collection] if o else '')
# bedspread drape vs table legs
sp = bpy.data.objects['BED_Bedspread']; e = sp.evaluated_get(dg); me = e.to_mesh(); pts = [sp.matrix_world @ v.co * 100 for v in me.vertices]; e.to_mesh_clear()
near = [p for p in pts if p.x > 248 and p.y < 196 and p.z < 60]
print('bedspread verts over the table-end zone (x>248, y<196):', len(near), 'min y', round(min((p.y for p in near), default=0), 1))
print('boards', bb('STUDY_Wood_Wall_Boards'), '| plug', bb('ELEC_Outlet_W3_Low'), '| shelves back', bb('SHELF_Boards'), '| legs', bb('DESK_Legs'))
print('laptop z', bb('PROP_MacBook_Air_13_M4'), '| bed head x', M[1][0])
