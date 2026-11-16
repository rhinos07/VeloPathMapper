# Known issues

Found during a review of the code and data on 2026-11-16. Ordered by impact.

## Data

### Start/finish coordinates far from the GPX track

`sll`/`fll` place the start/finish markers and the stage-number badge, and they define the map extent. In these stages they are 10–24 km away from the GPX endpoints, so the markers sit off the route:

| Tour | Stage | Field | In JSON | GPX endpoint | Offset |
|---|---|---|---|---|---|
| tour2026 | 6 (Pau → Gavarnie-Gèdre) | `fll` | 42.955, -0.009 | 42.736, -0.013 | ~24 km |
| tour2026 | 7 (Hagetmau → Bordeaux) | `sll` | 43.658, -0.319 | 43.680, -0.584 | ~21 km |
| tour2026 | 15 (Champagnole → Plateau de Solaison) | `fll` | 46.150, 6.333 | 46.033, 6.427 | ~15 km |
| giro2026 | 7 (Formia → Blockhaus) | `fll` | 42.079, 14.136 | 42.170, 14.119 | ~10 km |
| giro2026 | 9 (Cervia → Corno alle Scale) | `fll` | 44.132, 10.951 | 44.133, 10.814 | ~11 km |

Most other Giro and Tour stages are 2–9 km off (town centre instead of the actual start line). The Vuelta and Deutschland Tour coordinates match the GPX files.

### Tour totals do not match the sum of the stages

| Tour | `totalDist` | Sum of `dist` | `totalElev` | Sum of `elev` |
|---|---|---|---|---|
| giro2026 | ~3.459 km | 3.455 km | ~49.150 Hm | 48.650 Hm |
| tour2026 | ~3.333 km | 3.333 km | ~51.200 Hm | 51.600 Hm |
| vuelta2026 | ~3.284 km | 3.283 km | ~58.150 Hm | 55.900 Hm |

The Vuelta difference of about 2.250 Hm is the largest. Either the totals or individual stage values are outdated.

### GPX length differs noticeably from the official distance

Giro stages 1 (155.8 vs 147 km), 6 (160.3 vs 150 km) and 15 (135.8 vs 145 km), and Tour stages 3 (187.1 vs 196 km) and 17 (180.4 vs 175 km). Either the GPX file is a different route version or `dist` is wrong. This also distorts the waypoint positions on the generated profiles, because waypoints are scaled by `GPX length / dist`.

### Unused fields

`startDesc`, `mapCenter` and `mapZoom` are present in every tour file but not read by the app or the generator.

## Web app (`index.html`)

### GPX progress badge is wrong when several tours load at once

`gpxTotal`/`gpxDone` are shared globals. When a second tour is selected while the first is still loading, the first loader to finish sets the badge to "GPS-Daten geladen", and its 2.5 s timer resets both counters to 0 while the second tour is still loading.

### GPX requests are aborted after 5 seconds without notice

`loadGPX` aborts each request after 5 s and silently keeps the straight placeholder line. Several GPX files are 1.2–1.5 MB (e.g. Tour stages 9, 13, 15), and selecting the Tour de France downloads about 14 MB. On a slow mobile connection, stages can therefore stay as straight lines with no message to the user.

### Re-selecting a tour during loading

If a tour is deselected and re-selected while its GPX files are loading, the first loader keeps writing into the discarded layer data. This is harmless for the map, but the progress counter counts the tour twice.

### Data inserted as HTML

Tour and stage strings are inserted with `innerHTML` and inline `onclick` handlers without escaping. This is not exploitable as long as the JSON files are maintained in the repository, but a name containing `'` or `<` would break the markup.

### Accessibility

Tour items and stage cards are `div`s with `onclick`, so they cannot be reached or activated with the keyboard. The dialog has no `role="dialog"`, no focus handling, and the close buttons (`✕`) have no accessible label. The tab buttons have no `role="tab"` state.

### Small-screen layout

Below 500 px the sidebar takes up to 40 % of the height and the info panel overlays the map; the panel can cover most of the remaining map.

### Leaflet loaded from unpkg without integrity hash

`leaflet.css` and `leaflet.js` are loaded from unpkg without `integrity`/`crossorigin` attributes.

## Tools

### `server.py`

- Listens on all network interfaces (`""`), so the development server is reachable from the local network.
- Fails with a stack trace if port 8090 is already in use.
- Suppresses all request logging, including 404s, which hides missing GPX or profile files during development.

### `generate_profiles.py`

- Fails with `KeyError` for a tour without a `times` object.
- Uses `gpx/<id>/` and `profile/<id>/` directly and ignores `gpxBase`/`profileBase` from the tour file.
- Passage labels from `times.points` are placed by linear interpolation of the clock time, which assumes constant speed; on mountain stages the labels can be far from the real position.
- No waypoints are defined for the Vuelta, so its profiles only show automatically detected summit heights.

## Repository

- No licence file. The README does not state the source or licence of the GPX files and route data (only the Deutschland Tour source is mentioned).
- `validate_tours.py` checks the data, but it only runs by hand; there is no CI job yet.

## 2027 tours (preliminary data)

### Tour de France 2027

`tours/tour2027.json` was created on 2026-11-16 from the route presentation, cross-checked against Domestique, ProCyclingStats UK and CyclingStage reports. Until the official GPX files are published:

- `sll`/`fll` are approximate town centres; the finish of stage 18 (Col du Portet) and stage 14 (Mende, Croix Neuve) are rough estimates.
- Per-stage `elev` values are rounded figures from press reports; they add up to the official total of 53,450 m.
- Stage 17 starts in Muret according to two sources; CyclingStage lists Toulouse.
- `times` is empty, and there are no GPX files or profiles yet.
- The `official` link template assumes letour.fr keeps its `/de/stage/{n}` URL pattern.

### Giro d'Italia 2027

`tours/giro2027.json` was created on 2026-11-16 from the route presentation (3 November 2026), cross-checked against ProCyclingUK, CyclingStage, Tour-Magazin, OA Sport and bicimtbebike.

- `sll`/`fll` are approximate town centres; summit finishes (Sassotetto, Monte Livata, Passo dei Due Santi, Piani di Bobbio, Monte Zoncolan) are rough estimates.
- Per-stage `elev` values come from bicimtbebike; they add up to the official 50,250 m. Some other outlets give different values for stages 14 and 18.
- The organizer only counts 7 mountain finishes, 7 flat, 5 undulating stages and 2 time trials; the per-stage assignment of `sprint`/`hilly` is based on press descriptions. Stage 3 (Possagno) and stage 11 (Mugello, 2,150 m) are borderline.
- Stage 7 is listed as 19.6 km in most sources, 19.4 km in one.
- `times` is empty, and there are no GPX files or profiles yet.
- The `official` link template assumes giroditalia.it keeps its 2026 URL pattern and that the slugs match; check once the stage pages are online.
