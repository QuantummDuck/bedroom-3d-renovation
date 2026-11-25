"""Turns the clear-sky city HDRI into a blue-hour sky (sun ~3 degrees below the horizon) and saves it as
textures/dusk_from_homecoming_center_rooftop.exr. The skyline stays as dark silhouettes with a few lit windows; the sky is
replaced by a twilight gradient: warm glow on the horizon where the sun set, lavender above it, deep blue at the zenith.

  Blender -b --factory-startup --python tools/make_dusk_sky.py [-- preview.png]
"""
import bpy, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'textures', 'homecoming_center_rooftop', 'homecoming_center_rooftop_4k.hdr')
OUT = os.path.join(HERE, '..', 'textures', 'dusk_from_homecoming_center_rooftop.exr')
ROT = math.radians(-36.0)       # the same Mapping rotation the scene uses for this panorama (SUN_HDRI_ROTATION)
GLOW_AZ = math.radians(-105.0)  # where the sun set (same bearing as the afternoon sun, outside your window)
PREVIEW = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else None


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)


im = bpy.data.images.load(os.path.abspath(SRC)); w, h = im.size
px = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(px); px = px.reshape(h, w, 4)[::-1, :, :3]   # row 0 = zenith
elev = np.broadcast_to(((0.5 - (np.arange(h) + 0.5) / h) * 180.0)[:, None], (h, w))
az = np.broadcast_to((math.pi - 2 * math.pi * (np.arange(w) + 0.5) / w - ROT)[None, :], (h, w))     # world azimuth of each column
r, g, b = px[..., 0], px[..., 1], px[..., 2]
lum = 0.2126 * r + 0.7152 * g + 0.0722 * b

sky = np.clip((b / np.maximum(np.maximum(r, g), 1e-4) - 1.25) / 0.35, 0, 1)     # clear sky is strongly blue, buildings are not
sky = np.where(elev > 30, 1.0, sky) * (elev > -1.0)

# twilight sky (linear RGB, relative units)
toward = ((1 + np.cos(az - GLOW_AZ)) / 2)
Ch, Cm, Cz = np.array([0.30, 0.29, 0.42]), np.array([0.10, 0.13, 0.30]), np.array([0.022, 0.040, 0.12])
t1, t2 = smooth(0, 15, elev)[..., None], smooth(15, 70, elev)[..., None]
base = Ch * (1 - t1) + Cm * t1; base = base * (1 - t2) + Cz * t2
e_pos = np.maximum(elev, 0)[..., None]
glow = np.array([1.0, 0.42, 0.14]) * 1.6 * np.exp(-e_pos / 5.0) * toward[..., None] ** 4
pink = np.array([0.55, 0.25, 0.35]) * 0.5 * np.exp(-((elev[..., None] - 8) / 6) ** 2) * toward[..., None] ** 2
twilight = base + glow + pink

# skyline: sky-lit silhouettes, a little bluer; a few warm lit windows; the rooftop below even darker
city = px * 0.14 * np.array([0.75, 0.85, 1.15]) * np.where(elev < -2.5, 0.3, 1.0)[..., None]
cell = (np.arange(h)[:, None] // 2) * 7919 + (np.arange(w)[None, :] // 3) * 104729
rnd = np.sin(cell * 12.9898) * 43758.5453; rnd = rnd - np.floor(rnd)
green = (g > r) & (g > 1.05 * b)                                                   # hillside vegetation: no windows
lit = (rnd < 0.035) & (elev > -3) & (elev < 8) & (sky < 0.2) & (lum > 0.04) & ~green
city = np.where(lit[..., None], np.array([1.0, 0.72, 0.42]) * (0.35 + 0.6 * rnd[..., None] / 0.035), city)

out = twilight * sky[..., None] + city * (1 - sky[..., None])
rgba = np.concatenate([out, np.ones((h, w, 1))], -1)[::-1].astype(np.float32)
img = bpy.data.images.new('dusk', w, h, float_buffer=True); img.pixels.foreach_set(rgba.ravel())
sc = bpy.context.scene; s = sc.render.image_settings
s.file_format = 'OPEN_EXR'; s.color_depth = '16'; s.exr_codec = 'ZIP'; s.color_mode = 'RGB'
img.save_render(os.path.abspath(OUT), scene=sc)
print('SAVED', os.path.abspath(OUT), f'{os.path.getsize(os.path.abspath(OUT)) / 1e6:.1f} MB',
      'horizon toward sunset', out[int(h * 0.49), int(w * ((math.pi - GLOW_AZ - ROT) / (2 * math.pi) % 1))].round(3))
if PREVIEW:                                    # quick look: simple tone map, 1024 wide
    sm = out[::4, ::4]; sm = 1 - np.exp(-sm * 3.0); sm = np.clip(sm, 0, 1) ** (1 / 2.2)
    p = bpy.data.images.new('pv', sm.shape[1], sm.shape[0])
    p.pixels.foreach_set(np.concatenate([sm, np.ones(sm.shape[:2] + (1,))], -1)[::-1].astype(np.float32).ravel())
    p.filepath_raw = PREVIEW; p.file_format = 'PNG'; p.save(); print('PREVIEW', PREVIEW)
