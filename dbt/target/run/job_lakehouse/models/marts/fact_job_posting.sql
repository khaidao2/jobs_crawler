
  
  create view "job_lakehouse"."main"."fact_job_posting__dbt_tmp" as (
    

SELECT
    job_id,
    company,
    salary_min,
    salary_max,
    deal_salary,
    experience_min,
    experience_max,
    experience_not_mentioned,
    crawled_at
FROM "job_lakehouse"."main"."stg_jobs"
  );
