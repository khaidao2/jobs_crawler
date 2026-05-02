# 🚀 Job Listings Data Lakehouse Pipeline

A modern, end-to-end Data Lakehouse architecture designed for crawling, ingesting, transforming, and visualizing job market data.

## 🏗 Architecture Overview

The project implements a **Modern Data Stack** (MDS) with a focus on high performance and cost-efficiency:

1.  **Source Layer**: Python-based crawlers (e.g., TopCV) fetch job listings.
2.  **Streaming Ingestion**: 
    *   **Kafka**: Distributed message broker for real-time data streaming.
    *   **Apicurio Registry**: Manages Avro schemas to ensure data contracts.
3.  **Data Lake (Storage)**:
    *   **Kafka Consumer**: Real-time subscriber that persists messages to S3.
    *   **MinIO**: S3-compatible object storage acting as the Raw (Bronze) layer.
4.  **Transformation (Lakehouse)**:
    *   **DuckDB**: In-process analytical database for lightning-fast compute.
    *   **dbt**: Manages the T (Transform) in ELT via Medallion architecture (Staging -> Intermediate -> Marts).
5.  **Orchestration**:
    *   **Apache Airflow**: Schedules and monitors the end-to-end pipeline.
6.  **Visualization (BI)**:
    *   **Apache Superset**: Rich dashboards for exploring job trends, salaries, and skills.

---

## 🛠 Tech Stack

*   **Languages**: Python, SQL
*   **Infrastructure**: Docker, Docker Compose
*   **Data Transport**: Kafka, Zookeeper, Apicurio
*   **Storage**: MinIO, DuckDB
*   **Pipeline**: Apache Airflow, dbt
*   **Visualization**: Apache Superset

---

## 🚀 Quick Start

### 1. Prerequisites
*   Docker & Docker Compose
*   Python 3.10+ (for local development)

### 2. Environment Setup
Copy the example environment file and fill in your secrets:
```bash
cp .env.example .env
```

### 3. Spin up Infrastructure
```bash
docker compose up -d --build
```

### 4. Initialize BI Tool
Ensure the initialization script is executable:
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

---

## 📊 Data Transformation Layers (dbt)

*   **Staging (`stg_jobs`)**: Standardizes raw Parquet files from MinIO.
*   **Intermediate (`int_jobs_dedup`)**: Handles deduplication and cross-source mapping.
*   **Marts**:
    *   `dim_job`: Descriptive attributes (salary, title, location).
    *   `dim_company`: Company profiles and metadata.
    *   `fact_job_posting`: Transactional record of job occurrences.

---

## 🔍 Connecting Superset to DuckDB

To visualize your data, connect Superset to the persistent DuckDB file:
1.  Go to **Settings** -> **Database Connections**.
2.  Add a new **DuckDB** database.
3.  Use the following **SQLAlchemy URI**:
    ```text
    duckdb:////app/dbt/job_lakehouse.duckdb
    ```

---

## 📄 License
This project is licensed under the MIT License.