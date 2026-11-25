"""Navy study sheets: per palette, swatches + rationale, then day / golden hour / night rows of the same 4 views.
  python3 make_navy_sheet.py RENDER_DIR KEYS OUT.jpg [title]"""
import os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, 'navy_palettes.py')).read()
ns = {}; exec(src[src.index('WOOD = {'):src.index("A = dict(")], ns)
PAL, WOODHEX = ns['PALETTES'], ns['WOODHEX']
R, KEYS, OUT = sys.argv[1], sys.argv[2].split(','), sys.argv[3]
TITLE = sys.argv[4] if len(sys.argv) > 4 else 'Navy variations: same 4 views; rows = day / golden hour / night'
F = '/System/Library/Fonts/Avenir.ttc'; W, H = 600, 338
VIEWS = ['L18_Corner_High_Bed', 'F2_Doorway_View', 'R1_Wide_Table_Corner', 'L3_Bed_Door']
tmp = tempfile.mkdtemp()
def mk(*a): subprocess.run(['magick', *map(str, a)], check=True)


def block(key):
    p = PAL[key]; wh = WOODHEX[p['wood']]
    def sw(v): return wh if v == 'wood' else ('#B8955A' if v == 'brass' else v)
    items = [('Walls', p['walls']), ('Ceiling', p['ceil']), ('Rodapé', p['rod']), ('Door', p['door']), ('Wardrobe', sw(p['ward'])),
             ('Ward. strips' + (' (brass)' if p['strips'] == 'brass' else ''), sw(p['strips'])), ('Wall slats' + (' (painted)' if p['slats'] not in ('wood',) else ''), sw(p['slats'])),
             ('Slat gaps', p['felt']), ('Wood', wh)]
    ops = ['-size', f'{4 * W}x200', 'xc:#F4F4F1', '-font', F, '-fill', '#1D1D1F', '-pointsize', 40, '-gravity', 'NorthWest', '-annotate', '+20+14', f"{key}  {p['title']}"]
    for i, (lab, hx) in enumerate(items):
        x = 20 + i * 132
        ops += ['-fill', hx, '-stroke', '#B8B8B4', '-strokewidth', 2, '-draw', f'roundrectangle {x},76 {x + 108},126 6,6', '-stroke', 'none',
                '-fill', '#6E6E73', '-pointsize', 17, '-annotate', f'+{x}+134', lab]
    head = os.path.join(tmp, f'{key}_h.png'); mk(*ops, head)
    cap = os.path.join(tmp, f'{key}_c.png')
    mk('-size', f'{4 * W - 1240}x', '-background', '#F4F4F1', '-font', F, '-pointsize', 21, '-fill', '#3A3A3C', f"caption:{p['why']}", cap)
    mk(head, cap, '-gravity', 'NorthWest', '-geometry', '+1220+60', '-composite', head)
    rows = []
    for scen in ('overcast_morning', 'golden_hour', 'night_cozy'):
        fs = [os.path.join(R, f'{key}__{v}__{scen}.jpg') for v in VIEWS]
        if all(os.path.exists(f) for f in fs):
            r = os.path.join(tmp, f'{key}_{scen}.png'); mk(*fs, '-resize', f'{W}x{H}!', '+append', r); rows.append(r)
    out = os.path.join(tmp, f'{key}.png'); mk(head, *rows, '-append', '-bordercolor', 'white', '-border', '0x14', out)
    return out


mk('(', '-size', f'{4 * W}x110', 'xc:white', '-font', F, '-pointsize', 46, '-fill', '#1D1D1F', '-gravity', 'West', '-annotate', '+20+0', TITLE, ')',
   *[block(k) for k in KEYS], '-append', '-quality', 86, OUT)
print('sheet', OUT)
