

SELECT
    job_id,
    md5(cast(coalesce(cast(company as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) AS company_id,
    crawled_at
FROM "job_lakehouse"."main"."int_jobs_dedup"


  -- Chỉ lấy những job được cào sau thời điểm mới nhất hiện có trong bảng Fact
  WHERE crawled_at > (SELECT MAX(crawled_at) FROM "job_lakehouse"."main"."fact_job_posting")
