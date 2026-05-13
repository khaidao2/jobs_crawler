{{ config(materialized='view') }}

SELECT * FROM {{ ref('int_jobs_dedup') }}