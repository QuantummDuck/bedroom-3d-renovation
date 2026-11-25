"""Builds the labelled comparison sheets from renders/ + renders/stats.json (needs ImageMagick 7: `magick`).
  python3 make_sheets.py"""
import json, os, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(HERE, 'renders')
FONT = '/System/Library/Fonts/Avenir.ttc'
BG, INK, MUTED = '#F4F4F1', '#1D1D1F', '#6E6E73'
VIEWS = {'A': 'View A, from the door: window, bed, piano, desk', 'B': 'View B, from the window: door, wardrobe, desk, shelves'}
stats = json.load(open(os.path.join(R, 'stats.json')))
tmp = tempfile.mkdtemp()


def magick(*args):
    subprocess.run(['magick', *map(str, args)], check=True)


for v, title in VIEWS.items():
    tiles = []
    for slug, s in stats.items():
        t = os.path.join(tmp, f'{slug}_{v}.png'); tiles.append(t)
        light = 'reference' if s['light_vs_current_pct'] == 100 and slug.startswith('01') else f"{s['light_vs_current_pct']}%% light"
        magick('(', os.path.join(R, f'{slug}_{v}.png'), '-resize', '900x675!', ')',
               '(', '-size', '900x84', 'xc:white', '-fill', s['hex'], '-stroke', '#C8C8C4', '-strokewidth', '2',
               '-draw', 'roundrectangle 18,16 70,68 8,8', '-stroke', 'none', '-font', FONT,
               '-fill', INK, '-pointsize', '30', '-annotate', '+88+40', s['label'],
               '-fill', MUTED, '-pointsize', '21', '-annotate', '+88+70', s['hex'],
               '-gravity', 'northeast', '-fill', INK, '-pointsize', '24', '-annotate', '+20+16', f"LRV {s['lrv']:.0f}",
               '-fill', MUTED, '-pointsize', '21', '-annotate', '+20+50', light, ')',
               '-append', t)
    grid = os.path.join(tmp, f'grid_{v}.png')
    magick('montage', '-font', FONT, *tiles, '-tile', '4x2', '-geometry', '+14+14', '-background', BG, grid)
    magick(grid, '-background', BG, '-gravity', 'north', '-splice', '0x128', '-font', FONT,
           '-fill', INK, '-pointsize', '46', '-annotate', '+0+26', f'Wall colour study  ·  {title}',
           '-fill', MUTED, '-pointsize', '24', '-annotate', '+0+86',
           'Cycles · real overcast daylight · scanned textures · calibrated to your photos. LRV = how much light the paint reflects (0-100). '
           'Light %% = light on the white surfaces vs your current walls.',
           '-quality', '92', os.path.join(R, f'compare_view_{v}.jpg'))
    print('sheet', v)
