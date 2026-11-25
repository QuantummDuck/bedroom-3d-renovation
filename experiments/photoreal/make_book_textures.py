"""Your books, one spine texture each, cut out of the shelf photos (46-49) with a perspective rectification.
  python3 make_book_textures.py  ->  textures/books/<id>.png + textures/books/books.json
Spine corners were read off zoomed, gridded crops of each photo (display coords + crop origin/scale below).
Physical sizes come from each row's px/cm scale, set by a book of known height in that row (e.g. L&PM pocket 17.8 cm)."""
import json, os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from imgtool import load
REF = os.path.join(ROOT, 'reference', 'round5'); OUT = os.path.join(ROOT, 'textures', 'books'); os.makedirs(OUT, exist_ok=True)
PXCM = 40   # texture resolution, px per cm

# crops the corners were read in: name -> (photo, x0, y0, scale)
CROPS = {'r1': (46, 730, 300, 1.5), 'c': (46, 60, 1020, 2.0), 'a': (46, 100, 560, 2.0), 'de': (46, 270, 1000, 1.0),
         'p47': (47, 0, 380, 0.75), 'p48': (48, 0, 300, 0.7), 'p49': (49, 200, 400, 0.95)}

# STANDING books: id, crop, bottom-left x, bottom-right x, bottom y, top-left x, top-right x, top y   (display coords)
# row px/cm scale (full-res photo px per cm) per crop
STAND = {
    'r1': (25.9, [('ego_inimigo', 70, 145, 967, 25, 100, 150), ('meditacoes', 145, 205, 967, 95, 155, 142),
                  ('epicteto', 205, 250, 967, 155, 215, 145), ('pense_estoico', 250, 325, 967, 225, 295, 142),
                  ('48_leis', 325, 385, 967, 295, 360, 115), ('arte_seducao', 385, 452, 967, 362, 430, 112),
                  ('teste_qi', 455, 505, 967, 435, 490, 110), ('olhos_prateados', 505, 600, 967, 488, 582, 95),
                  ('metafisica', 605, 655, 967, 595, 640, 100), ('raciocinio', 655, 770, 967, 635, 748, 63),
                  ('almanaque', 770, 852, 967, 752, 850, 75), ('simplicidades', 852, 935, 967, 855, 912, 58)]),
    'c': (26.7, [('memorias_subsolo', 150, 205, 1165, 205, 262, 85), ('essencialismo', 207, 290, 1165, 285, 365, 40),
                 ('o_principe', 293, 350, 1162, 355, 410, 210), ('schopenhauer', 352, 395, 1158, 448, 492, 150),
                 ('genealogia', 395, 450, 1160, 478, 545, 210), ('nascimento_tragedia', 455, 510, 1162, 535, 600, 210),
                 ('entender_nietzsche', 508, 565, 1150, 600, 655, 360)]),
    'de': (30.2, [('revolucao_bichos', 708, 760, 675, 712, 752, 40), ('hugo_cabret', 760, 865, 675, 760, 862, 40),
                  ('etica', 865, 950, 675, 866, 948, 45), ('cortella', 950, 995, 675, 950, 993, 40),
                  ('enigma_quantico', 995, 1055, 675, 995, 1053, 40)]),
    'p49': (30.7, [('eu_robo', 45, 105, 662, 45, 105, 50), ('todo_dia_deus', 108, 180, 662, 120, 185, 48)]),
}
# LYING books (spine bands): id, crop, x_left, x_right, top/bottom y at the left end, top/bottom y at the right end, length cm, depth cm
LIE = {
    'a': (26.0, [('orwell_1984', 180, 640, 105, 200, 75, 180, 21.0, 14.0), ('steve_jobs', 165, 640, 200, 384, 176, 360, 23.5, 16.0),
                 ('contos_machado', 165, 640, 394, 524, 370, 500, 21.0, 14.0), ('classicos_ouro', 165, 640, 524, 574, 500, 550, 19.0, 13.0),
                 ('tom_gilbin', 165, 640, 574, 634, 550, 610, 21.0, 14.0), ('universo_casca', 55, 640, 644, 720, 620, 696, 24.5, 18.0),
                 ('mc_escher', 45, 640, 724, 790, 700, 770, 26.0, 21.0)]),
    'de': (30.2, [('habitos_atomicos', 205, 718, 515, 590, 515, 592, 23.0, 16.0), ('7_habitos', 205, 718, 590, 627, 592, 629, 21.0, 14.0),
                  ('crepusculo_idolos', 205, 718, 627, 660, 629, 662, 18.0, 11.0)]),
    'p49': (30.7, [('god_science', 175, 905, 375, 475, 375, 475, 24.0, 16.0), ('diario_perdido', 160, 920, 483, 550, 483, 550, 23.0, 16.0),
                   ('91_truques', 160, 1035, 553, 578, 553, 578, 27.0, 20.0), ('aumente_qi', 155, 1032, 580, 618, 580, 618, 27.0, 20.0),
                   ('padre_pio', 150, 1050, 620, 662, 620, 662, 28.0, 20.0)]),
    'p48': (22.3, [('blue_notebook', 340, 570, 710, 760, 710, 760, 21.0, 14.5), ('darwin_origem', 325, 740, 765, 838, 765, 838, 23.0, 16.0),
                   ('uma_vida_propositos', 325, 740, 840, 880, 840, 880, 23.0, 16.0)]),
    'p47': (21.5, [('mar_sem_fim', 430, 840, 822, 860, 822, 860, 23.0, 16.0)]),
}


def full(crop, dx, dy):
    _, x0, y0, s = CROPS[crop]
    return x0 + dx / s, y0 + dy / s


def warp(photo, pts, w, h, out):
    (blx, bly), (brx, bry), (trx, try_), (tlx, tly) = pts
    subprocess.run(['magick', os.path.join(REF, f'ref_{photo}.jpg'), '-virtual-pixel', 'edge', '-distort', 'Perspective',
                    f'{blx},{bly} 0,{h}  {brx},{bry} {w},{h}  {trx},{try_} {w},0  {tlx},{tly} 0,0',
                    '-crop', f'{w}x{h}+0+0', '+repage', out], check=True)


def mean_color(path):
    a = load(path).astype(float) / 255
    a = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    return [round(float(v), 4) for v in np.median(a.reshape(-1, 3), axis=0)]


def main():
    books = {}
    for crop, (s, rows) in STAND.items():
        photo = CROPS[crop][0]
        for bid, blx, brx, by, tlx, trx, ty in rows:
            BL, BR, TR, TL = full(crop, blx, by), full(crop, brx, by), full(crop, trx, ty), full(crop, tlx, ty)
            t = (BR[0] - BL[0]) / s; h = (BL[1] - TL[1]) / s
            w_, h_ = max(8, round(t * PXCM)), round(h * PXCM); out = os.path.join(OUT, f'{bid}.png')
            warp(photo, (BL, BR, TR, TL), w_, h_, out)
            books[bid] = dict(kind='stand', thick=round(t, 2), height=round(h, 2), color=mean_color(out), tex=f'{bid}.png')
    for crop, (s, rows) in LIE.items():
        photo = CROPS[crop][0]
        for bid, xl, xr, ytl, ybl, ytr, ybr, length, depth in rows:
            BL, BR, TR, TL = full(crop, xl, ybl), full(crop, xr, ybr), full(crop, xr, ytr), full(crop, xl, ytl)
            t = (BL[1] - TL[1]) / s; vis = (BR[0] - BL[0]) / s          # visible spine length (may be less than the book)
            w_, h_ = round(min(vis, length) * PXCM), max(8, round(t * PXCM)); out = os.path.join(OUT, f'{bid}.png')
            warp(photo, (BL, BR, TR, TL), w_, h_, out)
            books[bid] = dict(kind='lie', thick=round(t, 2), length=length, depth=depth, vis=round(min(vis, length) / length, 3),
                              color=mean_color(out), tex=f'{bid}.png')
    json.dump(books, open(os.path.join(OUT, 'books.json'), 'w'), indent=1)
    print(len(books), 'books ->', OUT)
    for k, v in books.items(): print(f'  {k:22s} {v["kind"]:5s} t={v["thick"]:5.2f} ' + (f'h={v["height"]:5.1f}' if v['kind'] == 'stand' else f'L={v["length"]}'))


if __name__ == '__main__':
    assert full('r1', 0, 0) == (730, 300)
    main()
