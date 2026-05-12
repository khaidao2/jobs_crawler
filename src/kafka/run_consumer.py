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
from src.kafka.kafka_consumer import KafkaConsumer
from src.sinks.minio_sink import MinIOSink

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
        batch_size=500  # Increased for production speed
    )

    # 3. Generate a run ID for the sink to group batches
    current_run_id = str(uuid.uuid4())[:8]

    import time
    last_flush_time = time.time()

    try:
        while _running:
            # Poll data from Kafka
            record = consumer_client.poll_messages(timeout=1.0)
            
            if record:
                try:
                    # Append data to MinIO Sink
                    batch_flushed = minio_sink.append(record, run_id=current_run_id)
                    
                    # If the sink flushed the batch to MinIO successfully
                    if batch_flushed:
                        # Commit the offset to Kafka only after successful flush
                        consumer_client.commit()
                        _logger.info("Successfully committed batch offset to Kafka.")
                        last_flush_time = time.time()
                    else:
                        # Record added to buffer but not flushed yet - don't commit
                        pass
                except Exception as rec_err:
                    _logger.error(f"Error processing record from Kafka: {rec_err}. Skipping to next...")
                    continue
            else:
                # Idle time check: if buffer has data and hasn't been flushed for 30s
                if len(minio_sink.buffer) > 0 and (time.time() - last_flush_time > 30):
                    _logger.info(f"Idle timeout reached ({len(minio_sink.buffer)} records). Flushing...")
                    minio_sink.flush()
                    consumer_client.commit()
                    last_flush_time = time.time()

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
