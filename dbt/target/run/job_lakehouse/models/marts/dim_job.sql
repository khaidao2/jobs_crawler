
  
    
    

    create  table
      "job_lakehouse"."main"."dim_job__dbt_tmp"
  
    as (
      SELECT
    job_id,
    title,
    md5(cast(coalesce(cast(company as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) AS company_id,
    salary,
    location,
    experience
FROM "job_lakehouse"."main"."int_jobs_dedup"
    );
  
  