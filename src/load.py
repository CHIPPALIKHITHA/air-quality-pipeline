import os

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_values

from config import STATIONS
from transform import latest_run_folder, flatten_run, clean

load_dotenv()


def connect():
    # Postgres runs in Docker; port 5433 on this computer maps to it
    return psycopg2.connect(
        host=os.getenv("WAREHOUSE_HOST", "localhost"),
        port=int(os.getenv("WAREHOUSE_PORT", "5433")),
        user=os.getenv("WAREHOUSE_USER"),
        password=os.getenv("WAREHOUSE_PASSWORD"),
        dbname=os.getenv("WAREHOUSE_DB"),
    )


def load(good, rejected):
    conn = connect()
    with conn, conn.cursor() as cur:        # commits on success, rolls back on error
        # Makes re-runs safe for rejected rows too
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_rejected "
                    "ON rejected_readings (sensor_id, measured_at, reason)")

        # 1. Dimensions
        execute_values(cur, """
            INSERT INTO dim_station (station_id, name, city, kind) VALUES %s
            ON CONFLICT (station_id) DO UPDATE
            SET name = EXCLUDED.name, city = EXCLUDED.city, kind = EXCLUDED.kind""",
            [(s["id"], s["name"], s["city"], s["kind"]) for s in STATIONS])

        params = sorted(set(zip(good["parameter"], good["units"])))
        execute_values(cur, """
            INSERT INTO dim_parameter (parameter, units) VALUES %s
            ON CONFLICT (parameter, units) DO NOTHING""", params)

        # Look up the surrogate keys the fact table needs
        cur.execute("SELECT station_id, station_key FROM dim_station")
        skey = dict(cur.fetchall())
        cur.execute("SELECT parameter, units, parameter_key FROM dim_parameter")
        pkey = {(p, u): k for p, u, k in cur.fetchall()}

        # 2. Facts
        fact_rows = [
            (skey[r.station_id], pkey[(r.parameter, r.units)],
             int(r.measured_at.strftime("%Y%m%d")),          # date_key (UTC date)
             float(r.value), r.measured_at.to_pydatetime(),
             r.ingested_at.to_pydatetime(), round(float(r.lag_hours), 2))
            for r in good.itertuples()
        ]
        execute_values(cur, """
            INSERT INTO fact_air_quality
              (station_key, parameter_key, date_key, value, measured_at, ingested_at, lag_hours)
            VALUES %s
            ON CONFLICT (station_key, parameter_key, measured_at) DO NOTHING""", fact_rows)
        new_facts = cur.rowcount

        # 3. Rejected rows, with the reason
        rej_rows = [
            (int(r.station_id), int(r.sensor_id), r.parameter, r.units,
             None if r.value != r.value else float(r.value),   # NaN -> NULL
             r.measured_at.to_pydatetime(), r.reason)
            for r in rejected.itertuples()
        ]
        execute_values(cur, """
            INSERT INTO rejected_readings
              (station_id, sensor_id, parameter, units, value, measured_at, reason)
            VALUES %s
            ON CONFLICT (sensor_id, measured_at, reason) DO NOTHING""", rej_rows)
        new_rejected = cur.rowcount

        cur.execute("SELECT count(*) FROM fact_air_quality")
        total_facts = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM rejected_readings")
        total_rej = cur.fetchone()[0]

    conn.close()
    print(f"Facts: {new_facts} new | table total {total_facts}")
    print(f"Rejected: {new_rejected} new | table total {total_rej}")


if __name__ == "__main__":
    run_dir, ingested_at = latest_run_folder()
    good, rejected = clean(flatten_run(run_dir, ingested_at))
    load(good, rejected)