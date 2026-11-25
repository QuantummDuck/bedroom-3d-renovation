"""Sun path for the bedroom window, computed offline (NOAA solar-position equations, ~0.5 deg accuracy).
  python3 sun_study.py  ->  sun_positions.json + Sun_Path_Diagram.png

Room frame (cm): window wall = wall 2 at y = 0, outside is -y. The window faces compass bearing 260 deg (measured with a phone compass),
so world direction angle phi (CCW from +x) = 170 - bearing.  Sun vector (toward the sun) = (cos e cos phi, cos e sin phi, sin e)."""
import json, math, os, subprocess
from datetime import date, datetime, timedelta

# Placeholder site: Sao Paulo city centre (BRT, no daylight saving). Set BEDROOM_LAT / BEDROOM_LON / BEDROOM_TZ to compute your own.
LAT = float(os.environ.get('BEDROOM_LAT', -23.5505)); LON = float(os.environ.get('BEDROOM_LON', -46.6333)); TZ = float(os.environ.get('BEDROOM_TZ', -3.0))
WINDOW_BEARING = 260.0
NEIGHBOUR = (LAT - 0.000548, LON - 0.000428)          # next tower: ~75 m away, bearing ~216 deg
HERE = os.path.dirname(os.path.abspath(__file__))


def sun(d: datetime):
    """Return (elevation, compass azimuth) in degrees for local time d."""
    doy = d.timetuple().tm_yday; hour = d.hour + d.minute / 60 + d.second / 3600
    g = 2 * math.pi / 365 * (doy - 1 + (hour - 12) / 24)
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g) - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    decl = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g) + 0.000907 * math.sin(2 * g)
            - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    tst = hour * 60 + eqt + 4 * LON - 60 * TZ
    ha = math.radians(tst / 4 - 180); lat = math.radians(LAT)
    cz = math.sin(lat) * math.sin(decl) + math.cos(lat) * math.cos(decl) * math.cos(ha)
    e = 90 - math.degrees(math.acos(max(-1, min(1, cz))))
    if -1 < e < 15:   # Bennett refraction
        e += 1.02 / math.tan(math.radians(e + 10.3 / (e + 5.11))) / 60
    az = math.degrees(math.atan2(math.sin(ha), math.cos(ha) * math.sin(lat) - math.tan(decl) * math.cos(lat)))
    return e, (az + 180) % 360


def world_vec(e, bearing):
    phi = math.radians(170 - bearing); e = math.radians(e)
    return (math.cos(e) * math.cos(phi), math.cos(e) * math.sin(phi), math.sin(e))


def into_window(e, bearing):
    """Sun shines on the window glass (in front of the wall) and above the horizon."""
    return e > 0 and world_vec(e, bearing)[1] < 0


def bearing_to(p):
    dy = (p[0] - LAT) * 111320; dx = (p[1] - LON) * 111320 * math.cos(math.radians(LAT))
    return (math.degrees(math.atan2(dx, dy)) + 360) % 360, math.hypot(dx, dy)


DAYS = {'2026-10-15': 'tomorrow (Oct 15)', '2026-12-21': 'summer solstice (Dec 21)', '2027-03-20': 'equinox (Mar 20)',
        '2027-06-21': 'winter solstice (Jun 21)'}


def main():
    out = {'lat': LAT, 'lon': LON, 'window_bearing': WINDOW_BEARING, 'days': {}}
    nb, nd = bearing_to(NEIGHBOUR); out['neighbour'] = {'bearing': nb, 'distance_m': nd}
    for ds, label in DAYS.items():
        y, m, dd = map(int, ds.split('-')); rows = []; t = datetime(y, m, dd, 6, 0)
        first = sunset = None
        while t.hour < 19 or (t.hour == 19 and t.minute == 0):
            e, b = sun(t)
            if e > -0.833 and t.hour >= 12: sunset = t
            if into_window(e, b) and first is None: first = t
            rows.append({'time': t.strftime('%H:%M'), 'elev': round(e, 2), 'bearing': round(b, 2), 'in_window': into_window(e, b),
                         'vec': [round(v, 5) for v in world_vec(e, b)]})
            t += timedelta(minutes=5)
        out['days'][ds] = {'label': label, 'sun_in_window_from': first.strftime('%H:%M') if first else None,
                           'sunset': sunset.strftime('%H:%M') if sunset else None, 'samples': rows}
        print(f"{label:28s} sun on the window from {out['days'][ds]['sun_in_window_from']} until sunset {out['days'][ds]['sunset']}")
        for r in rows:
            if r['time'] in ('12:00', '13:00', '14:00', '15:00', '16:00', '16:30', '17:00', '17:30', '18:00'):
                print(f"   {r['time']}  elev {r['elev']:5.1f}  bearing {r['bearing']:5.1f}  {'IN' if r['in_window'] else '--'}")
    json.dump(out, open(os.path.join(HERE, 'sun_positions.json'), 'w'), indent=1)
    diagram(out)


def diagram(out):
    """Top-down sun-path diagram (SVG -> PNG with ImageMagick). Up = north."""
    W, C, R = 1400, 700, 520
    def pt(e, b):           # elevation -> radius (horizon at R), bearing clockwise from north
        r = R * (90 - max(e, 0)) / 90; a = math.radians(b)
        return C + r * math.sin(a), C - r * math.cos(a)
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{W}" viewBox="0 0 {W} {W}">',
         f'<rect width="{W}" height="{W}" fill="#F4F4F1"/>']
    for e in (0, 30, 60):
        s.append(f'<circle cx="{C}" cy="{C}" r="{R * (90 - e) / 90}" fill="none" stroke="#C9C9C4" stroke-width="2"/>')
        s.append(f'<text x="{C + 6}" y="{C - R * (90 - e) / 90 - 6}" font-size="22" fill="#8A8A85" font-family="Arial">{e}°</text>')
    for b, lab in ((0, 'N'), (90, 'E'), (180, 'S'), (270, 'W')):
        x, y = pt(-5, b); s.append(f'<text x="{x - 10 + 25 * math.sin(math.radians(b))}" y="{y + 10 - 25 * math.cos(math.radians(b))}" font-size="34" font-weight="bold" fill="#1D1D1F" font-family="Arial">{lab}</text>')
    # window: what the glass faces (+-90 deg) shaded, normal arrow
    a0, a1 = WINDOW_BEARING - 90, WINDOW_BEARING + 90
    x0, y0 = pt(0, a0); x1, y1 = pt(0, a1)
    s.append(f'<path d="M{C},{C} L{x0},{y0} A{R},{R} 0 0,1 {x1},{y1} Z" fill="#F2C14E" fill-opacity="0.18" stroke="none"/>')
    xn, yn = pt(0, WINDOW_BEARING); s.append(f'<line x1="{C}" y1="{C}" x2="{xn}" y2="{yn}" stroke="#C47F00" stroke-width="5" stroke-dasharray="14,10"/>')
    s.append(f'<text x="{xn - 150}" y="{yn - 20}" font-size="26" fill="#9A6400" font-family="Arial">window faces 260°</text>')
    nb = out['neighbour']['bearing']; xb, yb = pt(0, nb)
    s.append(f'<line x1="{C}" y1="{C}" x2="{xb}" y2="{yb}" stroke="#6E6E73" stroke-width="4"/>')
    s.append(f'<text x="{xb - 40}" y="{yb + 40}" font-size="24" fill="#4A4A4F" font-family="Arial">next tower, ~{out["neighbour"]["distance_m"]:.0f} m</text>')
    cols = {'2026-10-15': '#D9480F', '2026-12-21': '#C2255C', '2027-03-20': '#2B8A3E', '2027-06-21': '#1C7ED6'}
    ly = 60
    for ds, d in out['days'].items():
        pts = [pt(r['elev'], r['bearing']) for r in d['samples'] if r['elev'] > 0]
        s.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="none" stroke="{cols[ds]}" stroke-width="5"/>')
        for r in d['samples']:
            if r['elev'] > 0 and r['time'].endswith(':00') and int(r['time'][:2]) >= 12:
                x, y = pt(r['elev'], r['bearing']); fill = cols[ds] if r['in_window'] else '#FFFFFF'
                s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="{fill}" stroke="{cols[ds]}" stroke-width="3"/>')
                s.append(f'<text x="{x + 12:.1f}" y="{y - 10:.1f}" font-size="19" fill="{cols[ds]}" font-family="Arial">{r["time"][:2]}h</text>')
        s.append(f'<rect x="40" y="{ly - 22}" width="34" height="10" fill="{cols[ds]}"/>')
        s.append(f'<text x="86" y="{ly - 10}" font-size="26" fill="#1D1D1F" font-family="Arial">{d["label"]}: sun on the window {d["sun_in_window_from"]}–{d["sunset"]}</text>')
        ly += 40
    s.append(f'<text x="40" y="{W - 40}" font-size="22" fill="#6E6E73" font-family="Arial">Filled dots = sun shining on your window (in front of the wall, above the horizon). Rings = elevation.</text>')
    s.append('</svg>')
    svg = os.path.join(HERE, 'Sun_Path_Diagram.svg'); open(svg, 'w').write('\n'.join(s))
    subprocess.run(['magick', '-font', '/System/Library/Fonts/Supplemental/Arial.ttf', '-density', '96', svg, os.path.join(HERE, 'Sun_Path_Diagram.png')], check=True)


if __name__ == '__main__':
    assert sun(datetime(2026, 12, 21, 12, 0))[0] > 88      # the sun passes almost overhead at noon on the solstice (tropic)
    main()
