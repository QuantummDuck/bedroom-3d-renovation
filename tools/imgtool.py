"""Crop a reference photo, upscale it and draw a labelled pixel grid so coordinates can be read off.
usage: python3 imgtool.py IMG x0 y0 w h scale step OUT.png
"""
import os, struct, subprocess, sys, tempfile, zlib
import numpy as np

FONT = {  # 3x5 digits
    '0': "111101101101111", '1': "010110010010111", '2': "111001111100111", '3': "111001111001111",
    '4': "101101111001001", '5': "111100111001111", '6': "111100111101111", '7': "111001010010010",
    '8': "111101111101111", '9': "111101111001111",
}


def load(path):
    tmp = tempfile.mktemp(suffix='.bmp')
    subprocess.run(['sips', '-s', 'format', 'bmp', path, '--out', tmp], check=True, capture_output=True)
    b = open(tmp, 'rb').read(); os.remove(tmp)
    off, w, h, bpp = struct.unpack_from('<I', b, 10)[0], *struct.unpack_from('<ii', b, 18), struct.unpack_from('<H', b, 28)[0]
    bypp = bpp // 8; row = (w * bypp + 3) & ~3
    a = np.frombuffer(b, np.uint8, row * abs(h), off).reshape(abs(h), row)[:, :w * bypp].reshape(abs(h), w, bypp)
    a = a[::-1] if h > 0 else a
    return a[..., [2, 1, 0]].copy()


def save_png(a, path):
    h, w, _ = a.shape
    raw = b''.join(b'\x00' + a[y].tobytes() for y in range(h))
    chunk = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                           + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))


def text(a, s, x, y, k=3, col=(255, 0, 0)):
    for i, ch in enumerate(s):
        g = FONT.get(ch)
        if not g: continue
        for j, bit in enumerate(g):
            if bit == '1':
                yy, xx = y + (j // 3) * k, x + i * 4 * k + (j % 3) * k
                a[max(yy, 0):max(yy + k, 0), max(xx, 0):max(xx + k, 0)] = col


def grid(path, x0, y0, w, h, scale, step, out):
    a = load(path)[y0:y0 + h, x0:x0 + w]
    a = np.repeat(np.repeat(a, scale, 0), scale, 1)
    for gx in range((x0 // step + 1) * step, x0 + w, step):
        c = (255, 0, 0) if gx % (step * 2) == 0 else (0, 160, 255)
        a[:, (gx - x0) * scale] = c
        text(a, str(gx), (gx - x0) * scale + 3, 3, col=c)
    for gy in range((y0 // step + 1) * step, y0 + h, step):
        c = (255, 0, 0) if gy % (step * 2) == 0 else (0, 160, 255)
        a[(gy - y0) * scale, :] = c
        text(a, str(gy), 3, (gy - y0) * scale + 3, col=c)
    save_png(a, out)


if __name__ == '__main__':
    p = sys.argv
    grid(p[1], *map(int, p[2:8]), p[8])
