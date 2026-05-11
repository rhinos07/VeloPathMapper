# VeloPathMapper
VeloPathMapper is a lightweight map viewer for cycling Grand Tour stages (currently Giro 2026 and Tour 2026), including GPX routes and elevation profile images.

https://rhinos07.github.io/VeloPathMapper/


## Quick start
1. Serve the project locally:
   ```bash
   python3 server.py
   ```
2. Open `http://localhost:8090`.
## Regenerate elevation profiles (optional)
```bash
pip install gpxpy matplotlib numpy
python3 generate_profiles.py
```
