-- Read from latest partition
SELECT * FROM read_parquet('s3://job-postings-raw/job_postings_raw/**/*.parquet', union_by_name=true)