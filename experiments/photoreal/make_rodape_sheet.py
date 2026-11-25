"""Rodape colour sheets + drawer sheet from renders/rodape and renders/drawers.  python3 make_rodape_sheet.py"""
import os, subprocess, tempfile, sys
HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(HERE, 'renders'); F = '/System/Library/Fonts/Avenir.ttc'
COLORS = [('01_off_white', 'Off-white (now)', '#F0EFEA'), ('02_warm_ivory', 'Warm ivory', '#EBE0C8'), ('03_sand_greige', 'Sand greige', '#C9B99D'),
          ('04_mustard_ochre', 'Mustard ochre', '#C0923F'), ('05_terracotta', 'Terracotta', '#B0603F'), ('06_oxblood', 'Oxblood', '#6A2C2A'),
          ('07_olive_moss', 'Olive moss', '#6A6B45'), ('08_walnut_brown', 'Walnut brown (painted)', '#5B3F2C'), ('09_teak_wood', 'Teak wood, like the boards', None),
          ('10_navy_drench', 'Navy, same as the walls', '#2F3D52'), ('11_charcoal', 'Charcoal', '#2B2A28')]   # same list as rodape_render.py
COLS = ['R1_Wide_Table_Corner__overcast_morning', 'L20_Center_To_Door__overcast_morning', 'R3_Skirting_Door_Corner__overcast_morning',
        'R4_Crown_Corner__overcast_morning', 'R1_Wide_Table_Corner__night_cozy', 'R4_Crown_Corner__night_cozy']
HEAD = ['Wide, day', 'Toward the door, day', 'Skirting by the door, day', 'Crown corner, day', 'Wide, night', 'Crown corner, night']
W, Hh = 480, 270; tmp = tempfile.mkdtemp()
def mk(*a): subprocess.run(['magick', *map(str, a)], check=True)
def row(files, label, hexc):
    sw = ['(', '-size', '60x60', f'xc:{hexc or "#9A6A3E"}', '-bordercolor', '#BBBBBB', '-border', '2', ')']
    out = os.path.join(tmp, label.replace(' ', '_') + '.png')
    mk(*files, '-resize', f'{W}x{Hh}!', '+append', '(', '-size', f'{6 * W}x76', 'xc:#F4F4F1', '-font', F, '-pointsize', 34, '-fill', '#1D1D1F',
       '-gravity', 'West', '-annotate', '+90+0', f'{label}   {hexc or "teak veneer"}', *sw, '-gravity', 'West', '-geometry', '+14+0', '-composite', ')', '+swap', '-append', out)
    return out
rows = [row([os.path.join(R, 'rodape', f'{slug}__{c}.jpg') for c in COLS], label, hexc) for slug, label, hexc in COLORS]
head = os.path.join(tmp, 'head.png')
mk('-size', f'{6 * W}x50', 'xc:white', '-font', F, '-pointsize', 26, '-fill', '#6E6E73', *sum([['-gravity', 'NorthWest', '-annotate', f'+{i * W + 12}+12', h] for i, h in enumerate(HEAD)], []), head)
title = lambda t, n=6: ['(', '-size', f'{n * W}x90', 'xc:white', '-font', F, '-pointsize', 44, '-fill', '#1D1D1F', '-gravity', 'West', '-annotate', '+14+0', t, ')']
mk(*title('Rodapé colours (skirting + crown molding + cove ledge), 1 of 2'), head, *rows[:6], '-append', '-quality', 88, os.path.join(R, 'Rodape_colours_1.jpg'))
mk(*title('Rodapé colours (skirting + crown molding + cove ledge), 2 of 2'), head, *rows[6:], '-append', '-quality', 88, os.path.join(R, 'Rodape_colours_2.jpg'))
d = os.path.join(R, 'drawers'); cams = ['DR1_Drawers_Wide', 'DR2_Drawer_Front', 'DR3_Corner_Unit', 'L2_Table_Shelves', 'L18_Corner_High_Bed']
mk(*title('Rolling drawer unit + standardised 9.5 cm boards (top: day, bottom: night)', 5),
   '(', *[os.path.join(d, f'{c}__overcast_morning.jpg') for c in cams], '-resize', f'{W}x{Hh}!', '+append', ')',
   '(', *[os.path.join(d, f'{c}__night_cozy.jpg') for c in cams], '-resize', f'{W}x{Hh}!', '+append', ')', '-append', '-quality', 88, os.path.join(R, 'Drawers_and_boards.jpg'))
print('sheets ok')
