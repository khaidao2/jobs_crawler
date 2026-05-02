
  
  create view "job_lakehouse"."main"."int_jobs_dedup__dbt_tmp" as (
    WITH staging AS (
    SELECT * FROM "job_lakehouse"."main"."stg_jobs"
),

ranked_jobs AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY job_id 
            ORDER BY crawled_at DESC
        ) AS rn
    FROM staging
)

SELECT *
FROM ranked_jobs
WHERE rn = 1
  );
