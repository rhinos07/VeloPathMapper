# VeloPathMapper

VeloPathMapper is a lightweight, static map viewer for cycling stage races. It currently includes the Giro d'Italia 2026, Tour de France 2026, Lidl Deutschland Tour 2026, Vuelta a España 2026, Giro d'Italia 2027 and Tour de France 2027, with GPX routes, elevation profiles, stage details, timings, and external race links.

Live site: https://rhinos07.github.io/VeloPathMapper/

## Features

The user interface is in German.

- **Sidebar – Jahr:** year buttons at the top of the sidebar. Only the tours of the selected year are listed. On start-up the current calendar year is chosen; if there is no data for it, the latest earlier year (or else the earliest year). Switching the year deselects all tours and selects the first tour of the new year. The buttons are hidden while all tours belong to one year.
- **Sidebar – Touren:** click a tour to show or hide it. Several tours of the same year can be shown at once; the map zooms to all selected tours.
- **Sidebar – Etappentypen:** toggle stage types (Flach, Hügelig, Berg, Zeitfahren) on the map. The filter applies to the map only, not to the stage overview.
- **Kartenansicht (map):** each stage is first drawn as a straight line between start and finish and replaced by the GPX track once it has loaded. Time trials are dashed. A layer switch offers OpenTopoMap (default) and OpenStreetMap. Clicking a stage line, marker or number badge opens an info panel and zooms to the stage.
- **Etappenübersicht (stage overview):** one card per stage with date, distance, climbing, start/finish times, short description, elevation profile and external links. Rest days are shown as separate cards. With more than one tour selected, the cards are grouped per tour.
- **Stage details:** clicking a card opens a dialog with the full-size profile (zoomable) and, where available, estimated passage times.
- `Esc` closes the dialog and the info panel.

## Project layout

```
index.html              complete web app (HTML, CSS, JavaScript)
favicon.svg
server.py               local development server (port 8090)
generate_profiles.py    elevation profile generator
validate_tours.py       consistency check for the tour data
tours/manifest.json     list of tour files in display order
tours/<id>.json         tour and stage metadata
gpx/<id>/               stage-<n>-route.gpx
profile/<id>/           stage-<n>-profile.jpg (generated)
```

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
  "year": 2026,
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

### Field reference

Tour fields:

| Field | Required | Used by | Meaning |
|---|---|---|---|
| `id` | yes | app, generator | Tour id; must match the folder names under `gpx/` and `profile/`. |
| `year` | yes | app | Season (number). Groups the tours in the year selector and is used by the validator to check weekdays. A tour without `year` is not shown. |
| `name`, `shortName` | yes | app | Full name (sidebar, overview) and short name (tooltips, legend, badges). |
| `emoji` | yes | app | Icon shown in front of the name. |
| `color` | yes | app | Route and accent colour (CSS colour). |
| `textColor` | no | app | Text colour on `color` backgrounds; default `#fff`. |
| `edition`, `dates`, `totalDist`, `totalElev` | yes | app | Display strings; not calculated from the stages. |
| `gpxBase`, `profileBase` | yes | app | Path prefixes with a trailing `/`. The generator ignores them and always uses `gpx/<id>/` and `profile/<id>/`. |
| `urls` | no | app | Link templates by name. The app renders `official`, `pcs` (ProCyclingStats) and `cs` (CyclingStage); other names are ignored. |
| `times` | yes* | app, generator | Times per stage, see below. *The generator fails for a tour without `times`; use `{}` if there are none. |
| `stages` | yes | app, generator | Stages in display order. |
| `rest` | no | app | Rest days, see below. |
| `startDesc`, `mapCenter`, `mapZoom` | no | – | Currently not used by the app; the map view is fitted to the selected stages. |

Stage fields:

| Field | Required | Meaning |
|---|---|---|
| `n` | yes | Stage number; determines GPX and profile filenames. |
| `label` | no | Replaces `Etappe <n>`; its first letter is used as the map badge. |
| `date` | yes | Display string, e.g. `Sa 4. Juli`. |
| `start`, `finish` | yes | Place names. |
| `dist` | yes | Official distance in km (number). Also used to scale profile waypoints. |
| `elev` | yes | Climbing in metres (number). |
| `type` | yes | `sprint`, `hilly`, `mountain` or `itt`. |
| `sll`, `fll` | yes | Start and finish `[lat, lon]`. They place the start/finish markers and the number badge, and they define the map extent, so they should match the GPX endpoints. If both are identical (circuit), the finish marker is shifted slightly so both stay visible. |
| `slug` | no | Value for the `{slug}` URL placeholder. |
| `climbs` | yes | Short description shown as "Charakter". |
| `urls` | no | Per-stage URL overrides by link name. |

Times (`times["<n>"]`):

| Field | Meaning |
|---|---|
| `start` | Start time `HH:MM`; for time trials the first rider's start. |
| `finish` | Expected finish `HH:MM`; for time trials the last rider's finish. Displayed with a leading `~`. |
| `itt` | `true` switches the labels to "Erster Start" / "Letzter Finish". |
| `points` | Optional list of `{ "name": "...", "time": "HH:MM" }` passages, shown in the stage dialog and used to label the profile. |

Rest days (`rest[]`): `before` is the number of the stage that follows the rest day; the card is inserted after stage `before - 1`. `date` and `label` are display strings.

For example, the Lidl Deutschland Tour uses `n: 0`, `label: "Prolog"`, and a stage-level official URL override because its prologue page is `/de/prolog-0`, while stages 1–4 use the tour template `/de/etappe-{n}`.

Profile-only waypoint annotations remain in `generate_profiles.py`; they are rendering hints rather than tour metadata.

Waypoint kilometres are taken from the organizer's roadbook and are normally scaled onto the GPX track from the start. Tour ids listed in `NEUTRALISED_START` are measured from the finish instead, because their GPX files include a neutralised approach before race kilometre 0, so only the distance to go matches the roadbook. The Lidl Deutschland Tour needs this: its GPX tracks run 3–8 km longer than the official stage distances.

## Add or update a tour

1. Create or edit `tours/<id>.json` using an existing file as a reference. Use `<race><year>` as id (e.g. `giro2027`) and set `year`.
2. Add the filename to `tours/manifest.json` if it is a new tour, ordered by start date.
3. Run `python3 validate_tours.py <id>` and fix all errors. Before the GPX files exist, only the "GPX-Datei fehlt" and "Profilbild fehlt" warnings are expected; the app then draws straight lines and shows "Kein Profil verfügbar".
4. Add all stage routes under `gpx/<id>/` using the documented filename pattern.
5. Run the validator again. Move `sll`/`fll` to the GPX endpoints it reports, and check stages whose GPX length differs from `dist`.
6. Optionally add profile waypoints to `generate_profiles.py` (`PROFILE_WAYPOINTS`, and `NEUTRALISED_START` for tracks with a neutralised start), then regenerate and review the elevation profiles.
7. Add `times` once the organizer publishes the timetable (usually with the roadbook shortly before the race); until then use `{}`.
8. Serve the app locally and check the map, stage cards, profile images, and external links.

### Typical timeline

| When | What becomes available |
|---|---|
| Route presentation (Tour: October, Giro: autumn/winter, Vuelta: December/January, Deutschland Tour: spring) | Stages, dates, distances, types → tour JSON |
| A few weeks before the race | Official GPX files → tracks, coordinates, profiles |
| Roadbook, days to weeks before the race | Timetable → `times` |

## Validate the tour data

```bash
python3 validate_tours.py            # all tours
python3 validate_tours.py tour2027   # selected tour ids
python3 validate_tours.py --strict   # treat warnings as errors
```

Only the Python standard library is needed. Errors (exit code 1) cover missing or mistyped fields, unknown stage types, duplicate stage numbers, a weekday that does not match the date in the tour's year, `times` entries without a stage, and rest days that do not sit between two stages. Warnings cover missing GPX or profile files, start/finish coordinates more than 2 km from the GPX endpoints, GPX lengths more than 5 % off `dist`, and totals more than 1 % off the sum of the stages.

Do not duplicate tour or stage metadata in JavaScript or Python; both consumers read the JSON files directly.

## Regenerate elevation profiles

The generator needs Python 3.9 or newer. Install its dependencies:

```bash
pip install gpxpy matplotlib numpy
```

Then run:

```bash
python3 generate_profiles.py
```

The command reads every tour in `tours/manifest.json` and overwrites the corresponding JPG files under `profile/`. Missing or invalid GPX files are reported and skipped. It runs offline.

Intermediate labels on a profile are chosen per stage by the first matching rule:

1. `times[n].points` exists: passage names, positioned linearly between start and finish time.
2. Waypoints exist and the tour is in `NEUTRALISED_START`: roadbook kilometres measured from the finish.
3. Waypoints exist: roadbook kilometres scaled to the GPX length.
4. Mountain or hilly stage: automatically detected summits (prominence above 100 m), labelled with their altitude.
5. Otherwise only start and finish are labelled.

The distance in the profile's info box is the GPX track length, which can differ from the official `dist` (for example on the Deutschland Tour).

## Deployment

The live site is served by GitHub Pages. There is no build step: the repository files are served as-is, so publishing means pushing to the branch configured for Pages. All paths in the app are relative, so it also works from a sub-path such as `/VeloPathMapper/`.

## Known issues

See [KNOWN_ISSUES.md](KNOWN_ISSUES.md).


The official Deutschland Tour GPX downloads are published by A.S.O. on the organizer's route page. Some included road sections are closed or restricted to bicycle traffic outside the event; check local rules before attempting to ride a route.
