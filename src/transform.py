import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from config import STATIONS

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"


def latest_run_folder():
    """Find the newest extract run: data/raw/<date>/<HHMM>/"""
    day = sorted(p for p in RAW.iterdir() if p.is_dir())[-1]
    run = sorted(p for p in day.iterdir() if p.is_dir())[-1]
    ingested_at = datetime.strptime(f"{day.name} {run.name}", "%Y-%m-%d %H%M")
    return run, ingested_at.replace(tzinfo=timezone.utc)


def flatten_run(run_dir, ingested_at):
    """Turn the raw JSON files of one run into a flat table (one row per reading)."""
    rows = []
    for st in STATIONS:
        sid = st["id"]
        meta = json.loads((run_dir / f"{sid}_meta.json").read_text())
        latest = json.loads((run_dir / f"{sid}_latest.json").read_text())

        # sensor id -> pollutant info (the /latest data only has sensor ids)
        lookup = {s["id"]: s["parameter"] for s in meta["results"][0]["sensors"]}

        for r in latest["results"]:
            param = lookup.get(r["sensorsId"])
            if param is None:
                continue
            rows.append({
                "station_id": sid,
                "city": st["city"],
                "kind": st["kind"],
                "sensor_id": r["sensorsId"],
                "parameter": param["name"],
                "units": param["units"],
                "value": r["value"],
                "measured_at": pd.to_datetime(r["datetime"]["utc"]),
                "ingested_at": ingested_at,
            })

    df = pd.DataFrame(rows)
    df["lag_hours"] = (df["ingested_at"] - df["measured_at"]).dt.total_seconds() / 3600
    return df
STALE_DAYS = 7
POLLUTANTS = ["pm25", "pm10", "no2", "o3", "so2", "co", "no", "nox"]


def clean(df):
    """Return (clean_rows, rejected_rows). Every drop is recorded with a reason."""
    rejected = []

    # Rule 1: sensors whose newest value is very old (legacy duplicates)
    newest = df.groupby("station_id")["measured_at"].transform("max")
    stale = (newest - df["measured_at"]) > pd.Timedelta(days=STALE_DAYS)
    r = df[stale].copy()
    r["reason"] = "stale_sensor"
    rejected.append(r)
    df = df[~stale]

    # Rule 2: impossible values (negative pollutant, or missing)
    bad = df["value"].isna() | (df["parameter"].isin(POLLUTANTS) & (df["value"] < 0))
    r = df[bad].copy()
    r["reason"] = "invalid_value"
    rejected.append(r)
    df = df[~bad]

    # Rule 2b: physically implausible values (most likely a sensor fault)
    implausible = (((df["parameter"] == "pm25") & (df["value"] > 500)) |
                   ((df["parameter"] == "pm10") & (df["value"] > 1000)))
    r = df[implausible].copy()
    r["reason"] = "implausible_value"
    rejected.append(r)
    df = df[~implausible]

    # Rule 3: one reading per station + pollutant -> newest, prefer ug/m3 on ties
    df = df.assign(not_ugm3=(df["units"] != "µg/m³").astype(int))
    df = df.sort_values(["station_id", "parameter", "measured_at", "not_ugm3"],
                        ascending=[True, True, False, True])
    dup = df.duplicated(["station_id", "parameter"], keep="first")
    r = df[dup].copy()
    r["reason"] = "duplicate_sensor"
    rejected.append(r)
    df = df[~dup].drop(columns="not_ugm3")

    return df, pd.concat(rejected)

if __name__ == "__main__":
    run_dir, ingested_at = latest_run_folder()
    raw = flatten_run(run_dir, ingested_at)

    print("Station 5623 (Hyderabad), all pm25 / pm10 sensors BEFORE cleaning:")
    look = raw[(raw["station_id"] == 5623) & raw["parameter"].isin(["pm25", "pm10"])]
    print(look[["sensor_id", "parameter", "units", "value", "measured_at"]].to_string(index=False))

    good, rejected = clean(raw)

    print("\nRows before:", len(raw), "| kept:", len(good), "| rejected:", len(rejected))
    print("\nRejected by reason:")
    print(rejected["reason"].value_counts().to_string())

    print("\nMax data lag in hours per station AFTER cleaning:")
    print(good.groupby("station_id")["lag_hours"].max().round(1).to_string())