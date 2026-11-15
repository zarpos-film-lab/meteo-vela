"""Scarica il vento misurato dalle stazioni vicine e scrive live.json.

Gira nella GitHub Action ogni 10 minuti (le API delle stazioni non permettono
la lettura diretta dal browser: niente CORS). Solo libreria standard.
Uso: python3 scripts/live.py percorso/live.json
"""
import json, sys, urllib.request
from datetime import datetime, timezone

UA = {"User-Agent": "meteo-vela/1.0 (uso personale)"}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def metar(icao, name):
    """METAR da aviationweather.gov (NOAA, dominio pubblico)."""
    d = get(f"https://aviationweather.gov/api/data/metar?ids={icao}&format=json")
    if not d:
        return None
    m = d[0]
    wdir = m.get("wdir")
    return {
        "id": icao,
        "name": name,
        "lat": m.get("lat"),
        "lon": m.get("lon"),
        "time": datetime.fromtimestamp(m["obsTime"], timezone.utc).isoformat().replace("+00:00", "Z"),
        "dir": wdir if isinstance(wdir, (int, float)) else None,   # "VRB" = variabile
        "kn": m.get("wspd"),
        "gust": m.get("wgst"),
        "temp": m.get("temp"),
        "raw": m.get("rawOb"),
        "source": "aviationweather.gov",
    }


def main(out):
    stations, errors = [], []
    for fn, args in [(metar, ("LIEE", "Cagliari-Elmas (aeroporto)"))]:
        try:
            s = fn(*args)
            if s:
                stations.append(s)
        except Exception as e:  # una stazione giù non deve bloccare le altre
            errors.append(f"{args[0]}: {e}")
    data = {
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "stations": stations,
        "errors": errors,
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(json.dumps(data, ensure_ascii=False)[:400])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "live.json")
