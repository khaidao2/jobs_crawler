-- ==================================================
-- PostgreSQL init script
-- Chạy tự động khi container Postgres khởi động lần đầu
-- jobs_dwh đã được tạo tự động qua POSTGRES_DB env
-- ==================================================

-- DB cho Apicurio Schema Registry
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'registry') THEN
      CREATE DATABASE registry;
   END IF;
END $$;

-- DB cho Airflow metadata
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow_metadata') THEN
      CREATE DATABASE airflow_metadata;
   END IF;
END $$;