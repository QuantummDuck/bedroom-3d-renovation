"""Labelled option sheets from renders_v2/ (ImageMagick 7): strips S1-S6 and desk legs L1-L4.
  python3 make_sheets_v2.py"""
import json, os, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(HERE, 'renders_v2')
FONT = '/System/Library/Fonts/Avenir.ttc'; BG, INK, MUTED = '#F4F4F1', '#1D1D1F', '#6E6E73'
opts = json.load(open(os.path.join(R, 'options.json'))); tmp = tempfile.mkdtemp()


def magick(*a):
    subprocess.run(['magick', *map(str, a)], check=True)


for key, folder, title, cols in (('strips', 'strips', 'Wardrobe strip colour', 3), ('legs', 'legs', 'Desk legs (door-side end)', 2)):
    tiles = []
    for o in opts[key]:
        t = os.path.join(tmp, o['code'] + '.png'); tiles.append(t)
        magick('(', os.path.join(R, folder, f"{o['code']}_{o['slug']}.png"), '-resize', '960x540!', ')',
               '(', '-size', '960x70', 'xc:white', '-font', FONT, '-fill', INK, '-pointsize', '32',
               '-annotate', '+22+48', f"{o['code']}   {o['label']}", ')', '-append', t)
    grid = os.path.join(tmp, 'grid.png')
    magick('montage', '-font', FONT, *tiles, '-tile', f'{cols}x', '-geometry', '+12+12', '-background', BG, grid)
    magick(grid, '-background', BG, '-gravity', 'north', '-splice', '0x110', '-font', FONT,
           '-fill', INK, '-pointsize', '46', '-annotate', '+0+22', f'{title}  ·  options',
           '-fill', MUTED, '-pointsize', '24', '-annotate', '+0+80', 'Teak boards, deep navy walls, afternoon sun. Reply with the code you like.',
           '-quality', '90', os.path.join(R, f'options_{key}.jpg'))
    print('sheet', key)
