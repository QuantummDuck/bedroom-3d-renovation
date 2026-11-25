"""Exports the v19 room as one flat-coloured GLB for the web planner (index.html): one mesh per catalog item, origin at the item's
floor-centre, glTF extras = {label, cat, locked, stored, wall}. Nothing is saved back to the .blend.
  Blender -b experiments/teak_navy/Bedroom_v19_Wall_Shelves.blend --python experiments/room_planner/export_room.py"""
import bpy, bmesh, os, re
import numpy as np
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'room.glb')
MAX_TRIS = 7000                     # per item; heavier items are decimated
ROOM = (3.0, 2.9)

# ------------------------------------------------------------------ catalog: (key, label, category, matcher); first match wins
ARCH = 'Architecture'
GROUPS = [
    ('floor', 'Floor', ARCH, ['ARCH_Floor']), ('ceiling', 'Ceiling', ARCH, ['ARCH_Ceiling']),
    ('wall1', 'Wall 1 (door)', ARCH, ['ARCH_Wall_1_Door']), ('wall2', 'Wall 2 (window)', ARCH, ['ARCH_Wall_2_Window']),
    ('wall3', 'Wall 3', ARCH, ['ARCH_Wall_3']), ('wall4', 'Wall 4', ARCH, ['ARCH_Wall_4']),
    ('baseboards', 'Skirting', ARCH, ['ARCH_Baseboards']), ('crown', 'Crown molding', ARCH, ['ARCH_Crown_Molding']),
    ('outlet', 'Wall outlet', ARCH, ['ELEC_']),
    ('door', 'Door', ARCH, ['DOOR_']), ('window', 'Window', ARCH, ['WIN_Trim', 'WIN_Frame', 'WIN_Sash_', 'WIN_Glass', 'WIN_Latches']),
    ('cove', 'Cove ledge', 'Built-ins', ['ARCH_Cove_Ledge', 'LED_Channels_Cove', 'LED_Diffusers_Cove']),
    ('slats', 'Slat wall', 'Built-ins', ['WALL3_Slat_Wall']), ('winpanel', 'Window-wall panel', 'Built-ins', ['WIN_Wall_Panel']),
    ('bedpanel', 'Bed-wall panel', 'Built-ins', ['BED_Headboard_Wall1', 'LED_Channels_BedPanel', 'LED_Diffusers_BedPanel']),
    ('wardrobe', 'Wardrobe', 'Furniture', ['WARD_', 'LED_Channels_Wardrobe', 'LED_Diffusers_Wardrobe']),
    ('bed', 'Bed', 'Furniture', ['BED_Base', 'BED_Mattress', 'BED_Bedspread']),
    ('pillow_up', 'Pillow, dotted', 'Decor', ['BED_Pillow_Upright_Dots']), ('pillow_lie', 'Pillow, printed', 'Decor', ['BED_Pillow_Lying_Print']),
    ('throw', 'Zigzag throw', 'Decor', ['BED_Throw_Zigzag']),
    ('desk', 'L-shaped desk', 'Furniture', ['DESK_Wood', 'DESK_Legs', 'LED_Channels_Desk', 'LED_Diffusers_Desk']),
    ('drawer', 'Rolling drawer unit', 'Furniture', ['DRAWER_Unit']), ('chair', 'MyMax MX6 chair', 'Furniture', ['CHAIR_']),
    ('stool', 'Bar stool', 'Furniture', ['STOOL_']), ('footrest', 'Footrest', 'Furniture', ['PROP_Footrest']),
    ('aquarium', 'Aquarium', 'Decor', ['AQ_']),
    ('shelfunit', 'Wall-3 shelf unit', 'Wall', ['SHELF_', 'LED_Channels_Shelves', 'LED_Diffusers_Shelves']),
    ('tshelf', 'Floating shelf', 'Wall', ['TSHELF_Boards']),
    ('w1top', 'Door-wall shelf, upper', 'Wall', ['WALL1_Shelf_Top']), ('w1bot', 'Door-wall shelf, lower', 'Wall', ['WALL1_Shelf_Bottom']),
    ('frame', 'Puzzle frame', 'Wall', ['WALL1_Frame', 'WALL1_Picture']),
    ('rug', 'Rug', 'Decor', ['DECOR_Rug']), ('purifier_w', 'Air purifier, white', 'Decor', ['DECOR_Purifier_White']),
    ('purifier_b', 'Air purifier, black', 'Decor', ['DECOR_Purifier_Black']),
    ('slipper1', 'Slipper, left', 'Decor', ['PROP_Slipper_1']), ('slipper2', 'Slipper, right', 'Decor', ['PROP_Slipper_2']),
    ('laptop', 'MacBook Air 13', 'Tech', ['PROP_MacBook', 'PROP_Cable_MagSafe', 'PROP_MagSafe_Plug']),
    ('echo', 'Echo Dot', 'Tech', ['PROP_Echo_Dot']), ('deskitems', 'Desk organiser', 'Decor', ['PROP_Desk_Items']),
    ('lamp', 'Desk lamp', 'Lighting', ['geo_']), ('fan', 'Ceiling fan', 'Lighting', ['FAN_']),
    ('pothos', 'Marble pothos', 'Plants', ['POTHOS_']), ('peperomia', 'Peperomia Hope', 'Plants', ['PEPEROMIA_']),
    ('balcony_plant', 'Potted plant', 'Plants', ['potted_plant_02_']),
    ('piano', 'Korg SP-250 piano', 'Stored', ['PIANO_']), ('old_frame', 'Old puzzle frame', 'Stored', ['DECOR_Puzzle_']),
]
STORED = {'piano', 'old_frame', 'balcony_plant'}
SPLIT_WALLS = {'baseboards', 'crown', 'cove'}       # one item per wall, so the cutaway can hide each side
SPLIT_ISLANDS = {'tshelf'}                           # one item per loose part
SKIP = re.compile(r'^(CUT_|wdg_|cur_|EXT_|LED_|CAM_)')

# ------------------------------------------------------------------ flat colours
OVERRIDE = {'M_Boards_teak': '#A27146', 'M_Desk_Wood': '#A27146', 'M_Shelf_Wood': '#5C3D27', 'M_Floor_Tile': '#C8C2B7',
            'M_Chair_Blue_Quilted': '#1F4FA0', 'M_Pillow_Dots': '#E6E1D8', 'M_Throw_Zigzag': '#C7AE86', 'M_Paper_Notes': '#F1E7C6',
            'M_Peperomia_Hope': '#4F6E30', 'M_Pothos_Marble': '#86A060', 'M_Aq_Gravel': '#B7A687', 'M_Book_Pages': '#ECE5D4',
            'M_Glass': '#D7E6EA', 'M_Aq_Water': '#BFD9E2', 'M_Plywood_Laser': '#C9A27A', 'M_Rodape': '#EDEBE5'}
ALPHA = {'M_Glass': 0.25, 'M_Aq_Water': 0.35, 'M_Car_Glass': 1.0}


def to_hex(lin):
    s = [(12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055) for c in lin[:3]]
    return '#' + ''.join(f'{max(0, min(255, round(v * 255))):02X}' for v in s)


def img_avg(img):
    try:
        im = img.copy(); im.scale(32, 32); a = np.empty(32 * 32 * 4, 'f'); im.pixels.foreach_get(a); bpy.data.images.remove(im)
        a = a.reshape(-1, 4)[:, :3].mean(0)
        if a.sum() <= 0: return None
        return '#' + ''.join(f'{round(v * 255):02X}' for v in a)      # byte images come back display-encoded
    except Exception:
        return None


def mat_hex(m):
    if m is None: return '#B8B4AC'
    if m.name in OVERRIDE: return OVERRIDE[m.name]
    nt = m.node_tree
    if not nt: return to_hex(m.diffuse_color)
    pc = nt.nodes.get('PAINT_COLOR')
    if pc: return to_hex(pc.outputs[0].default_value)
    p = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not p: return '#B8B4AC'
    bc = p.inputs['Base Color']
    if not bc.is_linked: return to_hex(bc.default_value)
    stack, seen = [bc.links[0].from_node], set()
    while stack:
        n = stack.pop()
        if n in seen: continue
        seen.add(n)
        if n.type == 'TEX_IMAGE' and n.image:
            h = img_avg(n.image)
            if h: return h
        stack += [i.links[0].from_node for i in n.inputs if i.is_linked]
    return '#B8B4AC'


FLAT = {}
def flat(m):
    key = m.name if m else 'None'
    if key not in FLAT:
        f = bpy.data.materials.new('F_' + key.replace('M_', '')); f.use_nodes = True
        p = f.node_tree.nodes['Principled BSDF']
        h = mat_hex(m); lin = [((int(h[i:i + 2], 16) / 255 + 0.055) / 1.055) ** 2.4 if int(h[i:i + 2], 16) / 255 > 0.04045 else int(h[i:i + 2], 16) / 255 / 12.92 for i in (1, 3, 5)]
        p.inputs['Base Color'].default_value = (*lin, 1); p.inputs['Roughness'].default_value = 0.8; p.inputs['Metallic'].default_value = 0
        if key in ALPHA and ALPHA[key] < 1:
            p.inputs['Alpha'].default_value = ALPHA[key]
            try: f.surface_render_method = 'BLENDED'
            except Exception: f.blend_method = 'BLEND'
        FLAT[key] = f
    return FLAT[key]


# ------------------------------------------------------------------ geometry helpers
def faces_mesh(src, keep):
    """Copy of mesh `src` keeping only faces whose index is in `keep`."""
    bm = bmesh.new(); bm.from_mesh(src); bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context='FACES')
    me = bpy.data.meshes.new(src.name + '_part'); bm.to_mesh(me); bm.free()
    for m in src.materials: me.materials.append(m)
    return me


def islands(me):
    parent = list(range(len(me.vertices)))
    def find(a):
        while parent[a] != a: parent[a] = parent[parent[a]]; a = parent[a]
        return a
    for e in me.edges:
        a, b = find(e.vertices[0]), find(e.vertices[1])
        if a != b: parent[a] = b
    groups = {}
    for p in me.polygons: groups.setdefault(find(p.vertices[0]), set()).add(p.index)
    return list(groups.values())


def nearest_wall(c):
    d = {4: c.x, 3: ROOM[0] - c.x, 2: c.y, 1: ROOM[1] - c.y}
    return min(d, key=d.get)


def tris(me): return sum(len(p.vertices) - 2 for p in me.polygons)


coll = bpy.data.collections.new('EXPORT'); bpy.context.scene.collection.children.link(coll)
dg = bpy.context.evaluated_depsgraph_get()


def make_item(key, label, cat, me, extra=None):
    """me is in world space; recentre on the floor-centre of its bounds and wrap it in an object."""
    vs = np.empty(len(me.vertices) * 3, 'f'); me.vertices.foreach_get('co', vs); vs = vs.reshape(-1, 3)
    lo, hi = vs.min(0), vs.max(0)
    piv = Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]))
    me.transform(Matrix.Translation(-piv))
    ob = bpy.data.objects.new(key, me); coll.objects.link(ob); ob.location = piv
    n = tris(me)
    if n > MAX_TRIS:
        mod = ob.modifiers.new('dec', 'DECIMATE'); mod.ratio = MAX_TRIS / n
        bpy.context.view_layer.update()
        me2 = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
        ob.modifiers.clear(); ob.data = me2
    ob['label'] = label; ob['cat'] = cat
    ob['size'] = [round(float(v) * 100) for v in (hi - lo)]
    if cat == ARCH: ob['locked'] = 1
    if key.split('_')[0] in STORED or key in STORED: ob['stored'] = 1
    for k, v in (extra or {}).items(): ob[k] = v
    for i, m in enumerate(ob.data.materials): ob.data.materials[i] = flat(m)
    print(f'ITEM {key:24s} {tris(ob.data):6d} tris  {label}')
    return ob


def world_mesh(objs):
    bm = bmesh.new(); mats = []
    for o in objs:
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg)); me.transform(o.matrix_world)
        base = len(mats); remap = []
        for m in me.materials:
            if m not in mats: mats.append(m)
            remap.append(mats.index(m))
        if not me.materials: remap = [len(mats)]; mats.append(None)
        for p in me.polygons: p.material_index = remap[min(p.material_index, len(remap) - 1)]
        bm.from_mesh(me); bpy.data.meshes.remove(me)
    out = bpy.data.meshes.new('m'); bm.to_mesh(out); bm.free()
    for m in mats: out.materials.append(m)
    return out


# ------------------------------------------------------------------ collect objects
STORAGE = set(o.name for o in bpy.data.collections['STORAGE_Removed'].all_objects)
cands = [o for o in bpy.data.objects if o.type in ('MESH', 'CURVE', 'FONT') and not SKIP.match(o.name)
         and (o.name in STORAGE or (o.visible_get() and not o.hide_render)) and o.name not in ('PROP_Wall_Notes',)]
claimed = {}
for o in cands:
    for key, label, cat, pats in GROUPS:
        if any(o.name == p or o.name.startswith(p) for p in pats): claimed.setdefault(key, []).append(o); break
    else:
        if o.name.startswith(('BOOK_', 'DEC_')): claimed.setdefault(o.name, []).append(o)
        else: print('UNCLAIMED', o.name)

if 'STORAGE_Removed' in bpy.context.view_layer.layer_collection.children:      # stored objects must be evaluated
    bpy.context.view_layer.layer_collection.children['STORAGE_Removed'].exclude = False
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()

meta = {k: (l, c) for k, l, c, _ in GROUPS}
for key, objs in claimed.items():
    if key in meta: label, cat = meta[key]
    else:
        nm = re.sub(r'^(BOOK|DEC)_', '', key).replace('_', ' ')
        label = ('Book: ' if key.startswith('BOOK_') else '') + nm[:1].upper() + nm[1:]
        cat = 'Books' if key.startswith('BOOK_') else 'Decor'
    me = world_mesh(objs)
    if key in SPLIT_WALLS:
        byw = {}
        for p in me.polygons: byw.setdefault(nearest_wall(p.center), set()).add(p.index)
        for w, idx in sorted(byw.items()): make_item(f'{key}_w{w}', f'{label}, wall {w}', cat, faces_mesh(me, idx), {'wall': w})
    elif key in SPLIT_ISLANDS:
        parts = sorted(islands(me), key=lambda s: min(me.polygons[i].center.z for i in s))
        for i, idx in enumerate(parts): make_item(f'{key}_{i + 1}', f'{label} {i + 1}', cat, faces_mesh(me, idx))
    else:
        extra = {}
        if key.startswith('wall'): extra['wall'] = int(key[4])
        if key == 'door': extra['wall'] = 1
        if key == 'window': extra['wall'] = 2
        if key == 'outlet': extra['wall'] = 3
        if key == 'ceiling': extra['mount'] = 'ceiling'
        make_item(key, label, cat, me, extra)

for o in bpy.context.scene.objects: o.select_set(False)
for o in coll.objects: o.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_extras=True, export_texcoords=False,
                          export_cameras=False, export_lights=False, export_apply=False, export_materials='EXPORT', export_yup=True)
print('WROTE', OUT, round(os.path.getsize(OUT) / 1e6, 2), 'MB', len(coll.objects), 'items')
