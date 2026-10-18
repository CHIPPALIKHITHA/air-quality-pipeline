# Stations we track. Chosen from the OpenAQ India station list (Oct 2026).
# "full"  = government monitor, many pollutants, readings arrive ~4 days late
# "live"  = PM2.5 only, readings within the hour (used for alerts)

STATIONS = [
    {"id": 8118,    "city": "Delhi",     "name": "New Delhi",               "kind": "live"},
    {"id": 6254594, "city": "Delhi",     "name": "Talkatora Garden - DPCC", "kind": "full"},
    {"id": 8039,    "city": "Mumbai",    "name": "Mumbai",                  "kind": "live"},
    {"id": 3409510, "city": "Mumbai",    "name": "Byculla - BMC",           "kind": "full"},
    {"id": 5655,    "city": "Chennai",   "name": "Velachery - CPCB",        "kind": "full"},
    {"id": 6950,    "city": "Kolkata",   "name": "Jadavpur - WBPCB",        "kind": "full"},
    {"id": 5623,    "city": "Hyderabad", "name": "Central University - TSPCB", "kind": "full"},
]

MAX_LIVE_LAG_HOURS = 3     # alerts use only readings fresher than this