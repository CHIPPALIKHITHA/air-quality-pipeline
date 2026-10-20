import alerts
import extract
from load import load
from transform import latest_run_folder, flatten_run, clean


def run_extract():
    extract.main()


def run_transform_load():
    run_dir, ingested_at = latest_run_folder()
    good, rejected = clean(flatten_run(run_dir, ingested_at))
    load(good, rejected)


def run_alerts():
    alerts.main()


if __name__ == "__main__":
    run_extract()
    run_transform_load()
    run_alerts()