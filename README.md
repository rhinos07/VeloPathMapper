# VeloPathMapper

VeloPathMapper is a lightweight, static map viewer for cycling stage races. It currently includes the Giro d'Italia 2026, Tour de France 2026, Lidl Deutschland Tour 2026, and Vuelta a España 2026, with GPX routes, elevation profiles, stage details, timings, and external race links.

Live site: https://rhinos07.github.io/VeloPathMapper/

## Architecture

The app has no backend or build step. `index.html` loads Leaflet from a CDN, reads the tour manifest and JSON files, and fetches GPX routes in the browser.

- `tours/manifest.json` lists the canonical tour files in display order. The order is maintained by hand and follows each race's start date; nothing sorts it at runtime.
- `tours/<id>.json` is the single source of truth for tour and stage metadata.
- `gpx/<id>/stage-<n>-route.gpx` contains route geometry and elevation data.
- `profile/<id>/stage-<n>-profile.jpg` contains generated elevation profiles.
- `generate_profiles.py` reads the same tour JSON used by the browser and regenerates profile images.
- `server.py` serves the repository locally on port 8090.

An internet connection is required for Leaflet and the OpenStreetMap/OpenTopoMap tiles.

## Quick start

Python 3 is required. Serve the project rather than opening `index.html` directly because tour data is loaded with `fetch`.

```bash
python3 server.py
```

On Windows, `python server.py` or `py server.py` may be used instead. Open http://localhost:8090 if the browser does not open automatically.

## Canonical tour-data format

Each entry in `tours/manifest.json` points to one JSON document. A tour document has this shape:

```json
{
  "id": "tour2026",
  "name": "Tour de France 2026",
  "shortName": "Tour 2026",
  "emoji": "🏆",
  "color": "#f59e0b",
  "textColor": "#1a1a2e",
  "edition": "113. Ausgabe",
  "dates": "4.–26. Juli 2026",
  "startDesc": "Grand Départ: Barcelona",
  "totalDist": "~3.333 km",
  "totalElev": "~51.200 Hm",
  "mapCenter": [46, 3],
  "mapZoom": 6,
  "gpxBase": "gpx/tour2026/",
  "profileBase": "profile/tour2026/",
  "urls": {
    "official": "https://example.test/stage/{n}/{slug}",
    "pcs": "https://example.test/stage-{n}"
  },
  "times": {
    "1": { "start": "15:30", "finish": "17:15", "itt": true, "points": [] }
  },
  "stages": [
    {
      "n": 1,
      "label": "Prolog",
      "date": "Sa 4. Juli",
      "start": "Barcelona",
      "finish": "Barcelona",
      "dist": 19,
      "elev": 50,
      "type": "itt",
      "sll": [41.385, 2.173],
      "fll": [41.385, 2.173],
      "slug": "barcelona-barcelona",
      "climbs": "Mannschaftszeitfahren",
      "urls": { "official": "https://example.test/prologue" }
    }
  ],
  "rest": [
    { "before": 10, "date": "Mo 13. Juli", "label": "Ruhetag 1" }
  ]
}
```

Stage `n` is a non-negative integer; stage `0` can represent a prologue and is retained in lookups and filenames. The optional stage `label` replaces the default `Etappe <n>` display text. Stage `type` must be one of `sprint`, `hilly`, `mountain`, or `itt`. Coordinates use `[latitude, longitude]`. URL templates support `{n}` and `{slug}` placeholders. Optional stage-level `urls` override tour-level templates by link name. JSON object keys in `times` are stage numbers expressed as strings.

For example, the Lidl Deutschland Tour uses `n: 0`, `label: "Prolog"`, and a stage-level official URL override because its prologue page is `/de/prolog-0`, while stages 1–4 use the tour template `/de/etappe-{n}`.

Profile-only waypoint annotations remain in `generate_profiles.py`; they are rendering hints rather than tour metadata.

Waypoint kilometres are taken from the organizer's roadbook and are normally scaled onto the GPX track from the start. Tour ids listed in `NEUTRALISED_START` are measured from the finish instead, because their GPX files include a neutralised approach before race kilometre 0, so only the distance to go matches the roadbook. The Lidl Deutschland Tour needs this: its GPX tracks run 3–8 km longer than the official stage distances.

## Add or update a tour

1. Create or edit `tours/<id>.json` using an existing file as a reference.
2. Add the filename to `tours/manifest.json` if it is a new tour.
3. Add all stage routes under `gpx/<id>/` using the documented filename pattern.
4. Regenerate and review the elevation profiles.
5. Serve the app locally and check the map, stage cards, profile images, and external links.

Do not duplicate tour or stage metadata in JavaScript or Python; both consumers read the JSON files directly.

## Regenerate elevation profiles

Install the generator dependencies:

```bash
pip install gpxpy matplotlib numpy
```

Then run:

```bash
python3 generate_profiles.py
```

The command reads every tour in `tours/manifest.json` and overwrites the corresponding JPG files under `profile/`. Missing or invalid GPX files are reported and skipped.


The official Deutschland Tour GPX downloads are published by A.S.O. on the organizer's route page. Some included road sections are closed or restricted to bicycle traffic outside the event; check local rules before attempting to ride a route.
