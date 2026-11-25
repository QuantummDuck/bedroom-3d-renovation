"""Labelled contact sheets of the final renders (ImageMagick 7).  python3 make_sheets.py
renders/final/*.jpg -> renders/Sheet_Teak_Navy.jpg, renders/Sheet_Current_Room.jpg, renders/Sheet_Sun_Study.jpg"""
import glob, os, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(HERE, 'renders')
FONT = '/System/Library/Fonts/Avenir.ttc'
SCEN = {'overcast_morning': 'Overcast morning', 'afternoon_sun': 'Sun, 4:00 pm', 'late_sun': 'Sun, 5:00 pm', 'golden_hour': 'Golden hour, 5:40 pm',
        'blue_hour': 'Blue hour, LEDs on', 'night_cozy': 'Night: all cozy layers', 'night_work': 'Night: work light', 'night_everyday': 'Night: fan light on'}


def label(path):
    base = os.path.basename(path)[:-4]; cam, scen = base.split('__', 1)
    cam = cam.replace('PR_', '').replace('_', ' ')
    if scen.startswith('sun_'):
        _, day, t = scen.split('_'); return f'{day}  {t[:2]}:{t[2:]}'
    if '/current/' in path:     # your room today has no LED strips: say what is actually on
        scen_lab = {'blue_hour': 'Blue hour, desk lamp + shelf fairy lights', 'night_cozy': 'Night: desk lamp + fairy lights',
                    'night_work': 'Night: desk lamp + fairy lights, dimmer'}.get(scen, SCEN.get(scen, scen))
        return f'{cam}  ·  {scen_lab}'
    return f'{cam}  ·  {SCEN.get(scen, scen)}'


def sheet(files, out, title, cols=3, w=900):
    tmp = tempfile.mkdtemp(); tiles = []
    for i, f in enumerate(files):
        t = os.path.join(tmp, f'{i:03d}.jpg')
        subprocess.run(['magick', f, '-resize', f'{w}x{round(w * 9 / 16)}', '-gravity', 'center', '-background', '#111111', '-extent', f'{w}x{round(w * 9 / 16)}',
                        '(', '-size', f'{w}x44', 'xc:#F4F4F1', '-font', FONT, '-pointsize', '22', '-fill', '#1D1D1F', '-gravity', 'West',
                        '-annotate', '+14+0', label(f), ')', '-append', t], check=True)
        tiles.append(t)
    rows = []
    for r in range(0, len(tiles), cols):
        row = os.path.join(tmp, f'row{r:03d}.jpg')
        subprocess.run(['magick', *tiles[r:r + cols], '-background', '#F4F4F1', '-gravity', 'West', '-splice', '10x0', '+append', '-chop', '10x0', row], check=True)
        rows.append(row)
    subprocess.run(['magick', '(', '-size', f'{cols * w + (cols - 1) * 10}x90', 'xc:#F4F4F1', '-font', FONT, '-pointsize', '40', '-fill', '#1D1D1F',
                    '-gravity', 'West', '-annotate', '+14+0', title, ')', *rows, '-background', '#F4F4F1', '-gravity', 'North', '-splice', '0x10', '-append', '-quality', '90', out],
                   check=True)
    print('sheet', out, len(files))


if __name__ == '__main__':
    assert label('/x/PR_01_Door__night_cozy.jpg') == '01 Door  ·  Night: all cozy layers'
    fin = sorted(glob.glob(os.path.join(R, 'final', 'v5', '*.jpg')))
    if fin: sheet(fin, os.path.join(R, 'Sheet_Teak_Navy.jpg'), 'Teak & navy (round 5): photoreal renders')
    cur = sorted(glob.glob(os.path.join(R, 'final', 'current', '*.jpg')))
    if cur: sheet(cur, os.path.join(R, 'Sheet_Current_Room.jpg'), 'Your room today: photoreal digital twin')
    order = ['overcast_morning', 'afternoon_sun', 'late_sun', 'golden_hour', 'blue_hour', 'night_cozy', 'night_work', 'night_everyday']
    for sub, title, out in (('v5', 'Same view, 8 lightings: teak & navy', 'Sheet_Lighting_Teak_Navy.jpg'),
                            ('current', 'Same view, 8 lightings: your room today', 'Sheet_Lighting_Current_Room.jpg')):
        fs = [os.path.join(R, 'final', sub, f'PR_01_Door__{o}.jpg') for o in order]
        fs = [f for f in fs if os.path.exists(f)]
        if len(fs) >= 4: sheet(fs, os.path.join(R, out), title, cols=4, w=700)
    sun = sorted(glob.glob(os.path.join(R, 'final', 'sun', '*.jpg')))
    if sun: sheet(sun, os.path.join(R, 'Sheet_Sun_Study.jpg'), 'Sun study: where the sun lands (window faces 260°)', cols=4, w=700)
