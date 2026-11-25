"""Colour-palette study on Bedroom_Teak_Navy_v10_slats.blend.
  Blender -b ../teak_navy/Bedroom_Teak_Navy_v10_slats.blend --python palettes.py -- out=renders/palettes [only=P1,P2] [spp=48] [save=P2]
Each palette sets every recolourable surface together:
  walls (walls 1, 2, 4)  ceiling  rodape (skirting + crown + cove ledge)  door leaf + trim  wardrobe body/doors  wardrobe strips
  slat-wall felt backing  wood stain (slats, table, wardrobe if wood, bed panel, shelves, drawer unit)
Fixed, not recoloured: floor tiles, window frame, your chair (blue), bedspread, rug, books, lighting."""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import photoreal_common as P

WOOD = {'teak': (0.745, 0.641, 0.505),      # the scanned teak graded to #9A6A3E (current)
        'walnut': (0.47, 0.40, 0.34),        # same scan, smoked/walnut stain (~#6E4C34)
        'oak': (1.05, 0.95, 0.80),           # lighter natural oak tone (~#B08A5E)
        'deep_teak': (0.545, 0.527, 0.475)}  # oiled, deeper and less orange teak (~#86603C), closer to the reference slat walls

# name: (title, rationale, walls, ceiling, rodape, door, wardrobe ('wood' or hex), strips ('wood' or hex), felt, wood)
PALETTES = {
 'P1': ('Clay Cocoon', 'Tonal drench: one warm clay-taupe on walls, trim, door and wardrobe (analogous to the teak, warm undertone shared with the floor). '
        'No edges, so the small room reads as one soft volume; the slat wall is the only feature.',
        '#A48B76', '#DDD2C3', '#A48B76', '#A48B76', '#A48B76', 'wood', '#2A1F18', 'teak'),
 'P2': ('Ink & Teak', 'Complementary: inky blue-black with a slight green undertone against orange-brown teak. Walls, trim, door and wardrobe drenched so '
        'the corners disappear and the room feels deeper; warm wood and light do the cozy work. Harmonises with your blue chair.',
        '#283240', '#D8D1C4', '#283240', '#283240', '#283240', 'wood', '#0F0F10', 'teak'),
 'P3': ('Olive Library', 'Earthy split: warm olive-moss (yellow undertone) with teak, like an old library. Green + wood reads natural and calm; '
        'warm parchment ceiling keeps the height.',
        '#4D4C39', '#DDD5C1', '#4D4C39', '#4D4C39', '#4D4C39', 'wood', '#1C1C15', 'teak'),
 'P4': ('Japandi Light', 'High-LRV warm greige everywhere (LRV ~60) for the most space and daylight; charcoal felt and wardrobe strips give a quiet '
        'graphic line that ties to the black steel legs and shelf frames. Coziness comes from the wood and the lamps.',
        '#D5CBBB', '#ECE6DC', '#D5CBBB', '#D5CBBB', '#D5CBBB', '#2E2C29', '#2E2C29', 'teak'),
 'P5': ('Terracotta Dusk', 'Analogous warm: muted terracotta walls with a teak wardrobe. Mediterranean and enveloping; your blue chair becomes the '
        'complementary accent.',
        '#9C5F4A', '#E4D6C6', '#9C5F4A', '#9C5F4A', 'wood', '#9C5F4A', '#2A1A14', 'teak'),
 'P6': ('Bone & Smoked Walnut', 'Inverse of Ink & Teak: light warm bone walls (drenched incl. ceiling) with darker smoked-walnut wood. Value contrast '
        'comes from the wood, so the room stays airy but grounded.',
        '#E2D8C8', '#E2D8C8', '#E2D8C8', '#E2D8C8', '#E2D8C8', 'wood', '#0F0F10', 'walnut'),
 'P7': ('Deep Teal', 'Complementary but softer than navy: deep blue-green with teak. Teal sits between your blue chair and green plants; '
        'cocooning without the cold of pure blue.',
        '#2F4846', '#DAD4C8', '#2F4846', '#2F4846', '#2F4846', 'wood', '#121514', 'teak'),
 # ---- round 2: refined survivors + two new directions (deep teak wood everywhere)
 'R1': ('Ink & Deep Teak', 'Complementary contrast, refined: inky blue-black (green-grey undertone) drenched on walls, trim, door and wardrobe, so the '
        'corners and the big wardrobe recede. The deeper teak keeps the warmth but no longer shouts orange; ceiling tinted warm so it is not a white lid.',
        '#283240', '#D3CABB', '#283240', '#283240', '#283240', 'wood', '#0F0F10', 'deep_teak'),
 'R2': ('Olive Library', 'Warm olive (yellow undertone) drenched; olive and teak sit next to each other on the warm side of the wheel, so the room '
        'reads calm and natural; mustard in your bedspread and the blue chair stay the only accents.',
        '#4B4A37', '#D6CDB8', '#4B4A37', '#4B4A37', '#4B4A37', 'wood', '#1A1A13', 'deep_teak'),
 'R3': ('Clay Cocoon', 'Tonal warm mid-tone: clay-taupe everywhere, a tinted ceiling one step lighter, dark-umber slat gaps. The lightest of the '
        'cozy options; the deeper teak now separates clearly from the walls.',
        '#A48B76', '#D8CBB9', '#A48B76', '#A48B76', '#A48B76', 'wood', '#2A1F18', 'deep_teak'),
 'R4': ('Smoked Teal', 'A muted grey-teal between ink and olive: cool enough to complement the wood, grey enough not to read as green or blue. '
        'Bridges your blue chair and the warm wood.',
        '#36433F', '#D4CCBD', '#36433F', '#36433F', '#36433F', 'wood', '#141716', 'deep_teak'),
 'R5': ('Mole & Mustard', 'Warm brown-grey (mole) drenched, with mustard wardrobe strips that pick up the mustard in your bedspread: one accent '
        'colour repeated twice, the classic way to make an accent look intended.',
        '#4A433C', '#D6CDBF', '#4A433C', '#4A433C', '#4A433C', '#B8892F', '#141210', 'deep_teak'),
}
A = dict(a.split('=', 1) for a in sys.argv[sys.argv.index('--') + 1:]) if '--' in sys.argv else {}
OBJ, MAT = bpy.data.objects, bpy.data.materials


def rgb(h): return (*P.lin(h), 1.0)


def apply(key):
    title, why, walls, ceil, rod, door, ward, strips, felt, wood = PALETTES[key]
    for mn, h in (('M_Wall_Paint', walls), ('M_Ceiling_Paint', ceil)):
        MAT[mn].node_tree.nodes['PAINT_COLOR'].outputs[0].default_value = rgb(h)
    for mn, h in (('M_Rodape', rod), ('M_Door_Leaf', door), ('M_Trim_White', door), ('M_Backing_Black_Felt', felt)):
        P.bsdf(MAT[mn]).inputs['Base Color'].default_value = rgb(h)
    for mn in ('M_Rodape', 'M_Door_Leaf', 'M_Trim_White'):          # painted joinery: satin
        P.bsdf(MAT[mn]).inputs['Roughness'].default_value = 0.38
    g = next(n for n in MAT['M_Boards_teak'].node_tree.nodes if n.bl_idname == 'ShaderNodeVectorMath' and n.operation == 'MULTIPLY')
    g.inputs[1].default_value = WOOD[wood]
    body = MAT['M_Boards_teak'] if ward == 'wood' else MAT['M_Ward_Paint']
    if ward != 'wood': P.bsdf(MAT['M_Ward_Paint']).inputs['Base Color'].default_value = rgb(ward)
    strip = MAT['M_Boards_teak'] if strips == 'wood' else MAT['M_Strip_navy']
    if strips != 'wood': P.bsdf(MAT['M_Strip_navy']).inputs['Base Color'].default_value = rgb(strips)
    OBJ['WARD_Carcass'].material_slots[0].material = body
    for n in ('WARD_Door_Left_back', 'WARD_Door_Right_front'):
        OBJ[n].material_slots[0].material = body; OBJ[n].material_slots[1].material = strip
    bpy.context.scene['palette'] = f'{key} {title}'


if __name__ == '__main__':
    import render_jobs as RJ
    sc = bpy.context.scene; out = A.get('out', os.path.join(P.HERE, 'renders', 'palettes')); os.makedirs(out, exist_ok=True)
    if 'save' in A:
        apply(A['save']); bpy.context.preferences.filepaths.save_version = 0
        path = A.get('path', bpy.data.filepath); bpy.ops.wm.save_as_mainfile(filepath=path, compress=True); print('SAVED', A['save'], path); sys.exit(0)
    VIEWS = A.get('cams', 'CAM_L18_Corner_High_Bed,CAM_R1_Wide_Table_Corner,CAM_L2_Table_Shelves,CAM_L3_Bed_Door').split(',')
    SCENS = A.get('scen', 'overcast_morning,night_cozy').split(',')
    keys = A['only'].split(',') if 'only' in A else list(PALETTES)
    for key in keys:
        apply(key)
        for scen in SCENS:
            RJ.scenario(scen); sc.cycles.samples = int(A.get('spp', 48))
            for cam in VIEWS:
                sc.camera = OBJ[cam]; sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 960, 540, 100
                sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 90
                sc.render.filepath = os.path.join(out, f'{key}__{cam[4:]}__{scen}.jpg'); bpy.ops.render.render(write_still=True)
                print('RENDERED', key, cam, scen, flush=True)
