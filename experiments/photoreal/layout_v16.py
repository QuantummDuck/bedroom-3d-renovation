"""Round 16, from Bedroom_v15_Shelves_Frame.blend -> ../teak_navy/Bedroom_v16_Plants_Panels.blend
  Blender -b ../teak_navy/Bedroom_v15_Shelves_Frame.blend --python layout_v16.py
1. Wall-1 frame + both shelves raised 20 cm (frame bottom 105 -> 125).
2. Bed panel (headboard board on wall 1) extended UP until it touches the bottom of the frame (z 87.5 -> 125); its LED halo strip moves with the new top edge.
3. Window wall: a 1.0 cm teak panel (as thick as the window trim stands proud of the wall) from the floor to the bottom edge of the window frame (z 97.5),
   running the full width between the wardrobe and the slat wall.
4. Trailing plants made procedurally (no download): Marble Queen pothos (heart leaves, cream marbling) on the upper shelf, Peperomia 'Hope'
   (round fleshy leaves in threes) on the lower shelf, both hanging over the front edge."""
import bpy, bmesh, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import photoreal_common as P
from mathutils import Vector, Matrix

S = 0.01; OBJ, MAT = bpy.data.objects, bpy.data.materials
RAISE = 20.0
Y1 = 290.0
FW, FH, FD, FB = 75.0, 51.4, 2.6, 2.1
fx0 = 200.0 - FW / 2; fx1 = fx0 + FW; fz0 = 105.0 + RAISE; fz1 = fz0 + FH

# ------------------------------------------------------------------ 1. rebuild the wall-1 composition 20 cm higher
for n in ('WALL1_Frame', 'WALL1_Picture', 'WALL1_Shelf_Top', 'WALL1_Shelf_Bottom'): P.remove(n)
frame_m, pic_m, wood, steel = MAT['M_Frame_Black_Satin'], MAT['M_Puzzle_Picture'], MAT['M_Shelf_Wood'], MAT['M_Steel_Black']
g = P.Geo(); y0 = Y1 - FD
g.box(fx0, fx1, y0, Y1, fz1 - FB, fz1).box(fx0, fx1, y0, Y1, fz0, fz0 + FB)
g.box(fx0, fx0 + FB, y0, Y1, fz0 + FB, fz1 - FB).box(fx1 - FB, fx1, y0, Y1, fz0 + FB, fz1 - FB)
g.box(fx0 + FB, fx1 - FB, Y1 - 0.6, Y1, fz0 + FB, fz1 - FB)
fo = g.finish('WALL1_Frame', 'DECOR_Loose', [frame_m], bevel=(0.12, 2)); fo['dim_source'] = 'USER'
bm = bmesh.new(); uv = bm.loops.layers.uv.new('UVMap'); py = Y1 - 0.75
vs = [bm.verts.new(Vector(c) * S) for c in [(fx0 + FB, py, fz0 + FB), (fx1 - FB, py, fz0 + FB), (fx1 - FB, py, fz1 - FB), (fx0 + FB, py, fz1 - FB)]]
f = bm.faces.new(vs)
for lp, (u, v) in zip(f.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]): lp[uv].uv = (u, v)
me = bpy.data.meshes.new('WALL1_Picture'); bm.to_mesh(me); bm.free(); me.materials.append(pic_m)
po = bpy.data.objects.new('WALL1_Picture', me); P.coll('DECOR_Loose').objects.link(po); po['dim_source'] = 'PHOTO'


def shelf(name, x0, x1, ztop, wall_y):
    g = P.Geo(); D, T = 15.0, 3.0
    g.box(x0, x1, wall_y - D, wall_y, ztop - T, ztop)
    for bx in (x0 + 6, x1 - 6):
        g.box(bx - 0.5, bx + 0.5, wall_y - 0.8, wall_y, ztop - T - 7, ztop - T).box(bx - 0.5, bx + 0.5, wall_y - D + 2, wall_y, ztop - T - 0.6, ztop - T)
    o = g.finish(name, 'FURN_Shelves', [wood, steel], bevel=(0.15, 1))
    for p in o.data.polygons: p.material_index = 0
    return o


PANEL_Y = 288.2                                          # front face of the bed panel on wall 1
TOP_Z, BOT_Z = fz1 + 11.0, fz0 - 5.0                     # shelf top surfaces
UP_X0 = fx0 + 0.75 * FW; LO_X0 = fx0 - 29.0
shelf('WALL1_Shelf_Top', UP_X0, UP_X0 + 48.0, TOP_Z, Y1)
shelf('WALL1_Shelf_Bottom', LO_X0, LO_X0 + 46.0, BOT_Z, PANEL_Y)     # sits on the panel's front face

# ------------------------------------------------------------------ 2. bed panel up to the frame
tk = MAT['M_Boards_teak']
g = P.Geo(); g.box(100.5, 296.0, PANEL_Y, Y1, 0, fz0)
g.finish('BED_Headboard_Wall1', 'FURN_Bed', [tk], bevel=(0.15, 1))['note'] = 'bed panel, extended up to touch the bottom of the frame'
for n in ('LED_Channels_BedPanel', 'LED_Diffusers_BedPanel', 'LED_BedPanel_W1'):                     # halo strip rides on the new top edge
    o = OBJ.get(n)
    if o is not None: o.matrix_world = Matrix.Translation(Vector((0, 0, fz0 - 87.5)) * S) @ o.matrix_world

# ------------------------------------------------------------------ 3. window-wall panel: floor -> bottom of the window frame, 1 cm thick
WIN_BOTTOM = 97.5
g = P.Geo(); g.box(63.0, 296.0, 0.0, 1.0, 0, WIN_BOTTOM)
g.finish('WIN_Wall_Panel', 'ARCH_Architecture', [tk], bevel=(0.12, 1))['note'] = '1 cm teak panel (= how far the window trim stands proud), floor to the bottom of the window frame'

# ------------------------------------------------------------------ 4. procedural trailing plants
def mat_pothos():
    m = MAT.get('M_Pothos_Marble') or P.material('M_Pothos_Marble', '#3E7B30', 0.38); m.use_fake_user = True
    if m.get('built'): return m
    nt = m.node_tree; p = P.bsdf(m); L = nt.links
    tc = P.node(nt, 'ShaderNodeTexCoord', -1500, 200); at = P.node(nt, 'ShaderNodeAttribute', -1500, 0); at.attribute_name = 'rnd'
    sep = P.node(nt, 'ShaderNodeSeparateXYZ', -1300, 250); L.new(tc.outputs['UV'], sep.inputs[0])
    sc_ = P.node(nt, 'ShaderNodeMath', -1300, 0, operation='MULTIPLY'); sc_.inputs[1].default_value = 40.0; L.new(at.outputs['Fac'], sc_.inputs[0])
    cx = P.node(nt, 'ShaderNodeCombineXYZ', -1100, 150); L.new(sep.outputs['X'], cx.inputs['X']); L.new(sep.outputs['Y'], cx.inputs['Y']); L.new(sc_.outputs[0], cx.inputs['Z'])
    n1 = P.node(nt, 'ShaderNodeTexNoise', -900, 250); n1.inputs['Scale'].default_value = 4.5; n1.inputs['Detail'].default_value = 7.0; n1.inputs['Roughness'].default_value = 0.62
    L.new(cx.outputs[0], n1.inputs['Vector'])
    mk = P.maprange(nt, n1.outputs['Fac'], 0.47, 0.60, 0.0, 1.0, -650, 250)                      # marbled cream patches
    # darker green rim: distance from the leaf's mid-line
    ab = P.node(nt, 'ShaderNodeMath', -900, -100, operation='SUBTRACT'); ab.inputs[1].default_value = 0.5; L.new(sep.outputs['X'], ab.inputs[0])
    ab2 = P.node(nt, 'ShaderNodeMath', -750, -100, operation='ABSOLUTE'); L.new(ab.outputs[0], ab2.inputs[0])
    mx = P.node(nt, 'ShaderNodeMix', -300, 250, data_type='RGBA'); L.new(mk, P.sock(mx, 'Factor_Float'))
    P.sock(mx, 'A_Color').default_value = (*P.lin('#3A7A2C'), 1); P.sock(mx, 'B_Color').default_value = (*P.lin('#ECE9B4'), 1)
    L.new(P.sock(mx, 'Result_Color', True), p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.34; p.inputs['Subsurface Weight'].default_value = 0.12; p.inputs['Coat Weight'].default_value = 0.12
    P.add_bump(nt, p, n1.outputs['Fac'], 0.08, 0.002, -300, -300)
    m['built'] = 1; return m


def mat_peperomia():
    m = MAT.get('M_Peperomia_Hope') or P.material('M_Peperomia_Hope', '#2F6A2C', 0.3); m.use_fake_user = True
    if m.get('built'): return m
    nt = m.node_tree; p = P.bsdf(m); L = nt.links
    tc = P.node(nt, 'ShaderNodeTexCoord', -1200, 200); sep = P.node(nt, 'ShaderNodeSeparateXYZ', -1000, 200); L.new(tc.outputs['UV'], sep.inputs[0])
    sb = P.node(nt, 'ShaderNodeMath', -800, 300, operation='SUBTRACT'); sb.inputs[1].default_value = 0.5; L.new(sep.outputs['X'], sb.inputs[0])
    ab = P.node(nt, 'ShaderNodeMath', -650, 300, operation='ABSOLUTE'); L.new(sb.outputs[0], ab.inputs[0])
    rib = P.maprange(nt, ab.outputs[0], 0.0, 0.07, 1.0, 0.0, -500, 300)                          # pale midrib
    nz = P.node(nt, 'ShaderNodeTexNoise', -800, 0); nz.inputs['Scale'].default_value = 9.0; nz.inputs['Detail'].default_value = 4.0; L.new(tc.outputs['UV'], nz.inputs['Vector'])
    tone = P.maprange(nt, nz.outputs['Fac'], 0.3, 0.7, 0.0, 1.0, -500, 0)
    c1 = P.node(nt, 'ShaderNodeMix', -300, 200, data_type='RGBA'); L.new(tone, P.sock(c1, 'Factor_Float'))
    P.sock(c1, 'A_Color').default_value = (*P.lin('#2A5E28'), 1); P.sock(c1, 'B_Color').default_value = (*P.lin('#3F7A35'), 1)
    c2 = P.node(nt, 'ShaderNodeMix', -100, 200, data_type='RGBA'); L.new(rib, P.sock(c2, 'Factor_Float'))
    L.new(P.sock(c1, 'Result_Color', True), P.sock(c2, 'A_Color')); P.sock(c2, 'B_Color').default_value = (*P.lin('#8DBE6A'), 1)
    L.new(P.sock(c2, 'Result_Color', True), p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.28; p.inputs['Subsurface Weight'].default_value = 0.15; p.inputs['Coat Weight'].default_value = 0.2
    m['built'] = 1; return m


class Leaves:
    """One mesh of many leaves; each leaf = ring-fan with a midrib fold and a random value (attribute 'rnd') for per-leaf variation."""
    def __init__(self, name): self.name = name; self.bm = bmesh.new(); self.uv = self.bm.loops.layers.uv.new('UVMap'); self.rn = self.bm.verts.layers.float.new('rnd')

    def leaf(self, base, d, n, length, width, kind, rnd, fold=0.2, cup=0.0, droop=0.0):
        d = Vector(d).normalized(); w = d.cross(Vector(n)).normalized(); nn = w.cross(d).normalized()
        def outline(N):
            pts = []
            for k in range(N):
                t = 2 * math.pi * k / N
                if kind == 'heart':
                    x = 16 * math.sin(t) ** 3; y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
                    pts.append((x / 16.0, (5.0 - y) / 22.0))
                else:
                    pts.append((0.95 * math.sin(t), 0.5 * (1 - math.cos(t)) + 0.07 * max(0.0, -math.cos(t))))
            return pts
        N = 26; outer = outline(N); cu, cv = 0.0, 0.42 if kind == 'heart' else 0.5
        def mk(u, v):
            z = -fold * abs(u) * width * 0.5 + cup * (u * u + (v - 0.5) ** 2) * width - droop * max(v, 0) ** 2 * length
            pos = Vector(base) + d * (v * length) + w * (u * width * 0.5) + nn * z
            vert = self.bm.verts.new(pos * S); vert[self.rn] = rnd; return vert, (0.5 + u / 2, v)
        ring_o = [mk(u, v) for u, v in outer]; ring_i = [mk(cu + (u - cu) * 0.5, cv + (v - cv) * 0.5) for u, v in outer]; ctr = mk(cu, cv)
        def face(vs):
            try: f = self.bm.faces.new([a[0] for a in vs])
            except ValueError: return
            for lp, a in zip(f.loops, vs): lp[self.uv].uv = a[1]
        for k in range(N):
            k2 = (k + 1) % N
            face((ring_o[k], ring_o[k2], ring_i[k2], ring_i[k])); face((ring_i[k], ring_i[k2], ctr))

    def finish(self, mat, collection):
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces[:])
        me = bpy.data.meshes.new(self.name); self.bm.to_mesh(me); self.bm.free(); me.materials.append(mat)
        for p_ in me.polygons: p_.use_smooth = True
        ob = bpy.data.objects.new(self.name, me); P.coll(collection).objects.link(ob); return ob


def bezier(p0, p1, p2, p3, n):
    out = []
    for i in range(n + 1):
        t = i / n; a = (1 - t) ** 3; b = 3 * (1 - t) ** 2 * t; c = 3 * (1 - t) * t * t; d = t ** 3
        out.append(p0 * a + p1 * b + p2 * c + p3 * d)
    return out


def vine(rng, rim, edge_y, edge_z, dx, length):
    """From the pot rim over the shelf's front edge, then hanging with a gentle sway and a curled tip. Returns an arc-length-sampled polyline (cm)."""
    p0 = Vector(rim); p3 = Vector((rim.x + dx, edge_y - 1.6, edge_z - 3.5))
    p1 = p0 + Vector((dx * 0.3, -3.0, 3.0)); p2 = Vector((rim.x + dx * 0.7, edge_y - 0.6, edge_z + 2.0))
    path = bezier(p0, p1, p2, p3, 14)
    ph = rng.uniform(0, 6.28); k = rng.uniform(0.10, 0.17); A = rng.uniform(0.8, 2.2); fwd = rng.uniform(-0.7, 0.7)
    s = 0.0; cur = path[-1].copy(); L0 = sum((path[i + 1] - path[i]).length for i in range(len(path) - 1))
    while L0 + s < length:
        s += 0.8
        cur = Vector((p3.x + A * math.sin(k * (L0 + s) + ph) - A * math.sin(k * L0 + ph), p3.y + fwd * (s / length) * 3.0 - 0.9 * (1 - math.cos(0.08 * s)), p3.z - s * (1 - 0.04 * s / length)))
        path.append(cur)
    return path


def sample(path, step):
    pts, acc, last = [(path[0], 0.0)], 0.0, path[0]
    for q in path[1:]:
        acc += (q - last).length; last = q
        if acc >= step: pts.append((q, 0.0)); acc = 0.0
    return [p for p, _ in pts]


def plant(kind, name, cx, wall_y, ztop, nvines, lengths, seed, pot_color):
    rng = random.Random(seed); pm = mat_pothos() if kind == 'pothos' else mat_peperomia()
    lv = Leaves(name + '_Leaves'); st = P.Geo(); stem_m = P.material(name + '_Stem', '#6F8F3F' if kind == 'pothos' else '#7A7A45', 0.5)
    py = wall_y - 8.5; PR_T, PR_B, PH = 5.4, 3.9, 9.5
    pot = P.Geo(); pot.revolve((cx, py), [(0, ztop), (PR_B, ztop), (PR_B + 0.5, ztop + 0.6), (PR_T, ztop + PH - 0.8), (PR_T + 0.35, ztop + PH - 0.4), (PR_T + 0.2, ztop + PH), (PR_T - 0.8, ztop + PH - 0.2), (PR_T - 0.8, ztop + PH - 1.6)], n=40)
    po = pot.finish(name + '_Pot', 'PLANTS_Wall1', [P.material('M_Pot_' + name, pot_color, 0.45, **{'Coat Weight': 0.3})], smooth=True)
    soil = P.Geo(); soil.revolve((cx, py), [(0, ztop + PH - 1.5), (PR_T - 0.9, ztop + PH - 1.5)], n=24)
    so = P.Geo().cyl((cx, py, ztop + PH - 2.0), (cx, py, ztop + PH - 1.2), PR_T - 0.9, 24).finish(name + '_Soil', 'PLANTS_Wall1', [P.material('M_Soil', '#2A1D14', 0.95)])
    rim_z = ztop + PH - 0.8; edge_y = wall_y - 15.0
    out = Vector((0, -1, 0))
    for vi in range(nvines):
        a = -1.0 + 2.0 * (vi + rng.random() * 0.6) / nvines                                  # spread across the pot front
        rim = Vector((cx + a * 3.8, py - 3.2 - rng.random() * 1.0, rim_z))
        path = vine(rng, rim, edge_y, ztop, a * 2.2 + rng.uniform(-1, 1), rng.uniform(*lengths))
        st.tube(path, 0.13 if kind == 'pothos' else 0.11, 6)
        nodes = sample(path, 6.2 if kind == 'pothos' else 3.0)
        for ni in range(1, len(nodes)):
            pos = nodes[ni]; T = (nodes[ni] - nodes[ni - 1]).normalized(); pos_scale = 1.0 - 0.25 * ni / len(nodes)
            if kind == 'pothos':
                side = Vector((1 if ni % 2 else -1, 0, 0)); yaw = rng.uniform(-0.5, 0.5)
                d = (side * 0.55 + out * 0.5 + T * 0.55).normalized(); d.rotate(Matrix.Rotation(yaw, 3, 'Z'))
                npref = (out * 0.8 + Vector((0, 0, 0.35))).normalized(); ln = rng.uniform(5.0, 7.4) * pos_scale
                lv.leaf(pos + d * 1.2, d, npref, ln, ln * 0.92, 'heart', rng.random(), fold=0.30, cup=0.0, droop=0.10)
                st.cyl(pos, pos + d * 1.2, 0.09, 5, 0, caps=False) if False else None
            else:
                A = T.orthogonal().normalized(); B = T.cross(A).normalized(); th0 = rng.uniform(0, 6.28)
                for j in range(3):
                    th = th0 + j * 2.094 + rng.uniform(-0.3, 0.3); r = A * math.cos(th) + B * math.sin(th)
                    d = (r * 0.85 + T * 0.30).normalized(); ln = rng.uniform(1.9, 2.7) * pos_scale
                    lv.leaf(pos + d * 0.5, d, (r * 0.4 + Vector((0, 0, 0.9)) + out * 0.3).normalized(), ln, ln * 0.95, 'round', rng.random(), fold=0.10, cup=0.35, droop=0.05)
    for j in range(8 if kind == 'pothos' else 14):                                           # leaves rising from the pot
        th = 6.28 * j / (8 if kind == 'pothos' else 14) + rng.uniform(-0.3, 0.3); r = Vector((math.cos(th), math.sin(th), 0)); base = Vector((cx, py, rim_z - 1.2)) + r * 1.5
        d = (r * 0.6 + Vector((0, 0, 0.9))).normalized(); ln = rng.uniform(4.0, 6.0) if kind == 'pothos' else rng.uniform(1.9, 2.5)
        lv.leaf(base, d, (r * 0.3 + Vector((0, 0, 0.6)) + out * 0.5).normalized(), ln, ln * 0.9, 'heart' if kind == 'pothos' else 'round', rng.random(),
                fold=0.25, cup=0.0 if kind == 'pothos' else 0.3, droop=0.12)
    sto = st.finish(name + '_Stems', 'PLANTS_Wall1', [stem_m], smooth=True); lo = lv.finish(pm, 'PLANTS_Wall1')
    return po


P.coll('PLANTS_Wall1', 'PROPS_Lived_In')
for n in [o.name for o in OBJ if o.name.startswith(('POTHOS_', 'PEPEROMIA_'))]: P.remove(n)
plant('pothos', 'POTHOS', UP_X0 + 48.0 - 9.0, Y1, TOP_Z, 6, (40, 64), 21, '#E9E6DE')                  # Marble Queen pothos, white pot, upper shelf
plant('peperomia', 'PEPEROMIA', LO_X0 + 10.0, PANEL_Y, BOT_Z, 8, (28, 50), 22, '#B5683F')            # Peperomia Hope, terracotta pot, lower shelf

# ------------------------------------------------------------------ cameras + save
P.cam('CAM_W1_Frame_Wall', (200, 120, 150), (200, 290, 140), 24, 8.0)
P.cam('CAM_W1_Plants_Close', (200, 205, 150), (205, 290, 142), 35, 4.0, level=False)
P.cam('CAM_W2_Window_Panel', (150, 250, 100), (150, 0, 92), 22, 8.0)
P.cam('CAM_W2_Panel_Detail', (130, 60, 98), (150, 0, 95), 35, 5.6, level=False)
bpy.context.scene['experiment'] = bpy.context.scene.get('experiment', '') + ' | round 16: frame+shelves raised 20, bed panel up to frame, window-wall panel, trailing plants'
bpy.context.preferences.filepaths.save_version = 0
out = os.path.join(P.ROOT, 'experiments', 'teak_navy', 'Bedroom_v16_Plants_Panels.blend')
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True); print('SAVED', out)
