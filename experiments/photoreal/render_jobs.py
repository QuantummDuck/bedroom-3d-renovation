"""Render (camera x lighting scenario) jobs from a photoreal .blend.
  Blender -b FILE.blend --python render_jobs.py -- out=DIR cams=CAM_A,CAM_B scen=night_cozy,blue_hour [w=2400 h=1600] [spp=1024] [pct=100]
Portrait cameras (*_Portrait) swap w/h. Photo-matched cameras (CAM_Photo_NN) render at their photo's aspect.
Each image is saved as DIR/<camera>__<scenario>.png (16-bit) plus a .jpg preview."""
import bpy, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import photoreal_common as P

A = dict(a.split('=', 1) for a in sys.argv[sys.argv.index('--') + 1:]) if '--' in sys.argv else {}
sc = bpy.context.scene
V5 = 'LED_Master' in sc
GROUPS = ('Cove', 'Shelves', 'Piano', 'BedPanel', 'Desk', 'Wardrobe')
BASE = {'BedPanel': 0.16, 'Cove': 0.55}         # blue = a quiet accent; the cove is a dim base light


def leds(levels):
    if not V5: return
    for k in GROUPS: sc[f'{k}_Brightness'] = BASE.get(k, 1.0) * levels.get(k, levels.get('all', 0.0))


def practicals(desk=0.0, fan=0.0, fairy=0.0, screen=1.0):
    lt = bpy.data.objects.get('LIGHT_Desk_Lamp')
    if lt: lt.data.energy = desk; lt.hide_render = desk <= 0
    for m in bpy.data.materials:
        g = m.node_tree.nodes.get('LAMP_GLOW') if m.use_nodes and m.node_tree else None
        if g: g.inputs[1].default_value = 40.0 * desk / 40.0
    fb = bpy.data.objects.get('LIGHT_Fan_Bulb')
    if fb: fb.data.energy = fan; fb.hide_render = fan <= 0
    op = bpy.data.materials.get('M_Fan_Opal')
    if op: op.node_tree.nodes['FAN_GLOW'].inputs['Strength'].default_value = 1.6 * fan / 60.0
    for n in ('LIGHT_Shelf_Fairy_1', 'LIGHT_Shelf_Fairy_2', 'LIGHT_Shelf_Fairy_3'):
        o = bpy.data.objects.get(n)
        if o: o.data.energy = fairy * o.get('base_energy', 1.0); o.hide_render = fairy <= 0
    sm = bpy.data.materials.get('M_MBA_Screen_Glass')
    if sm and sm.node_tree.nodes.get('SCREEN_ON'): sm.node_tree.nodes['SCREEN_ON'].outputs[0].default_value = 4.0 * screen
    fm = bpy.data.materials.get('M_Fairy_Bulb')
    if fm: P.bsdf(fm).inputs['Emission Strength'].default_value = 60.0 * fairy


# name: world, sun (day, time, K, W/m2), sky scale/tint, LEDs, practicals, exposure (v5, current), white balance K
SCEN = {
    'overcast_morning': dict(world=('WORLD_Daylight', 0), leds={}, prac={}, expo=(2.3, 0.6), wb=8500, tint_wb=12.0),   # wb/tint matched to your photos 06/19
    'afternoon_sun':    dict(world=('WORLD_Daylight', 1), sun=('2026-10-15', '16:00', 5300, 29.4), leds={}, prac={}, expo=(1.9, 0.3), wb=7000, tint_wb=10.0),
    'late_sun':         dict(world=('WORLD_Daylight', 1), sun=('2026-10-15', '17:00', 4300, 26.0), sky=0.7, tint=(1.0, 0.93, 0.85),
                             leds={}, prac={}, expo=(2.1, 0.4), wb=6400, tint_wb=10.0),
    'golden_hour':      dict(world=('WORLD_Daylight', 1), sun=('2026-10-15', '17:40', 3100, 14.0), sky=0.28, tint=(1.0, 0.78, 0.6),
                             leds={'Cove': 0.25, 'Shelves': 0.3, 'Piano': 0.12}, prac={'fairy': 0.5}, expo=(1.7, 0.5), wb=4600, tint_wb=6.0),
    'blue_hour':        dict(world=('WORLD_Dusk', None, 1.6), leds={'all': 1.0}, prac={'desk': 40.0, 'fairy': 1.0}, expo=(-0.8, -0.4), wb=4600, tower=0.6),
    'night_cozy':       dict(world=('WORLD_Night', None, 0.025), leds={'all': 1.0}, prac={'desk': 40.0, 'fairy': 1.0}, expo=(-0.6, -0.4), wb=4300, tower=1.0),
    'night_work':       dict(world=('WORLD_Night', None, 0.025), leds={'Shelves': 0.7, 'Desk': 0.6, 'Cove': 0.35}, prac={'desk': 60.0, 'fairy': 0.5},
                             expo=(0.1, -0.2), wb=3500, tower=1.0),
    'night_everyday':   dict(world=('WORLD_Night', None, 0.025), leds={}, prac={'desk': 40.0, 'fan': 60.0, 'fairy': 1.0}, fan_spin=True,
                             expo=(-0.2, -0.2), wb=3700, tower=1.0),
}


def scenario(name):
    if name.startswith('sun@'):          # sun@2026-10-15@16:30 : sun study frame (clear sky, sun placed for that moment)
        _, day, hhmm = name.split('@'); e = P.sun_at(day, hhmm)['elev']
        k = 3000 + 2600 * min(1.0, max(0.0, e / 30.0))                 # lower sun -> warmer light
        SCEN[name] = dict(world=('WORLD_Daylight', 1), sun=(day, hhmm, k, 29.4 * min(1.0, 0.35 + e / 40.0)), sky=min(1.0, 0.3 + e / 40),
                          tint=(1.0, 0.85 + 0.15 * min(1.0, e / 30), 0.75 + 0.25 * min(1.0, e / 30)), leds={}, prac={}, expo=(1.9, 0.6), wb=6400, tint_wb=10.0)
    s = SCEN[name]
    w = s['world']
    if w[0] == 'WORLD_Daylight': P.set_world('WORLD_Daylight', sunny=w[1], sky_scale=s.get('sky', 1.0), tint=s.get('tint', (1, 1, 1)))
    else: P.set_world(w[0], strength=w[2])
    if 'sun' in s: P.set_sun(s['sun'][0], s['sun'][1], s['sun'][2], s['sun'][3])
    else: P.set_sun(None)
    leds(s['leds']); practicals(**s['prac']); P.fan_spin(s.get('fan_spin', False))
    P.set_tower_night(s.get('tower', 0.0))
    sc.view_settings.exposure = s['expo'][0 if V5 else 1]
    P.white_balance(float(A['wb']) if 'wb' in A else s['wb'], float(A.get('tint', s.get('tint_wb', 0.0))))
    if 'expo' in A: sc.view_settings.exposure = float(A['expo'])
    sc.update_tag(); bpy.context.view_layer.update()


def main():
    out = A.get('out', os.path.join(P.HERE, 'renders', 'test')); os.makedirs(out, exist_ok=True)
    W, H = int(A.get('w', 2400)), int(A.get('h', 1600)); pct = int(A.get('pct', 100))
    ov = {}
    ovp = os.path.join(P.HERE, 'queue_overrides.json')      # tweak a running queue without restarting it
    if os.path.exists(ovp):
        import json; ov = json.load(open(ovp))
    if 'spp' in A: sc.cycles.samples = min(int(A['spp']), int(ov.get('spp_max', 10 ** 6)))
    if 'thr' in ov: sc.cycles.adaptive_threshold = float(ov['thr'])
    if 'thr' in A: sc.cycles.adaptive_threshold = float(A['thr'])
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_depth = '16'
    for scen in A.get('scen', 'night_cozy').split(','):
        scenario(scen)
        for cname in A.get('cams', 'CAM_PR_01_Door').split(','):
            cam = bpy.data.objects[cname]; sc.camera = cam
            w, h = (H, W) if cname.endswith('Portrait') else (W, H)
            if 'photo_size' in cam: pw, ph = cam['photo_size']; w, h = (W, round(W * ph / pw)) if pw >= ph else (round(H * pw / ph), H)
            sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = w, h, pct
            path = os.path.join(out, f'{cname.replace("CAM_", "")}__{scen.replace("@", "_").replace(":", "")}.png'); sc.render.filepath = path
            t0 = time.time(); bpy.ops.render.render(write_still=True)
            subprocess.run(['magick', path, '-quality', '92', path[:-4] + '.jpg'], check=False)
            print(f'RENDERED {os.path.basename(path)} {time.time() - t0:.0f}s', flush=True)


if __name__ == '__main__':
    main()
