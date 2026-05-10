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

    run_topcv_crawler = BashOperator(
        task_id='run_topcv_crawler',
        bash_command='cd /opt/airflow && export PYTHONPATH=$PYTHONPATH:/opt/airflow && python3 -m src.crawlers.generic_crawler --config /opt/airflow/configs/crawlers/topcv.yaml --max-pages 0',
    )

    run_topdev_crawler = BashOperator(
        task_id='run_topdev_crawler',
        bash_command='cd /opt/airflow && export PYTHONPATH=$PYTHONPATH:/opt/airflow && python3 -m src.crawlers.generic_crawler --config /opt/airflow/configs/crawlers/topdev.yaml --max-pages 0',
    )

    wait_for_ingestion = BashOperator(
        task_id='wait_for_ingestion',
        bash_command='sleep 35',
    )

    dbt_run = BashOperator(
        task_id='dbt_run',
        bash_command='cd /opt/airflow/dbt && /home/airflow/.local/bin/dbt run --profiles-dir .',
        env={
            'HOME': '/home/airflow',
            'MINIO_USER': 'admin',
            'MINIO_PASSWORD': 'changeme123',
        },
    )

    [run_topcv_crawler, run_topdev_crawler] >> wait_for_ingestion >> dbt_run
