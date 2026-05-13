from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2026, 4, 30),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

BASE_CMD = (
    "cd /opt/airflow && "
    "export PYTHONPATH=$PYTHONPATH:/opt/airflow && "
)

with DAG(
    dag_id="job_lakehouse_dbt_pipeline",
    default_args=default_args,
    description="Job Lakehouse Pipeline",
    schedule="@daily",
    catchup=False,
    tags=["jobs", "dbt", "duckdb"],
) as dag:

    run_topcv_crawler = BashOperator(
        task_id="run_topcv_crawler",
        bash_command=BASE_CMD +
        "python3 -m src.crawlers.generic_crawler "
        "--config /opt/airflow/configs/crawlers/topcv.yaml "
        "--max-pages 0",
    )

    run_topdev_crawler = BashOperator(
        task_id="run_topdev_crawler",
        bash_command=BASE_CMD +
        "python3 -m src.crawlers.generic_crawler "
        "--config /opt/airflow/configs/crawlers/topdev.yaml "
        "--max-pages 0",
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=(
            "cd /opt/airflow/dbt && "
            "/home/airflow/.local/bin/dbt run --profiles-dir ."
        ),
        env={
            "HOME": "/home/airflow",
            "MINIO_USER": "admin",
            "MINIO_PASSWORD": "changeme123",
            "DUCKDB_FILE": "/opt/airflow/dbt/job_lakehouse.duckdb",
        },
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=(
            "cd /opt/airflow/dbt && "
            "/home/airflow/.local/bin/dbt test --profiles-dir ."
        ),
    )

    [run_topcv_crawler, run_topdev_crawler] >> dbt_run >> dbt_test