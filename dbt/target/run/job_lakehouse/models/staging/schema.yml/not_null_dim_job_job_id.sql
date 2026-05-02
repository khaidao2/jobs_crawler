select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select job_id
from "job_lakehouse"."main"."dim_job"
where job_id is null



      
    ) dbt_internal_test