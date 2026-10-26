# GTA Rush

A browser-based 3D racing game set on real GTA streets, with local driver humour (Brampton signals left and turns right; Oakville has no signals at all).

**Level 1:** Woodbine Casino → Queens Plate Dr → Rexdale Blvd → Derry Rd W → Airport Rd → The International Centre.

## Run
No build step. Open `index.html`, or serve it:

```
python3 -m http.server 8000
```

Controls: WASD / arrows, Space = brake, R = reset onto the road.

## Status (v0.1)
Single self-contained `index.html` using Three.js r128 from cdnjs. Route waypoints are hand-placed approximations: street names are real, geometry is not yet.

## Roadmap
- [ ] Crash ends the run (game-over screen)
- [ ] Real road geometry from OpenStreetMap (curved, non-linear road)
- [ ] Road signs (street names, speed limits) from OSM `maxspeed` / `name`
- [ ] Stop signs and traffic lights from OSM (`highway=stop`, `highway=traffic_signals`), with traffic that obeys them
- [ ] Realistic automatic gearbox: gear ratios, shift delay, torque curve, top speed
- [ ] Speed cameras (City of Toronto Automated Speed Enforcement locations, open data) with fines
- [ ] Live data: real clock for time of day and lighting; live traffic flow via a provider API (needs a key and a small backend proxy)
- [ ] Brampton vs Oakville traffic personalities
- [ ] Tesla Roadster with flight mode
- [ ] Split into modules (Vite)

## Data sources (planned)
- Roads, signals, stop signs, speed limits: OpenStreetMap (© OpenStreetMap contributors, ODbL)
- Speed cameras: City of Toronto Open Data
- Live traffic: TBD (TomTom / HERE flow API, server-side key)
