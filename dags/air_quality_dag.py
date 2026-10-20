from datetime import datetime, timedelta

from airflow.sdk import dag, task


@dag(
    dag_id="air_quality_pipeline",
    schedule="@hourly",
    start_date=datetime(2026, 10, 1),
    catchup=False,                      # don't backfill missed hours
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
    tags=["air-quality"],
)
def air_quality_pipeline():

    @task
    def extract():
        import pipeline                 # imported inside the task to keep DAG parsing fast
        pipeline.run_extract()

    @task
    def transform_load():
        import pipeline
        pipeline.run_transform_load()

    @task
    def alerts():
        import pipeline
        pipeline.run_alerts()

    extract() >> transform_load() >> alerts()


air_quality_pipeline()