
    
    

select
    company_id as unique_field,
    count(*) as n_records

from "job_lakehouse"."main"."dim_company"
where company_id is not null
group by company_id
having count(*) > 1


