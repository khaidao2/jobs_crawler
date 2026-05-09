{{ config(materialized='view') }}

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
FROM {{ ref('stg_jobs') }}