"""Aquarium position sheets from renders/aq: per variant, a morning row (+ plan) and a night row."""
import os, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(HERE, 'renders', 'aq'); F = '/System/Library/Fonts/Supplemental/Arial.ttf'
LAB = {'V1': 'V1  back corner, against the window wall', 'V2': 'V2  window-arm end, against the window wall', 'V3': 'V3  window-arm end, front corner', 'V4': 'V4  bed-end corner, along the frame wall'}
CAMS = ['L2_Table_Shelves', 'L4_Wardrobe_Gap', 'L11_Window_Arm_To_Bed', 'L18_Corner_High_Bed']
tmp = tempfile.mkdtemp()
def mk(*a): subprocess.run(['magick', *map(str, a)], check=True)
blocks = {}
for v, lab in LAB.items():
    row1 = [f'{R}/{v}__{c}__overcast_morning.png' for c in CAMS] + ['(', f'{R}/{v}__plan.png', '-resize', '720x720', '-gravity', 'center', '-background', '#F4F4F1', '-extent', '1280x720', ')']
    row2 = [f'{R}/{v}__{c}__night_cozy.png' for c in CAMS]
    mk(*row1, '+append', '-resize', '3000x', f'{tmp}/{v}a.png'); mk(*row2, '+append', '-resize', '3000x', f'{tmp}/{v}b.png')
    mk(f'{tmp}/{v}a.png', f'{tmp}/{v}b.png', '-append', '-font', F, '-gravity', 'northwest', '-background', 'white', '-splice', '0x70', '-pointsize', 48, '-fill', '#1D1D1F', '-annotate', '+20+10', lab, f'{tmp}/{v}.png')
for k, (a, b) in enumerate((('V1', 'V2'), ('V3', 'V4'))):
    mk(f'{tmp}/{a}.png', f'{tmp}/{b}.png', '-append', '-quality', 88, os.path.join(HERE, 'renders', f'Aquarium_positions_{k + 1}.jpg'))
print('ok')
