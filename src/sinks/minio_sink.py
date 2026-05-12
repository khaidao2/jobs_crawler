import logging
import pandas as pd
import s3fs
import time
from typing import Dict, Any

_LOGGER = logging.getLogger("minio-sink")


class MinIOSink:
    def __init__(self, bucket_name: str, minio_endpoint: str, access_key: str, secret_key: str, batch_size: int = 30):
        try:
            self.bucket_name = bucket_name
            self.minio_endpoint = minio_endpoint
            self.access_key = access_key
            self.secret = secret_key
            self.batch_size = batch_size
            self.buffer = []
            self.run_id = None
            self.timestamp = None

            # Set up s3fs
            self.s3 = s3fs.S3FileSystem(
                key=self.access_key,
                secret=self.secret,
                client_kwargs={'endpoint_url': minio_endpoint}
            )
            
            if not self.s3.exists(self.bucket_name):
                _LOGGER.info(f"Bucket '{self.bucket_name}' does not exist. Creating...")
                self.s3.mkdir(self.bucket_name)

            _LOGGER.info(f"MinIOSink ready | bucket={self.bucket_name} | batch_size={self.batch_size}")
        except Exception as e:
            _LOGGER.error(f"Creating MinIO Sink failed: {e}", exc_info=True)
            raise

    def _build_path(self, run_id: str, timestamp: float) -> str:
        try:
            import uuid
            suffix = str(uuid.uuid4())[:8]
            path = (
                f"s3://{self.bucket_name}/job_postings_raw"
                f"/batch_date={time.strftime('%Y-%m-%d', time.localtime(timestamp))}"
                f"/batch_hour={time.strftime('%H', time.localtime(timestamp))}"
                f"/batch_minute={time.strftime('%M', time.localtime(timestamp))}"
                f"/batch_second={time.strftime('%S', time.localtime(timestamp))}"
                f"/run_id={run_id}_{suffix}.parquet"
            )
            _LOGGER.debug(f"Built path: {path}")
            return path
        except Exception as e:
            _LOGGER.error(f"Failed to build path | run_id={run_id} | timestamp={timestamp} | error={e}", exc_info=True)
            raise

    def append(self, record: Dict[str, Any], run_id: str, force_write: bool = False) -> bool:
        try:
            if not self.buffer:
                self.run_id = run_id
                self.timestamp = time.time()
                _LOGGER.debug(f"Buffer initialized | run_id={run_id} | timestamp={self.timestamp}")

            self.buffer.append(record)
            _LOGGER.debug(f"Record appended | buffer_size={len(self.buffer)}/{self.batch_size}")

            if len(self.buffer) >= self.batch_size or force_write:
                reason = "batch_size_reached" if len(self.buffer) >= self.batch_size else "force_write"
                _LOGGER.info(f"Triggering flush | reason={reason} | buffer_size={len(self.buffer)}")
                self.flush()
                return True

            return False
        except Exception as e:
            _LOGGER.error(f"Failed to append record | run_id={run_id} | timestamp={self.timestamp} | error={e}", exc_info=True)
            raise

    def flush(self):
        if not self.buffer:
            _LOGGER.debug("Flush called but buffer is empty, skipping.")
            return

        file_name = None
        try:
            file_name = self._build_path(self.run_id, self.timestamp)
            _LOGGER.info(f"Flushing {len(self.buffer)} records to {file_name}")

            df = pd.DataFrame(self.buffer)
            df.to_parquet(file_name, index=False, engine='pyarrow', filesystem=self.s3)

            _LOGGER.info(f"Wrote {len(df)} records to {file_name}")
            self.buffer.clear()
            _LOGGER.debug("Buffer cleared after successful flush.")
        except Exception as e:
            _LOGGER.error(f"Failed to flush buffer | file={file_name} | records={len(self.buffer)} | error={e}", exc_info=True)
            raise