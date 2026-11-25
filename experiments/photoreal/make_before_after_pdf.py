"""Before_After_Teak_Navy.pdf (A4 landscape): your room today vs the teak & navy renovation, from the round-5 renders.
Every pair is the same camera and the same light. Two pairs per page.  python3 make_before_after_pdf.py"""
import os, subprocess, tempfile
from make_sheets import SCEN, label

HERE = os.path.dirname(os.path.abspath(__file__)); F = os.path.join(HERE, 'renders', 'final')
FONT = '/System/Library/Fonts/Avenir.ttc'; INK, MUTED = '#1D1D1F', '#6E6E73'
W, H, M, GAP = 2339, 1654, 80, 30                      # A4 landscape at 200 dpi
IW = (W - 2 * M - GAP) // 2; IH = IW * 9 // 16
VIEWS = {'PR_01_Door': 'From the door', 'PR_02_Toward_Door': 'Toward the door and wardrobe', 'PR_03_Bed_Corner': 'Bed corner',
         'PR_04_Desk_Seated': 'At the desk, seated', 'PR_05_From_Bed': 'From the bed', 'PR_06_Piano_Wall': 'Piano wall',
         'PR_10_Chair_Turned': 'Desk chair turned to the room'}
CHANGES = """What changed
•  Desk and shelf wall: horizontal teak boards, floor to crown
•  Other walls: deep navy (#2F3D52)
•  Desk: teak top, white cabinet and back board removed, two square black steel legs
•  Wardrobe: clad in teak, with deep navy strips
•  Bed panel: teak along the whole piano wall, down to the floor
•  New lighting: ceiling cove, shelf, piano, under-desk and wardrobe LED strips, plus a soft blue halo over the bed panel; the desk lamp stays warm white
•  Styling only: stacked pillows, no piano music rest, cleared desk

How to read it
Every pair uses the same camera and the same sun or sky. The room today has no LED strips, so its night pictures are lit only by the desk lamp and the fairy lights under the shelves."""


def magick(*a):
    subprocess.run(['magick', *map(str, a)], check=True)


def txt(s, x, y, size, color=INK):
    return ['-font', FONT, '-pointsize', size, '-fill', color, '-gravity', 'northwest', '-annotate', f'+{x}+{y}', s.replace('%', '%%')]


def img(path, x, y, w, h):
    return ['(', path, '-resize', f'{w}x{h}!', ')', '-gravity', 'northwest', '-geometry', f'+{x}+{y}', '-composite']   # gravity is sticky: always place from the top-left


def pairs():
    out = []
    for view in VIEWS:
        for scen in SCEN:                                  # SCEN keeps the morning -> night order
            b, a = (os.path.join(F, d, f'{view}__{scen}.jpg') for d in ('current', 'v5'))
            if os.path.exists(b) and os.path.exists(a): out.append((view, scen, b, a))
    return out


def main():
    tmp = tempfile.mkdtemp(); pages = []; P = pairs()
    def page(ops):
        out = os.path.join(tmp, f'p{len(pages) + 1:02d}.jpg'); pages.append(out)
        magick('-size', f'{W}x{H}', 'xc:white', *ops, *txt(f'Before & after  ·  page {len(pages)}', M, H - 60, 22, MUTED), '-quality', 90, out)
    # cover: title, the change list, and one pair stacked on the right
    view, scen, b, a = next(p for p in P if p[0] == 'PR_01_Door' and p[1] == 'golden_hour')
    cw, ch = 980, 980 * 9 // 16; cx = W - M - cw; y0 = 280; y1 = y0 + 45 + ch + 25
    assert y1 + 45 + ch + 20 + 40 < H - 70                # both cover images and the caption fit above the footer
    ops = txt('Before & after', M, 70, 76) + txt('Your bedroom today  vs  the teak & navy renovation', M + 4, 185, 34, MUTED)
    ops += ['(', '-size', f'{cx - M - 60}x', '-background', 'white', '-font', FONT, '-pointsize', 31, '-interline-spacing', 10, '-fill', INK,
            f'caption:{CHANGES}', ')', '-geometry', f'+{M}+300', '-composite']
    ops += txt('BEFORE  ·  today', cx, y0, 26, MUTED) + img(b, cx, y0 + 45, cw, ch)
    ops += txt('AFTER  ·  teak & navy', cx, y1, 26, MUTED) + img(a, cx, y1 + 45, cw, ch)
    ops += txt(f'{VIEWS[view]}  ·  {SCEN[scen]}', cx, y1 + 45 + ch + 20, 24, MUTED)
    page(ops)
    # two pairs per page
    for i in range(0, len(P), 2):
        ops = txt('BEFORE  ·  your room today', M, 60, 30, MUTED) + txt('AFTER  ·  teak & navy', M + IW + GAP, 60, 30, MUTED)
        y = 130
        for view, scen, b, a in P[i:i + 2]:
            before_light = label(b).split('  ·  ')[1]; after_light = SCEN[scen]
            ops += txt(f'{VIEWS[view]}  ·  {after_light}', M, y, 34)
            if before_light != after_light:                # no LED strips in the room today
                ops += ['-font', FONT, '-pointsize', 24, '-fill', MUTED, '-gravity', 'northeast', '-annotate', f'+{M}+{y + 8}',
                        'Before has no LED strips: desk lamp and fairy lights only']
            ops += img(b, M, y + 58, IW, IH) + img(a, M + IW + GAP, y + 58, IW, IH)
            y += 58 + IH + 60
        page(ops)
    out = os.path.join(HERE, 'Before_After_Teak_Navy.pdf')
    magick('-density', 200, '-units', 'PixelsPerInch', *pages, '-compress', 'jpeg', '-quality', 85, out)
    print('PDF', out, len(pages), 'pages,', len(P), 'pairs,', f'{os.path.getsize(out) / 1e6:.1f} MB')


if __name__ == '__main__':
    assert 58 + IH + 60 + 58 + IH + 130 < H - 70      # two rows fit above the footer
    main()
