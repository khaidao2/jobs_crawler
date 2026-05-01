SELECT
    job_id,
    title,
    {{ dbt_utils.generate_surrogate_key(['company']) }} AS company_id,
    salary,
    location,
    experience
FROM {{ ref('int_jobs_dedup') }}