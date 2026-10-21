import os
import time
from datetime import datetime, timezone
from dotenv import load_dotenv
import requests

load_dotenv()
headers = {"X-API-Key": os.getenv("OPENAQ_API_KEY")}
url = "https://api.openaq.org/v3/locations"

CITIES = ["delhi", "chennai", "mumbai", "kolkata", "hyderabad"]
all_stations = []
page = 1

while True:
    r = requests.get(url, headers=headers,
                     params={"countries_id": 9, "limit": 100, "page": page}, timeout=30)
    if r.status_code != 200:
        print("Stopped at page", page, "status", r.status_code, r.text[:200])
        break
    data = r.json()
    results = data["results"]
    if not results:
        break
    all_stations.extend(results)
    if len(results)<100 or page >= 30:
        break
    page += 1
    time.sleep(1)                          # be gentle with the API

print("Total Indian stations fetched:", len(all_stations))

def last_seen(loc):
    s = (loc.get("datetimeLast") or {}).get("utc")
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None

dates = [last_seen(s) for s in all_stations if last_seen(s)]
print("Most recent reading across ALL stations:", max(dates))
print()

now = datetime.now(timezone.utc)
for loc in all_stations:
    name = loc["name"]
    if any(c in name.lower() for c in CITIES):
        ls = last_seen(loc)
        age = (now - ls).days if ls else "?"
        pollutants = sorted({s["parameter"]["name"] for s in loc["sensors"]})
        print(loc["id"], "|", name, "| days since last data:", age, "|", pollutants)
        print()
print("=== LIVE stations (data within last 24h) ===")
for loc in all_stations:
    ls = last_seen(loc)
    if ls and (now - ls).total_seconds() < 86400:
        pollutants = sorted({s["parameter"]["name"] for s in loc["sensors"]})
        print(loc["id"], "|", loc["name"], "|", ls.strftime("%Y-%m-%d %H:%M"), "|", pollutants)