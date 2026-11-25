"""Textures made from your close-up photos (round 5) -> textures/photo/
  python3 make_photo_textures.py
puzzle.png      ref_45 rectified (inner picture 70.8 x 47.2 cm), white-balanced on the wall around it
bedspread.png   ref_50 de-lit + flattened, remapped to the bedspread cloth's top-down UVs (x 60-300 cm, y 0-150 cm, 10 px/cm)
rug.png         ref_44 luminance, seamless (94 x 48 cm per tile)
wall_micro.png  ref_42 paint relief (high-pass), seamless (30 cm per tile, assumed)
floor_speckle.png ref_43 glaze speckle (high-pass), seamless (18 cm per tile)"""
import os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from imgtool import load, save_png
REF = os.path.join(ROOT, 'reference', 'round5'); OUT = os.path.join(ROOT, 'textures', 'photo'); os.makedirs(OUT, exist_ok=True)
TMP = os.path.join(OUT, '_tmp'); os.makedirs(TMP, exist_ok=True)


def mk(*a):
    subprocess.run(['magick', *map(str, a)], check=True)


def to_lin(a): a = a / 255.0; return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
def to_srgb(a): a = np.clip(a, 0, 1); return np.where(a <= 0.0031308, a * 12.92, 1.055 * a ** (1 / 2.4) - 0.055) * 255


def seamless(a):
    """Blend the image with a half-rolled copy under a feathered centre mask -> wraps without seams (2-D float array)."""
    h, w = a.shape[:2]; b = np.roll(np.roll(a, h // 2, 0), w // 2, 1)
    my = 1 - np.abs(np.linspace(-1, 1, h))[:, None]; mx = 1 - np.abs(np.linspace(-1, 1, w))[None, :]
    m = np.clip(np.minimum(my, mx) * 2.2, 0, 1) ** 1.5
    if a.ndim == 3: m = m[..., None]
    return a * m + b * (1 - m)


def save_gray16(a, path):
    """a in 0..1 -> 16-bit grey PNG (via raw + magick)."""
    raw = os.path.join(TMP, 'g.raw'); (np.clip(a, 0, 1) * 65535).astype('>u2').tofile(raw)
    mk('-endian', 'MSB', '-size', f'{a.shape[1]}x{a.shape[0]}', '-depth', '16', f'gray:{raw}', path)


def puzzle():
    # inner picture corners read off ref_45 (zoomed, gridded crops): TL, TR, BR, BL
    W, H = 1416, 944                                                 # 20 px/cm for 70.8 x 47.2 cm
    tmp = os.path.join(TMP, 'pz.png')
    mk(os.path.join(REF, 'ref_45.jpg'), '-distort', 'Perspective',
       f'60,50 0,0  1422,60 {W},0  1417,977 {W},{H}  48,957 0,{H}', '-crop', f'{W}x{H}+0+0', '+repage', tmp)
    wall = to_lin(load(os.path.join(REF, 'ref_45.jpg'))[1040:1110, 40:1400].reshape(-1, 3).astype(float)).mean(0)
    target = np.array([0.791, 0.753, 0.630])                         # calibrated wall paint #E6E1CF (linear)
    a = to_lin(load(tmp).astype(float)) * (target / wall)
    save_png(to_srgb(a).astype(np.uint8), os.path.join(OUT, 'puzzle.png'))
    print('puzzle gain', np.round(target / wall, 3))


def bedspread():
    src = os.path.join(REF, 'ref_50.jpg'); flat = os.path.join(TMP, 'bed_flat.png')
    # flatten wrinkle shading: 5x5 median (keeps the hard triangle edges, dots and stripes), then divide by a very soft
    # luminance blur (removes the light fall-off across the bed)
    mk(src, '-statistic', 'Median', '5x5', '(', '+clone', '-colorspace', 'gray', '-blur', '0x120', '-evaluate', 'multiply', '1.7', ')',
       '-compose', 'Divide_Src', '-composite', flat)                # divisor scaled up so nothing clips at 1.0
    a = to_lin(load(flat).astype(float))
    lum = a @ np.array([0.2126, 0.7152, 0.0722])
    white = a[lum >= np.percentile(lum, 96)].mean(0)
    a = a * (np.array([0.83, 0.82, 0.79]) / white)                   # white triangles -> off-white cotton
    PX = 14.7                                                        # px per cm in ref_50 (dot pitch / bed width)
    W, H = 2400, 1500; x = 60 + (np.arange(W) + 0.5) / 10; y = 150 * (1 - (np.arange(H) + 0.5) / H)
    X, Y = np.meshgrid(x, y)
    X = np.where(X > 239.2, X - 70.7, X)                             # hidden head end: continue the lattice (period 35.4 cm, autocorrelation)
    X = np.where(X < 110.2, 2 * 110.2 - X, X)                        # foot drape: mirror at the fold
    Y = np.where(Y > 95.8, 2 * 95.8 - Y, Y); Y = np.where(Y < 1.8, 2 * 1.8 - Y, Y)
    py = np.clip(1900 - (X - 110.2) * PX, 0, a.shape[0] - 1).astype(int); px = np.clip(90 + (95.8 - Y) * PX, 0, a.shape[1] - 1).astype(int)
    save_png(to_srgb(a[py, px]).astype(np.uint8), os.path.join(OUT, 'bedspread.png'))
    print('bedspread white', np.round(white, 3))


def gray(path, crop, hp=None):
    a = load(path).astype(float)
    if crop: x, y, w, h = crop; a = a[y:y + h, x:x + w]
    g = a @ np.array([0.2126, 0.7152, 0.0722]) / 255
    if hp:   # high-pass: remove lighting gradients, keep the surface texture
        tmp_in, tmp_bl = os.path.join(TMP, 'hp_in.png'), os.path.join(TMP, 'hp_bl.png')
        save_png(np.repeat((g * 255).astype(np.uint8)[..., None], 3, 2), tmp_in)
        mk(tmp_in, '-blur', f'0x{hp}', tmp_bl)
        g = g - load(tmp_bl).astype(float)[..., 0] / 255
        g = 0.5 + g / (6 * g.std())
    return g


def rug():
    g = gray(os.path.join(REF, 'ref_44.jpg'), (0, 180, 1125, 580))
    g = (g - g.min()) / (g.max() - g.min())
    save_gray16(seamless(g), os.path.join(OUT, 'rug.png'))


def wall_micro():
    save_gray16(seamless(gray(os.path.join(REF, 'ref_42.jpg'), (50, 300, 1400, 1400), hp=8)), os.path.join(OUT, 'wall_micro.png'))


def floor_speckle():
    save_gray16(seamless(gray(os.path.join(REF, 'ref_43.jpg'), (610, 550, 300, 300), hp=10)), os.path.join(OUT, 'floor_speckle.png'))


if __name__ == '__main__':
    t = np.add.outer(np.linspace(0, 1, 64), np.linspace(0, 1, 48)); s = seamless(t)   # a ramp wraps badly until made seamless
    assert abs(s[0] - s[-1]).mean() < abs(t[0] - t[-1]).mean()     # wraps better than the input
    puzzle(); bedspread(); rug(); wall_micro(); floor_speckle()
    print('photo textures ->', OUT)
