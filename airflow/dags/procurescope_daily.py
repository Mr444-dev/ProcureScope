from __future__ import annotations

import logging
import subprocess
from datetime import timedelta

import pendulum
from airflow.decorators import dag, task

LOGGER = logging.getLogger(__name__)
LOCAL_TZ = pendulum.timezone("Europe/Warsaw")


@dag(
    dag_id="procurescope_daily",
    description="Daily TED IT procurement ingestion with a 14-day correction window.",
    schedule="30 10 * * *",
    start_date=pendulum.datetime(2025, 1, 1, tz=LOCAL_TZ),
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "procurescope",
        "retries": 3,
        "retry_delay": timedelta(minutes=5),
        "execution_timeout": timedelta(hours=2),
    },
    tags=["ted", "procurement", "data-quality"],
)
def procurescope_daily():
    @task
    def ingest(**context) -> dict:
        from procurescope.pipeline import run_pipeline

        start = context["data_interval_start"].subtract(days=14).date()
        end = context["data_interval_end"].date()
        result = run_pipeline(start, end)
        LOGGER.info("Ingestion summary: %s", result)
        return result

    @task
    def transform(ingestion_summary: dict) -> None:
        LOGGER.info("Starting dbt after ingestion: %s", ingestion_summary["run_id"])
        subprocess.run(
            [
                "dbt",
                "build",
                "--project-dir",
                "/opt/airflow/app/dbt",
                "--profiles-dir",
                "/opt/airflow/app/dbt",
            ],
            check=True,
            text=True,
        )

    transform(ingest())


procurescope_daily()
