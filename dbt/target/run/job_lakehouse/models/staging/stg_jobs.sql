
  
  create view "job_lakehouse"."main"."stg_jobs__dbt_tmp" as (
    WITH raw_data AS (
    SELECT *
    FROM read_parquet('s3://job-postings-raw/job_postings_raw/**/*.parquet', union_by_name=True)
)

SELECT
    -- core
    job_id::VARCHAR                         AS job_id,
    title::VARCHAR                          AS title,
    company::VARCHAR                        AS company,
    source::VARCHAR                         AS source,

    -- urls
    url::VARCHAR                            AS url,
    company_url::VARCHAR                    AS company_url,
    logo_url::VARCHAR                       AS logo_url,

    -- job info
    salary::VARCHAR                         AS salary,
    location::VARCHAR                       AS location,
    experience::VARCHAR                     AS experience,

    -- arrays (giữ nguyên hoặc convert tùy engine)
    tags                                    AS tags,
    working_times                           AS working_times,

    -- flags
    is_urgent::BOOLEAN                      AS is_urgent,
    is_highlight::BOOLEAN                   AS is_highlight,
    is_flash::BOOLEAN                       AS is_flash,
    company_verified::BOOLEAN               AS company_verified,

    -- content
    job_description::VARCHAR                AS job_description,
    job_requirement::VARCHAR                AS job_requirement,
    job_benefit::VARCHAR                    AS job_benefit,

    -- time (parse từ string/long → timestamp)
    TRY_CAST(updated_at AS TIMESTAMP)       AS updated_at,
    TRY_CAST(posted_at AS TIMESTAMP)        AS posted_at,
    TRY_CAST(deadline AS TIMESTAMP)         AS deadline,
    to_timestamp(COALESCE(raw_data.crawled_at, 0)) AS crawled_at

FROM raw_data
  );
