"""Technical_Views_v7.pdf (A4 landscape): dimensioned plan, cut-away aerials, wall elevations, wide-lens views, construction details.
  python3 make_tech_pdf.py   (needs renders/tech/*.png from tech_render.py)"""
import os, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(HERE, 'renders', 'tech')
FONT = '/System/Library/Fonts/Avenir.ttc'; INK, MUTED = '#1D1D1F', '#6E6E73'; DIM = '#D6246E'
W, H, M = 2339, 1654, 80
TITLES = {'T01': 'Plan (ceiling removed), with dimensions in cm', 'T02': 'Cut-away aerial from the door / desk-wall corner', 'T03': 'Cut-away aerial from the window / frame-wall corner',
          'T04': 'Cut-away aerial from the bed corner', 'T05': 'Cut-away aerial from the window / wardrobe corner',
          'T06': 'Elevation: wall 3 (shelves, table, bed head, plug)', 'T07': 'Elevation: wall 4 (wardrobe)', 'T08': 'Elevation: wall 2 (window, wardrobe end, table)',
          'T09': 'Elevation: wall 1 (door, bed)', 'T10': 'Wide 14 mm: from the table corner', 'T11': 'Wide 14 mm: from the bed foot, sun at 4 pm',
          'T12': 'Wide 14 mm: from the bed head at night', 'T13': 'Wide 12 mm: from the ceiling, looking down',
          'D01': 'Detail: table leg, glide and rug', 'D02': 'Detail: cove ledge, crown molding and LED', 'D03': 'Detail: flush wall plug in the boards',
          'D04': 'Detail: cable grommet in the table corner', 'D05': 'Detail: under-table LED and legs', 'D06': 'Detail: bed panel LED and head board',
          'D07': 'Detail: wardrobe track, plinth and floor', 'D08': 'Detail: door handle, hinge and trim', 'D09': 'Detail: shelf bracket, boards and books',
          'D10': 'Detail: window louvres and frame'}


def mk(*a): subprocess.run(['magick', *map(str, a)], check=True)


def txt(s, x, y, size, color=INK, gravity='northwest'):
    return ['-font', FONT, '-pointsize', size, '-fill', color, '-gravity', gravity, '-annotate', f'+{x}+{y}', s.replace('%', '%%')]


def dimensioned_plan(src, out):
    """Overlay dimension lines on the plan. Image: 1600 px = 350 cm, centre = (150, 145) cm, right = -x, down = +y."""
    k = 1600 / 350.0
    px = lambda x, y: (800 - (x - 150) * k, 800 + (y - 145) * k)
    ops = ['-gravity', 'northwest', '-fill', 'none', '-stroke', DIM, '-strokewidth', 3]

    def dim(p0, p1, text, off=(0, 0), tdx=0, tdy=0):
        a, b = px(*p0), px(*p1); a = (a[0] + off[0], a[1] + off[1]); b = (b[0] + off[0], b[1] + off[1])
        ops.extend(['-draw', f'line {a[0]:.0f},{a[1]:.0f} {b[0]:.0f},{b[1]:.0f}'])
        for q in (a, b):
            ex = 12 if abs(a[1] - b[1]) < 1 else 0; ey = 12 if abs(a[0] - b[0]) < 1 else 0
            ops.extend(['-draw', f'line {q[0] - ey:.0f},{q[1] - ex:.0f} {q[0] + ey:.0f},{q[1] + ex:.0f}'])
        mx, my = (a[0] + b[0]) / 2 + tdx, (a[1] + b[1]) / 2 + tdy
        ops.extend(['-stroke', 'none', '-fill', DIM, '-font', FONT, '-pointsize', 34, '-annotate', f'+{mx:.0f}+{my:.0f}', text, '-fill', 'none', '-stroke', DIM])

    dim((300, 0), (0, 0), '300', (0, 40), -40, -48)                       # window wall length (inside the room, along the top)
    dim((0, 0), (0, 290), '290', (-40, 0), -110, -17)                     # desk wall (right side of the picture)
    dim((63, 0), (138, 0), 'gap 75', (0, 150), -75, -48)                  # clearance wardrobe -> table
    dim((0, 0), (0, 181), 'wardrobe 181', (-150, 0), -140, -17)
    dim((0, 0), (63, 0), '63', (0, 240), -22, -48)
    dim((296, 194.2), (296, 0), 'table 194', (-6, 0), 12, -17)
    dim((296, 49), (138, 49), 'table 158', (0, 150), -75, 8)
    dim((247, 194.2), (296, 194.2), '49', (0, 28), -22, 6)
    dim((106.2, 280), (294.2, 280), 'bed 188 x 94', (0, 0), -88, 10)
    mk(src, '-resize', '1600x1600', *ops, out)


def main():
    tmp = tempfile.mkdtemp(); pages = []
    def page(ops):
        o = os.path.join(tmp, f'p{len(pages) + 1:02d}.jpg'); pages.append(o)
        mk('-size', f'{W}x{H}', 'xc:white', *ops, *txt(f'Technical views  ·  layout v7  ·  page {len(pages)}', M, H - 60, 22, MUTED), '-quality', 90, o)
    def img(path, x, y, w, h): return ['(', path, '-resize', f'{w}x{h}', ')', '-gravity', 'northwest', '-geometry', f'+{x}+{y}', '-composite']
    ids = [i for i in TITLES if os.path.exists(os.path.join(R, f'{i}.png'))]
    for i in ids:
        src = os.path.join(R, f'{i}.png')
        if i == 'T01':
            dp = os.path.join(tmp, 'plan_dim.png'); dimensioned_plan(src, dp); src = dp
        w, h = map(int, subprocess.run(['magick', 'identify', '-format', '%w %h', src], capture_output=True, text=True).stdout.split())
        bw, bh = W - 2 * M, H - 260; s = min(bw / w, bh / h); iw, ih = int(w * s), int(h * s)
        page(txt(f'{i}   {TITLES[i]}', M, 60, 44) + img(src, (W - iw) // 2, 150, iw, ih))
    out = os.path.join(HERE, 'Technical_Views_v7.pdf')
    mk('-density', 200, '-units', 'PixelsPerInch', *pages, '-compress', 'jpeg', '-quality', 86, out)
    print('PDF', out, len(pages), 'pages', f'{os.path.getsize(out) / 1e6:.1f} MB')


if __name__ == '__main__':
    main()
