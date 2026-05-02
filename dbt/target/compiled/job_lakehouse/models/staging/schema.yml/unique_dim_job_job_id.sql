
    
    

select
    job_id as unique_field,
    count(*) as n_records

from "job_lakehouse"."main"."dim_job"
where job_id is not null
group by job_id
having count(*) > 1


