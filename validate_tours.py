#!/usr/bin/env python3
"""
VeloPathMapper – Prüfung der Tour-Daten

Prüft alle Touren aus tours/manifest.json auf Fehler, die beim Pflegen der
JSON-Dateien leicht passieren. Nur Standardbibliothek, läuft offline.

Fehler (Exit-Code 1):
  - fehlende Pflichtfelder, falsche Typen, unbekannter Etappentyp
  - doppelte Tour-Ids oder Etappennummern
  - Wochentag passt nicht zum Datum (z. B. "Sa 4. Juli" im Jahr der Tour)
  - times-Einträge ohne passende Etappe, itt-Flag passt nicht zum Etappentyp
  - Ruhetag verweist auf eine nicht vorhandene Etappe

Warnungen (Exit-Code 0, mit --strict ebenfalls 1):
  - GPX-Datei oder Profilbild fehlt
  - Start/Ziel (sll/fll) weiter als 2 km vom Anfang/Ende des GPX-Tracks
  - GPX-Länge weicht mehr als 5 % von dist ab
  - totalDist/totalElev weichen von der Summe der Etappen ab

Ausführen:
    python3 validate_tours.py            # alle Touren
    python3 validate_tours.py tour2027   # nur ausgewählte Tour-Ids
    python3 validate_tours.py --strict   # Warnungen als Fehler werten
"""

import datetime
import json
import math
import os
import re
import sys
import xml.etree.ElementTree as ET

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STAGE_TYPES = {'sprint', 'hilly', 'mountain', 'itt'}
MONTHS = {'Januar': 1, 'Februar': 2, 'März': 3, 'April': 4, 'Mai': 5,
          'Juni': 6, 'Juli': 7, 'August': 8, 'September': 9,
          'Oktober': 10, 'November': 11, 'Dezember': 12}
WEEKDAYS = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']
DATE_RE = re.compile(r'^(Mo|Di|Mi|Do|Fr|Sa|So) (\d{1,2})\. (\w+)$')
TIME_RE = re.compile(r'^~?\d{1,2}:\d{2}$')

TOUR_FIELDS = {
    'id': str, 'year': int, 'name': str, 'shortName': str, 'emoji': str,
    'color': str, 'edition': str, 'dates': str, 'totalDist': str,
    'totalElev': str, 'gpxBase': str, 'profileBase': str, 'times': dict,
    'stages': list,
}
STAGE_FIELDS = {
    'n': int, 'date': str, 'start': str, 'finish': str, 'dist': (int, float),
    'elev': int, 'type': str, 'sll': list, 'fll': list, 'climbs': str,
}

MAX_ENDPOINT_KM = 2.0
MAX_LENGTH_DIFF = 0.05
MAX_TOTAL_DIFF = 0.01


class Report:
    def __init__(self):
        self.errors = 0
        self.warnings = 0

    def error(self, where, msg):
        self.errors += 1
        print(f'  FEHLER   {where}: {msg}')

    def warn(self, where, msg):
        self.warnings += 1
        print(f'  WARNUNG  {where}: {msg}')


def haversine(a, b):
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    h = (math.sin((lat2 - lat1) / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 6371.0 * 2 * math.asin(min(1.0, math.sqrt(h)))


def gpx_points(path):
    """Liest Track- bzw. Routenpunkte, unabhängig vom GPX-Namespace."""
    root = ET.parse(path).getroot()
    pts = []
    for tag in ('trkpt', 'rtept'):
        for el in root.iter():
            if el.tag.rsplit('}', 1)[-1] == tag:
                pts.append((float(el.get('lat')), float(el.get('lon'))))
        if pts:
            break
    return pts


def track_length(pts):
    return sum(haversine(pts[i - 1], pts[i]) for i in range(1, len(pts)))


def parse_number(text):
    """'~3.333 km' → 3333.0, '~741,5 km' → 741.5"""
    digits = re.sub(r'[^\d,]', '', text).replace(',', '.')
    return float(digits) if digits else None


def check_date(rep, where, text, year):
    m = DATE_RE.match(text)
    if not m:
        rep.error(where, f'Datum "{text}" hat nicht das Format "Sa 4. Juli"')
        return None
    wd, day, month = m.group(1), int(m.group(2)), m.group(3)
    if month not in MONTHS:
        rep.error(where, f'unbekannter Monat "{month}"')
        return None
    try:
        date = datetime.date(year, MONTHS[month], day)
    except ValueError:
        rep.error(where, f'ungültiges Datum "{text}" im Jahr {year}')
        return None
    if WEEKDAYS[date.weekday()] != wd:
        rep.error(where, f'"{text}": der {day}. {month} {year} ist ein '
                         f'{WEEKDAYS[date.weekday()]}, nicht {wd}')
    return date


def check_fields(rep, where, obj, fields):
    ok = True
    for key, typ in fields.items():
        if key not in obj:
            rep.error(where, f'Pflichtfeld "{key}" fehlt')
            ok = False
        elif isinstance(obj[key], bool) or not isinstance(obj[key], typ):
            rep.error(where, f'"{key}" hat den falschen Typ')
            ok = False
    return ok


def check_coord(rep, where, key, value):
    if (not isinstance(value, list) or len(value) != 2
            or not all(isinstance(v, (int, float)) for v in value)
            or not -90 <= value[0] <= 90 or not -180 <= value[1] <= 180):
        rep.error(where, f'"{key}" muss [lat, lon] sein')
        return False
    return True


def check_tour(rep, tour, filename):
    where = filename
    if not check_fields(rep, where, tour, TOUR_FIELDS):
        return
    tid, year = tour['id'], tour['year']
    if filename != f'{tid}.json':
        rep.warn(where, f'Dateiname passt nicht zur id "{tid}"')
    if str(year) not in tour['dates']:
        rep.warn(where, f'"dates" ({tour["dates"]}) enthält das Jahr {year} nicht')
    for base in ('gpxBase', 'profileBase'):
        if not tour[base].endswith('/'):
            rep.error(where, f'"{base}" muss mit "/" enden')

    numbers = set()
    dates = []
    for stage in tour['stages']:
        sw = f'{tid} Etappe {stage.get("n", "?")}'
        if not check_fields(rep, sw, stage, STAGE_FIELDS):
            continue
        n = stage['n']
        if n in numbers:
            rep.error(sw, 'Etappennummer doppelt')
        numbers.add(n)
        if n < 0:
            rep.error(sw, 'Etappennummer ist negativ')
        if stage['type'] not in STAGE_TYPES:
            rep.error(sw, f'unbekannter Typ "{stage["type"]}"')
        if stage['dist'] <= 0:
            rep.error(sw, '"dist" muss größer als 0 sein')
        coords_ok = (check_coord(rep, sw, 'sll', stage['sll'])
                     & check_coord(rep, sw, 'fll', stage['fll']))
        date = check_date(rep, sw, stage['date'], year)
        if date:
            dates.append((date, n))

        gpx = os.path.join(BASE_DIR, tour['gpxBase'], f'stage-{n}-route.gpx')
        prof = os.path.join(BASE_DIR, tour['profileBase'], f'stage-{n}-profile.jpg')
        if not os.path.exists(prof):
            rep.warn(sw, 'Profilbild fehlt')
        if not os.path.exists(gpx):
            rep.warn(sw, 'GPX-Datei fehlt')
            continue
        try:
            pts = gpx_points(gpx)
        except ET.ParseError as e:
            rep.error(sw, f'GPX nicht lesbar: {e}')
            continue
        if len(pts) < 2:
            rep.error(sw, 'GPX enthält keine Track- oder Routenpunkte')
            continue
        if coords_ok:
            for key, label, pt in (('sll', 'Start', pts[0]), ('fll', 'Ziel', pts[-1])):
                d = haversine(stage[key], pt)
                if d > MAX_ENDPOINT_KM:
                    rep.warn(sw, f'{label} "{key}" liegt {d:.1f} km neben dem '
                                 f'GPX-{label} [{pt[0]:.5f}, {pt[1]:.5f}]')
        length = track_length(pts)
        if abs(length - stage['dist']) / stage['dist'] > MAX_LENGTH_DIFF:
            rep.warn(sw, f'GPX-Länge {length:.1f} km, dist {stage["dist"]} km')

    dates.sort()
    for (d1, n1), (d2, n2) in zip(dates, dates[1:]):
        if d1 == d2:
            rep.error(tid, f'Etappen {n1} und {n2} am selben Tag')

    for key, t in tour['times'].items():
        tw = f'{tid} times[{key}]'
        if not key.isdigit() or int(key) not in numbers:
            rep.error(tw, 'keine passende Etappe')
            continue
        for f in ('start', 'finish'):
            if not TIME_RE.match(str(t.get(f, ''))):
                rep.error(tw, f'"{f}" fehlt oder ist nicht HH:MM')
        stage = next(s for s in tour['stages'] if s.get('n') == int(key))
        if bool(t.get('itt')) != (stage.get('type') == 'itt'):
            rep.warn(tw, f'itt={t.get("itt")} passt nicht zum Typ "{stage.get("type")}"')
        for p in t.get('points', []):
            if not TIME_RE.match(str(p.get('time', ''))) or not p.get('name'):
                rep.error(tw, f'Passage {p} braucht "name" und "time" (HH:MM)')

    for r in tour.get('rest', []):
        rw = f'{tid} Ruhetag {r.get("label", "?")}'
        if r.get('before') not in numbers or r.get('before') - 1 not in numbers:
            rep.error(rw, f'"before": {r.get("before")} liegt nicht zwischen zwei Etappen')
        if 'date' in r:
            check_date(rep, rw, r['date'], year)

    sum_dist = sum(s.get('dist', 0) for s in tour['stages'])
    sum_elev = sum(s.get('elev', 0) for s in tour['stages'])
    for key, total, unit in (('totalDist', sum_dist, 'km'), ('totalElev', sum_elev, 'Hm')):
        stated = parse_number(tour[key])
        if stated and abs(stated - total) / stated > MAX_TOTAL_DIFF:
            rep.warn(tid, f'{key} = {tour[key]}, Summe der Etappen = {total:g} {unit}')


def main(argv):
    strict = '--strict' in argv
    only = {a for a in argv if not a.startswith('--')}
    rep = Report()

    with open(os.path.join(BASE_DIR, 'tours', 'manifest.json'), encoding='utf-8-sig') as f:
        files = json.load(f)
    seen = set()
    for filename in files:
        path = os.path.join(BASE_DIR, 'tours', filename)
        try:
            with open(path, encoding='utf-8') as f:
                tour = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f'\n{filename}')
            rep.error(filename, f'nicht lesbar: {e}')
            continue
        if only and tour.get('id') not in only:
            continue
        print(f'\n{filename}')
        if tour.get('id') in seen:
            rep.error(filename, f'Tour-Id "{tour.get("id")}" doppelt')
        seen.add(tour.get('id'))
        before = rep.errors + rep.warnings
        check_tour(rep, tour, filename)
        if rep.errors + rep.warnings == before:
            print('  OK')

    print(f'\n{rep.errors} Fehler, {rep.warnings} Warnungen')
    return 1 if rep.errors or (strict and rep.warnings) else 0


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main(sys.argv[1:]))
