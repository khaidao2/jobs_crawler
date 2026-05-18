"""
Standardized Airflow operators for job crawler tasks.
"""
import logging
import asyncio
import sys
import os

sys.path.insert(0, "/opt/airflow")
sys.path.insert(0, "/opt/airflow/src")

from src.crawlers.generic_crawler import GenericCrawler
from src.crawlers.sink import KafkaSink
from src.config import KAFKA_TOPIC, SCHEMA_PATH

logger = logging.getLogger(__name__)


def run_crawler(source: str, config_path: str, max_pages: int = 1, concurrency: int = 5) -> dict:
    """
    Run crawler for a specific source.
    
    Args:
        source: Source name (e.g., 'topcv', 'topdev')
        config_path: Path to YAML config file
        max_pages: Maximum pages to crawl (0 = unlimited)
        concurrency: Max concurrent requests
    
    Returns:
        dict with execution metadata
    """
    logger.info(f"Starting crawler for source={source}, config={config_path}")
    
    try:
        sink = KafkaSink(topic=KAFKA_TOPIC, schema_path=SCHEMA_PATH)
        crawler = GenericCrawler(
            config_path=config_path,
            sink=sink,
            schema_path=SCHEMA_PATH,
            concurrency=concurrency
        )
        
        asyncio.run(crawler.run(max_pages=max_pages))
        sink.close()
        
        result = {
            "source": source,
            "status": "success",
            "config_path": config_path,
            "max_pages": max_pages
        }
        
        logger.info(f"Crawler completed for source={source}")
        return result
        
    except Exception as e:
        logger.error(f"Crawler failed for source={source}: {e}")
        raise


def run_dbt_command(command: str, profiles_dir: str = "/opt/airflow/dbt", env: dict = None) -> dict:
    """
    Run dbt command.
    
    Args:
        command: dbt command (e.g., 'dbt run', 'dbt test')
        profiles_dir: Path to dbt profiles directory
        env: Environment variables
    
    Returns:
        dict with execution metadata
    """
    import subprocess
    
    logger.info(f"Running dbt command: {command}")
    
    env_vars = os.environ.copy()
    if env:
        env_vars.update(env)
    
    try:
        result = subprocess.run(
            f"cd {profiles_dir} && /home/airflow/.local/bin/{command}",
            shell=True,
            env=env_vars,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"dbt command failed: {result.stderr}")
            raise Exception(f"dbt command failed: {result.stderr}")
        
        logger.info(f"dbt command completed: {command}")
        return {
            "command": command,
            "status": "success",
            "output": result.stdout
        }
        
    except Exception as e:
        logger.error(f"dbt command failed: {e}")
        raise