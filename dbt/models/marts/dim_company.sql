SELECT DISTINCT
    MD5(COALESCE(company, 'unknown'))::VARCHAR AS company_id,
    COALESCE(company, 'Unknown')::VARCHAR AS company_name
FROM {{ ref('int_jobs_dedup') }}