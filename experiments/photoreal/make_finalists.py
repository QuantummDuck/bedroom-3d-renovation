"""Finalists side by side: rows = palettes, columns = the same 4 shots.  python3 make_finalists.py"""
import os, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(HERE, 'renders', 'palettes_r2'); F = '/System/Library/Fonts/Avenir.ttc'
ROWS = [('R4', 'Smoked Teal  (recommended)', '#36433F'), ('R2', 'Olive Library', '#4B4A37'), ('R3', 'Clay Cocoon', '#A48B76'), ('R1', 'Ink & Deep Teak', '#283240')]
COLS = [('L18_Corner_High_Bed__overcast_morning', 'Overview, day'), ('R1_Wide_Table_Corner__overcast_morning', 'Wardrobe + door, day'),
        ('L3_Bed_Door__golden_hour', 'Bed wall, golden hour'), ('L2_Table_Shelves__night_cozy', 'Slat wall, night')]
W, H = 640, 360; tmp = tempfile.mkdtemp()
def mk(*a): subprocess.run(['magick', *map(str, a)], check=True)
rows = []
for key, title, hx in ROWS:
    r = os.path.join(tmp, key + '.png')
    lab = ['(', '-size', '300x360', 'xc:#F4F4F1', '-fill', hx, '-stroke', '#B8B8B4', '-draw', 'roundrectangle 24,110 124,190 8,8', '-stroke', 'none',
           '-font', F, '-pointsize', 30, '-fill', '#1D1D1F', '-gravity', 'NorthWest', '-annotate', '+24+40', title.split('  ')[0],
           '-pointsize', 20, '-fill', '#6E6E73', '-annotate', '+24+206', (title.split('  ')[1] if '  ' in title else '') + f'\nwalls {hx}', ')']
    mk(*lab, *[os.path.join(R, f'{key}__{c}.jpg') for c, _ in COLS], '-resize', f'x{H}', '+append', r); rows.append(r)
head = ['(', '-size', f'{300 + 4 * W}x60', 'xc:white', '-font', F, '-pointsize', 24, '-fill', '#6E6E73',
        *sum([['-gravity', 'NorthWest', '-annotate', f'+{300 + i * W + 12}+20', t] for i, (_, t) in enumerate(COLS)], []), ')']
mk('(', '-size', f'{300 + 4 * W}x100', 'xc:white', '-font', F, '-pointsize', 44, '-fill', '#1D1D1F', '-gravity', 'West', '-annotate', '+24+0',
   'Four finalists, same shots (all with the deep-teak wood)', ')', *head, *rows, '-append', '-quality', 88, os.path.join(HERE, 'renders', 'Palettes_finalists.jpg'))
print('ok')
