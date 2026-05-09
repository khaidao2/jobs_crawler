-- Read from specific date partition with all columns as VARCHAR to avoid type issues
SELECT * FROM read_parquet('s3://job-postings-raw/job_postings_raw/batch_date=2026-05-09/**/*.parquet')