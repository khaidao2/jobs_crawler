SELECT DISTINCT
    {{ dbt_utils.generate_surrogate_key(['company']) }} AS company_id,
    company AS company_name
FROM {{ ref('int_jobs_dedup') }}