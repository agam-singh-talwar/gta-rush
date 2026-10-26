#!/usr/bin/env python3
"""Export the real Woodbine Casino -> The International Centre drive into route.json.

Uses only public services (no API keys): Nominatim (geocoding), OSRM (routing),
Overpass (OpenStreetMap stop signs, traffic lights, speed limits).
Run from anywhere:  python3 tools/export_route.py
Data (c) OpenStreetMap contributors, ODbL.
"""
import argparse, json, math, pathlib, sys, time, urllib.parse, urllib.request

UA = {"User-Agent": "gta-rush/0.3 (personal game project; github.com/agam-singh-talwar/gta-rush)", "Accept-Language": "en"}
START_QUERIES = ["1133 Queens Plate Drive, Toronto, Ontario", "Great Canadian Casino Resort Toronto", "Woodbine Racetrack, Toronto"]
END_QUERIES = ["6900 Airport Road, Mississauga, Ontario", "The International Centre, Mississauga", "International Centre, Airport Road, Mississauga"]
OVERPASS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
OUT = pathlib.Path(__file__).resolve().parent.parent / "route.json"


def get(url, data=None, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers=UA)
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read())
        except Exception as e:
            print(f"  retry {i + 1}: {e}")
            time.sleep(2 * (i + 1))
    raise RuntimeError("request failed: " + url[:80])


def geocode(queries):
    """Try Nominatim, then Photon, for each query. Returns (lat, lng, matched name) or None."""
    for q in queries:
        try:
            r = get("https://nominatim.openstreetmap.org/search?" +
                    urllib.parse.urlencode({"q": q, "format": "json", "limit": 1, "countrycodes": "ca"}), tries=2)
            time.sleep(1.1)
            if r:
                return float(r[0]["lat"]), float(r[0]["lon"]), r[0].get("display_name", q)
        except RuntimeError:
            pass
        try:
            r = get("https://photon.komoot.io/api/?" + urllib.parse.urlencode({"q": q, "limit": 1, "lat": 43.71, "lon": -79.62}), tries=2)
            if r.get("features"):
                f = r["features"][0]
                lng, lat = f["geometry"]["coordinates"]
                return lat, lng, f["properties"].get("name", q)
        except RuntimeError:
            pass
        print(f"  no result for: {q}")
    return None


def resolve(label, override, queries):
    if override:
        lat, lng = (float(x) for x in override.split(","))
        print(f"  {label}: using your coordinates {lat}, {lng}")
        return lat, lng
    r = geocode(queries)
    if not r:
        sys.exit(f"\nCould not find the {label} automatically.\n"
                 f"Open openstreetmap.org, right-click the exact spot > 'Show address', then run e.g.\n"
                 f"  python3 tools/export_route.py --{label} 43.7061,-79.6335\n")
    print(f"  {label}: {r[2]}  ({r[0]:.5f}, {r[1]:.5f})")
    return r[0], r[1]


def meters(a, b):
    k = math.cos(math.radians(a[0]))
    return math.hypot((a[1] - b[1]) * 111320 * k, (a[0] - b[0]) * 110540)


def parse_speed(v):
    try:
        n = int("".join(c for c in v.split(";")[0] if c.isdigit()))
        return round(n * 1.609) if "mph" in v else n
    except ValueError:
        return None


def fetch_route(a, b):
    u = (f"https://router.project-osrm.org/route/v1/driving/{a[1]},{a[0]};{b[1]},{b[0]}"
         "?overview=full&geometries=geojson&steps=true")
    rt = get(u)["routes"][0]
    pts, names = [], []
    for leg in rt["legs"]:
        for st in leg["steps"]:
            nm = st.get("name") or st.get("ref") or ""
            for lng, lat in (st["geometry"]["coordinates"][1:] if pts else st["geometry"]["coordinates"]):
                pts.append([round(lat, 6), round(lng, 6)])
                names.append(nm or (names[-1] if names else ""))
    return pts, names, rt["distance"]


def fetch_osm(pts):
    m = 0.004
    s, n = min(p[0] for p in pts) - m, max(p[0] for p in pts) + m
    w, e = min(p[1] for p in pts) - m, max(p[1] for p in pts) + m
    box = f"{s:.5f},{w:.5f},{n:.5f},{e:.5f}"
    q = (f'[out:json][timeout:90];(node["highway"~"^(stop|traffic_signals)$"]({box});'
         f'way["highway"]["maxspeed"]({box}););out tags geom;')
    body = urllib.parse.urlencode({"data": q}).encode()
    for url in OVERPASS:
        try:
            return get(url, data=body, tries=2)["elements"]
        except RuntimeError:
            continue
    raise RuntimeError("all Overpass servers failed; try again in a minute")


def build(pts, names, elements):
    verts = []
    for el in elements:
        if el["type"] == "way":
            sp = parse_speed(el["tags"].get("maxspeed", ""))
            if sp:
                verts += [((g["lat"], g["lon"]), sp) for g in el.get("geometry", [])]
    limits = []
    for p in pts:
        best, val = 18.0, None
        for v, sp in verts:
            if abs(v[0] - p[0]) > .0003 or abs(v[1] - p[1]) > .0005:
                continue
            d = meters(p, v)
            if d < best:
                best, val = d, sp
        limits.append(val)
    controls = []
    for el in elements:
        if el["type"] != "node":
            continue
        kind = {"stop": "stop", "traffic_signals": "signal"}.get(el["tags"].get("highway"))
        if kind and min(meters((el["lat"], el["lon"]), p) for p in pts) <= 25:
            controls.append({"type": kind, "lat": el["lat"], "lng": el["lon"]})
    return limits, controls


def main():
    ap = argparse.ArgumentParser(description="Export the Woodbine -> International Centre route to route.json")
    ap.add_argument("--start", help="override start as lat,lng")
    ap.add_argument("--end", help="override end as lat,lng")
    args = ap.parse_args()
    print("Finding start and end...")
    a, b = resolve("start", args.start, START_QUERIES), resolve("end", args.end, END_QUERIES)
    print("Routing (OSRM)...")
    pts, names, dist = fetch_route(a, b)
    if "airport" not in names[-1].lower():
        print(f"  WARNING: route ends on '{names[-1]}', not Airport Rd. Check the end point (use --end lat,lng).")
    print("Fetching OpenStreetMap signs, signals, speed limits (Overpass)...")
    limits, controls = build(pts, names, fetch_osm(pts))
    OUT.write_text(json.dumps({"start": {"lat": a[0], "lng": a[1]}, "end": {"lat": b[0], "lng": b[1]},
                               "points": pts, "names": names, "limits": limits,
                               "controls": controls}, separators=(",", ":")))
    order = [n for i, n in enumerate(names) if i == 0 or n != names[i - 1]]
    print(f"\nWrote {OUT}\n  {dist / 1000:.1f} km, {len(pts)} points")
    print(f"  {sum(c['type'] == 'signal' for c in controls)} traffic lights, "
          f"{sum(c['type'] == 'stop' for c in controls)} stop signs, "
          f"{sum(v is not None for v in limits)} points with a speed limit")
    print("  Streets:", " > ".join(order))


if __name__ == "__main__":
    main()
