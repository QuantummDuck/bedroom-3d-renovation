"""Your photo vs the photoreal twin, from the same camera (CAM_Photo_NN solved from each photo).
  python3 make_compare.py  ->  renders/Compare_Photo_vs_Render.jpg"""
import os, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
FONT = '/System/Library/Fonts/Avenir.ttc'; W = 1100


def main():
    tmp = tempfile.mkdtemp(); rows = []
    for n in ('06', '08', '16', '19'):
        ren = os.path.join(HERE, 'renders', 'final', 'current', f'Photo_{n}__overcast_morning.jpg')
        if not os.path.exists(ren): continue
        pair = []
        for src, lab in ((os.path.join(ROOT, 'reference', f'ref_{n}.jpg'), f'Your photo {n}'), (ren, 'Render (same camera)')):
            t = os.path.join(tmp, f'{n}_{len(pair)}.jpg')
            subprocess.run(['magick', src, '-resize', f'{W}x', '(', '-size', f'{W}x44', 'xc:#F4F4F1', '-font', FONT, '-pointsize', '24',
                            '-fill', '#1D1D1F', '-gravity', 'West', '-annotate', '+14+0', lab, ')', '-append', t], check=True)
            pair.append(t)
        r = os.path.join(tmp, f'row_{n}.jpg')
        subprocess.run(['magick', pair[0], pair[1], '-background', '#F4F4F1', '-gravity', 'West', '-splice', '12x0', '+append', '-chop', '12x0', r], check=True)
        rows.append(r)
    if not rows: print('no renders yet'); return
    out = os.path.join(HERE, 'renders', 'Compare_Photo_vs_Render.jpg')
    subprocess.run(['magick', *rows, '-background', '#F4F4F1', '-gravity', 'North', '-splice', '0x12', '-append', '-quality', '90', out], check=True)
    print('compare ->', out)


if __name__ == '__main__':
    main()
