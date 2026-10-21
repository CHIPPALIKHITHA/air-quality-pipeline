from transform import latest_run_folder, flatten_run, clean

run_dir, ingested_at = latest_run_folder()
good, _ = clean(flatten_run(run_dir, ingested_at))

old = good[good["lag_hours"] > 168]          # older than 7 days
print(old[["station_id", "parameter", "units", "value", "measured_at", "lag_hours"]]
      .round(1).to_string(index=False))