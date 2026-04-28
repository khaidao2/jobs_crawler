
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import threading
import logging
from typing import Any, Dict

from kafka_producer import KafkaProducer
_LOG = logging.getLogger(__name__)

class KafkaSink:
    def __init__(self, topic: str, schema_path: str) -> None:
        try:
            self.topic = topic
            self.producer = KafkaProducer(topic, schema_path)
            self._lock = threading.Lock()
        except Exception as e:
            _LOG.error(f"Failed to initialize KafkaSink: {e}")
            raise e
    
    def emit(self, record: Dict[str, Any], key:str) -> None:
        try:
            message_key=key or record.get("job_id")
            with self._lock:
                self.producer.send(record=record, key=message_key)
        except Exception as e:
            _LOG.error(f"Failed to emit record: {e}")
            raise e
    
    def flush(self, timeout: float = 30.0) -> None:
        try:
            with self._lock:
                self.producer.flush(timeout)
        except Exception as e:
            _LOG.error(f"Failed to flush: {e}")
            raise e

    def close(self) -> None:
        try:
            with self._lock:
                self.producer.close()
        except Exception as e:
            _LOG.error(f"Failed to close: {e}")
            raise e
