from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2026, 4, 30),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'job_lakehouse_dbt_pipeline',
    default_args=default_args,
    description='A simple pipeline to run dbt transformations on job data',
    schedule_interval=timedelta(days=1),
    catchup=False,
) as dag:

    run_crawler = BashOperator(
        task_id='run_topcv_crawler',
        bash_command='export PYTHONPATH=$PYTHONPATH:/opt/airflow && python3 -m src.crawlers.topcv --max-pages 2',
    )

    dbt_run = BashOperator(
        task_id='dbt_run',
        bash_command='cd /opt/airflow/dbt && dbt run --profiles-dir .',
    )

    dbt_test = BashOperator(
        task_id='dbt_test',
        bash_command='cd /opt/airflow/dbt && dbt test --profiles-dir .',
    )

    run_crawler >> dbt_run >> dbt_test
