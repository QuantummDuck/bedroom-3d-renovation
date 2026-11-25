"""Palette comparison sheets: per palette, swatches + rationale, then day and night rows of the same 4 views.
  python3 make_palette_sheet.py [renders/palettes] [P1,P2,...] [out.jpg]"""
import os, re, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, 'palettes.py')).read()
ns = {}; exec(src[src.index('WOOD = {'):src.index("A = dict(")], ns)
PAL, WOODHEX = ns['PALETTES'], {'teak': '#9A6A3E', 'walnut': '#6E4C34', 'oak': '#B08A5E', 'deep_teak': '#86603C'}
R = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'renders', 'palettes')
KEYS = sys.argv[2].split(',') if len(sys.argv) > 2 else list(PAL)
OUT = sys.argv[3] if len(sys.argv) > 3 else os.path.join(HERE, 'renders', 'Palettes_overview.jpg')
F = '/System/Library/Fonts/Avenir.ttc'; W, H = 600, 338
VIEWS = ['L18_Corner_High_Bed', 'R1_Wide_Table_Corner', 'L2_Table_Shelves', 'L3_Bed_Door']
tmp = tempfile.mkdtemp()
def mk(*a): subprocess.run(['magick', *map(str, a)], check=True)


def block(key):
    title, why, walls, ceil, rod, door, ward, strips, felt, wood = PAL[key]
    wh = WOODHEX[wood]
    sw = [('Walls', walls), ('Ceiling', ceil), ('Rodapé', rod), ('Door', door), ('Wardrobe', wh if ward == 'wood' else ward),
          ('Strips', wh if strips == 'wood' else strips), ('Slat gaps', felt), (f'Wood ({wood})', wh)]
    ops = ['-size', f'{4 * W}x190', 'xc:#F4F4F1', '-font', F, '-fill', '#1D1D1F', '-pointsize', 40, '-gravity', 'NorthWest', '-annotate', '+20+14', f'{key}  {title}']
    for i, (lab, hx) in enumerate(sw):
        x = 20 + i * 150
        ops += ['-fill', hx, '-stroke', '#B8B8B4', '-strokewidth', 2, '-draw', f'roundrectangle {x},76 {x + 120},126 6,6', '-stroke', 'none',
                '-fill', '#6E6E73', '-pointsize', 18, '-annotate', f'+{x}+134', lab + ('' if hx == wh and lab != f'Wood ({wood})' and lab in ('Wardrobe', 'Strips') and False else '')]
    head = os.path.join(tmp, f'{key}_head.png'); mk(*ops, head)
    cap = os.path.join(tmp, f'{key}_cap.png')
    mk('-size', f'{4 * W - 1280}x', '-background', '#F4F4F1', '-font', F, '-pointsize', 21, '-fill', '#3A3A3C', f'caption:{why}', cap)
    mk(head, cap, '-gravity', 'NorthWest', '-geometry', '+1260+70', '-composite', head)
    rows = []
    for scen in ('overcast_morning', 'golden_hour', 'night_cozy'):
        fs = [os.path.join(R, f'{key}__{v}__{scen}.jpg') for v in VIEWS]
        if not all(os.path.exists(f) for f in fs): continue
        r = os.path.join(tmp, f'{key}_{scen}.png'); mk(*fs, '-resize', f'{W}x{H}!', '+append', r); rows.append(r)
    out = os.path.join(tmp, f'{key}.png'); mk(head, *rows, '-append', '-bordercolor', 'white', '-border', '0x14', out)
    return out


blocks = [block(k) for k in KEYS]
mk('(', '-size', f'{4 * W}x110', 'xc:white', '-font', F, '-pointsize', 48, '-fill', '#1D1D1F', '-gravity', 'West', '-annotate', '+20+0',
   'Colour directions: same 4 views; rows = day / golden hour / night (where rendered)', ')', *blocks, '-append', '-quality', 86, OUT)
print('sheet', OUT, len(blocks))
