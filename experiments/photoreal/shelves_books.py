"""Your shelves, books and shelf objects (photos 46-49), shared by the twin and v5.
Shelf spacing corrected from the new photos: 21-23 cm books stand under each board with ~1 cm to spare, so the boards are
26.5 cm apart (top surfaces 144.5 / 171.0 / 197.5) instead of the 23 cm read earlier from distant photos."""
import bpy, bmesh, json, math, os
from mathutils import Vector, Matrix
import photoreal_common as P

S = P.S
BOOKS = os.path.join(P.TEX, 'books')
ZMAP = [(-100, -100), (140, 140), (150, 150), (162.5, 166.5), (164.5, 168.5), (167, 171), (185.5, 193), (187.5, 195), (190, 197.5),
        (211, 218.5), (215, 222.5), (400, 407.5)]
TOPS = {'bottom': 144.5, 'middle': 171.0, 'top': 197.5}


def zmap(z):
    for (a, fa), (b, fb) in zip(ZMAP, ZMAP[1:]):
        if a <= z <= b: return fa + (fb - fa) * (z - a) / (b - a)
    return z


def fix_shelf_heights():
    names = ['SHELF_Boards', 'SHELF_Steel_Frames', 'LED_Channels_Shelves', 'LED_Diffusers_Shelves']
    for n in names:
        ob = bpy.data.objects.get(n)
        if not ob or ob.get('pr5_shelf'): continue
        mw = ob.matrix_world; inv = mw.inverted()
        for v in ob.data.vertices:
            w = mw @ v.co; w.z = zmap(w.z / S) * S; v.co = inv @ w
        ob.data.update(); ob['pr5_shelf'] = 1
    for n in ('LED_Shelf_1', 'LED_Shelf_2', 'LED_Shelf_3'):
        ob = bpy.data.objects.get(n)
        if ob and not ob.get('pr5_shelf'):
            ob.location.z = zmap(ob.location.z / S) * S; ob['pr5_shelf'] = 1


# ------------------------------------------------------------------ materials
def page_material():
    m = bpy.data.materials.get('M_Book_Pages')
    if m: return m
    m = P.material('M_Book_Pages', '#E6DECB', 0.85); nt = m.node_tree; p = P.bsdf(m)
    tc = P.node(nt, 'ShaderNodeTexCoord', -900, 0); wv = P.node(nt, 'ShaderNodeTexWave', -700, 0, wave_type='BANDS', bands_direction='Z')
    wv.inputs['Scale'].default_value = 900.0; wv.inputs['Distortion'].default_value = 2.0
    nt.links.new(tc.outputs['Object'], wv.inputs['Vector'])
    P.mul_color(nt, p, P.maprange(nt, wv.outputs['Factor'], 0, 1, 0.9, 1.0, -500, 0), -200, 200)
    return m


def spine_material(bid, info):
    name = f'M_Spine_{bid}'
    m = bpy.data.materials.get(name)
    if m: return m
    m = P.material(name, '#808080', 0.45, **{'Coat Weight': 0.15}); nt = m.node_tree; p = P.bsdf(m)
    t = P.tex(nt, os.path.join(BOOKS, info['tex']), None, -500, 200); t.extension = 'EXTEND'
    nt.links.new(t.outputs['Color'], p.inputs['Base Color'])
    return m


def cover_material(bid, info):
    name = f'M_Cover_{bid}'
    m = bpy.data.materials.get(name)
    if m: return m
    return P.material(name, (*[min(1.0, c * 1.05) for c in info['color']], 1.0), 0.5, **{'Coat Weight': 0.1})


def book(name, x_spine, y0, z0, t, h, depth, bid, info, lying=False, lean=0.0):
    """Standing: spine face at +x, thickness t along y, height h. Lying: length h along y, thickness t along z."""
    bm = bmesh.new(); uv = bm.loops.layers.uv.new('UVMap')
    x0, x1 = x_spine - depth, x_spine
    yl, zl = (h, t) if lying else (t, h)
    c = [Vector(q) * S for q in [(x0, y0, z0), (x1, y0, z0), (x1, y0 + yl, z0), (x0, y0 + yl, z0),
                                 (x0, y0, z0 + zl), (x1, y0, z0 + zl), (x1, y0 + yl, z0 + zl), (x0, y0 + yl, z0 + zl)]]
    v = [bm.verts.new(q) for q in c]
    faces = [((0, 3, 2, 1), 2), ((4, 5, 6, 7), 2), ((0, 1, 5, 4), 0), ((2, 3, 7, 6), 0), ((1, 2, 6, 5), 1), ((3, 0, 4, 7), 2)]
    if lying: faces = [((0, 3, 2, 1), 0), ((4, 5, 6, 7), 0), ((0, 1, 5, 4), 2), ((2, 3, 7, 6), 2), ((1, 2, 6, 5), 1), ((3, 0, 4, 7), 2)]
    umax = 1.0 / max(info.get('vis', 1.0), 0.05) if lying else 1.0
    for idx, mi in faces:
        f = bm.faces.new([v[i] for i in idx]); f.material_index = mi
        for lp in f.loops:
            co = lp.vert.co / S
            if mi == 1: lp[uv].uv = (umax * (co.y - y0) / yl, (co.z - z0) / zl)
            else: lp[uv].uv = (co.y * S * 3, co.z * S * 3)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in (cover_material(bid, info), spine_material(bid, info), page_material()): me.materials.append(m)
    ob = bpy.data.objects.new(name, me); P.coll('PROPS_Books', 'PROPS_Lived_In' if bpy.data.collections.get('PROPS_Lived_In') else None).objects.link(ob)
    md = ob.modifiers.new('Bevel', 'BEVEL'); md.width = 0.0012; md.segments = 2; md.limit_method = 'ANGLE'
    if lean:          # tip toward +y about the bottom edge
        pivot = Vector((x_spine - depth / 2, y0 + (yl if lean > 0 else 0), z0)) * S
        ob.data.transform(Matrix.Translation(-pivot)); ob.data.transform(Matrix.Rotation(-math.radians(lean), 4, 'X'))
        ob.data.transform(Matrix.Translation(pivot))
    ob['dim_source'] = 'PHOTO'; ob['note'] = f'{bid}: spine from your shelf photo'
    return ob


# ------------------------------------------------------------------ layout (order and sizes from photos 46-49)
def build_books(front):
    P.remove('PROP_Books', 'PROP_Shelf_Objects')
    for ob in list(bpy.data.collections['PROPS_Books'].objects) if bpy.data.collections.get('PROPS_Books') else []:
        bpy.data.objects.remove(ob)
    info = json.load(open(os.path.join(BOOKS, 'books.json')))
    xs = front + 22.3                                     # spines just behind the front posts
    def depth_for(h): return max(11.0, min(16.0, 0.68 * h))
    def row(ids, y, z, shelf_lean=None):
        for bid in ids:
            b = info[bid]; lean = (shelf_lean or {}).get(bid, 0.0)
            book(f'BOOK_{bid}', xs, y, z, b['thick'], b['height'], depth_for(b['height']), bid, b, lean=lean); y += b['thick'] + 0.05
        return y
    def stack(ids, y, z, align='left'):
        for bid in ids:                                  # bottom -> top
            b = info[bid]; book(f'BOOK_{bid}', xs, y, z, b['thick'], b['length'], min(b['depth'], 20.0), bid, b, lying=True); z += b['thick']
        return z
    zb, zm = TOPS['bottom'], TOPS['middle']
    # middle shelf
    stack(['mc_escher', 'universo_casca', 'tom_gilbin', 'classicos_ouro', 'contos_machado', 'steve_jobs', 'orwell_1984'], 4.5, zm)
    y = row(['ego_inimigo', 'meditacoes', 'epicteto', 'pense_estoico', '48_leis', 'arte_seducao', 'teste_qi', 'olhos_prateados',
             'metafisica', 'raciocinio', 'almanaque', 'simplicidades'], 29.0, zm)
    decor_middle(front, y, zm)
    row(['eu_robo'], 137.5, zm)
    tb = info['todo_dia_deus']
    ob = book('BOOK_todo_dia_deus', xs, 139.8, zm, tb['thick'], tb['height'], 15.0, 'todo_dia_deus', tb); ob.rotation_euler.z = 0.0
    stack(['padre_pio', 'aumente_qi', '91_truques', 'diario_perdido', 'god_science'], 142.8, zm)
    # bottom shelf
    y = row(['memorias_subsolo', 'essencialismo', 'o_principe', 'schopenhauer', 'genealogia', 'nascimento_tragedia', 'entender_nietzsche'],
            4.5, zb, {'entender_nietzsche': 5.0})
    z = stack(['crepusculo_idolos', '7_habitos', 'habitos_atomicos'], y + 1.3, zb)
    decor_stack_top(front, y + 1.3, z)
    y = row(['revolucao_bichos', 'hugo_cabret', 'etica', 'cortella', 'enigma_quantico'], y + 24.6, zb)
    decor_bottom(front, y, zb)


def mat(name, hexc, rough, metal=0.0, **kw):
    return bpy.data.materials.get(name) or P.material(name, hexc, rough, metal, **kw)


def label_mat(name, png, rough=0.3, metal=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = P.material(name, '#888888', rough, metal); nt = m.node_tree; p = P.bsdf(m)
    t = P.tex(nt, os.path.join(BOOKS, png), None, -500, 200); t.extension = 'EXTEND'; nt.links.new(t.outputs['Color'], p.inputs['Base Color'])
    return m


def can(name, x, y, z, r, h, label, metal=0.6):
    """Cylinder with the photo label wrapped on the front half (facing the room)."""
    g = P.Geo(); n = 32; bm = g.bm; uv = bm.loops.layers.uv.new('UVMap')
    bot = [g.v((x + r * math.cos(2 * math.pi * k / n), y + r * math.sin(2 * math.pi * k / n), z)) for k in range(n)]
    top = [g.v((x + r * math.cos(2 * math.pi * k / n), y + r * math.sin(2 * math.pi * k / n), z + h)) for k in range(n)]
    for k in range(n):
        j = (k + 1) % n; f = g.f((bot[k], bot[j], top[j], top[k]))
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        for lp, (a, w) in zip(f.loops, ((a0, 0), (a1, 0), (a1, 1), (a0, 1))):
            lp[uv].uv = (0.5 + 0.5 * math.sin(a), w)      # front half (facing the room) shows the label left->right
    g.f(bot[::-1], 1); g.f(top, 1)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.materials.append(label_mat(f'M_Label_{name}', label, 0.25, metal)); me.materials.append(mat('M_Can_Top', '#B9BBBE', 0.25, 1.0))
    for p_ in me.polygons: p_.use_smooth = True
    ob = bpy.data.objects.new(name, me); P.coll('PROPS_Books').objects.link(ob)
    return ob


def decor_middle(front, y_after_books, zm):
    xc = front + 13.0
    wood_dark = mat('M_Bookend_Wood', '#4A3424', 0.5)
    P.Geo().box(xc - 6, xc + 6, y_after_books + 0.2, y_after_books + 2.0, zm, zm + 21.5).finish('DEC_Bookend_1', 'PROPS_Books', [wood_dark], bevel=(0.15, 2))
    yb = y_after_books + 2.6                                           # thin light book + Lego McLaren F1 on it
    P.Geo().box(xc - 8, xc + 8, yb, yb + 22, zm, zm + 0.9).finish('DEC_McLaren_Book', 'PROPS_Books', [mat('M_Book_Light', '#E2DED3', 0.6)], bevel=(0.1, 1))
    g = P.Geo(); zc = zm + 0.9; y0 = yb + 2.5
    g.box(xc - 3.2, xc + 3.2, y0, y0 + 16.5, zc + 0.6, zc + 3.2, 0)          # chassis
    g.box(xc - 1.2, xc + 1.2, y0 + 5, y0 + 11, zc + 3.2, zc + 4.6, 1)        # cockpit / halo
    g.box(xc - 4.6, xc + 4.6, y0, y0 + 1.6, zc + 0.6, zc + 1.6, 1)           # front wing
    g.box(xc - 4.2, xc + 4.2, y0 + 15, y0 + 16.5, zc + 3.2, zc + 5.0, 1)     # rear wing
    for yy in (y0 + 3.0, y0 + 13.0):
        for sx in (-1, 1): g.cyl((xc + sx * 3.4, yy, zc + 1.8), (xc + sx * 5.0, yy, zc + 1.8), 1.8, 20, 2)
    g.finish('DEC_Lego_McLaren', 'PROPS_Books', [mat('M_Lego_Papaya', '#E8761C', 0.3), mat('M_Lego_Black', '#141414', 0.35), mat('M_Rubber_Black', '#1D1D1D', 0.8)],
             bevel=(0.12, 1))
    white = mat('M_Figure_White', '#ECEBE6', 0.35); gold = mat('M_Visor_Gold', '#C9A04A', 0.15, 1.0)
    for k, yy in enumerate((yb + 25.0, yb + 30.5)):                      # astronaut figurines
        g = P.Geo(); g.box(xc - 1.6, xc + 1.6, yy - 1.8, yy + 1.8, zm, zm + 5.2, 0).sphere((xc, yy, zm + 7.4), 2.2, 0, 16)
        g.sphere((xc + 1.4, yy, zm + 7.5), 1.3, 1, 12); g.box(xc - 2.6, xc - 1.6, yy - 1.5, yy + 1.5, zm + 2.5, zm + 5.5, 0)
        g.finish(f'DEC_Astronaut_{k}', 'PROPS_Books', [white, gold], smooth=True)
    g = P.Geo(); yr = yb + 35.5; g.cyl((xc, yr, zm), (xc, yr, zm + 11.0), 0.9, 16).cyl((xc, yr, zm + 11.0), (xc, yr, zm + 13.0), 0.9, 16, r1=0.05)
    g.finish('DEC_Rocket', 'PROPS_Books', [white], smooth=True)
    ys = yb + 38.0                                                      # pencil sharpener (black, cat ears)
    g = P.Geo(); g.box(xc - 4, xc + 4, ys, ys + 7.5, zm, zm + 10.5).box(xc - 3.5, xc - 1.5, ys + 0.5, ys + 2.5, zm + 10.5, zm + 12.0)
    g.box(xc - 3.5, xc - 1.5, ys + 5, ys + 7, zm + 10.5, zm + 12.0)
    g.finish('DEC_Pencil_Sharpener', 'PROPS_Books', [mat('M_Plastic_Black_Gloss', '#121212', 0.25)], bevel=(0.6, 3))
    yf = ys + 9.0                                                       # black document box with latch
    g = P.Geo(); g.box(xc - 6, xc + 6, yf, yf + 24.0, zm, zm + 21.0, 0).box(xc + 6, xc + 6.4, yf + 11, yf + 13, zm + 13, zm + 16.5, 1)
    g.finish('DEC_File_Box', 'PROPS_Books', [mat('M_File_Box', '#2A2A2B', 0.55), mat('M_Plastic_Black_Gloss', '#121212', 0.25)], bevel=(0.3, 2))
    yd = yf + 25.5                                                      # deodorants + Fisiofort tube
    can('DEC_Deo_Navy', xc + 2, yd + 2.5, zm, 2.5, 15.5, 'deo_navy.png', 0.0)
    can('DEC_Spray_Teal', xc + 1, yd + 8.2, zm, 3.3, 20.5, 'spray_teal.png', 0.0)
    can('DEC_Fisiofort', xc + 1.5, yd + 13.5, zm, 2.5, 19.0, 'fisiofort.png', 0.0)


def decor_stack_top(front, y, z):
    xc = front + 13.0                                                   # incense dish + RGB remote on the Habitos stack
    g = P.Geo(); g.revolve((xc - 1, y + 9), [(0, z), (6.5, z + 0.3), (7.2, z + 1.2), (7.0, z + 1.3), (6.2, z + 0.7), (0, z + 0.5)], n=48)
    g.finish('DEC_Incense_Dish', 'PROPS_Books', [mat('M_Metal_Brushed', '#BDBDBD', 0.32, 1.0)], smooth=True)
    P.Geo().box(xc - 4, xc + 4, y + 17, y + 22, z, z + 1.2).finish('DEC_RGB_Remote', 'PROPS_Books', [mat('M_Plastic_Black_Gloss', '#121212', 0.25)], bevel=(0.3, 2))


def decor_bottom(front, y, zb):
    xc = front + 13.0
    cal = label_mat('M_Calendar_Front', 'calendar.png', 0.5)
    g = P.Geo(); g.box(xc + 2.0, xc + 6.5, y + 0.5, y + 13.5, zb, zb + 13.0); cob = g.finish('DEC_Calendar_2025', 'PROPS_Books', [cal], bevel=(0.2, 2))
    for p_ in cob.data.polygons:
        if p_.normal.x > 0.9:      # front face shows the photo
            for li in p_.loop_indices:
                co = cob.data.vertices[cob.data.loops[li].vertex_index].co / S
                cob.data.uv_layers[0].data[li].uv = ((co.y - (y + 0.5)) / 13.0, (co.z - zb) / 13.0)
    yk = y + 14.5                                                       # Mar sem fim + two red Ferrari models
    info = json.load(open(os.path.join(BOOKS, 'books.json')))
    b = info['mar_sem_fim']; book('BOOK_mar_sem_fim', front + 22.3, yk, zb, b['thick'], b['length'], 16.0, 'mar_sem_fim', b, lying=True)
    red = mat('M_Ferrari_Red', '#B5121B', 0.15, **{'Coat Weight': 1.0}); glass = mat('M_Car_Glass', '#202326', 0.05)
    for k, (dy, dx) in enumerate(((2.0, -1.0), (11.5, 1.5))):
        g = P.Geo(); z0 = zb + b['thick']; x0 = xc + dx; y0 = yk + dy
        g.box(x0 - 2.0, x0 + 2.0, y0, y0 + 9.5, z0 + 0.6, z0 + 2.0, 0).box(x0 - 1.6, x0 + 1.6, y0 + 3.0, y0 + 6.8, z0 + 2.0, z0 + 3.0, 1)
        for yy in (y0 + 1.8, y0 + 7.7):
            for sx in (-1, 1): g.cyl((x0 + sx * 1.9, yy, z0 + 0.8), (x0 + sx * 2.3, yy, z0 + 0.8), 0.8, 16, 2)
        g.finish(f'DEC_Ferrari_{k}', 'PROPS_Books', [red, glass, mat('M_Rubber_Black', '#1D1D1D', 0.8)], bevel=(0.5, 3), smooth=True)
    yc = yk + 24.5
    g = P.Geo(); g.cyl((xc, yc + 4.0, zb), (xc, yc + 4.0, zb + 0.6), 4.6, 40); g.finish('DEC_Cork_Coaster', 'PROPS_Books', [mat('M_Cork', '#B68B5B', 0.8)])
    can('DEC_Monster_Blue', xc, yc + 4.0, zb + 0.6, 3.3, 15.7, 'can_blue.png')
    ye = yc + 8.8
    P.Geo().box(xc - 6, xc + 6, ye, ye + 1.8, zb, zb + 22.5).finish('DEC_Bookend_2', 'PROPS_Books', [mat('M_Bookend_Wood', '#4A3424', 0.5)], bevel=(0.15, 2))
    nb = mat('M_Notebook_Black', '#1A1A1B', 0.6)
    for k in range(5):
        P.Geo().box(xc - 8.5, xc + 7.5, ye + 2.0 + 1.45 * k, ye + 3.35 + 1.45 * k, zb, zb + 18.3).finish(f'DEC_Notebook_{k}', 'PROPS_Books', [nb], bevel=(0.25, 2))
    yd = ye + 10.0
    z = zb
    for bid in ('uma_vida_propositos', 'darwin_origem', 'blue_notebook'):
        b = info[bid]; book(f'BOOK_{bid}', front + 22.3, yd, z, b['thick'], min(b['length'], 21.0), 15.0, bid, b, lying=True); z += b['thick']
    g = P.Geo(); g.sphere((xc - 2, yd + 6, z + 0.9), 1.6, 0, 12, rz=0.9)
    g.finish('DEC_Stone', 'PROPS_Books', [mat('M_Stone', '#5E5B57', 0.8)], smooth=True)
    g = P.Geo(); x0 = xc; y0 = yd + 12                                 # white Lego hypercar on the stack
    g.box(x0 - 2.6, x0 + 2.6, y0, y0 + 9.5, z + 0.6, z + 2.6, 0).box(x0 - 1.8, x0 + 1.8, y0 + 3.2, y0 + 6.5, z + 2.6, z + 3.6, 1)
    g.finish('DEC_Lego_Hypercar', 'PROPS_Books', [mat('M_Lego_White', '#E9E9E6', 0.3), mat('M_Lego_Black', '#141414', 0.35)], bevel=(0.15, 1))
    yp = yd + 22.0                                                      # pen tin
    if yp + 7 < 131:
        g = P.Geo(); g.cyl((xc, yp + 3.5, zb), (xc, yp + 3.5, zb + 10.5), 3.4, 40, caps=True)
        g.finish('DEC_Pen_Tin', 'PROPS_Books', [mat('M_Tin', '#A9ABAD', 0.35, 1.0)], smooth=True)
        for k in range(7):
            a = 2 * math.pi * k / 7; g = P.Geo()
            g.cyl((xc + 1.8 * math.cos(a), yp + 3.5 + 1.8 * math.sin(a), zb + 4), (xc + 3.0 * math.cos(a), yp + 3.5 + 3.0 * math.sin(a), zb + 18.5 + k % 3), 0.45, 8)
            g.finish(f'DEC_Pen_{k}', 'PROPS_Books', [mat(['M_Pen_Black', 'M_Pen_Red', 'M_Pen_Green'][k % 3], ['#1B1B1B', '#B3261E', '#3E9B4F'][k % 3], 0.3)], smooth=True)


def decor_top(front):
    zt = TOPS['top']; xc = front + 12.5
    ply = bpy.data.materials.get('M_Plywood_Laser')
    if not ply:
        ply = P.material('M_Plywood_Laser', '#C9A37A', 0.6); nt = ply.node_tree; p = P.bsdf(ply)
        v = P.uv_vec(nt, 0.5, rot=90, x=-1500, y=200, coord='Object')
        t = P.tex(nt, os.path.join(P.TEX, 'oak_veneer_01', 'oak_veneer_01_diff_2k.jpg'), v, -1200, 200)
        hs = P.node(nt, 'ShaderNodeHueSaturation', -900, 200); hs.inputs['Value'].default_value = 1.6; hs.inputs['Saturation'].default_value = 0.8
        nt.links.new(t.outputs['Color'], hs.inputs['Color']); nt.links.new(hs.outputs['Color'], p.inputs['Base Color'])
    g = P.Geo()                                                         # marble-run machine (laser-cut plywood)
    g.box(xc - 7, xc + 7, 6, 44, zt, zt + 0.6)
    for yy in (8, 20, 32, 42): g.box(xc - 5, xc + 5, yy, yy + 0.4, zt + 0.6, zt + 18)
    for k, (yc, zc, R) in enumerate(((16, 9, 6.5), (27, 13, 5.0), (37, 8, 4.0))):
        g.tube([(xc - 3, yc + R * math.cos(math.pi * i / 28), zt + zc + R * math.sin(math.pi * i / 28)) for i in range(29)], 0.35, 8)
    for yy in range(10, 42, 4): g.box(xc + 2, xc + 4, yy, yy + 2.4, zt + 3 + (yy % 7), zt + 3.6 + (yy % 7))
    g.finish('DEC_Wooden_Marble_Run', 'PROPS_Books', [ply])
    g = P.Geo()                                                         # vintage film projector (laser-cut)
    g.box(xc - 6, xc + 6, 52, 70, zt, zt + 11).cyl((xc + 6, 61, zt + 6), (xc + 10, 61, zt + 6), 2.2, 24)
    for yy in (55, 67): g.cyl((xc - 1, yy, zt + 17), (xc + 1, yy, zt + 17), 5.5, 32)
    g.finish('DEC_Wooden_Projector', 'PROPS_Books', [ply])
    g = P.Geo(); g.box(xc - 9, xc - 8, 92, 132, zt, zt + 30)              # black board leaning at the back
    g.finish('DEC_Black_Board', 'PROPS_Books', [mat('M_Black_Board', '#1E1E1F', 0.7)])
    yel = mat('M_Robot_Yellow', '#F2C200', 0.35); blk = mat('M_Plastic_Black_Gloss', '#121212', 0.25)
    g = P.Geo(); g.cyl((xc, 108, zt), (xc, 108, zt + 3.5), 6.5, 32, 1).cyl((xc, 108, zt + 3.5), (xc, 108, zt + 7), 4.5, 32, 0)
    g.box(xc - 1.5, xc + 1.5, 105.5, 110.5, zt + 7, zt + 19, 0).box(xc - 1.2, xc + 1.2, 108, 122, zt + 17, zt + 20, 0).box(xc - 1, xc + 1, 120, 124, zt + 12, zt + 20, 1)
    g.finish('DEC_Robot_Arm', 'PROPS_Books', [yel, blk], bevel=(0.3, 2))
    brn = mat('M_Lego_Brown', '#6B4A2E', 0.3)
    g = P.Geo(); g.box(xc - 4, xc + 4, 138, 150, zt, zt + 1.2).box(xc - 1, xc + 1, 143, 145, zt + 1.2, zt + 9).box(xc - 3, xc + 3, 141, 147, zt + 9, zt + 13)
    g.finish('DEC_Lego_Display', 'PROPS_Books', [brn], bevel=(0.15, 1))
    g = P.Geo(); g.box(xc - 2, xc + 2, 156, 161, zt, zt + 6).sphere((xc, 158.5, zt + 9.5), 3.6, 0, 20)
    g.finish('DEC_Funko', 'PROPS_Books', [mat('M_Funko', '#3A3F4A', 0.4)], smooth=True)


def shelf_fairy_lights(front):
    """Twin only: your warm copper-wire fairy lights hanging under the three boards (photos 46-49)."""
    bead = bpy.data.materials.get('M_Fairy_Bulb') or P.material('M_Fairy_Bulb', '#FFF2D6', 0.2, **{'Emission Color': (1.0, 0.72, 0.38, 1)})
    wire = mat('M_Copper_Wire', '#B87333', 0.35, 1.0)
    for k, (zt, y0, y1) in enumerate(((TOPS['bottom'] - 2.5, 6, 129), (TOPS['middle'] - 2.5, 6, 169), (TOPS['top'] - 2.5, 6, 169))):
        pts = []; n = 60
        for i in range(n + 1):
            yy = y0 + (y1 - y0) * i / n; sag = 2.2 * abs(math.sin(math.pi * (yy - y0) / 23.0))
            pts.append((front + 6.0 + 1.5 * math.sin(i * 1.3), yy, zt - 0.6 - sag))
        g = P.Geo(); g.tube(pts, 0.05, 5); g.finish(f'DEC_Fairy_Wire_{k}', 'PROPS_Books', [wire])
        g = P.Geo()
        for i in range(0, n + 1, 3):
            x, yy, zz = pts[i]; g.sphere((x, yy, zz - 0.35), 0.28, 0, 8)
        b = g.finish(f'DEC_Fairy_Beads_{k}', 'PROPS_Books', [bead], smooth=True)
        lt = bpy.data.lights.new(f'LIGHT_Shelf_Fairy_{k + 1}', 'AREA'); lt.shape = 'RECTANGLE'; lt.size = 0.05; lt.size_y = (y1 - y0) * S
        lt.use_temperature = True; lt.temperature = 2400.0; lt.energy = 0.0
        lo = bpy.data.objects.new(f'LIGHT_Shelf_Fairy_{k + 1}', lt); P.coll('PROPS_Books').objects.link(lo)
        lo.location = Vector((front + 6.0, (y0 + y1) / 2, zt - 3.0)) * S; lo.rotation_euler = (0, math.radians(-60), 0)
        lo['base_energy'] = 6.0 * (y1 - y0) / 100
