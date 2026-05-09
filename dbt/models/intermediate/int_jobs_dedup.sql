WITH staging AS (
    SELECT
        job_id::VARCHAR AS job_id,
        title::VARCHAR AS title,
        company::VARCHAR AS company,
        source::VARCHAR AS source,
        url::VARCHAR AS url,
        company_url::VARCHAR AS company_url,
        logo_url::VARCHAR AS logo_url,
        salary::VARCHAR AS salary,
        location::VARCHAR AS location,
        experience::VARCHAR AS experience,
        tags,
        working_times,
        is_urgent::BOOLEAN AS is_urgent,
        is_highlight::BOOLEAN AS is_highlight,
        is_flash::BOOLEAN AS is_flash,
        company_verified::BOOLEAN AS company_verified,
        job_description::VARCHAR AS job_description,
        job_requirement::VARCHAR AS job_requirement,
        job_benefit::VARCHAR AS job_benefit,
        updated_at::TIMESTAMP AS updated_at,
        posted_at::TIMESTAMP AS posted_at,
        deadline::TIMESTAMP AS deadline,
        crawled_at::BIGINT AS crawled_at
    FROM {{ ref('stg_jobs') }}
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

SELECT job_id, title, company, source, url, company_url, logo_url,
       salary, location, experience, tags, working_times,
       is_urgent, is_highlight, is_flash, company_verified,
       job_description, job_requirement, job_benefit,
       updated_at, posted_at, deadline, crawled_at
FROM ranked_jobs
WHERE rn = 1