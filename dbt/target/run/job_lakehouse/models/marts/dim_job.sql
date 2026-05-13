
  
  create view "job_lakehouse"."main"."dim_job__dbt_tmp" as (
    

SELECT * FROM "job_lakehouse"."main"."int_jobs_dedup"
  );
