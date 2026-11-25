"""Builds the A3 fabrication drawing set from views/*.png + views/*.json (render_views.py) -> Fabrication_Drawings_v19.html / .pdf
  python3 experiments/schematic/build_sheets.py        (then Chrome headless prints the PDF)
Sheet coordinates are millimetres (SVG viewBox 420 x 297)."""
import json, math, os, subprocess
import spec as S
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'Fabrication_Drawings_v19')
FONT = "Helvetica Neue, Helvetica, Arial, sans-serif"
INK, THIN = '#1d1f22', 0.18
NSHEETS = len(S.SHEETS)


def esc(t): return str(t).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def T(x, y, s, size=2.5, anchor='start', weight=400, rot=0, fill=INK, halo=False, italic=False):
    tr = f' transform="rotate({rot:.2f} {x:.2f} {y:.2f})"' if rot else ''
    h = ' stroke="#fff" stroke-width="0.9" paint-order="stroke"' if halo else ''
    st = ' font-style="italic"' if italic else ''
    return f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" fill="{fill}"{tr}{h}{st}>{esc(s)}</text>'


def L(x1, y1, x2, y2, w=THIN, extra=''):
    return f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{INK}" stroke-width="{w}" {extra}/>'


def R(x, y, w, h, fill='none', sw=0.25, extra=''):
    return f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{fill}" stroke="{INK}" stroke-width="{sw}" {extra}/>'


def tw(s, size): return sum(0.7 if c.isupper() or c.isdigit() else 0.3 if c in ' .,:·()' else 0.52 for c in str(s)) * size


# ------------------------------------------------------------------ annotation primitives (view-local mm + origin)
def dim(a, b, a2, b2, text, ox=0, oy=0, size=2.4):
    a, b, a2, b2 = [(p[0] + ox, p[1] + oy) for p in (a, b, a2, b2)]
    out = []
    for p, q in ((a, a2), (b, b2)):                       # extension lines with a 1 mm gap, 1.5 mm overshoot
        ex, ey = q[0] - p[0], q[1] - p[1]; n = math.hypot(ex, ey)
        if n > 1.6:
            ux, uy = ex / n, ey / n
            out.append(L(p[0] + ux, p[1] + uy, q[0] + ux * 1.5, q[1] + uy * 1.5, 0.13))
    dx, dy = b2[0] - a2[0], b2[1] - a2[1]; n = math.hypot(dx, dy) or 1; ux, uy = dx / n, dy / n
    ang = math.degrees(math.atan2(dy, dx))
    if ang > 90.1 or ang <= -89.9: ang -= 180 if ang > 0 else -180
    nx, ny = math.sin(math.radians(ang)), -math.cos(math.radians(ang))   # text side: "above" the rotated baseline
    if n >= tw(text, size) + 5:
        out.append(f'<line x1="{a2[0]:.2f}" y1="{a2[1]:.2f}" x2="{b2[0]:.2f}" y2="{b2[1]:.2f}" stroke="{INK}" stroke-width="{THIN}" marker-start="url(#ar)" marker-end="url(#ar)"/>')
        mx, my = (a2[0] + b2[0]) / 2 + nx * 0.8, (a2[1] + b2[1]) / 2 + ny * 0.8
        out.append(T(mx, my, text, size, 'middle', rot=ang, halo=True))
    else:                                                  # short dimension: arrows from outside, text past the end
        out.append(L(a2[0], a2[1], b2[0], b2[1]))
        for p, s in ((a2, -1), (b2, 1)):
            out.append(f'<line x1="{p[0] + s * ux * 4:.2f}" y1="{p[1] + s * uy * 4:.2f}" x2="{p[0]:.2f}" y2="{p[1]:.2f}" stroke="{INK}" stroke-width="{THIN}" marker-end="url(#ar)"/>')
        d = 5 + tw(text, size) / 2
        out.append(T(b2[0] + ux * d + nx * 0.8, b2[1] + uy * d + ny * 0.8, text, size, 'middle', rot=ang, halo=True))
    return ''.join(out)


def note(p, text, dx, dy, ox=0, oy=0, size=2.4):
    x, y = p[0] + ox, p[1] + oy
    if not dx and not dy: return T(x, y + size * 0.35, text, size, 'middle', 600, halo=True)
    qx, qy = x + dx, y + dy; s = 1 if dx >= 0 else -1
    return (f'<circle cx="{x:.2f}" cy="{y:.2f}" r="0.45" fill="{INK}"/>' + L(x, y, qx, qy, 0.15) + L(qx, qy, qx + 3 * s, qy, 0.15)
            + T(qx + 4 * s, qy + size * 0.35, text, size, 'start' if s > 0 else 'end', halo=True))


def balloon(p, n, dx, dy, ox=0, oy=0, r=3.6):
    x, y = p[0] + ox, p[1] + oy; qx, qy = x + dx, y + dy; d = math.hypot(dx, dy) or 1
    return (f'<circle cx="{x:.2f}" cy="{y:.2f}" r="0.6" fill="{INK}"/>' + L(x, y, qx - dx / d * r, qy - dy / d * r, 0.2)
            + f'<circle cx="{qx:.2f}" cy="{qy:.2f}" r="{r}" fill="#fff" stroke="{INK}" stroke-width="0.3"/>' + T(qx, qy + 1.2, n, 3.2, 'middle', 700))


def hidden_box(pts, label, ox, oy):
    pp = ' '.join(f'{x + ox:.2f},{y + oy:.2f}' for x, y in pts)
    s = f'<polygon points="{pp}" fill="none" stroke="{INK}" stroke-width="0.2" stroke-dasharray="1.2 0.8"/>'
    if label:
        cx, cy = sum(p[0] for p in pts) / 4 + ox, sum(p[1] for p in pts) / 4 + oy
        s += T(cx, cy + 0.8, label, 2.1, 'middle', italic=True, halo=True)
    return s


def view(name, x, y):
    v = json.load(open(os.path.join(HERE, 'views', name + '.json'))); w, h = v['box']
    s = [f'<image href="views/{name}.png" x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="none"/>']
    for a in v['ann']:
        k = a['kind']
        if k == 'dim': s.append(dim(a['a'], a['b'], a['a2'], a['b2'], a['text'], x, y))
        elif k == 'note': s.append(note(a['p'], a['text'], a['dx'], a['dy'], x, y))
        elif k == 'bal': s.append(balloon(a['p'], a['n'], a['dx'], a['dy'], x, y))
        elif k == 'box': s.append(hidden_box(a['pts'], a['label'], x, y))
    letter, title, scale = S.VIEW_TITLES[name]
    s.append(view_label(x, y + h + 6, letter, title, scale))
    return ''.join(s)


def view_label(x, y, letter, title, scale):
    if not letter: return T(x, y + 0.2, title.upper(), 2.9, weight=600) + T(x, y + 4.2, 'SCALE ' + scale, 2.2, fill='#555')
    return (f'<circle cx="{x + 3.2:.2f}" cy="{y - 1.1:.2f}" r="3.2" fill="none" stroke="{INK}" stroke-width="0.3"/>' + T(x + 3.2, y + 0.1, letter, 3.4, 'middle', 700)
            + T(x + 8.5, y + 0.2, title.upper(), 2.9, weight=600) + T(x + 8.5, y + 4.2, 'SCALE ' + scale, 2.2, fill='#555'))


# ------------------------------------------------------------------ vector part drawings
def part(x, y, Lmm, Wmm, scale, tag, title, fill=S.COLORS['teak'], holes=(), tdim=None, sub=''):
    """Flat part in plan: rectangle Lmm x Wmm drawn at 1:scale with overall dims; holes = (cx, cy, d) in part mm from top-left."""
    w, h = Lmm / scale, Wmm / scale
    s = [R(x, y, w, h, fill, 0.3)]
    for cx, cy, d in holes:
        s.append(f'<circle cx="{x + cx / scale:.2f}" cy="{y + cy / scale:.2f}" r="{d / 2 / scale:.2f}" fill="#fff" stroke="{INK}" stroke-width="0.25"/>')
        s.append(L(x + cx / scale - 1.5, y + cy / scale, x + cx / scale + 1.5, y + cy / scale, 0.1) + L(x + cx / scale, y + cy / scale - 1.5, x + cx / scale, y + cy / scale + 1.5, 0.1))
    s.append(dim((x, y + h), (x + w, y + h), (x, y + h + 5), (x + w, y + h + 5), fmt(Lmm)))
    s.append(dim((x + w, y), (x + w, y + h), (x + w + 5, y), (x + w + 5, y + h), fmt(Wmm)))
    if tdim: s.append(R(x, y - 3 - tdim / scale, w, tdim / scale, fill, 0.25) + T(x + w + 2, y - 3 - tdim / scale / 2 + 0.8, f't = {fmt(tdim)}', 2.2))
    s.append(tag_label(x, y + h + 13, tag, title, f'1:{scale}', sub))
    return ''.join(s)


def broken(x, y, Lmm, Wmm, draw_w, scale, tag, title, fill=S.COLORS['teak'], sub=''):
    """Long part drawn with a break: true width at 1:scale, length shortened to draw_w mm."""
    h = Wmm / scale; g = 3; m = x + draw_w / 2
    zig = lambda cx: f'M{cx - 0.8:.2f},{y - 1.5:.2f} L{cx + 0.8:.2f},{y + h * 0.35:.2f} L{cx - 0.8:.2f},{y + h * 0.65:.2f} L{cx + 0.8:.2f},{y + h + 1.5:.2f}'
    s = [R(x, y, draw_w / 2 - g, h, fill, 0.3), R(m + g, y, draw_w / 2 - g, h, fill, 0.3),
         f'<path d="{zig(m - g)} M{zig(m + g)[1:]}" fill="none" stroke="{INK}" stroke-width="0.2"/>'.replace('M M', 'M')]
    s.append(dim((x, y + h), (x + draw_w, y + h), (x, y + h + 5), (x + draw_w, y + h + 5), fmt(Lmm)))
    s.append(dim((x + draw_w, y), (x + draw_w, y + h), (x + draw_w + 5, y), (x + draw_w + 5, y + h), fmt(Wmm)))
    s.append(tag_label(x, y + h + 13, tag, title, f'1:{scale} (broken)', sub))
    return ''.join(s)


def tag_label(x, y, tag, title, scale, sub=''):
    s = (f'<rect x="{x:.2f}" y="{y - 3.6:.2f}" width="{tw(tag, 2.8) + 3:.2f}" height="4.8" fill="{INK}"/>' + T(x + 1.5, y, tag, 2.8, weight=700, fill='#fff')
         + T(x + tw(tag, 2.8) + 5, y, title.upper(), 2.6, weight=600))
    return s + T(x, y + 4.4, f'SCALE {scale}' + (f'  ·  {sub}' if sub else ''), 2.2, fill='#444')


def fmt(v): return f'{v:g}'


def text_block(x, y, lines, size=2.4, lh=4.0, head=None):
    s = [T(x, y, head, 3.0, weight=700)] if head else []
    y += 5.5 if head else 0
    for ln in lines:
        s.append(T(x, y, ln, size, weight=600 if ln.startswith('#') else 400) if not ln.startswith('#') else T(x, y, ln[1:], size, weight=700)); y += lh
    return ''.join(s)


def table(x, y, cols, rows, size=2.25, rh=4.6, head_fill='#E9E7E2'):
    """cols = [(header, width, anchor)], rows = list of lists of str."""
    W = sum(c[1] for c in cols); s = [R(x, y, W, rh, head_fill, 0.25)]
    cx = x
    for h, w, an in cols:
        s.append(T(cx + (1.2 if an == 'start' else w - 1.2 if an == 'end' else w / 2), y + rh - 1.4, h, size, an, 700)); cx += w
    for i, r in enumerate(rows):
        yy = y + rh * (i + 1)
        s.append(R(x, yy, W, rh, '#fff' if i % 2 == 0 else '#F7F6F3', 0.12))
        cx = x
        for (h, w, an), val in zip(cols, r):
            s.append(T(cx + (1.2 if an == 'start' else w - 1.2 if an == 'end' else w / 2), yy + rh - 1.4, val, size, an)); cx += w
    cx = x
    for h, w, an in cols[:-1]:
        cx += w; s.append(L(cx, y, cx, y + rh * (len(rows) + 1), 0.12))
    s.append(R(x, y, W, rh * (len(rows) + 1), 'none', 0.3))
    return ''.join(s)


# ------------------------------------------------------------------ sheet frame
def frame(sh):
    s = [R(10, 10, 400, 277, 'none', 0.6)]
    for i in range(8):                       # zone markers
        x = 10 + 50 * i
        s += [L(x, 10, x, 6, 0.25), L(x, 287, x, 291, 0.25), T(x + 25, 8.6, str(i + 1), 2.4, 'middle', fill='#666'), T(x + 25, 290.4, str(i + 1), 2.4, 'middle', fill='#666')]
    for i, c in enumerate('ABCD'):
        y = 10 + 69.25 * i
        s += [L(10, y, 6, y, 0.25), L(410, y, 414, y, 0.25), T(8, y + 35.5, c, 2.4, 'middle', fill='#666'), T(412, y + 35.5, c, 2.4, 'middle', fill='#666')]
    x0, y0 = 250, 252; s.append(R(x0, y0, 160, 35, '#fff', 0.5))
    s += [L(x0, y0 + 12, 410, y0 + 12, 0.3), L(x0, y0 + 24, 410, y0 + 24, 0.3), L(x0 + 110, y0 + 12, x0 + 110, 287, 0.3), L(x0 + 55, y0 + 24, x0 + 55, 287, 0.3),
          L(x0 + 135, y0 + 24, x0 + 135, 287, 0.3)]
    lab = lambda x, y, t: T(x, y, t, 1.8, fill='#777')
    s += [lab(x0 + 2, y0 + 3, 'PROJECT'), T(x0 + 2, y0 + 9.4, 'BEDROOM RENOVATION  ·  TEAK & NAVY', 4.2, weight=700),
          lab(x0 + 2, y0 + 15, 'DRAWING'), T(x0 + 2, y0 + 21.2, sh['title'], 3.6, weight=700),
          lab(x0 + 112, y0 + 15, 'SHEET'), T(x0 + 112, y0 + 21.2, f'{sh["n"]} / {NSHEETS}', 3.6, weight=700),
          lab(x0 + 2, y0 + 27, 'MODEL'), T(x0 + 2, y0 + 32, 'Bedroom_v19_Wall_Shelves.blend', 2.3),
          lab(x0 + 57, y0 + 27, 'UNITS  ·  TOLERANCE'), T(x0 + 57, y0 + 32, 'mm  ·  ±1 unless noted', 2.3),
          lab(x0 + 112, y0 + 27, 'DATE'), T(x0 + 112, y0 + 32, '2026-10-21', 2.3),
          lab(x0 + 137, y0 + 27, 'REV'), T(x0 + 137, y0 + 32, 'A', 2.6, weight=700)]
    s.append(T(14, 284.5, 'Verify all dimensions on site before cutting. Walls are not perfectly square: parts that meet walls are cut +10 mm long and scribed.', 2.0, fill='#666'))
    return ''.join(s)


# ------------------------------------------------------------------ sheet contents
PARTS_INDEX = [('1', 'Slat wall: 72 slats + felt + battens', 'teak / black PET felt', '2'), ('2', 'L-shaped desk top T1 + T2', 'teak, 30 mm', '3'),
               ('3', 'Desk legs ×5', 'black steel 30×30 tube', '3'), ('4', 'Rolling drawer unit', 'teak-veneered 18 mm', '6'),
               ('5', 'Floating shelves ×5 (window wall)', 'dark wood, 25 mm', '4'), ('6', 'Window-wall panel', 'teak plywood, 10 mm', '4'),
               ('7', 'Bed-wall panel', 'teak plywood, 18 mm', '5'), ('8', 'Door-wall shelves ×2 + L-brackets', 'dark wood 30 mm + steel', '5'),
               ('9', 'Cove ledge (4 walls)', 'MDF, painted navy', '7'), ('10', 'Wardrobe re-facing (optional)', 'teak veneer + navy strips', '7')]
NOTES = ['1.  All dimensions in millimetres; drawn from the v19 Blender model of the room.',
         '2.  Walls: 1 door  ·  2 window  ·  3 slat wall  ·  4 wardrobe. Room 3000 × 2900, ceiling 2550.',
         '3.  Parts meeting walls (panels 6, 7, cove 9) are ordered +10 mm long and scribed on site.',
         '4.  Wood finish: teak, oiled (deep teak tone). Shelves 5 and 8 in a darker stained hardwood.',
         '5.  Cove ledge and lips painted navy, satin. Exposed MDF edges sealed before painting.',
         '6.  Steel: matt black powder coat. Fixings shown are indicative; size to the wall type.',
         '7.  Cove lengths 2800–2860 exceed a 2750 sheet: use 3 m solid boards or a 45° scarf joint.',
         '8.  Sheet goods nested on 2750 × 1850 panels (sheet 8); 4 mm saw kerf allowed.']


def sheet1():
    s = [view('ov1', 15, 16), view('ov2', 213, 16)]
    s.append(T(15, 160, 'PARTS INDEX', 3.0, weight=700))
    rows = [[n, p, m, sh] for n, p, m, sh in PARTS_INDEX]
    s.append(table(15, 163, [('#', 9, 'middle'), ('Part', 82, 'start'), ('Material', 62, 'start'), ('Sheet', 14, 'middle')], rows, 2.4, 5.6))
    s.append(text_block(200, 160, NOTES, 2.35, 5.2, 'GENERAL NOTES'))
    sw = [('teak', 'Teak (oiled)'), ('dark', 'Dark hardwood'), ('steel', 'Black steel'), ('felt', 'Black felt'), ('paint', 'Painted MDF (navy)'), ('ghost', 'Existing / context')]
    for i, (k, t) in enumerate(sw):
        x = 200 + (i % 3) * 50; y = 210 + (i // 3) * 7
        s.append(R(x, y - 3.4, 6, 4.2, S.COLORS[k], 0.25) + T(x + 8, y, t, 2.4))
    return ''.join(s)


def sheet2():
    s = [view('s_elev', 15, 16), view('s_plan', 200, 16), view('s_iso', 200, 104)]
    s.append(broken(15, 196, 2520, 27, 150, 5, 'S1', 'Slat  ×72', sub='solid teak (or teak-veneered MDF) 27 × 12 × 2520, oiled all faces, ends sealed'))
    s.append(R(195, 194.5, 2.7 * 4, 1.2 * 4, S.COLORS['teak'], 0.3) + T(209, 198.5, 'section 27 × 12  (1:2.5)', 2.2))
    s.append(text_block(318, 20, [
        '#Materials', 'S1  72 slats 27 × 12 × 2520', 'S2  black PET acoustic felt 9 mm,', '      2900 × 2520 (in panel widths)',
        'S3  battens 40 × 19, horizontal,', '      5 rows @ ~600 c/c, plugged + screwed', '', '#Layout',
        'Pitch 40.5 (27 slat + 13.5 gap).', 'Start with a full slat in each corner,', 'face 4 mm from wall 2 panel edge.',
        'Spacer block 13.5 keeps the rhythm.', '', '#Sequence', '1  Fix battens level, shim flat.',
        '2  Glue/staple felt to battens.', '3  Mark the slat centres at 40.5.', '4  Fix slats with 2 brad nails per', '    batten from the felt side',
        '    or pocket screws from the back.', '5  5 mm shadow gap at the floor;', '    top tight to the crown molding.'], 2.35, 4.4))
    return ''.join(s)


def sheet3():
    s = [view('t_plan', 15, 16), view('t_front', 152, 16), view('t_side', 152, 90), view('t_iso', 288, 16)]
    s.append(part(15, 168, 2080, 490, 10, 'T1', 'Desktop, main', holes=[(90, 130, 60)], tdim=30, sub='teak 30 mm · Ø60 grommet hole 90 from slat end, 130 from back edge'))
    s.append(part(240, 168, 1452, 490, 10, 'T2', 'Desktop, return', tdim=30, sub='teak 30 mm · butt-joins T1 with 3 dominos + 2 bolt connectors'))
    s.append(broken(288, 124, 716, 30, 100, 5, 'L1', 'Desk leg  ×5', S.COLORS['steel'], sub='30 × 30 × 2 steel tube, 4 mm top plate, M8 glide Ø22'))
    return ''.join(s)


def sheet4():
    s = [view('w_elev', 15, 16), view('w_side', 190, 16), view('w_iso', 250, 16)]
    s.append(part(190, 128, 2330, 975, 20, 'W1', 'Window-wall panel', tdim=10, sub='teak plywood 10 mm · top edge butts the window frame, scribe ends'))
    s.append(part(320, 128, 460, 230, 5, 'F1', 'Floating shelf  ×5', S.COLORS['dark'], tdim=25,
                  sub='dark hardwood 25 mm · 2 × Ø10 × 180 blind holes in the back edge'))
    for cx in (80, 380):   # concealed rods (hidden lines)
        s.append(L(320 + cx / 5, 128, 320 + cx / 5, 128 + 180 / 5, 0.25, 'stroke-dasharray="1 0.7"'))
    s.append(text_block(15, 200, ['#Floating shelves', 'Shelf tops at 1100 / 1360 / 1620 / 1880 / 2140 from the floor (260 pitch).',
                                  'Each shelf on 2 concealed steel rods Ø10 × 250 (70 into the wall, chemical anchor, 180 into the shelf).',
                                  'Bottom shelf clears the 300 mm aquarium on the desk by 50 mm. Load ≤ 15 kg per shelf.',
                                  '#Window panel', 'Glued + pinned to wall 2; top edge tight under the window frame, left end butts the wardrobe.'], 2.35, 4.6))
    return ''.join(s)


def sheet5():
    s = [view('d_elev', 15, 16), view('d_iso', 190, 16)]
    x, y, k = 312, 26, 2        # L-bracket profile at 1:2 (side view, wall on the left)
    s.append(R(x - 6, y - 2, 4, 48, '#E4E2DD', 0.2) + T(x - 4, y + 52, 'wall', 2.0, 'middle', fill='#777'))
    s.append(f'<path d="M{x},{y} h{130 / k} v{6 / k} h{-(130 - 8) / k} v{(70 - 6) / k} h{-8 / k} z" fill="{S.COLORS["steel"]}" stroke="{INK}" stroke-width="0.3"/>')
    s.append(R(x, y - 30 / k, 150 / k, 30 / k, S.COLORS['dark'], 0.3, 'stroke-dasharray="1 0.6" fill-opacity="0.35"'))
    s.append(dim((x, y + 70 / k), (x + 130 / k, y + 70 / k), (x, y + 70 / k + 4), (x + 130 / k, y + 70 / k + 4), '130'))
    s.append(dim((x + 130 / k, y), (x + 130 / k, y + 70 / k), (x + 130 / k + 8, y), (x + 130 / k + 8, y + 70 / k), '70'))
    s.append(dim((x + 4 / k, y + 70 / k), (x + 8 / k, y + 70 / k), (x + 4 / k, y + 70 / k + 10), (x + 8 / k, y + 70 / k + 10), '8') if False else '')
    s.append(T(x + 6, y + 18, 'flat bar 10 wide: 6 thk arm, 8 thk leg', 2.1) + T(x + 6, y + 22, '2 × Ø5 screws to wall, 2 × 4 to shelf', 2.1))
    s.append(tag_label(x - 6, y + 62, 'K1', 'L-bracket  ×4', '1:2', 'black steel, shelf (dashed) sits on the 130 arm'))
    s.append(part(190, 128, 1955, 875, 20, 'B1', 'Bed-wall panel', tdim=18, sub='teak plywood 18 mm · floor to 875, scribe to wall 3'))
    s.append(part(305, 120, 480, 150, 5, 'H1', 'Upper shelf', S.COLORS['dark'], tdim=30, sub='dark hardwood 30 mm · top at 1874'))
    s.append(part(305, 182, 460, 150, 5, 'H2', 'Lower shelf', S.COLORS['dark'], tdim=30, sub='dark hardwood 30 mm · top at 1200'))
    return ''.join(s)


DRAWER = [['D1', 'Side', '2', '652.5 × 450', '18', 'teak-veneered MDF'], ['D2', 'Top / bottom', '2', '450 × 364', '18', 'teak-veneered MDF'],
          ['D3', 'Back', '1', '616.5 × 364', '6', 'MDF, black'], ['D4', 'Front, deep drawer', '1', '358 × 290', '18', 'teak-veneered MDF'],
          ['D5', 'Front, shallow drawer', '2', '358 × 142', '18', 'teak-veneered MDF'], ['D6', 'Rail between fronts', '2', '364 × 18', '12', 'teak'],
          ['—', 'Twin-wheel caster Ø48', '4', '65 high', '', 'plate 44 × 44'], ['—', 'Round knob', '3', 'Ø25', '', 'black'],
          ['—', 'Drawer boxes + runners', '3', '400 deep', '', 'size to runner type']]


def sheet6():
    s = [view('k_front', 15, 16), view('k_side', 105, 16), view('k_iso', 195, 16)]
    s.append(T(15, 140, 'DRAWER UNIT PANELS', 3.0, weight=700))
    s.append(table(15, 143, [('ID', 10, 'middle'), ('Part', 52, 'start'), ('Qty', 10, 'middle'), ('Size', 34, 'start'), ('T', 10, 'middle'), ('Material', 44, 'start')], DRAWER, 2.4, 5.4))
    s.append(text_block(195, 140, ['#Notes', 'Overall 450 deep × 400 wide × 717.5 high on casters.',
                                   'Top is 2.5 mm below the desk underside (720) so it rolls out freely.',
                                   'Fronts 358 wide, inset with a 3 mm reveal; 12 mm rails between fronts.',
                                   'Faces toward the chair (x = 250.5); sits under desk return T2.',
                                   'Assemble with 8 mm dowels + glue; back panel in a 6 mm groove.'], 2.35, 4.8))
    return ''.join(s)


COVE = [['C1', 'Ledge plate, wall 2 (window)', '1', '2325 × 50', '30'], ['C2', 'Ledge plate, wall 3 (slats)', '1', '2850 × 50', '30'],
        ['C3', 'Ledge plate, wall 1 (door)', '1', '2860 × 50', '30'], ['C4', 'Ledge plate, wall 4 (wardrobe)', '1', '1085 × 50', '30'],
        ['C5', 'Lip, wall 2', '1', '2325 × 25', '10'], ['C6', 'Lip, wall 3', '1', '2800 × 25', '10'], ['C7', 'Lip, wall 1', '1', '2860 × 25', '10'],
        ['C8', 'Lip, wall 4', '1', '1035 × 25', '10']]
WARD = [['R1', 'Door overlay, top', '2', '907 × 650', '6'], ['R2', 'Door overlay, upper mid', '2', '907 × 627', '6'],
        ['R3', 'Door overlay, lower mid', '2', '907 × 582', '6'], ['R4', 'Door overlay, bottom', '2', '907 × 574', '6'],
        ['R5', 'Navy inlay strip', '6', '907 × 23', '16.5']]


def sheet7():
    s = [view('c_plan', 15, 16), view('r_elev', 155, 16)]
    x, y, k = 268, 30, 1        # cove profile 1:1, wall on the right
    s.append(R(x + 50, y - 12, 8, 62, '#E4E2DD', 0.2) + T(x + 54, y + 56, 'wall', 2.0, 'middle', fill='#777'))
    s.append(R(x, y - 12, 50, 5, '#EEEDEA', 0.15) + T(x + 2, y - 8, 'ceiling 2550', 1.9, fill='#777'))
    s.append(R(x, y + 25, 50, 30, S.COLORS['paint'], 0.3) + R(x, y, 10, 25, S.COLORS['paint'], 0.3))
    s.append(R(x + 16, y + 21, 20, 4, '#F2D27A', 0.2) + T(x + 26, y + 18, 'LED strip + Al channel', 2.0, 'middle'))
    s.append(dim((x, y + 55), (x + 50, y + 55), (x, y + 61), (x + 50, y + 61), '50'))
    s.append(dim((x, y + 25), (x, y + 55), (x - 6, y + 25), (x - 6, y + 55), '30'))
    s.append(dim((x, y), (x, y + 25), (x - 6, y), (x - 6, y + 25), '25'))
    s.append(dim((x, y), (x + 10, y), (x, y - 4), (x + 10, y - 4), '10'))
    s.append(note((x + 50, y + 55), 'underside at 2430 from the floor', 6, 8))
    s.append(tag_label(x - 4, y + 78, 'C', 'Cove ledge profile', '1:1', 'MDF plate + lip, glued + screwed to wall; painted navy'))
    s.append(T(268, 130, 'COVE LEDGE PARTS', 3.0, weight=700))
    s.append(table(268, 133, [('ID', 9, 'middle'), ('Part', 70, 'start'), ('Qty', 8, 'middle'), ('L × W', 37, 'start'), ('T', 12, 'middle')], COVE, 2.3, 4.8))
    s.append(T(15, 172, 'WARDROBE RE-FACING (OPTIONAL, EXISTING CARCASS 1810 × 630 × 2700)', 3.0, weight=700))
    s.append(table(15, 175, [('ID', 9, 'middle'), ('Part', 62, 'start'), ('Qty', 8, 'middle'), ('L × W', 30, 'start'), ('T', 12, 'middle')], WARD, 2.3, 4.8))
    s.append(text_block(140, 178, ['Teak-veneer overlay panels glued to the existing', 'sliding doors (907 wide each).',
                                   'Navy strips R5 907 × 23 × 16.5, three per door,', 'between the panels, proud by 1.5 mm.',
                                   'Remove handles first; refit through the overlay.'], 2.3, 4.4))
    return ''.join(s)


# ------------------------------------------------------------------ cut list + nesting
CUT = [  # id, part, qty, L, W, T, material, group (for nesting)
    ('T1', 'Desktop, main', 1, 2080, 490, 30, 'teak, edge-glued', 'T30'), ('T2', 'Desktop, return', 1, 1452, 490, 30, 'teak, edge-glued', 'T30'),
    ('B1', 'Bed-wall panel', 1, 1965, 885, 18, 'teak plywood / veneered MDF', 'V18'), ('D1', 'Drawer side', 2, 652.5, 450, 18, 'teak-veneered MDF', 'V18'),
    ('D2', 'Drawer top / bottom', 2, 450, 364, 18, 'teak-veneered MDF', 'V18'), ('D4', 'Drawer front, deep', 1, 358, 290, 18, 'teak-veneered MDF', 'V18'),
    ('D5', 'Drawer front, shallow', 2, 358, 142, 18, 'teak-veneered MDF', 'V18'), ('D3', 'Drawer back', 1, 616.5, 364, 6, 'MDF, black', '-'),
    ('W1', 'Window-wall panel', 1, 2340, 985, 10, 'teak plywood', 'P10'), ('C5', 'Cove lip, wall 2', 1, 2335, 25, 10, 'MDF', 'P10'),
    ('C8', 'Cove lip, wall 4', 1, 1045, 25, 10, 'MDF', 'P10'),
    ('C1', 'Cove plate, wall 2', 1, 2335, 50, 30, 'MDF', '-'), ('C2', 'Cove plate, wall 3', 1, 2860, 50, 30, '3 m board', '-'),
    ('C3', 'Cove plate, wall 1', 1, 2870, 50, 30, '3 m board', '-'), ('C4', 'Cove plate, wall 4', 1, 1095, 50, 30, 'MDF', '-'),
    ('C6/C7', 'Cove lip, walls 3 / 1', 2, 2870, 25, 10, '3 m board', '-'),
    ('F1', 'Floating shelf', 5, 460, 230, 25, 'dark hardwood', '-'), ('H1', 'Door-wall shelf, upper', 1, 480, 150, 30, 'dark hardwood', '-'),
    ('H2', 'Door-wall shelf, lower', 1, 460, 150, 30, 'dark hardwood', '-'), ('S1', 'Slat', 72, 2520, 27, 12, 'teak', '-'),
    ('S2', 'Acoustic felt', 1, 2900, 2520, 9, 'black PET felt', '-'), ('S3', 'Batten', 5, 2900, 40, 19, 'pine, treated', '-'),
    ('D6', 'Drawer rail', 2, 364, 18, 12, 'teak', '-'), ('R1–R4', 'Wardrobe overlays (opt.)', 8, 907, '574–650', 6, 'teak veneer ply', '-'),
    ('R5', 'Navy strip (opt.)', 6, 907, 23, 16.5, 'MDF, painted navy', '-'),
    ('L1', 'Desk leg', 5, 716, 30, 30, 'steel tube 30×30×2', '-'), ('K1', 'L-bracket', 4, 130, 70, 10, 'steel flat bar', '-'),
    ('—', 'Shelf rod', 10, 250, 'Ø10', '', 'steel rod', '-')]
SHEET_W, SHEET_H, KERF = 2750, 1850, 4


def nest(parts):
    """Shelf packing, tallest first: rows across the 2750 length. Returns list of sheets, each a list of (x, y, l, w, id)."""
    items = sorted([(max(l, w), min(l, w), i) for i, l, w in parts], key=lambda t: (-t[1], -t[0]))
    sheets = []
    for l, w, i in items:
        for sh in sheets:
            for row in sh['rows']:      # same row if it fits and is tall enough
                if row['x'] + l <= SHEET_W and w <= row['h']:
                    sh['cuts'].append((row['x'], row['y'], l, w, i)); row['x'] += l + KERF; break
            else:
                y = sh['rows'][-1]['y'] + sh['rows'][-1]['h'] + KERF
                if y + w <= SHEET_H:
                    sh['rows'].append(dict(x=l + KERF, y=y, h=w)); sh['cuts'].append((0, y, l, w, i))
                else: continue
            break
        else:
            sheets.append(dict(rows=[dict(x=l + KERF, y=0, h=w)], cuts=[(0, 0, l, w, i)]))
    return [sh['cuts'] for sh in sheets]


NEST_GROUPS = [('V18', '18 mm teak-veneered MDF / plywood'), ('P10', '10 mm teak plywood'), ('T30', '30 mm teak panel')]


def sheet8():
    s = [T(15, 20, 'CUT LIST  (sizes include +10 mm scribe allowance where noted in the drawings)', 3.0, weight=700)]
    rows = [[c[0], c[1], str(c[2]), fmt(c[3]) if not isinstance(c[3], str) else c[3], fmt(c[4]) if not isinstance(c[4], str) else c[4],
             fmt(c[5]) if c[5] != '' else '', c[6]] for c in CUT]
    cols = [('ID', 13, 'middle'), ('Part', 50, 'start'), ('Qty', 9, 'middle'), ('L', 14, 'end'), ('W', 14, 'end'), ('T', 10, 'end'), ('Material', 46, 'start')]
    half = (len(rows) + 1) // 2
    s.append(table(15, 23, cols, rows[:half], 2.25, 4.5)); s.append(table(215, 23, cols, rows[half:], 2.25, 4.5))
    y0 = 100 if half <= 14 else 23 + 4.5 * (half + 1) + 12
    k = 25; x = 15
    for g, title in NEST_GROUPS:
        parts = [(c[0], c[3], c[4]) for c in CUT if c[7] == g for _ in range(c[2])]
        for n, cuts in enumerate(nest(parts)):
            used = sum(l * w for _, _, l, w, _ in cuts) / (SHEET_W * SHEET_H)
            s.append(T(x, y0, f'{title}  ·  sheet {n + 1}', 2.6, weight=700) + T(x, y0 + 4, f'2750 × 1850  ·  yield {used:.0%}  ·  1:25', 2.2, fill='#555'))
            sy = y0 + 7
            s.append(R(x, sy, SHEET_W / k, SHEET_H / k, '#F3F2EF', 0.3, 'stroke-dasharray="0"'))
            col = S.COLORS['teak'] if g != 'T30' else '#B98450'
            for cx, cy, l, w, i in cuts:
                s.append(R(x + cx / k, sy + cy / k, l / k, w / k, col, 0.2))
                if w / k > 3.5: s.append(T(x + (cx + l / 2) / k, sy + (cy + w / 2) / k + 0.9, i, 2.2 if w / k > 5 else 1.8, 'middle', 700))
            x += SHEET_W / k + 14
    s.append(text_block(15, 195, ['#Buying list (summary)', '1 × 18 mm teak-veneered MDF 2750 × 1850  ·  1 × 10 mm teak plywood 2750 × 1850  ·  1 × 30 mm teak panel 2750 × 1850 (or 2 edge-glued tops)',
                                  '72 teak slats 27 × 12 × 2520 (≈ 182 m)  ·  7.3 m² black PET felt 9 mm  ·  5 battens 40 × 19 × 3000',
                                  'Dark hardwood board 25 mm: 2400 × 250 (5 floating shelves)  ·  dark hardwood 30 mm: 1000 × 160 (2 door-wall shelves)',
                                  'MDF 30 mm strips 50 wide: 2 × 3000, 1 × 2400, 1 × 1200  ·  MDF 10 mm strips 25 wide: 2 × 3000 (+ 2 from the 10 mm sheet)',
                                  'Steel: 5 legs 30 × 30 × 716 with plates + glides  ·  4 L-brackets  ·  10 rods Ø10 × 250  ·  4 casters  ·  3 knobs  ·  1 Ø60 grommet'], 2.3, 4.8))
    return ''.join(s)


def sheet9():
    return view('hero', 15, 16)


BUILD = {9: sheet9, 1: sheet1, 2: sheet2, 3: sheet3, 4: sheet4, 5: sheet5, 6: sheet6, 7: sheet7, 8: sheet8}
DEFS = ('<defs><marker id="ar" viewBox="0 0 10 4" refX="10" refY="2" markerWidth="2.4" markerHeight="0.96" markerUnits="userSpaceOnUse" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,2 L0,4 z" fill="{INK}"/></marker></defs>')


def main():
    pages = []
    for sh in S.SHEETS:
        body = BUILD[sh['n']]()
        pages.append(f'<section><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 297" width="420mm" height="297mm" font-family="{FONT}">{DEFS}'
                     f'<rect width="420" height="297" fill="#fff"/>{body}{frame(sh)}</svg></section>')
    html = ('<!doctype html><html><head><meta charset="utf-8"><title>Fabrication Drawings v19</title><style>@page{size:420mm 297mm;margin:0}'
            'html,body{margin:0;background:#fff}section{width:420mm;height:297mm;page-break-after:always;overflow:hidden}svg{display:block}</style></head><body>'
            + ''.join(pages) + '</body></html>')
    open(OUT + '.html', 'w').write(html)
    chrome = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    subprocess.run([chrome, '--headless', '--disable-gpu', '--no-pdf-header-footer', '--allow-file-access-from-files', f'--print-to-pdf={OUT}.pdf',
                    'file://' + OUT + '.html'], check=True, capture_output=True)
    print('PDF', OUT + '.pdf')


if __name__ == '__main__':
    main()
