"""
Function: Main entrypoint for running the Kafka consumer and MinIO sink.
"""
import signal
import sys
import logging
import uuid
from src.config import (
    KAFKA_TOPIC, 
    KAFKA_BOOTSTRAP_SERVERS, 
    SCHEMA_REGISTRY_URL,
    MINIO_ENDPOINT,
    MINIO_ACCESS_KEY,
    MINIO_SECRET_KEY,
    MINIO_BUCKET_NAME
)
from src.kafka_consumer import KafkaConsumer
from src.crawlers.receive_sink.minio_sink import MinIOSink

# Setup logging for easy monitoring
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
_logger = logging.getLogger("run-consumer")

# Loop control flag
_running = True

def _shutdown(signum, _frame):
    global _running
    _logger.info(f"Received stop signal ({signum}), shutting down service safely...")
    _running = False

# Catch OS signals
signal.signal(signal.SIGINT, _shutdown)
signal.signal(signal.SIGTERM, _shutdown)

def main():
    _logger.info("Starting Kafka Consumer Service...")
    
    # 1. Initialize Kafka Consumer
    consumer_client = KafkaConsumer(
        topic=KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        schema_registry_url=SCHEMA_REGISTRY_URL,
        group_id="job-lakehouse-ingestion-group"
    )
    
    # 2. Initialize MinIO Sink
    minio_sink = MinIOSink(
        bucket_name=MINIO_BUCKET_NAME, 
        minio_endpoint=MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        batch_size=1  # Flush to file every record for testing
    )

    # 3. Generate a run ID for the sink to group batches
    current_run_id = str(uuid.uuid4())[:8]

    try:
        while _running:
            # Poll data from Kafka
            record = consumer_client.poll_messages(timeout=1.0)
            
            if record:
                # Append data to MinIO Sink
                batch_flushed = minio_sink.append(record, run_id=current_run_id)
                
                # If the sink flushed the batch to MinIO successfully
                if batch_flushed:
                    # Commit the offset to Kafka
                    consumer_client.commit()
                    _logger.info("Successfully committed batch offset to Kafka.")

    except KeyboardInterrupt:
        pass
    except Exception as e:
        _logger.error(f"Service encountered a critical error: {e}")
    finally:
        _logger.info("Cleaning up and closing connections...")
        
        # Flush remaining records if any
        if len(minio_sink.buffer) > 0:
            minio_sink.flush()
            consumer_client.commit()
            
        consumer_client.close()
        _logger.info("Service stopped completely.")

if __name__ == "__main__":
    main()
