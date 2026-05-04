{{ config(materialized='incremental') }}

SELECT
    job_id,
    {{ dbt_utils.generate_surrogate_key(['company']) }} AS company_id,
    crawled_at
FROM {{ ref('int_jobs_dedup') }}

{% if is_incremental() %}
  WHERE crawled_at > (SELECT MAX(crawled_at) FROM {{ this }})
{% endif %}