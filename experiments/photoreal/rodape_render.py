"""Rodape (skirting + crown molding + cove ledge) colour study on Bedroom_Teak_Navy_v9_layout.blend, fast low-res renders.
  Blender -b ../teak_navy/Bedroom_Teak_Navy_v9_layout.blend --python rodape_render.py -- out=renders/rodape [spp=32]"""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import photoreal_common as P
import render_jobs as RJ
A = dict(a.split('=', 1) for a in sys.argv[sys.argv.index('--') + 1:])
OUT = A['out']; os.makedirs(OUT, exist_ok=True); sc = bpy.context.scene; OBJ = bpy.data.objects
COLORS = [('01_off_white', 'Off-white (now)', '#F0EFEA'), ('02_warm_ivory', 'Warm ivory', '#EBE0C8'), ('03_sand_greige', 'Sand greige', '#C9B99D'),
          ('04_mustard_ochre', 'Mustard ochre', '#C0923F'), ('05_terracotta', 'Terracotta', '#B0603F'), ('06_oxblood', 'Oxblood', '#6A2C2A'),
          ('07_olive_moss', 'Olive moss', '#6A6B45'), ('08_walnut_brown', 'Walnut brown (painted)', '#5B3F2C'), ('09_teak_wood', 'Teak wood, like the boards', None),
          ('10_navy_drench', 'Navy, same as the walls', '#2F3D52'), ('11_charcoal', 'Charcoal', '#2B2A28')]
SHOTS = [('CAM_R1_Wide_Table_Corner', 'overcast_morning'), ('CAM_L20_Center_To_Door', 'overcast_morning'), ('CAM_R3_Skirting_Door_Corner', 'overcast_morning'),
         ('CAM_R4_Crown_Corner', 'overcast_morning'), ('CAM_R1_Wide_Table_Corner', 'night_cozy'), ('CAM_R4_Crown_Corner', 'night_cozy')]
rod, teak = bpy.data.materials['M_Rodape'], bpy.data.materials['M_Boards_teak']
TRIMS = ('ARCH_Baseboards', 'ARCH_Crown_Molding', 'ARCH_Cove_Ledge')
only = set(A['only'].split(',')) if 'only' in A else None
for slug, label, hexc in COLORS:
    if only and slug[:2] not in only: continue
    mat = teak if hexc is None else rod
    if hexc: P.bsdf(rod).inputs['Base Color'].default_value = (*P.lin(hexc), 1)
    for n in TRIMS: OBJ[n].data.materials[0] = mat
    for cam, scen in SHOTS:
        RJ.scenario(scen); sc.cycles.samples = int(A.get('spp', 32))
        sc.camera = OBJ[cam]; sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 960, 540, 100
        sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 90
        sc.render.filepath = os.path.join(OUT, f'{slug}__{cam[4:]}__{scen}.jpg'); bpy.ops.render.render(write_still=True)
        print('RENDERED', slug, cam, scen, flush=True)
