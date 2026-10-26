#!/usr/bin/env python3
"""Export the real Woodbine Casino -> The International Centre drive into route.json.

Uses only public services (no API keys): Nominatim (geocoding), OSRM (routing),
Overpass (OpenStreetMap stop signs, traffic lights, speed limits).
Run from anywhere:  python3 tools/export_route.py
Data (c) OpenStreetMap contributors, ODbL.
"""
import json, math, pathlib, time, urllib.parse, urllib.request

UA = {"User-Agent": "gta-rush/0.3 (personal game project)"}
START = ("Great Canadian Casino Resort Toronto, 1133 Queens Plate Dr, Toronto", (43.7172, -79.6002))
END = ("The International Centre, 6900 Airport Rd, Mississauga", (43.7164, -79.6320))
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


def geocode(label, fallback):
    try:
        q = urllib.parse.urlencode({"q": label, "format": "json", "limit": 1})
        r = get("https://nominatim.openstreetmap.org/search?" + q, tries=2)
        time.sleep(1.1)
        if r:
            return float(r[0]["lat"]), float(r[0]["lon"])
    except RuntimeError:
        pass
    print("  geocoding failed, using fallback coordinates for", label)
    return fallback


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
    print("Geocoding...")
    a, b = geocode(*START), geocode(*END)
    print("Routing (OSRM)...")
    pts, names, dist = fetch_route(a, b)
    print("Fetching OpenStreetMap signs, signals, speed limits (Overpass)...")
    limits, controls = build(pts, names, fetch_osm(pts))
    OUT.write_text(json.dumps({"start": {"name": START[0], "lat": a[0], "lng": a[1]},
                               "end": {"name": END[0], "lat": b[0], "lng": b[1]},
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
