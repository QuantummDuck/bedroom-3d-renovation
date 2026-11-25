"""Navy-centred colour study (round 11) on Bedroom_v11_Smoked_Teal.blend (slat wall, same geometry).
  Blender -b ../teak_navy/Bedroom_v11_Smoked_Teal.blend --python navy_palettes.py -- out=renders/navy [only=N1,N2] [scen=...] [spp=48] [save=N1 path=OUT.blend]
Recoloured together: walls 1/2/4, ceiling, rodape (skirting + crown + cove ledge), door + frame, wardrobe body/doors, wardrobe strips,
vertical slats (wood stain or paint), slat gaps (felt), wood stain (desk, bed panel, shelves, drawer unit, wood slats/strips).
Fixed: floor, window frame, your blue chair, bedspread, rug, lighting, geometry."""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import photoreal_common as P

WOOD = {'deep_teak': (0.545, 0.527, 0.475), 'oak': (0.92, 0.86, 0.74), 'walnut': (0.47, 0.40, 0.34)}
WOODHEX = {'deep_teak': '#86603C', 'oak': '#A9875D', 'walnut': '#6E4C34'}
NAVY = '#283548'          # warm-leaning navy: blue with a grey-green undertone, so it sits with wood instead of fighting it

def pal(title, why, walls, ceil, rod, door, ward, strips, slats, felt, wood):
    return dict(title=title, why=why, walls=walls, ceil=ceil, rod=rod, door=door, ward=ward, strips=strips, slats=slats, felt=felt, wood=wood)

PALETTES = {
 # ---------------- round 1: six distinct navy identities
 'N1': pal('Club Navy', 'Navy drenched on walls, trim, door and wardrobe; all the warmth comes from deep teak (slats, desk, strips) - the classic '
           'complementary navy + orange-brown pairing of old libraries and clubs. Warm parchment ceiling so the room keeps its height.',
           NAVY, '#D6CCBA', NAVY, NAVY, NAVY, 'wood', 'wood', '#0E1015', 'deep_teak'),
 'N2': pal('Navy & Camel', 'Two-tone: navy walls and trim, the big wardrobe in a soft camel with navy inlay strips. The warm neutral block bounces '
           'light and balances the dark walls 60/30/10 (navy / camel + wood / chair and bedspread accents).',
           NAVY, '#DED5C5', NAVY, NAVY, '#A88B6A', NAVY, 'wood', '#121620', 'deep_teak'),
 'N3': pal('Navy & Honey Oak', 'Navy drench with a lighter honey-oak wood instead of deep teak: same complementary logic, but the brighter wood '
           'lifts the whole room and keeps navy from feeling heavy - the most daylight-friendly navy.',
           NAVY, '#E2DACC', NAVY, NAVY, NAVY, 'wood', 'wood', '#0E1015', 'oak'),
 'N4': pal('Tonal Navy & Brass', 'Monochrome navy: the slats are painted a satin navy one step lighter than the walls, so the slat wall becomes '
           'texture rather than contrast; brass wardrobe strips are the single warm metal. Hotel-bar cocoon; teak stays on the desk and bed.',
           NAVY, '#D2C9B8', NAVY, NAVY, NAVY, 'brass', '#33435A', '#121620', 'deep_teak'),
 'N5': pal('Linen & Navy Joinery', 'Inverse: warm linen walls keep the room light; navy goes on everything built - wardrobe, door, skirting, crown and '
           'the slat gaps. Navy still defines the room (the wardrobe is its biggest surface) but the walls breathe.',
           '#CFC2AD', '#E6DFD3', NAVY, NAVY, NAVY, 'wood', 'wood', NAVY, 'deep_teak'),
 'N6': pal('Navy & Brick', 'Complementary at full strength: navy walls with the wardrobe in a muted brick-terracotta and navy inlay. Rust and navy '
           'are opposite on the wheel; greyed down, they read rich and warm rather than loud.',
           NAVY, '#D9CEBC', NAVY, NAVY, '#7E4636', NAVY, 'wood', '#0E1015', 'deep_teak'),
 # ---------------- round 2: refinements of the strongest directions
 'M2': pal('Navy & Camel', 'Refined: the camel is pulled toward brown (less peach) so it reads as a warm leather tone next to the teak, not a pale block. '
           'Navy walls, trim and door; navy inlay strips tie the wardrobe back to the walls.',
           NAVY, '#DDD3C2', NAVY, NAVY, '#9E8467', NAVY, 'wood', '#121620', 'deep_teak'),
 'M3': pal('Navy & Oat', 'Navy walls with an oatmeal wardrobe and teak strips: the classic navy + cream contrast, warmed to oat so it stays soft. '
           'The 181 cm wardrobe becomes the light surface of the room and pushes wall 4 back visually.',
           NAVY, '#E0D8CA', NAVY, NAVY, '#CBBDA4', 'wood', 'wood', '#0E1015', 'deep_teak'),
 'M4': pal('Stone & Navy Joinery', 'Refined inverse: warm stone walls (deeper than linen, so not a beige box) with navy on everything built - '
           'wardrobe, door, skirting, crown and the slat gaps. Lightest room of the set; navy is still its defining colour.',
           '#BBAD97', '#E2DACD', NAVY, NAVY, NAVY, 'wood', 'wood', NAVY, 'deep_teak'),
}
A = dict(a.split('=', 1) for a in sys.argv[sys.argv.index('--') + 1:]) if '--' in sys.argv else {}
OBJ, MAT = bpy.data.objects, bpy.data.materials


def rgb(h): return (*P.lin(h), 1.0)


def paint_mat(name, rough):
    m = MAT.get(name) or P.material(name, '#283548', rough, **{'Coat Weight': 0.12, 'Coat Roughness': 0.3})
    m.use_fake_user = True; return m


def brass():
    m = MAT.get('M_Brass_Strip')
    if not m:
        m = P.material('M_Brass_Strip', '#B8955A', 0.28, 1.0); m.use_fake_user = True
    return m


def apply(key):
    p = PALETTES[key]
    for mn, h in (('M_Wall_Paint', p['walls']), ('M_Ceiling_Paint', p['ceil'])):
        MAT[mn].node_tree.nodes['PAINT_COLOR'].outputs[0].default_value = rgb(h)
    for mn, h in (('M_Rodape', p['rod']), ('M_Door_Leaf', p['door']), ('M_Trim_White', p['door']), ('M_Backing_Black_Felt', p['felt'])):
        P.bsdf(MAT[mn]).inputs['Base Color'].default_value = rgb(h)
    for mn in ('M_Rodape', 'M_Door_Leaf', 'M_Trim_White'):
        P.bsdf(MAT[mn]).inputs['Roughness'].default_value = 0.38
    g = next(n for n in MAT['M_Boards_teak'].node_tree.nodes if n.bl_idname == 'ShaderNodeVectorMath' and n.operation == 'MULTIPLY')
    g.inputs[1].default_value = WOOD[p['wood']]
    wood = MAT['M_Boards_teak']
    body = wood if p['ward'] == 'wood' else paint_mat('M_Ward_Paint', 0.32)
    if p['ward'] != 'wood': P.bsdf(body).inputs['Base Color'].default_value = rgb(p['ward'])
    if p['strips'] == 'wood': strip = wood
    elif p['strips'] == 'brass': strip = brass()
    else:
        strip = paint_mat('M_Strip_Paint', 0.4); P.bsdf(strip).inputs['Base Color'].default_value = rgb(p['strips'])
    OBJ['WARD_Carcass'].material_slots[0].material = body
    for n in ('WARD_Door_Left_back', 'WARD_Door_Right_front'):
        OBJ[n].material_slots[0].material = body; OBJ[n].material_slots[1].material = strip
    if p['slats'] == 'wood': sl = wood
    else:
        sl = paint_mat('M_Slat_Paint', 0.42); P.bsdf(sl).inputs['Base Color'].default_value = rgb(p['slats'])
    OBJ['WALL3_Slat_Wall'].material_slots[0].material = sl
    bpy.context.scene['palette'] = f"{key} {p['title']}"


if __name__ == '__main__':
    import render_jobs as RJ
    sc = bpy.context.scene
    if 'save' in A:
        apply(A['save']); bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=A.get('path', bpy.data.filepath), compress=True); print('SAVED', A['save']); sys.exit(0)
    out = A.get('out', os.path.join(P.HERE, 'renders', 'navy')); os.makedirs(out, exist_ok=True)
    VIEWS = A.get('cams', 'CAM_L18_Corner_High_Bed,CAM_F2_Doorway_View,CAM_R1_Wide_Table_Corner,CAM_L3_Bed_Door').split(',')
    SCENS = A.get('scen', 'overcast_morning,golden_hour,night_cozy').split(',')
    for key in (A['only'].split(',') if 'only' in A else list(PALETTES)):
        apply(key)
        for scen in SCENS:
            RJ.scenario(scen); sc.cycles.samples = int(A.get('spp', 48))
            for cam in VIEWS:
                sc.camera = OBJ[cam]; sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 960, 540, 100
                sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 90
                sc.render.filepath = os.path.join(out, f'{key}__{cam[4:]}__{scen}.jpg'); bpy.ops.render.render(write_still=True)
                print('RENDERED', key, cam, scen, flush=True)
