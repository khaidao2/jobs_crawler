from confluent_kafka import Consumer
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from confluent_kafka import KafkaError
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import SerializationContext, MessageField
from src.config import KAFKA_PRODUCER_CONFIG, SCHEMA_REGISTRY_CONFIG, SCHEMA_PATH, KAFKA_TOPIC,KAFKA_BOOTSTRAP_SERVERS,SCHEMA_REGISTRY_URL

_LOGGER = logging.getLogger("kafka-consumer")

class KafkaConsumer:
    def __init__(self, topic: str, bootstrap_servers: str, schema_registry_url: str,group_id: str):
        self.topic= topic
        self.bootstrap_servers= bootstrap_servers
        self.schema_registry_url= schema_registry_url
        self.group_id= group_id
        self.consumer_config={
            'bootstrap.servers': self.bootstrap_servers,
            'group.id': self.group_id,
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False
        }
        self.consumer=Consumer(self.consumer_config)
        self.consumer.subscribe([self.topic])
        self._schema_registry=SchemaRegistryClient(SCHEMA_REGISTRY_CONFIG)
        self._deserializer=AvroDeserializer(self._schema_registry)
        self._ctx=SerializationContext(self.topic, MessageField.VALUE)
        _LOGGER.info(f"Consumer reeady | topic={self.topic}")
    def poll_messages(self, timeout: float=1.0) -> Optional[Dict[str, Any]] :
        msg=self.consumer.poll(timeout)
        if msg is None:
            return None
        if msg.error():
            if msg.error().code() != KafkaError._PARTITION_EOF:
                _LOGGER.error(f"Consumer error: {msg.error()}")
            return None
        value=self._deserializer(msg.value(), self._ctx)
        self.consumer.commit(asynchronous=True)
        return value
    def commit(self, offsets: Optional[list] = None)
        if offsets:
            self.consumer.commit(offsets=offsets)
        else:
            self.consumer.commit(asynchronous=True)
    def close(self):
        self.consumer.close()

    