import os
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

from config import STATIONS

load_dotenv()
BASE = "https://api.openaq.org/v3"
HEADERS = {"X-API-Key": os.getenv("OPENAQ_API_KEY")}


def fetch(path, retries=3):
    """GET one API path. Retries with a growing wait if the API is busy."""
    for attempt in range(retries):
        r = requests.get(f"{BASE}{path}", headers=HEADERS, timeout=30)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429 or r.status_code >= 500:   # busy or server error
            wait = 5 * (2 ** attempt)
            print(f"  status {r.status_code} on {path}, retrying in {wait}s")
            time.sleep(wait)
            continue
        r.raise_for_status()                                # any other error: stop
    raise RuntimeError(f"Gave up on {path} after {retries} tries")


def save_raw(payload, kind, station_id, run_ts):
    """Keep the untouched API response so we can re-process it later."""
    folder = (Path(__file__).resolve().parent.parent / "data" / "raw"
              / f"{run_ts:%Y-%m-%d}" / f"{run_ts:%H%M}")
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{station_id}_{kind}.json").write_text(json.dumps(payload))


def main():
    run_ts = datetime.now(timezone.utc)
    print("Run started (UTC):", run_ts.strftime("%Y-%m-%d %H:%M"))

    for st in STATIONS:
        sid = st["id"]
        print(f"\n{st['city']} | {st['name']} ({sid})")

        meta = fetch(f"/locations/{sid}")          # tells us sensor id -> pollutant
        save_raw(meta, "meta", sid, run_ts)
        sensors = meta["results"][0]["sensors"]

        latest = fetch(f"/locations/{sid}/latest")  # newest value per sensor
        save_raw(latest, "latest", sid, run_ts)
        readings = latest["results"]

        times = [r["datetime"]["utc"] for r in readings if r.get("datetime")]
        newest = max(times) if times else "none"
        print(f"  sensors: {len(sensors)} | readings: {len(readings)} | newest: {newest}")

        time.sleep(1)                               # be gentle with the API


if __name__ == "__main__":
    main()