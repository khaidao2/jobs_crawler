select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select crawled_at
from "job_lakehouse"."main"."stg_jobs"
where crawled_at is null



      
    ) dbt_internal_test