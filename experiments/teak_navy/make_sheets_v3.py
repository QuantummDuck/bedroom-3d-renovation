"""LED colour sheet from renders_v3/colors (ImageMagick 7).  python3 make_sheets_v3.py"""
import json, os, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(HERE, 'renders_v3')
FONT = '/System/Library/Fonts/Avenir.ttc'; BG, INK, MUTED = '#F4F4F1', '#1D1D1F', '#6E6E73'
opts = json.load(open(os.path.join(R, 'options.json'))); tmp = tempfile.mkdtemp(); tiles = []
for o in opts['colors']:
    t = os.path.join(tmp, o['code'] + '.png'); tiles.append(t)
    subprocess.run(['magick', '(', os.path.join(R, 'colors', f"{o['code']}_{o['slug']}.png"), '-resize', '960x540!', ')',
                    '(', '-size', '960x70', 'xc:white', '-fill', o['hex'], '-stroke', '#C8C8C4', '-strokewidth', '2',
                    '-draw', 'roundrectangle 20,16 58,54 8,8', '-stroke', 'none', '-font', FONT, '-fill', INK, '-pointsize', '32',
                    '-annotate', '+74+48', f"{o['code']}   {o['label']}", ')', '-append', t], check=True)
grid = os.path.join(tmp, 'grid.png')
subprocess.run(['magick', 'montage', '-font', FONT, *tiles, '-tile', '3x', '-geometry', '+12+12', '-background', BG, grid], check=True)
subprocess.run(['magick', grid, '-background', BG, '-gravity', 'north', '-splice', '0x110', '-font', FONT, '-fill', INK, '-pointsize', '46',
                '-annotate', '+0+22', 'RGB LED strips  ·  colour options', '-fill', MUTED, '-pointsize', '24', '-annotate', '+0+80',
                'Blue hour, ceiling light off, desk lamp on. Shelf wall-wash + piano halo share the colour (Scene > LED_RGB).',
                '-quality', '90', os.path.join(R, 'options_led_colors.jpg')], check=True)
print('sheet ok')
