
  
    
    

    create  table
      "job_lakehouse"."main"."stg_jobs__dbt_tmp"
  
    as (
      -- Read from latest partition

SELECT * FROM read_parquet('s3://job-postings-raw/job_postings_raw/**/*.parquet', union_by_name=true)
    );
  
  