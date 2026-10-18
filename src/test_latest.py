import os
from dotenv import load_dotenv
import requests

load_dotenv()
headers = {"X-API-Key": os.getenv("OPENAQ_API_KEY")}

# 6254594 = Talkatora Garden (government monitor), 8118 = New Delhi (live)
for loc_id in [6254594, 8118]:
    r = requests.get(f"https://api.openaq.org/v3/locations/{loc_id}/latest",
                     headers=headers, timeout=30)
    print("Location", loc_id, "| status", r.status_code)
    if r.status_code != 200:
        print(r.text[:300])
        continue
    for item in r.json()["results"]:
        when = (item.get("datetime") or {}).get("utc")
        print("   sensor", item.get("sensorsId"), "| value", item.get("value"), "| time", when)