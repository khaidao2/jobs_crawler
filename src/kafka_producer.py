"""
Kafka Producer Base
- Registers AVRO schemas with Apicurio (Confluent-compatible API)
- Serializes messages using AvroSerializer
- Publishes messages to a Kafka topic
"""
 
import json
import os
import time
import uuid
import logging
from typing import Optional
from pathlib import Path

 
import requests
from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient, Schema
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import SerializationContext, MessageField

from config import KAFKA_PRODUCER_CONFIG, SCHEMA_REGISTRY_CONFIG, SCHEMA_PATH, KAFKA_TOPIC,KAFKA_BOOTSTRAP_SERVERS,SCHEMA_REGISTRY_URL

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
_logger = logging.getLogger("kafka-producer")

class KafkaProducer:
    def __init__(self, topic: str, schema_path: Path):
        try:
            self._topic = topic

            with open(schema_path) as f:
                schema_str = f.read()
            sr_client = SchemaRegistryClient(SCHEMA_REGISTRY_CONFIG)
            self._serializer = AvroSerializer(
                sr_client,
                Schema(schema_str, schema_type="AVRO")
            )
            self._producer = Producer(KAFKA_PRODUCER_CONFIG)

            _logger.info("Producer ready | topic=%s", topic)           
        except Exception as e:
            _logger.exception("Failed to initialize KafkaProducer: %s", topic, schema_path, str(e))
            raise
    def _on_delivery(self, err, msg):
        if err:
            _logger.error("Delivery failed: %s", err)
        else:
            _logger.debug(
                "Delivered | partition=%s offset=%s",
                msg.partition(), msg.offset()
            )
    def send(self, record: dict, key: str | None = None):
        ctx= SerializationContext(self._topic, MessageField.VALUE)
        value    = self._serializer(record, ctx)
        msg_key  = (key or str(uuid.uuid4())).encode()

        self._producer.produce(
            topic       = self._topic,
            key         = msg_key,
            value       = value,
            on_delivery = self._on_delivery,
        )
        self._producer.poll(0)
    def flush(self, timeout: float = 30.0):
        remaining = self._producer.flush(timeout)
        if remaining > 0:
            _logger.warning("%d messages not delivered", remaining)
 
    def close(self):
        self.flush()
        _logger.info("Producer closed")
 
    def __enter__(self):
        return self
 
    def __exit__(self, *_):
        self.close()