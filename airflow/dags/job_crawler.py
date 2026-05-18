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
    dag_id="job_crawler",
    default_args=default_args,
    description="Crawl job listings from TopCV and TopDev",
    schedule="@daily",
    catchup=False,
    tags=["auto-generated"],
) as dag:
    def callable_crawl_topcv():
        import sys
        sys.path.insert(0, '/opt/airflow')
        import importlib
        module_path, func_name = "src.airflow.operators.crawler_operators.run_crawler".rsplit(".", 1)
        mod = importlib.import_module(module_path)
        func = getattr(mod, func_name)
        return func(**{"source": "topcv", "config_path": "/opt/airflow/configs/crawlers/topcv.yaml", "max_pages": 0})
    
    task_crawl_topcv = PythonOperator(
        task_id="crawl_topcv",
        python_callable=callable_crawl_topcv,
    )
    def callable_crawl_topdev():
        import sys
        sys.path.insert(0, '/opt/airflow')
        import importlib
        module_path, func_name = "src.airflow.operators.crawler_operators.run_crawler".rsplit(".", 1)
        mod = importlib.import_module(module_path)
        func = getattr(mod, func_name)
        return func(**{"source": "topdev", "config_path": "/opt/airflow/configs/crawlers/topdev.yaml", "max_pages": 0})
    
    task_crawl_topdev = PythonOperator(
        task_id="crawl_topdev",
        python_callable=callable_crawl_topdev,
    )
    task_dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/dbt && /home/airflow/.local/bin/dbt run --profiles-dir .",
        env={"HOME": "/home/airflow", "MINIO_USER": "admin", "MINIO_PASSWORD": "changeme123", "DUCKDB_FILE": "/opt/airflow/dbt/job_lakehouse.duckdb", },
    )
    task_dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/airflow/dbt && /home/airflow/.local/bin/dbt test --profiles-dir .",
        env={"HOME": "/home/airflow", },
    )

    [task_crawl_topcv, task_crawl_topdev] >> task_dbt_run >> task_dbt_test