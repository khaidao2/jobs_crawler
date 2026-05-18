"""Auto-generated DAG file. Do not edit manually."""
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2026, 4, 30),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="dbt_pipeline",
    default_args=default_args,
    description="Run dbt transformations",
    schedule="@daily",
    catchup=False,
    tags=["auto-generated"],
) as dag:
    task_dbt_run_staging = BashOperator(
        task_id="dbt_run_staging",
        bash_command="cd /opt/airflow/dbt && /home/airflow/.local/bin/dbt run --select staging --profiles-dir .",
        env={"HOME": "/home/airflow", },
    )
    task_dbt_run_intermediate = BashOperator(
        task_id="dbt_run_intermediate",
        bash_command="cd /opt/airflow/dbt && /home/airflow/.local/bin/dbt run --select intermediate --profiles-dir .",
        env={"HOME": "/home/airflow", },
    )
    task_dbt_run_marts = BashOperator(
        task_id="dbt_run_marts",
        bash_command="cd /opt/airflow/dbt && /home/airflow/.local/bin/dbt run --select marts --profiles-dir .",
        env={"HOME": "/home/airflow", },
    )
    task_dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/airflow/dbt && /home/airflow/.local/bin/dbt test --profiles-dir .",
        env={"HOME": "/home/airflow", },
    )

    task_dbt_run_staging >> task_dbt_run_intermediate >> task_dbt_run_marts >> task_dbt_test