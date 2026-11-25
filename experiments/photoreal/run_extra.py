"""Second overnight queue (starts when run_final.py ends): full lighting set for the twin's main view, three human-eye views
(lying in bed, at the piano, desk chair turned), and extra daylight / detail shots. Resumable like run_final.py.
  python3 run_extra.py [--dry]"""
import sys
import run_final as R

V5, CUR, HD = R.V5, R.CUR, R.HD
R.JOBS = [
    (CUR, 'current', 'late_sun', ['CAM_PR_01_Door'], HD, 1024),
    (CUR, 'current', 'golden_hour', ['CAM_PR_01_Door'], HD, 1024),
    (CUR, 'current', 'night_cozy', ['CAM_PR_01_Door', 'CAM_PR_04_Desk_Seated'], HD, 1024),
    (CUR, 'current', 'night_work', ['CAM_PR_01_Door'], HD, 1024),
    (CUR, 'current', 'blue_hour', ['CAM_PR_01_Door'], HD, 1024),
    (V5, 'v5', 'night_cozy', ['CAM_PR_08_Lying_In_Bed', 'CAM_PR_09_Piano_Stool', 'CAM_PR_10_Chair_Turned'], HD, 1024),
    (CUR, 'current', 'night_everyday', ['CAM_PR_08_Lying_In_Bed', 'CAM_PR_09_Piano_Stool', 'CAM_PR_10_Chair_Turned'], HD, 1024),
    (V5, 'v5', 'overcast_morning', ['CAM_PR_03_Bed_Corner', 'CAM_PR_10_Chair_Turned'], HD, 1024),
    (V5, 'v5', 'afternoon_sun', ['CAM_PR_03_Bed_Corner'], HD, 1024),
    (V5, 'v5', 'night_everyday', ['CAM_PR_03_Bed_Corner'], HD, 1024),
    (V5, 'v5', 'golden_hour', ['CAM_PR_D6_Wardrobe_Glow', 'CAM_PR_D5_Stool_Rug'], HD, 1024),
    (CUR, 'current', 'overcast_morning', ['CAM_PR_08_Lying_In_Bed', 'CAM_PR_10_Chair_Turned'], HD, 1024),
]
if __name__ == '__main__':
    R.main('--dry' in sys.argv)
