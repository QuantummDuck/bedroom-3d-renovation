"""Numbered lighting-plan overlays on two views + the cozy comparison sheet (ImageMagick 7).  python3 make_plan_v4.py"""
import json, os, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(HERE, 'renders_v4')
FONT = '/System/Library/Fonts/Avenir.ttc'; BG, INK, MUTED = '#F4F4F1', '#1D1D1F', '#6E6E73'
ORDER = ['Cove', 'Shelves', 'Piano', 'BedPanel', 'Puzzle', 'Desk', 'Wardrobe', 'Fairy', 'Sconce', 'DeskLamp']
plan = json.load(open(os.path.join(R, 'plan.json'))); tmp = tempfile.mkdtemp()


def magick(*a):
    subprocess.run(['magick', *map(str, a)], check=True)


for cam in ('CAM_Dusk_Wide', 'CAM_Render_B_From_Window'):
    src = os.path.join(R, 'views', cam.replace('CAM_', '') + '.png'); ops = []
    for k, (x, y) in plan['callouts'][cam].items():
        px, py, n = round(x * 1920), round(y * 1080), ORDER.index(k) + 1
        ops += ['-fill', '#1D1D1FDD', '-stroke', 'white', '-strokewidth', 3, '-draw', f'circle {px},{py} {px + 24},{py}',
                '-stroke', 'none', '-fill', 'white', '-font', FONT, '-pointsize', 26, '-gravity', 'NorthWest',
                '-annotate', f'+{px - (8 if n < 10 else 15)}+{py - 17}', str(n)]
    magick(src, *ops, '-quality', 92, os.path.join(R, f'plan_{cam.replace("CAM_", "")}.jpg'))
    print('plan', cam)
a, b = os.path.join(R, 'compare', 'A_warm_base_only.png'), os.path.join(R, 'compare', 'B_cozy_layers.png')
for src, lab, out in ((a, 'Before: warm base only (shelves, piano, desk lamp)', 'a.png'), (b, 'After: all cozy layers', 'b.png')):
    magick(src, '-resize', '1280x720!', '(', '-size', '1280x60', 'xc:white', '-font', FONT, '-pointsize', 28, '-fill', INK,
           '-gravity', 'West', '-annotate', '+20+0', lab, ')', '-append', os.path.join(tmp, out))
magick(os.path.join(tmp, 'a.png'), os.path.join(tmp, 'b.png'), '-background', BG, '-splice', '12x0', '+append', '-quality', 92,
       os.path.join(R, 'compare_before_after.jpg'))
print('compare ok')
