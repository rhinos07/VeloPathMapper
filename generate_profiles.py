#!/usr/bin/env python3
"""
VeloPathMapper – Höhenprofilgenerator
Erzeugt Profil-Bilder aus den GPX-Dateien.

Beschriftungs-Strategie je Etappe (erste zutreffende Regel gewinnt):
  1. times[n].points vorhanden     → Ortsnamen aus Durchfahrtszeiten, linear
                                      zwischen Start- und Zielzeit positioniert
  2. Wegpunkte + NEUTRALISED_START → Roadbook-km, vom Ziel aus gemessen
  3. Wegpunkte (*_WAYPOINTS)       → Roadbook-km, auf die GPX-Länge skaliert
  4. Berg-/Hügeletappe             → automatische Gipfelerkennung (Prominenz
                                      > 100 m), beschriftet mit der Höhe in m
  5. sonst (Flach/Zeitfahren)      → nur Start und Ziel

Es werden keine externen Dienste abgefragt; das Skript arbeitet offline.
Voraussetzung: Python 3.9+, gpxpy, matplotlib, numpy.

Ausführen (aus beliebigem Verzeichnis, Pfade sind relativ zum Skript):
    python3 generate_profiles.py
"""

import json, os, sys, math
import numpy as np

try:
    import gpxpy
except ImportError:
    sys.exit("Fehler: gpxpy fehlt.  pip install gpxpy")
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
except ImportError:
    sys.exit("Fehler: matplotlib fehlt.  pip install matplotlib numpy")

# ──────────────────────────────────────────────────────────────
# TOUR-DATEN
# ──────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# WEGPUNKTE  (aus den offiziellen Streckenprofilen extrahiert)
# km-Werte = offizielle Rennkilometer laut Profil-Grafik
# ──────────────────────────────────────────────────────────────

GIRO_WAYPOINTS = {
    2: [  # Burgas → Veliko Tarnovo
        {'name': 'Sliven',               'km': 100.4},
        {'name': 'Byala Pass',           'km': 116.3},
        {'name': 'Vratnik Pass',         'km': 134.1},
        {'name': 'Lyaskovets Mon. Pass', 'km': 205.5},
    ],
    9: [  # Cervia → Corno alle Scale
        {'name': 'Marzabotto',           'km': 125.2},
        {'name': 'Querciola',            'km': 161.3},
        {'name': 'Red Bull KM',          'km': 172.6},
    ],
    18: [  # Fai della Paganella → Pieve di Soligo
        {'name': 'Fastro',               'km':  87.7},
        {'name': 'Guia',                 'km': 135.4},
        {'name': 'Muro di Cà del Poggio','km': 161.7},
    ],
}

TOUR_WAYPOINTS = {
    2: [  # Tarragona → Barcelona
        {'name': "Côte de Beguès",              'km':  74.5},
        {'name': "Côte de Santa Creu d'Olorda", 'km': 133.5},
        {'name': "Côte de Montjuïc",            'km': 154.0},
    ],
    3: [  # Granollers → Les Angles
        {'name': 'Côte de Sant Feliu',  'km':   7.0},
        {'name': 'Ripoll',              'km':  80.5},
        {'name': 'Col de Toses',        'km': 127.5},
        {'name': 'Col du Calvaire',     'km': 172.0},
    ],
    4: [  # Carcassonne → Foix
        {'name': 'Col de Bedos',        'km':  48.0},
        {'name': 'Col de Paradis',      'km':  64.5},
        {'name': 'Col de Coudons',      'km': 104.5},
        {'name': 'Col de Montségur',    'km': 146.5},
    ],
    9: [  # Malemort → Ussel
        {'name': 'Côte de Lagleygeolle','km':  29.0},
        {'name': 'Côte de Miel',        'km':  48.5},
        {'name': 'Suc au May',          'km': 105.0},
        {'name': 'Côte de la Croix du Pey','km':129.5},
        {'name': 'Mont Bessou',         'km': 161.0},
    ],
    10: [  # Aurillac → Le Lioran
        {'name': 'Côte de Pailherols',  'km':  68.0},
        {'name': 'Col de la Griffoul',  'km':  97.5},
        {'name': 'Col de Prat de Bouc', 'km': 104.0},
        {'name': 'Puy Mary',            'km': 127.5},
        {'name': 'Col du Pertus',       'km': 147.0},
    ],
    13: [  # Dole → Belfort
        {'name': 'Servance',            'km': 148.0},
        {'name': 'Col des Croix',       'km': 156.0},
        {'name': "Ballon d'Alsace",     'km': 174.5},
    ],
    14: [  # Mulhouse → Le Markstein
        {'name': 'Grand Ballon',        'km':  23.0},
        {'name': 'Col du Page',         'km':  61.0},
        {"name": "Ballon d'Alsace",     'km':  85.5},
        {'name': 'Col du Hundsruck',    'km': 120.5},
        {'name': 'Col du Haag',         'km': 142.5},
    ],
    15: [  # Champagnole → Plateau de Solaison
        {'name': 'Col de la Savine',    'km':  22.0},
        {'name': 'Côte des Doppes',     'km':  37.0},
        {'name': 'Côte de la Mulaz',    'km':  80.0},
        {'name': 'Le Salève',           'km': 131.5},
        {'name': 'Côte de la Moussière','km': 136.0},
    ],
    18: [  # Voiron → Orcières-Merlette
        {'name': "Côte d'Engins",       'km':  36.0},
        {'name': 'Côte de Monteynard',  'km':  92.0},
        {'name': 'Côte des Terrases',   'km':  98.5},
        {'name': 'St-Léger-les-Mélèzes','km': 166.5},
    ],
    19: [  # Gap → Alpe d'Huez
        {'name': 'Col Bayard',          'km':   5.5},
        {'name': 'Col du Noyer',        'km':  25.5},
        {'name': 'Côte de Corps',       'km':  56.5},
        {"name": "Col d'Ornon",         'km': 100.0},
    ],
    20: [  # Le Bourg-d'Oisans → Alpe d'Huez
        {'name': 'Col de la Croix de Fer','km': 34.0},
        {'name': 'Col du Télégraphe',   'km':  88.0},
        {'name': 'Col du Galibier',     'km': 111.0},
        {'name': 'Col de Sarenne',      'km': 157.0},
    ],
}

DEUTSCHLAND_WAYPOINTS = {
    1: [  # Bad Orb → Schwäbisch Hall
        {'name': 'Reicholzheim',        'km':  91.2},
        {'name': 'Hermersberg',         'km': 161.0},
    ],
    2: [  # Schwäbisch Hall → Offenbach an der Queich
        {'name': 'Juxkopf',             'km':  38.9},
    ],
    3: [  # Herxheim bei Landau/Pfalz → Bad Dürkheim
        {'name': 'Lolosruhe',           'km':  37.9},
        {'name': 'Kalmit (1.)',         'km':  56.4},
        {'name': 'Kalmit (2.)',         'km':  70.7},
        {'name': 'Rotsteig',            'km': 136.6},
        {'name': 'Annaberg',            'km': 154.4},
    ],
    4: [  # Heilbronn → Heilbronn
        {'name': 'Schloss Stocksberg',  'km':  15.8},
        {'name': 'Jägerhaus (1.)',      'km': 101.8},
        {'name': 'Jägerhaus (2.)',      'km': 123.2},
        {'name': 'Jägerhaus (3.)',      'km': 144.5},
    ],
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILE_WAYPOINTS = {
    'giro2026': GIRO_WAYPOINTS,
    'tour2026': TOUR_WAYPOINTS,
    'deutschland2026': DEUTSCHLAND_WAYPOINTS,
}

# Touren, deren GPX-Dateien eine neutralisierte Anfahrt vor dem Rennkilometer 0
# enthalten. Dort werden Wegpunkt-Kilometer vom Ziel aus gemessen, weil nur der
# Abstand zum Ziel in GPX und Roadbook übereinstimmt.
NEUTRALISED_START = {'deutschland2026'}


def load_tours():
    tours = []
    manifest_path = os.path.join(BASE_DIR, 'tours', 'manifest.json')
    with open(manifest_path, 'r', encoding='utf-8-sig') as source:
        filenames = json.load(source)
    for filename in filenames:
        path = os.path.join(BASE_DIR, 'tours', filename)
        with open(path, 'r', encoding='utf-8') as source:
            tour = json.load(source)
        tour['waypoints'] = PROFILE_WAYPOINTS.get(tour['id'], {})
        tour['neutralisedStart'] = tour['id'] in NEUTRALISED_START
        tours.append(tour)
    return tours

# ──────────────────────────────────────────────────────────────
# HILFSFUNKTIONEN
# ──────────────────────────────────────────────────────────────

TYPE_COLOR = {'sprint':'#22c55e','hilly':'#f97316','mountain':'#ef4444','itt':'#3b82f6'}
TYPE_LABEL = {'sprint':'Flachetappe','hilly':'Hügeliger','mountain':'Bergetappe','itt':'Zeitfahren'}


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = (math.sin(dLat/2)**2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dLon/2)**2)
    return R * 2 * math.asin(min(1.0, math.sqrt(a)))


def moving_avg(arr, w):
    if w < 2:
        return arr.copy()
    padded = np.pad(arr, w // 2, mode='edge')
    return np.convolve(padded, np.ones(w) / w, mode='valid')[:len(arr)]


def parse_time(s):
    s = s.strip().lstrip('~')
    h, m = s.split(':')
    return int(h) * 60 + int(m)


def time_to_km(pt_time, start_time, finish_time, total_km):
    t = parse_time(pt_time)
    s = parse_time(start_time)
    f = parse_time(finish_time)
    if f <= s:
        f += 1440
    ratio = max(0.04, min(0.96, (t - s) / (f - s)))
    return ratio * total_km


def find_peaks(dists, elevs, max_peaks=5):
    """Findet markante Hochpunkte per Prominenz-Analyse."""
    n   = len(elevs)
    hw  = max(25, n // 25)
    results = []
    for i in range(hw, n - hw):
        if elevs[i] < elevs[max(0, i-hw):min(n, i+hw+1)].max():
            continue
        left_min  = float(np.min(elevs[max(0, i - hw * 4):i]))
        right_min = float(np.min(elevs[i + 1:min(n, i + hw * 4)]))
        prom = elevs[i] - max(left_min, right_min)
        if prom > 100:
            results.append({'km': float(dists[i]), 'elev': float(elevs[i]),
                            'idx': i, 'prom': prom})

    total = float(dists[-1])
    filtered = []
    for p in sorted(results, key=lambda x: -x['prom']):
        if not any(abs(p['km'] - q['km']) < total * 0.08 for q in filtered):
            filtered.append(p)
        if len(filtered) >= max_peaks:
            break
    return filtered


def load_gpx(path):
    with open(path, 'r', encoding='utf-8') as f:
        gpx = gpxpy.parse(f)
    pts = []
    for track in gpx.tracks:
        for seg in track.segments:
            for pt in seg.points:
                if pt.elevation is not None:
                    pts.append((pt.latitude, pt.longitude, float(pt.elevation)))
    if not pts:
        for route in gpx.routes:
            for pt in route.points:
                if pt.elevation is not None:
                    pts.append((pt.latitude, pt.longitude, float(pt.elevation)))
    return pts

# ──────────────────────────────────────────────────────────────
# PROFIL ZEICHNEN
# ──────────────────────────────────────────────────────────────

def generate_profile(gpx_path, out_path, stage, times, waypoints=None,
                     waypoints_from_end=False):
    pts = load_gpx(gpx_path)
    if len(pts) < 10:
        print('⚠️  zu wenig Höhendaten')
        return False

    # Distanz- und Koordinaten-Arrays
    dists = [0.0]
    for i in range(1, len(pts)):
        dists.append(dists[-1] + haversine(
            pts[i-1][0], pts[i-1][1], pts[i][0], pts[i][1]))
    dists     = np.array(dists)
    elevs_raw = np.array([p[2] for p in pts])
    lats      = np.array([p[0] for p in pts])
    lons      = np.array([p[1] for p in pts])

    # Ausdünnen bei sehr dichtem GPX
    if len(dists) > 2500:
        idx       = np.round(np.linspace(0, len(dists) - 1, 2500)).astype(int)
        dists     = dists[idx]
        elevs_raw = elevs_raw[idx]
        lats      = lats[idx]
        lons      = lons[idx]

    total_km = float(dists[-1])
    win      = max(7, len(elevs_raw) // 60)
    elevs    = moving_avg(elevs_raw, win)
    color    = TYPE_COLOR.get(stage['type'], '#888')

    # ── Figure ──────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(13, 3.5), dpi=115)
    fig.patch.set_facecolor('#f8f9fa')
    ax.set_facecolor('#eef0f4')

    ax.fill_between(dists, elevs, alpha=0.28, color=color, zorder=2)
    ax.plot(dists, elevs, color=color, linewidth=2.2, zorder=3,
            solid_capstyle='round')

    ax.yaxis.grid(True, color='white', linewidth=1.0, alpha=0.75, zorder=1)
    ax.xaxis.grid(True, color='white', linewidth=0.5, alpha=0.5,  zorder=1)

    e_min   = max(0.0, float(elevs.min()) - 60)
    e_max   = float(elevs.max()) + 280
    e_range = e_max - e_min
    ax.set_xlim(0, total_km)
    ax.set_ylim(e_min, e_max)
    ax.tick_params(labelsize=8, colors='#666')
    ax.xaxis.set_major_locator(ticker.MultipleLocator(20 if total_km > 80 else 10))
    ax.set_xlabel('km', fontsize=8, color='#666', labelpad=1)
    ax.set_ylabel('m',  fontsize=8, color='#666', labelpad=1)
    for sp in ax.spines.values():
        sp.set_visible(False)

    # ── Beschriftungs-Helfer ─────────────────────────────────
    used_km: list[float] = []

    def occupied(km):
        return any(abs(km - k) < total_km * 0.07 for k in used_km)

    def annotate(km, text, red=False, forced=False):
        if not forced and occupied(km):
            return
        i   = int(np.argmin(np.abs(dists - km)))
        el  = float(elevs[i])
        fc  = '#991b1b' if red else '#1a1a2e'
        ax.annotate(
            text,
            xy=(km, el),
            xytext=(km, el + e_range * 0.22),
            fontsize=7.5, ha='center', va='bottom',
            color=fc, fontweight='bold', zorder=6,
            arrowprops=dict(arrowstyle='->', color=fc, lw=0.85,
                            shrinkA=2, shrinkB=2),
        )
        used_km.append(km)

    # ── Start / Ziel ─────────────────────────────────────────
    ax.annotate(
        stage['start'],
        xy=(0, float(elevs[0])),
        xytext=(total_km * 0.01, float(elevs[0]) + e_range * 0.22),
        fontsize=8.5, ha='left', va='bottom', color='#1a1a2e',
        fontweight='bold', zorder=6,
        arrowprops=dict(arrowstyle='->', color='#333', lw=1.0,
                        shrinkA=2, shrinkB=2),
    )
    used_km.append(0.0)

    ax.annotate(
        stage['finish'],
        xy=(total_km, float(elevs[-1])),
        xytext=(total_km * 0.99, float(elevs[-1]) + e_range * 0.22),
        fontsize=8.5, ha='right', va='bottom', color='#1a1a2e',
        fontweight='bold', zorder=6,
        arrowprops=dict(arrowstyle='->', color='#333', lw=1.0,
                        shrinkA=2, shrinkB=2),
    )
    used_km.append(total_km)

    # ── Zwischenpunkte ───────────────────────────────────────
    t_data = times.get(str(stage['n']), {})
    points = t_data.get('points', [])
    wpts   = waypoints.get(stage['n'], []) if waypoints else []

    if points:
        # Zeitbasierte Positionierung (Giro-Etappen mit Passagen-Daten)
        for pt in points:
            km = time_to_km(pt['time'], t_data['start'], t_data['finish'], total_km)
            annotate(km, pt['name'])

    elif wpts and waypoints_from_end:
        # Km-basierte Positionierung, vom Ziel aus gemessen: das GPX enthält
        # eine neutralisierte Anfahrt, daher stimmt nur der Restabstand.
        for pt in wpts:
            annotate(total_km - (stage['dist'] - pt['km']), pt['name'])

    elif wpts:
        # Km-basierte Positionierung aus offiziellen Profil-Grafiken
        scale = total_km / stage['dist'] if stage['dist'] > 0 else 1.0
        for pt in wpts:
            annotate(pt['km'] * scale, pt['name'])

    elif stage['type'] in ('mountain', 'hilly'):
        # Fallback: automatische Gipfelerkennung mit Höhenangabe
        for p in find_peaks(dists, elevs):
            annotate(p['km'], f"{int(round(p['elev']))} m", red=True)

    # ── Info-Box ─────────────────────────────────────────────
    stage_label = stage.get('label', f"Et. {stage['n']}")
    info = (f"{stage_label}  ·  {total_km:.0f} km  ·  "
            f"{stage['elev']:,} Hm  ·  {TYPE_LABEL.get(stage['type'], '')}")
    ax.text(0.995, 0.975, info,
            transform=ax.transAxes, fontsize=7.5, color='#555',
            ha='right', va='top',
            bbox=dict(boxstyle='round,pad=0.35', facecolor='white',
                      alpha=0.80, edgecolor='none'),
            zorder=7)

    plt.tight_layout(pad=0.5)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path, dpi=115, bbox_inches='tight',
                facecolor=fig.get_facecolor(),
                pil_kwargs={'quality': 92, 'optimize': True})
    plt.close(fig)
    return True

# ──────────────────────────────────────────────────────────────
# HAUPTPROGRAMM
# ──────────────────────────────────────────────────────────────

def main():
    total = ok = skipped = 0

    for tour in load_tours():
        tid      = tour['id']
        wpts     = tour.get('waypoints', {})
        from_end = tour.get('neutralisedStart', False)
        print(f"\n{'─'*54}")
        print(f"  {tid}")
        print(f"{'─'*54}")
        for stage in tour['stages']:
            n        = stage['n']
            gpx_path = os.path.join(BASE_DIR, 'gpx',     tid, f'stage-{n}-route.gpx')
            out_path = os.path.join(BASE_DIR, 'profile', tid, f'stage-{n}-profile.jpg')
            total   += 1
            stage_label = stage.get('label', f"Et. {n}")
            label    = (f"{stage_label:7s}  {stage['start'][:14]:14s}"
                        f" → {stage['finish'][:14]:14s}")
            if not os.path.exists(gpx_path):
                print(f"  {label}  ⚠️  GPX fehlt")
                skipped += 1
                continue
            print(f"  {label}  ", end='', flush=True)
            try:
                if generate_profile(gpx_path, out_path, stage, tour['times'], wpts,
                                    waypoints_from_end=from_end):
                    print('✅')
                    ok += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f'❌  {e}')
                skipped += 1

    print(f"\n{'═'*54}")
    print(f"  {ok}/{total} Profile erstellt, {skipped} übersprungen")
    print(f"{'═'*54}\n")


if __name__ == '__main__':
    main()
