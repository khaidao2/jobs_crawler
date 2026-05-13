

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
WHERE job_id IS NOT NULL