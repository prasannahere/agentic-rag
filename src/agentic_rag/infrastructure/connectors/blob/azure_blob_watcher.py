import time
from pathlib import Path

class AzureBlobWatcher:
    def __init__(self, api, tracker, processor, prefix: str, download_dir: Path, poll_interval: int = 5):
        self.api = api
        self.tracker = tracker
        self.processor = processor
        self.prefix = prefix
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        self.poll_interval = poll_interval

    def run(self):
        print("[Watcher] Monitoring Azure Blob Storage...")
        while True:
            try:
                blobs = self.api.list_files(self.prefix)
                for blob in blobs:
                    blob_name = blob.name
                    blob_id = blob.etag  # unique ID for blob version
                    local_path = self.download_dir / blob_name  # preserve folder structure

                    if not self.tracker.has_seen(blob_id):
                        try:
                            self.api.download_file(blob_name, local_path)
                            self.processor.process_file(local_path)
                            self.tracker.mark_seen(blob_id)
                            print(f"[Watcher] Downloaded + processed {blob_name}")
                        except Exception as e:
                            print(f"[Watcher] Failed {blob_name}: {e}")
                            self.tracker.mark_seen(blob_id)

                time.sleep(self.poll_interval)
            except Exception as e:
                print(f"[Watcher] Fatal loop error: {e}")
                time.sleep(self.poll_interval)
