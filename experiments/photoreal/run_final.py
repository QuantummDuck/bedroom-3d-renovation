"""Overnight render queue, in priority order. Resumable: images that already exist are skipped.
  python3 run_final.py [--dry]      (log: renders/final/queue.log)"""
import os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
B = os.path.expanduser('~/Library/Application Support/Steam/steamapps/common/Blender/Blender.app/Contents/MacOS/Blender')
V5 = os.path.join(ROOT, 'experiments', 'teak_navy', 'Bedroom_Teak_Navy_v5.blend')
CUR = os.path.join(HERE, 'Bedroom_Current_Photoreal.blend')
OUT = os.path.join(HERE, 'renders', 'final')
HD, K4, SUN = (2560, 1440), (3840, 2160), (1600, 900)

# (file, out subdir, scenario, cameras, size, samples)
JOBS = [
    (V5, 'v5', 'night_cozy', ['CAM_PR_01_Door'], K4, 1024),
    (V5, 'v5', 'blue_hour', ['CAM_PR_03_Bed_Corner'], K4, 1024),
    (V5, 'v5', 'golden_hour', ['CAM_PR_02_Toward_Door'], K4, 1024),
    (CUR, 'current', 'overcast_morning', ['CAM_PR_01_Door'], K4, 1024),
    (CUR, 'sun', 'sun@2026-10-15@12:30', ['CAM_Sun_Study'], SUN, 256),
    (CUR, 'sun', 'sun@2026-10-15@13:30', ['CAM_Sun_Study'], SUN, 256),
    (CUR, 'sun', 'sun@2026-10-15@14:30', ['CAM_Sun_Study'], SUN, 256),
    (CUR, 'sun', 'sun@2026-10-15@15:30', ['CAM_Sun_Study'], SUN, 256),
    (CUR, 'sun', 'sun@2026-10-15@16:30', ['CAM_Sun_Study'], SUN, 256),
    (CUR, 'sun', 'sun@2026-10-15@17:30', ['CAM_Sun_Study'], SUN, 256),
    (CUR, 'sun', 'sun@2026-12-21@16:00', ['CAM_Sun_Study'], SUN, 256),
    (CUR, 'sun', 'sun@2027-06-21@15:00', ['CAM_Sun_Study'], SUN, 256),
    (V5, 'v5', 'night_cozy', ['CAM_PR_02_Toward_Door', 'CAM_PR_03_Bed_Corner', 'CAM_PR_04_Desk_Seated', 'CAM_PR_05_From_Bed',
                              'CAM_PR_06_Piano_Wall', 'CAM_PR_07_Door_Portrait', 'CAM_PR_D2_Desk_Lamp',
                              'CAM_PR_D3_Books', 'CAM_PR_D4_Window', 'CAM_PR_D5_Stool_Rug', 'CAM_PR_D6_Wardrobe_Glow'], HD, 1024),
    (V5, 'v5', 'blue_hour', ['CAM_PR_01_Door', 'CAM_PR_02_Toward_Door', 'CAM_PR_05_From_Bed'], HD, 1024),
    (V5, 'v5', 'golden_hour', ['CAM_PR_01_Door', 'CAM_PR_03_Bed_Corner', 'CAM_PR_05_From_Bed', 'CAM_PR_D1_Pillows'], HD, 1024),
    (V5, 'v5', 'afternoon_sun', ['CAM_PR_01_Door', 'CAM_PR_02_Toward_Door', 'CAM_PR_05_From_Bed', 'CAM_PR_D4_Window'], HD, 1024),
    (CUR, 'current', 'overcast_morning', ['CAM_PR_02_Toward_Door', 'CAM_PR_03_Bed_Corner', 'CAM_PR_04_Desk_Seated', 'CAM_PR_05_From_Bed',
                                          'CAM_PR_06_Piano_Wall', 'CAM_PR_D3_Books', 'CAM_Photo_06', 'CAM_Photo_08', 'CAM_Photo_16', 'CAM_Photo_19'], HD, 1024),
    (CUR, 'current', 'night_everyday', ['CAM_PR_01_Door', 'CAM_PR_03_Bed_Corner', 'CAM_PR_04_Desk_Seated', 'CAM_PR_05_From_Bed'], HD, 1024),
    (V5, 'v5', 'overcast_morning', ['CAM_PR_01_Door', 'CAM_PR_04_Desk_Seated', 'CAM_PR_06_Piano_Wall'], HD, 1024),
    (V5, 'v5', 'late_sun', ['CAM_PR_01_Door', 'CAM_PR_02_Toward_Door', 'CAM_PR_03_Bed_Corner'], HD, 1024),
    (V5, 'v5', 'night_work', ['CAM_PR_04_Desk_Seated', 'CAM_PR_01_Door'], HD, 1024),
    (V5, 'v5', 'night_everyday', ['CAM_PR_01_Door', 'CAM_PR_05_From_Bed'], HD, 1024),
    (CUR, 'current', 'afternoon_sun', ['CAM_PR_01_Door', 'CAM_PR_05_From_Bed', 'CAM_PR_02_Toward_Door'], HD, 1024),
    (CUR, 'current', 'golden_hour', ['CAM_PR_02_Toward_Door', 'CAM_PR_03_Bed_Corner'], HD, 1024),
    (CUR, 'current', 'late_sun', ['CAM_PR_02_Toward_Door'], HD, 1024),
]


def name(cam, scen):
    return f'{cam.replace("CAM_", "")}__{scen.replace("@", "_").replace(":", "")}.png'


def main(dry=False):
    os.makedirs(OUT, exist_ok=True); log = open(os.path.join(OUT, 'queue.log'), 'a')
    def say(msg):
        line = f'{time.strftime("%H:%M:%S")} {msg}'; print(line, flush=True); log.write(line + '\n'); log.flush()
    say(f'queue start, {sum(len(j[3]) for j in JOBS)} images')
    for f, sub, scen, cams, (w, h), spp in JOBS:
        d = os.path.join(OUT, sub); todo = [c for c in cams if not os.path.exists(os.path.join(d, name(c, scen)))]
        if not todo: continue
        say(f'{os.path.basename(f)} {scen} {",".join(todo)} {w}x{h} {spp}spp')
        if dry: continue
        t0 = time.time()
        r = subprocess.run([B, '-b', f, '--python', os.path.join(HERE, 'render_jobs.py'), '--', f'out={d}', f'cams={",".join(todo)}',
                            f'scen={scen}', f'w={w}', f'h={h}', f'spp={spp}'], capture_output=True, text=True)
        for line in r.stdout.splitlines():
            if line.startswith('RENDERED') or 'Error' in line or 'Traceback' in line: say('   ' + line)
        if r.returncode: say(f'   FAILED rc={r.returncode}: {r.stderr[-400:]}')
        say(f'   group done in {time.time() - t0:.0f}s')
    subprocess.run([sys.executable, os.path.join(HERE, 'make_sheets.py')])
    say('queue finished')


if __name__ == '__main__':
    assert name('CAM_PR_01_Door', 'sun@2026-10-15@16:30') == 'PR_01_Door__sun_2026-10-15_1630.png'
    main('--dry' in sys.argv)
