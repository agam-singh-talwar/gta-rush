# GTA Rush

Browser-based 3D racing game on real Greater Toronto Area roads, with local driver humour.
Repo: github.com/agam-singh-talwar/gta-rush. Single static `index.html` using Three.js r128 from cdnjs (no build step yet).

## Concept
- Level 1: Woodbine Casino -> Queens Plate Dr -> Rexdale Blvd -> Derry Rd W -> Airport Rd -> The International Centre (6900 Airport Rd).
- Brampton traffic: compact sedans and hatchbacks, signal one way and turn the other, slow lane drifts.
- Oakville traffic (later): luxury cars, no signals, fast, tailgating.
- Use generic lookalike car names, not real brands or logos.
- Later: Tesla Roadster with a flight mode.

## Current state (v0.2)
- Route waypoints in `WP` are hand-placed approximations (street names real, geometry not).
- Crash with traffic ends the run. Automatic gearbox lives in the `CAR` block (gear ratios, shift time, top speed ~197 km/h).

## Roadmap (in order)
1. Real road geometry from OpenStreetMap (curved road); export a `route.json` by script, load it in the game.
2. Road signs, stop signs, traffic lights, speed limits from OSM tags; traffic obeys signals.
3. Speed cameras (City of Toronto ASE open data) with fines.
4. Live data: real clock for time of day; live traffic via a provider API behind a small server proxy (never expose keys in the page).
5. Brampton vs Oakville personalities, Roadster, split into modules with Vite.

## Working rules
- Keep the game playable at every commit; test by running `python3 -m http.server 8000`.
- Keep tunable numbers in config blocks at the top of the script.
- Commit small, with clear messages; `main` deploys via GitHub Pages.
- Data attribution: OpenStreetMap contributors (ODbL).
