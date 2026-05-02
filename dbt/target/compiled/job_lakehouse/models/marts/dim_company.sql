SELECT DISTINCT
    md5(cast(coalesce(cast(company as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) AS company_id,
    company AS company_name
FROM "job_lakehouse"."main"."int_jobs_dedup"