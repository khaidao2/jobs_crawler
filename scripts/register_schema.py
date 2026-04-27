from pathlib import Path
from typing import Dict
from confluent_kafka import Producer
from confluent_kafka.serialization import StringSerializer, SerializationContext, MessageField
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer


BOOTSTRAP_SERVERS = "localhost:9092"
SCHEMA_REGISTRY_URL = "http://localhost:8085/ccompat"

SCHEMA_DIR = Path(__file__).parent.parent / "schemas/raw"


# ---------------------------
# Load schemas
# ---------------------------
def load_schemas(schema_dir: Path) -> Dict[str, str]:
    schemas = {}

    for file in schema_dir.glob("*.avsc"):
        # Map filenames to topics
        if file.stem == "topcv_job":
            topic = "jobs.raw.topcv"
        else:
            topic = file.stem.replace("_", ".") # fallback

        with open(file) as f:
            schemas[topic] = f.read()

    if not schemas:
        raise ValueError(f"No schema found in {schema_dir}")

    return schemas


# ---------------------------
# Build serializers
# ---------------------------
def build_serializers(schema_registry_client, schemas: Dict[str, str]):
    serializers = {}

    for topic, schema_str in schemas.items():
        serializers[topic] = AvroSerializer(
            schema_registry_client,
            schema_str
        )

    return serializers


# ---------------------------
# Producer class
# ---------------------------
class KafkaAvroProducer:
    def __init__(self):
        # Schema Registry
        self.schema_registry_client = SchemaRegistryClient({
            "url": SCHEMA_REGISTRY_URL
        })

        # Load schemas
        self.schemas = load_schemas(SCHEMA_DIR)

        # Serializers
        self.serializers = build_serializers(
            self.schema_registry_client,
            self.schemas
        )
        
        self.key_serializer = StringSerializer("utf_8")

        # Kafka producer (base Producer)
        self.producer = Producer({
            "bootstrap.servers": BOOTSTRAP_SERVERS
        })

    def produce(self, topic: str, key: str, value: dict):
        serializer = self.serializers.get(topic)

        if not serializer:
            raise ValueError(f"No schema found for topic: {topic}")

        # Manual serialization
        ctx = SerializationContext(topic, MessageField.VALUE)
        serialized_key = self.key_serializer(key, SerializationContext(topic, MessageField.KEY))
        serialized_value = serializer(value, ctx)

        self.producer.produce(
            topic=topic,
            key=serialized_key,
            value=serialized_value
        )

        self.producer.poll(0)

    def flush(self):
        self.producer.flush()


# ---------------------------
# Test
# ---------------------------
if __name__ == "__main__":
    producer = KafkaAvroProducer()

    producer.produce(
        topic="jobs.raw.topcv",
        key="job-1",
        value={
            "job_id": "1",
            "title": "Data Engineer",
            "company": "ABC",
            "salary": "Negotiable",
            "location": "HCM",
            "posted_at": "2026-04-21",
            "url": "https://example.com",
            "company_url": None,
            "logo_url": None,
            "experience": "2 years",
            "tags": ["python", "kafka"],
            "updated_at": None,
            "is_urgent": False,
            "is_highlight": False,
            "is_flash": False,
            "company_verified": True,
            "category": "it",
            "page_number": 1,
            "crawled_at": 1713715200,
            "job_description": None,
            "job_requirement": None,
            "job_benefit": None,
            "deadline": None,
            "working_times": []
        }
    )

    producer.flush()