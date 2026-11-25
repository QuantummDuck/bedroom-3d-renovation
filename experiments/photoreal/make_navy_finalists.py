"""Navy finalists side by side (rows = palettes, columns = same 4 shots).  python3 make_navy_finalists.py"""
import os, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(HERE, 'renders', 'navy'); F = '/System/Library/Fonts/Avenir.ttc'
src = open(os.path.join(HERE, 'navy_palettes.py')).read(); ns = {}; exec(src[src.index('WOOD = {'):src.index("A = dict(")], ns); PAL = ns['PALETTES']
ROWS = [('M2', 'recommended'), ('N1', ''), ('M3', ''), ('M4', '')]
COLS = [('L18_Corner_High_Bed__overcast_morning', 'Overview, day'), ('R1_Wide_Table_Corner__overcast_morning', 'Wardrobe + door, day'),
        ('F2_Doorway_View__golden_hour', 'From the door, golden hour'), ('L3_Bed_Door__night_cozy', 'Bed wall, night')]
W, H = 640, 360; tmp = tempfile.mkdtemp()
def mk(*a): subprocess.run(['magick', *map(str, a)], check=True)
rows = []
for key, note in ROWS:
    p = PAL[key]; r = os.path.join(tmp, key + '.png')
    sw = [p['walls'], p['ward'] if p['ward'] != 'wood' else '#86603C', '#86603C']
    lab = ['(', '-size', '300x360', 'xc:#F4F4F1', '-font', F, '-pointsize', 26, '-fill', '#1D1D1F', '-gravity', 'NorthWest', '-annotate', '+24+36', p['title'].replace(' & Navy ', ' & Navy\n')]
    for i, hx in enumerate(sw):
        lab += ['-fill', hx, '-stroke', '#B8B8B4', '-draw', f'roundrectangle {24 + i * 84},100 {94 + i * 84},160 6,6', '-stroke', 'none']
    lab += ['-pointsize', 18, '-fill', '#6E6E73', '-annotate', '+24+168', 'walls   wardrobe   wood', '-pointsize', 22, '-fill', '#1D1D1F', '-annotate', '+24+210', note, ')']
    mk(*lab, *[os.path.join(R, f'{key}__{c}.jpg') for c, _ in COLS], '-resize', f'x{H}', '+append', r); rows.append(r)
head = ['(', '-size', f'{300 + 4 * W}x60', 'xc:white', '-font', F, '-pointsize', 24, '-fill', '#6E6E73',
        *sum([['-gravity', 'NorthWest', '-annotate', f'+{300 + i * W + 12}+20', t] for i, (_, t) in enumerate(COLS)], []), ')']
mk('(', '-size', f'{300 + 4 * W}x100', 'xc:white', '-font', F, '-pointsize', 44, '-fill', '#1D1D1F', '-gravity', 'West', '-annotate', '+24+0',
   'Navy finalists, same shots', ')', *head, *rows, '-append', '-quality', 88, os.path.join(HERE, 'renders', 'Navy_finalists.jpg'))
print('ok')
