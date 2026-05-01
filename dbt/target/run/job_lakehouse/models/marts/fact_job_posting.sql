

    insert into "job_lakehouse"."main"."fact_job_posting" ("job_id", "company_id", "crawled_at")
    (
        select "job_id", "company_id", "crawled_at"
        from "fact_job_posting__dbt_tmp20260501050445132059"
    )
  