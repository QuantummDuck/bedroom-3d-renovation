"""Real-estate sheets: dimensioned plan + contact sheet from renders/estate.  python3 make_estate_sheets.py"""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); SUB = os.environ.get('ESTATE_DIR', 'estate'); R = os.path.join(HERE, 'renders', SUB); F = '/System/Library/Fonts/Supplemental/Arial.ttf'; DIM = '#D6246E'
k = 1600 / 350.0
px = lambda x, y: (800 - (x - 150) * k, 800 + (y - 145) * k)       # plan camera: right = -x, down = +y
ops = ['-gravity', 'northwest', '-fill', 'none', '-stroke', DIM, '-strokewidth', '3']
def dim(p0, p1, text, off=(0, 0), tdx=0, tdy=0):
    a, b = px(*p0), px(*p1); a = (a[0] + off[0], a[1] + off[1]); b = (b[0] + off[0], b[1] + off[1])
    ops.extend(['-draw', f'line {a[0]:.0f},{a[1]:.0f} {b[0]:.0f},{b[1]:.0f}'])
    for q in (a, b):
        ex = 12 if abs(a[1] - b[1]) < 1 else 0; ey = 12 if abs(a[0] - b[0]) < 1 else 0
        ops.extend(['-draw', f'line {q[0] - ey:.0f},{q[1] - ex:.0f} {q[0] + ey:.0f},{q[1] + ex:.0f}'])
    ops.extend(['-stroke', 'none', '-fill', DIM, '-font', F, '-pointsize', '36', '-annotate', f'+{(a[0] + b[0]) / 2 + tdx:.0f}+{(a[1] + b[1]) / 2 + tdy:.0f}', text, '-fill', 'none', '-stroke', DIM])
dim((300, 0), (0, 0), 'room 300 cm', (0, 38), -90, -52)
dim((0, 0), (0, 290), 'room 290 cm', (-38, 0), -230, -18)
dim((0, 181), (63, 181), 'wardrobe 63', (0, 52), -48, 6)
dim((0, 0), (0, 181), 'wardrobe 181', (-150, 0), -228, -18)
dim((63, 0), (88, 0), 'gap 25', (0, 150), -40, -56)
dim((296, 194.2), (296, 0), 'table 194', (-4, 0), 18, -18)
dim((296, 49), (88, 49), 'table 208', (0, 150), -105, 8)
dim((106.2, 276), (294.2, 276), 'bed 188 x 94', (0, 0), -92, 10)
dim((15, 290), (86.5, 290), 'door 71.5', (0, -30), -62, -48)
subprocess.run(['magick', os.path.join(R, 'P01.jpg'), '-resize', '1600x1600', *map(str, ops), os.path.join(R, 'P01_dimensioned.jpg')], check=True)
ids = [f'E{i:02d}' for i in list(range(1, 11)) + [13, 14, 15, 16] if os.path.exists(os.path.join(R, f'E{i:02d}.jpg'))]
fs = [os.path.join(R, f'{i}.jpg') for i in ids]
subprocess.run(['magick', 'montage', '-font', F, *fs, '-tile', '2x', '-geometry', '900x506+6+6', '-background', 'white', os.path.join(HERE, 'renders', 'Estate_contact_sheet' + ('' if SUB == 'estate' else '_' + SUB) + '.jpg')], check=True)
print('ok')
