"""Drawing set definition for the fabrication schematics (model: Bedroom_v19_Wall_Shelves.blend). Units: cm in the model, mm on the drawings.
A view = how to render (camera / scale / objects); dims and notes are 3-D points (cm) projected by render_views.py."""
MODEL = 'experiments/teak_navy/Bedroom_v19_Wall_Shelves.blend'
PX_PER_MM = 12                               # ~305 dpi on paper

# ------------------------------------------------------------------ object categories (colours of the CAD look)
PARTS = {   # object -> colour key per original material (None = whole object one colour)
    'WALL3_Slat_Wall': None, 'DESK_Wood': None, 'DESK_Legs': None, 'TSHELF_Boards': None, 'WALL1_Shelf_Top': None, 'WALL1_Shelf_Bottom': None,
    'WIN_Wall_Panel': None, 'BED_Headboard_Wall1': None, 'ARCH_Cove_Ledge': None, 'DRAWER_Unit': None, 'WARD_Carcass': None,
    'WARD_Door_Left_back': None, 'WARD_Door_Right_front': None, 'DESK_Cable_Grommet': None,
}
MATCOL = {'M_Boards_teak': 'teak', 'M_Backing_Black_Felt': 'felt', 'M_Shelf_Wood': 'dark', 'M_Steel_Black': 'steel', 'M_Plastic_Black': 'steel',
          'M_Rubber_Black': 'rubber', 'M_Strip_navy': 'navy', 'M_Rodape': 'paint', 'M_Crown_Plaster': 'paint', 'M_Grommet_Brown': 'steel'}
COLORS = {'teak': '#C8935E', 'felt': '#2C2C2E', 'dark': '#8A5E3C', 'steel': '#45484D', 'rubber': '#2A2A2A', 'navy': '#34445C', 'paint': '#5A6A86',
          'ghost': '#DADAD6', 'wall': '#ECECE9', 'floor': '#F4F4F2', 'glass': '#C9D6DA'}
GHOST = {   # context objects (light grey)
    'ARCH_Floor': 'floor', 'ARCH_Wall_1_Door': 'wall', 'ARCH_Wall_2_Window': 'wall', 'ARCH_Wall_3': 'wall', 'ARCH_Wall_4': 'wall', 'ARCH_Baseboards': 'ghost',
    'WIN_Trim': 'ghost', 'WIN_Frame': 'ghost', 'WIN_Sash_Louvre': 'ghost', 'WIN_Sash_Glazed': 'ghost', 'WIN_Latches': 'ghost',
    'DOOR_Trim': 'ghost', 'DOOR_Jamb': 'ghost', 'DOOR_Leaf': 'ghost', 'DOOR_Handle_Lever': 'ghost',
    'BED_Base': 'ghost', 'BED_Mattress': 'ghost', 'WALL1_Frame': 'ghost', 'WALL1_Picture': 'ghost', 'AQ_Glass': 'glass', 'AQ_Frame': 'ghost',
    'SHELF_Boards': 'ghost', 'SHELF_Steel_Frames': 'ghost', 'WARD_Handle_Left_back': 'ghost', 'WARD_Handle_Right_front': 'ghost', 'WARD_Bottom_Track': 'ghost',
}

def D(a, b, off, text, side=1):       # dimension: two points, offset vector (cm), label
    return dict(kind='dim', a=a, b=b, off=off, text=text)

def N(p, text, dx, dy):               # leader note: point (cm), text, text offset from the point on paper (mm)
    return dict(kind='note', p=p, text=text, dx=dx, dy=dy)

def BOX(lo, hi, label=''):            # dashed (hidden) outline of a box's top face, for plan views
    return dict(kind='box', lo=lo, hi=hi, label=label)

def BAL(p, n, dx, dy):                # balloon
    return dict(kind='bal', p=p, n=n, dx=dx, dy=dy)

PLAN_DOWN = dict(fwd=(0, 0, -1), up=(0, -1, 0))   # window wall at the top, slat wall on the left
LOOK_WIN = dict(fwd=(0, -1, 0), up=(0, 0, 1))     # facing the window wall (slat wall on the left)
LOOK_W3 = dict(fwd=(1, 0, 0), up=(0, 0, 1))       # facing the slat wall (window on the right)
LOOK_W1 = dict(fwd=(0, 1, 0), up=(0, 0, 1))       # facing the door wall (slat wall on the right)
LOOK_W4 = dict(fwd=(-1, 0, 0), up=(0, 0, 1))      # facing the wardrobe (window on the left)

NEW_ALL = ['WALL3_Slat_Wall', 'DESK_Wood', 'DESK_Legs', 'DESK_Cable_Grommet', 'TSHELF_Boards', 'WALL1_Shelf_Top', 'WALL1_Shelf_Bottom', 'WIN_Wall_Panel',
           'BED_Headboard_Wall1', 'ARCH_Cove_Ledge', 'DRAWER_Unit', 'WARD_Carcass', 'WARD_Door_Left_back', 'WARD_Door_Right_front']

VIEWS = {
    # ---------------- sheet 9 presentation render (all new parts in place, walls removed, soft shadows)
    'hero': dict(cam='persp', loc=(-230, 580, 620), target=(200, 130, 115), lens=35, box=(390, 222), shadow=True, objs=[o for o in NEW_ALL if not o.startswith('WARD_')] + ['AQ_Glass', 'AQ_Frame', 'WALL1_Frame', 'WALL1_Picture']),
    # ---------------- sheet 1 overview
    'ov1': dict(cam='persp', loc=(-150, 430, 400), target=(175, 95, 85), lens=30, box=(190, 120),
                objs=['WALL3_Slat_Wall', 'DESK_Wood', 'DESK_Legs', 'TSHELF_Boards', 'WIN_Wall_Panel', 'DRAWER_Unit', 'DESK_Cable_Grommet',
                      'ARCH_Floor', 'ARCH_Wall_2_Window', 'ARCH_Wall_3', 'ARCH_Baseboards', 'WIN_Trim', 'WIN_Frame', 'WIN_Sash_Louvre', 'WIN_Sash_Glazed', 'WIN_Latches',
                      'SHELF_Boards', 'SHELF_Steel_Frames', 'AQ_Glass', 'AQ_Frame', 'BED_Base', 'BED_Mattress'],
                ann=[BAL((296, 120, 120), 1, -18, -10), BAL((180, 25, 75), 2, 0, 14), BAL((92, 45, 35), 3, 16, 8), BAL((251, 68, 40), 4, -14, 14),
                     BAL((271, 10, 175), 5, 14, -14), BAL((140, 1, 50), 6, 12, -16)]),
    'ov2': dict(cam='persp', loc=(470, -150, 400), target=(130, 190, 85), lens=30, box=(190, 120),
                objs=['DESK_Wood', 'DESK_Legs', 'DRAWER_Unit', 'WALL1_Shelf_Top', 'WALL1_Shelf_Bottom', 'BED_Headboard_Wall1',
                      'WARD_Carcass', 'WARD_Door_Left_back', 'WARD_Door_Right_front', 'WARD_Handle_Left_back', 'WARD_Handle_Right_front', 'WARD_Bottom_Track',
                      'ARCH_Floor', 'ARCH_Wall_1_Door', 'ARCH_Wall_4', 'ARCH_Baseboards', 'DOOR_Trim', 'DOOR_Jamb', 'DOOR_Leaf', 'DOOR_Handle_Lever',
                      'WALL1_Frame', 'BED_Base', 'BED_Mattress'],
                ann=[BAL((200, 289, 70), 7, 0, -16), BAL((243, 282, 187), 8, 14, -12), BAL((156, 282, 119), 8, -14, -10),
                     BAL((63, 140, 160), 10, -16, 0), BAL((200, 120, 75), 2, 10, 14)]),
    # ---------------- sheet 2 slat wall
    's_elev': dict(cam='ortho', **LOOK_W3, center=(200, 145, 126.5), box=(165, 145), scale=20, objs=['WALL3_Slat_Wall'],
                   ann=[D((296, 290, 0.5), (296, 0, 0.5), (0, 0, -14), '2900'), D((296, 0, 0.5), (296, 0, 252.5), (0, -14, 0), '2520'),
                        D((296, 0, 0), (296, 0, 252.5), (0, -26, 0), '2525 (floor to top)'),
                        N((296, 145, 0.5), '5 mm shadow gap at the floor', 30, 10), N((296, 200, 252.5), '72 slats 27 × 12 × 2520, top meets the crown molding', 18, -8)]),
    's_plan': dict(cam='ortho', **dict(fwd=(0, 0, -1), up=(1, 0, 0)), center=(297.0, 283.5, 300), box=(110, 70), scale=2,
                   objs=['WALL3_Slat_Wall', 'ARCH_Wall_3'],
                   ann=[D((296, 290, 252.5), (296, 287.3, 252.5), (-2.4, 0, 0), '27'), D((296, 287.3, 252.5), (296, 285.95, 252.5), (-2.4, 0, 0), '13.5'),
                        D((296, 290, 252.5), (296, 285.95, 252.5), (-4.4, 0, 0), '40.5 pitch'), D((296, 290, 252.5), (297.2, 290, 252.5), (0, 3, 0), '12'),
                        D((297.2, 274.0, 252.5), (298.1, 274.0, 252.5), (0, -1.6, 0), '9'), D((298.1, 279.2, 252.5), (300, 279.2, 252.5), (0, -1.6, 0), '19'),
                        N((297.65, 281.0, 252.5), 'black acoustic felt 9 mm', 14, 22), N((299.0, 284.6, 252.5), '19 mm battens / air gap', 22, -8),
                        N((302, 288, 252.5), 'WALL 3', 0, 0)]),
    's_iso': dict(cam='persp', loc=(190, 95, 115), target=(296, 12, 25), lens=35, box=(110, 70), objs=['WALL3_Slat_Wall', 'ARCH_Floor', 'ARCH_Wall_3', 'ARCH_Wall_2_Window', 'WIN_Wall_Panel']),
    # ---------------- sheet 3 table
    't_plan': dict(cam='ortho', **PLAN_DOWN, center=(192, 97, 300), box=(130, 125), scale=20,
                   objs=['DESK_Wood', 'WALL3_Slat_Wall', 'WIN_Wall_Panel', 'ARCH_Wall_2_Window', 'ARCH_Wall_3'],
                   ann=[D((88, 0, 75), (296, 0, 75), (0, -14, 0), '2080'), D((296, 0, 75), (296, 194.2, 75), (12, 0, 0), '1942'),
                        D((88, 0, 75), (88, 49, 75), (-8, 0, 0), '490'), D((247, 194.2, 75), (296, 194.2, 75), (0, 9, 0), '490'),
                        D((287, 0, 75), (287, 13, 75), (-12, 0, 0), '130'), D((296, 13, 75), (287, 13, 75), (0, 30, 0), '90'),
                        N((287, 13, 75), 'Ø60 cable grommet', 22, 26), N((170, 25, 75), 'T1  2080 × 490 × 30', 0, 0),
                        N((271, 120, 75), 'T2  1452 × 490 × 30', 0, 0), N((247, 49, 75), 'butt joint T1 / T2', 30, 22),
                        BOX((90.5, 3.5, 75), (93.5, 6.5, 75)), BOX((90.5, 43.5, 75), (93.5, 46.5, 75)), BOX((249.5, 43.5, 75), (252.5, 46.5, 75)),
                        BOX((249.5, 186.2, 75), (252.5, 189.2, 75)), BOX((289.5, 186.2, 75), (292.5, 189.2, 75)),
                        BOX((250.5, 48, 75), (295.5, 88, 75), 'drawer unit below')]),
    't_front': dict(cam='ortho', **LOOK_WIN, center=(192, 100, 40), box=(130, 60), scale=20, objs=['DESK_Wood', 'DESK_Legs', 'DRAWER_Unit'],
                    ann=[D((88, 0, 0), (88, 0, 75), (-12, 0, 0), '750'), D((88, 0, 72), (88, 0, 75), (-5, 0, 0), '30'),
                         D((88, 0, 0), (296, 0, 0), (0, 0, -9), '2080'), N((92, 5, 40), 'steel 30 × 30 legs, 716 + 4 mm glide', -36, -10)]),
    't_side': dict(cam='ortho', **LOOK_W3, center=(200, 97, 40), box=(125, 60), scale=20, objs=['DESK_Wood', 'DESK_Legs', 'DRAWER_Unit'],
                   ann=[D((296, 194.2, 75), (296, 0, 75), (0, 0, 9), '1942'), D((296, 194.2, 0), (296, 194.2, 72), (0, 12, 0), '720')]),
    't_iso': dict(cam='persp', loc=(-60, 330, 260), target=(195, 70, 40), lens=35, box=(120, 85), objs=['DESK_Wood', 'DESK_Legs', 'DESK_Cable_Grommet']),
    # ---------------- sheet 4 window wall
    'w_elev': dict(cam='ortho', **LOOK_WIN, center=(150, 100, 132), box=(165, 150), scale=20,
                   objs=['WIN_Wall_Panel', 'TSHELF_Boards', 'ARCH_Wall_2_Window', 'WIN_Trim', 'WIN_Frame', 'WIN_Sash_Louvre', 'WIN_Sash_Glazed', 'WIN_Latches',
                         'WARD_Carcass', 'WALL3_Slat_Wall', 'AQ_Glass', 'AQ_Frame', 'DESK_Wood'],
                   ann=[D((63, 1, 0), (296, 1, 0), (0, 0, -12), '2330'), D((63, 1, 0), (63, 1, 97.5), (-10, 0, 0), '975'),
                        D((294, 0, 0), (294, 0, 110), (16, 0, 0), '1100'), D((294, 0, 110), (294, 0, 136), (16, 0, 0), '260'),
                        D((294, 0, 136), (294, 0, 162), (16, 0, 0), '260'), D((294, 0, 162), (294, 0, 188), (16, 0, 0), '260'),
                        D((294, 0, 188), (294, 0, 214), (16, 0, 0), '260'), D((248, 0, 214), (294, 0, 214), (0, 0, 9), '460'),
                        N((150, 1, 50), 'panel: 10 mm teak plywood, top edge butts the window frame', 0, 26),
                        N((262, 0, 188), '5 floating shelves 460 × 230 × 25', 34, -40), N((271, 10, 90), 'aquarium 450 × 210 × 300 (ref.)', 40, 12)]),
    'w_side': dict(cam='ortho', **LOOK_W3, center=(200, 18, 145), box=(45, 85), scale=20,
                   objs=['TSHELF_Boards', 'AQ_Glass', 'AQ_Frame', 'DESK_Wood', 'WIN_Wall_Panel', 'ARCH_Wall_2_Window'],
                   ann=[D((271, 23, 214), (271, 0, 214), (0, 0, 8), '230'), N((271, 11, 162), 'concealed steel rods, Ø10 × 180', -18, -12)]),
    'w_iso': dict(cam='persp', loc=(170, 120, 190), target=(270, 12, 135), lens=30, box=(100, 85),
                  objs=['TSHELF_Boards', 'WIN_Wall_Panel', 'DESK_Wood', 'AQ_Glass', 'AQ_Frame', 'WALL3_Slat_Wall', 'ARCH_Wall_2_Window', 'WIN_Trim', 'WIN_Frame']),
    # ---------------- sheet 5 wall 1
    'd_elev': dict(cam='ortho', **LOOK_W1, center=(150, 200, 132), box=(165, 150), scale=20,
                   objs=['BED_Headboard_Wall1', 'WALL1_Shelf_Top', 'WALL1_Shelf_Bottom', 'ARCH_Wall_1_Door', 'DOOR_Trim', 'DOOR_Jamb', 'DOOR_Leaf', 'DOOR_Handle_Lever',
                         'WALL1_Frame', 'WALL3_Slat_Wall'],
                   ann=[D((100.5, 288.2, 0), (296, 288.2, 0), (0, 0, -12), '1955'), D((100.5, 288.2, 0), (100.5, 288.2, 87.5), (-12, 0, 0), '875'),
                        D((218.75, 290, 187.4), (266.75, 290, 187.4), (0, 0, 8), '480'), D((266.75, 290, 0), (266.75, 290, 187.4), (16, 0, 0), '1874'),
                        D((133.5, 290, 117), (179.5, 290, 117), (0, 0, -7), '460'), D((133.5, 290, 0), (133.5, 290, 120), (-14, 0, 0), '1200'),
                        D((162.5, 290, 176.4), (237.5, 290, 176.4), (0, 0, 22), '750 frame (ref.)'), D((237.5, 290, 87.5), (237.5, 290, 125), (8, 0, 0), '375'),
                        N((200, 288, 40), 'bed panel: 18 mm teak plywood', 0, 0), N((150, 289, 245), 'bed omitted for clarity  ·  frame 750 × 514 is existing', 0, 0)]),
    'd_iso': dict(cam='persp', loc=(150, 150, 165), target=(205, 290, 125), lens=24, box=(105, 80),
                  objs=['BED_Headboard_Wall1', 'WALL1_Shelf_Top', 'WALL1_Shelf_Bottom', 'WALL1_Frame', 'WALL1_Picture', 'ARCH_Wall_1_Door', 'WALL3_Slat_Wall', 'BED_Base', 'BED_Mattress']),
    # ---------------- sheet 6 drawer unit
    'k_front': dict(cam='ortho', **LOOK_W3, center=(240, 68, 36), box=(80, 100), scale=10, objs=['DRAWER_Unit'],
                    ann=[D((250.5, 88, 71.75), (250.5, 48, 71.75), (0, 0, 6), '400'), D((250.5, 48, 0), (250.5, 48, 71.75), (0, -8, 0), '717.5'),
                         D((250.5, 88, 0), (250.5, 88, 6.5), (0, 8, 0), '65'), D((250.5, 88, 8.6), (250.5, 88, 37.62), (0, 8, 0), '290'),
                         D((250.5, 88, 39.42), (250.5, 88, 53.64), (0, 8, 0), '142'), D((250.5, 88, 55.44), (250.5, 88, 69.65), (0, 8, 0), '142'),
                         N((250.5, 68, 71.75), 'top 2.5 mm under the table (720)', 0, -18)]),
    'k_side': dict(cam='ortho', **LOOK_W1, center=(273, 30, 36), box=(80, 100), scale=10, objs=['DRAWER_Unit'],
                   ann=[D((250.5, 48, 71.75), (295.5, 48, 71.75), (0, 0, 6), '450'), D((295.5, 48, 6.5), (295.5, 48, 71.75), (8, 0, 0), '652.5'),
                        N((256, 48, 3), 'Ø48 twin-wheel casters (4)', 10, 20)]),
    'k_iso': dict(cam='persp', loc=(170, -15, 130), target=(273, 68, 34), lens=40, box=(110, 100), objs=['DRAWER_Unit']),
    # ---------------- sheet 7 cove ledge + wardrobe
    'c_plan': dict(cam='ortho', **PLAN_DOWN, center=(150, 145, 400), box=(130, 125), scale=25,
                   objs=['ARCH_Cove_Ledge', 'ARCH_Wall_1_Door', 'ARCH_Wall_2_Window', 'ARCH_Wall_3', 'ARCH_Wall_4', 'WARD_Carcass'],
                   ann=[D((63.5, 0, 248.5), (296, 0, 248.5), (0, -12, 0), '2325'), D((296, 5, 248.5), (296, 290, 248.5), (12, 0, 0), '2850'),
                        D((5, 290, 248.5), (291, 290, 248.5), (0, 12, 0), '2860'), D((0, 181.5, 248.5), (0, 290, 248.5), (-12, 0, 0), '1085'),
                        N((31, 90, 248.5), 'wardrobe (to ceiling)', 0, 0)]),
    'r_elev': dict(cam='ortho', **LOOK_W4, center=(20, 90.5, 135), box=(95, 140), scale=25,
                   objs=['WARD_Carcass', 'WARD_Door_Left_back', 'WARD_Door_Right_front', 'WARD_Handle_Left_back', 'WARD_Handle_Right_front', 'WARD_Bottom_Track'],
                   ann=[D((63, 0, 270), (63, 181, 270), (0, 0, 8), '1810'), D((63, 181, 0), (63, 181, 270), (0, 12, 0), '2700'),
                        D((63, 0, 0), (63, 0, 11.4), (0, -8, 0), '114'), D((63, 0, 11.4), (63, 0, 68.85), (0, -8, 0), '574'),
                        D((63, 0, 71.15), (63, 0, 129.35), (0, -8, 0), '582'), D((63, 0, 131.65), (63, 0, 194.35), (0, -8, 0), '627'),
                        D((63, 0, 196.65), (63, 0, 261.6), (0, -8, 0), '650'), D((63, 1.8, 11.4), (63, 92.5, 11.4), (0, 0, -8), '907 door')]),
}

SHEETS = [
    dict(n=1, title='GENERAL ARRANGEMENT', views=['ov1', 'ov2'], extra='overview'),
    dict(n=2, title='SLAT WALL (WALL 3)', views=['s_elev', 's_plan', 's_iso']),
    dict(n=3, title='L-SHAPED DESK', views=['t_plan', 't_front', 't_side', 't_iso']),
    dict(n=4, title='WINDOW WALL: PANEL + FLOATING SHELVES', views=['w_elev', 'w_side', 'w_iso']),
    dict(n=5, title='DOOR WALL: BED PANEL + SHELVES', views=['d_elev', 'd_iso'], extra='bracket'),
    dict(n=6, title='ROLLING DRAWER UNIT', views=['k_front', 'k_side', 'k_iso']),
    dict(n=7, title='COVE LEDGE + WARDROBE CLADDING', views=['c_plan', 'r_elev'], extra='cove'),
    dict(n=8, title='CUT LIST + SHEET NESTING', views=[], extra='cutlist'),
    dict(n=9, title='PRESENTATION RENDER: ALL NEW PARTS', views=['hero']),
]

VIEW_TITLES = {
    'ov1': ('A', 'Isometric from the door corner', 'NTS'), 'ov2': ('B', 'Isometric from the window corner', 'NTS'),
    's_elev': ('A', 'Elevation of wall 3', '1:20'), 's_plan': ('B', 'Plan detail at the door-wall corner', '1:2'), 's_iso': ('C', 'Detail isometric', 'NTS'),
    't_plan': ('A', 'Plan', '1:20'), 't_front': ('B', 'Front elevation (facing the window)', '1:20'), 't_side': ('C', 'Side elevation (facing wall 3)', '1:20'),
    't_iso': ('D', 'Isometric', 'NTS'),
    'w_elev': ('A', 'Elevation of the window wall', '1:20'), 'w_side': ('B', 'Section', '1:20'), 'w_iso': ('C', 'Isometric', 'NTS'),
    'd_elev': ('A', 'Elevation of the door wall', '1:20'), 'd_iso': ('B', 'Isometric', 'NTS'),
    'k_front': ('A', 'Front', '1:10'), 'k_side': ('B', 'Side', '1:10'), 'k_iso': ('C', 'Isometric', 'NTS'),
    'hero': ('', 'All new parts in their installed positions (walls and wardrobe hidden)', 'NTS'),
    'c_plan': ('A', 'Cove ledge plan (from above)', '1:25'), 'r_elev': ('B', 'Wardrobe front elevation', '1:25'),
}
