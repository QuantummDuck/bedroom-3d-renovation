"""Side-by-side A (2 shelves) vs B (3 shelves) sheets.  python3 make_ab_sheet.py"""
import os, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(HERE, 'renders'); F = '/System/Library/Fonts/Avenir.ttc'
T = {'E17': 'Unit from the front', 'E18': 'Unit from the side', 'E07': 'Window wall, straight on', 'E01': 'Corner: door to window / slat-wall', 'E02': 'Corner: window to bed',
     'E03': 'Corner: from the bed corner', 'E04': 'High view across the room', 'E05': 'Entrance', 'E10': 'Wide 12 mm', 'E11': 'Twilight: door corner', 'E12': 'Twilight: window corner'}
tmp = tempfile.mkdtemp(); W, H = 880, 495
def mk(*a): subprocess.run(['magick', *map(str, a)], check=True)
rows = []
for k, t in T.items():
    r = os.path.join(tmp, k + '.png')
    tile = lambda v, lab: ['(', os.path.join(R, f'v18{v}', k + '.jpg'), '-resize', f'{W}x{H}!', '-gravity', 'NorthWest', '-font', F, '-pointsize', 30, '-fill', 'white', '-stroke', 'black', '-strokewidth', 1,
                           '-annotate', '+14+10', lab, ')']
    mk(*tile('A', 'A: two shelves'), *tile('B', 'B: three shelves'), '-background', 'white', '-splice', '8x0', '+append', '(', '-size', f'{2 * W + 8}x44', 'xc:#F4F4F1', '-font', F, '-pointsize', 24, '-fill', '#1D1D1F', '-gravity', 'West', '-annotate', '+12+0', t, ')', '-gravity', 'NorthWest', '+swap', '-append', r)
    rows.append(r)
for i, chunk in enumerate((rows[:4], rows[4:8], rows[8:])):
    mk(*chunk, '-background', 'white', '-append', '-quality', 88, os.path.join(R, f'ShelfUnit_A_vs_B_{i + 1}.jpg'))
print('ok')
