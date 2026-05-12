# Job Listings Data Lakehouse Pipeline

An end-to-end Data Lakehouse architecture for crawling, ingesting, transforming, and visualizing job market data.

## Architecture

1. **Source Layer**: Python crawlers (TopCV, TopDev) fetch job listings.
2. **Streaming Ingestion**:
   - **Kafka**: Distributed message broker for real-time data streaming.
   - **Apicurio Registry**: Manages Avro schemas for data contracts.
3. **Data Lake (Storage)**:
   - **Kafka Consumer**: Persists messages to S3 in real-time.
   - **MinIO**: S3-compatible object storage (Bronze/Raw layer).
4. **Transformation (Lakehouse)**:
   - **DuckDB**: In-process analytical database for fast compute.
   - **dbt**: Manages ELT transformations via Medallion architecture.
5. **Orchestration**:
   - **Apache Airflow**: Schedules and monitors the pipeline.
6. **Visualization**:
   - **Apache Superset**: Dashboards for job trends, salaries, and skills.

## Tech Stack

- **Languages**: Python, SQL
- **Infrastructure**: Docker, Docker Compose
- **Data Transport**: Kafka, Zookeeper, Apicurio
- **Storage**: MinIO, DuckDB
- **Pipeline**: Apache Airflow, dbt
- **Visualization**: Apache Superset

## Quick Start

### 1. Prerequisites
- Docker & Docker Compose
- Python 3.10+ (for local development)

### 2. Environment Setup
```bash
cp .env.example .env
```

### 3. Start Infrastructure
```bash
docker compose up -d --build
```

### 4. Initialize Superset
```bash
chmod +x scripts/superset-init.sh
docker compose up -d --build superset
```

### 5. Access Services
| Service | URL | Credentials |
| :--- | :--- | :--- |
| **Airflow** | `http://localhost:8080` | `admin` / `admin` |
| **Kafka UI** | `http://localhost:8090` | - |
| **MinIO Console** | `http://localhost:9001` | `admin` / `changeme123` |
| **Superset** | `http://localhost:8089` | `admin` / `admin` |

## Data Transformation Layers (dbt)

- **Staging (`stg_jobs`)**: Standardizes raw Parquet files from MinIO.
- **Intermediate (`int_jobs_dedup`)**: Deduplication and cross-source mapping.
- **Marts**:
  - `dim_job`: Descriptive attributes (salary, title, location).
  - `dim_company`: Company profiles and metadata.
  - `fact_job_posting`: Transactional record of job occurrences.

## Connecting Superset to DuckDB

1. Go to **Settings** -> **Database Connections**.
2. Add a new **DuckDB** database.
3. Use the SQLAlchemy URI:
   ```
   duckdb:////app/dbt/job_lakehouse.duckdb
   ```

## Running Crawlers

```bash
# Activate virtual environment
source .venv/bin/activate

# Crawl TopCV
python -m src.crawlers.generic_crawler --config configs/crawlers/topcv.yaml --max-pages 5

# Crawl TopDev
python -m src.crawlers.generic_crawler --config configs/crawlers/topdev.yaml --max-pages 5
```

## Querying Data

```bash
# CLI query tool
python scripts/query.py

# Interactive Flask app
python scripts/query_flask.py

# Streamlit dashboard
streamlit run scripts/dashboard.py
```