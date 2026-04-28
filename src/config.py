"""
config.py
Centralized configuration for Kafka Producer and Schema Registry
"""
import os

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC             = os.getenv("KAFKA_TOPIC", "job-listings")

KAFKA_PRODUCER_CONFIG = {
    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
    "client.id":         "job-crawler-producer",
    "acks":              "all",
    "retries":           3,
    "retry.backoff.ms":  500,
    "linger.ms":         10,
    "batch.size":        16384,
}

SCHEMA_REGISTRY_URL = os.getenv(
    "SCHEMA_REGISTRY_URL",
    "http://localhost:8085/apis/ccompat/v6"
)

SCHEMA_REGISTRY_CONFIG = {
    "url": SCHEMA_REGISTRY_URL,
}

SCHEMA_PATH = os.getenv("SCHEMA_PATH", "schemas/raw/job_listing.avsc")

KAFKA_TOPIC="Jobs"