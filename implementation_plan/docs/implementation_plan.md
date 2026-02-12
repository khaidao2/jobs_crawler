# Hybrid Architecture Implementation Plan

## Goal Description
Build a system with two main components:
1.  **Analytics & Machine Learning**: Uses **Google Cloud Storage (GCS)** as a Data Lake and **BigQuery** for analysis and ML model training.
2.  **Web Application**: A website for Students (job search) and Admins (viewing analysis), backed by a **Relational Database (SQL)**.

## User Review Required
> [!IMPORTANT]
> - **Cloud Costs**: Using GCS and BigQuery incurs costs (though low for small data).
> - **Architecture**: We are moving to a **Hybrid Model**.
>   - **Raw Data**: Stored in GCS (Json/CSV).
>   - **Analytics**: BigQuery queries GCS directly or imports data.
>   - **Web App**: Uses a separate SQL DB (e.g., PostgreSQL) for user data and fast retrieval of active jobs.

## Proposed Architecture

### 1. Data Lake Layer (GCS & BigQuery)
- **Storage**: Raw crawled data (JSON/CSV) is uploaded to GCS buckets (e.g., `gs://job-crawler-data/raw/YYYY-MM-DD/`).
- **Processing**: BigQuery mounts these buckets as **External Tables** or loads them into native tables.
- **Machine Learning**: Python scripts (or BigQuery ML) read from BigQuery to train models (e.g., Salary Prediction, Skill trend analysis).
- **Output**: ML results are saved back to BigQuery tables (e.g., `analytics.salary_trends`).

### 2. Application Layer (Web Website)
- **Database**: PostgreSQL/MySQL. Stores:
    - `Users` (Students, Admins)
    - `JobPostings` (Synced continuously from BigQuery/GCS for fast search)
    - `UserActivity` (Saved jobs, applications)
- **Admin Dashboard**: Fetches aggregated metrics from BigQuery or cached views in the App DB.

## Implementation Steps

### Phase 1: Data Pipeline (ETL)
#### [NEW] [scripts/gcs_upload.py](file:///wsl.localhost/Ubuntu/home/admin1/crawl_jobs/scripts/gcs_upload.py)
- Script to upload local crawled files to GCS.

#### [NEW] [sql/bigquery_schema.sql](file:///wsl.localhost/Ubuntu/home/admin1/crawl_jobs/sql/bigquery_schema.sql)
- SQL definitions to create BigQuery tables (Standard and External).

### Phase 2: Application Database
#### [NEW] [src/app/models.py](file:///wsl.localhost/Ubuntu/home/admin1/crawl_jobs/src/app/models.py)
- SQLAlchemy models for the Web App (Users, Jobs).

#### [NEW] [scripts/sync_jobs.py](file:///wsl.localhost/Ubuntu/home/admin1/crawl_jobs/scripts/sync_jobs.py)
- Script to sync "Active" jobs from BigQuery/GCS to the App DB for the website.

### Phase 3: Analytics & ML
#### [NEW] [notebooks/analysis.ipynb](file:///wsl.localhost/Ubuntu/home/admin1/crawl_jobs/notebooks/analysis.ipynb)
- Sample analysis notebook connecting to BigQuery.

## Verification Plan

### Manual Verification
- **GCS**: Upload a sample file and verify it appears in the bucket.
- **BigQuery**: Run a query on the uploaded file via External Table.
- **Web App**: Start the API server and query a job endpoint.
