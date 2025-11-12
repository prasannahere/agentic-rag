import time
from pathlib import Path

class SharePointWatcher:
    def __init__(self, sp_api, tracker, processor, download_dir: Path, poll_interval: int = 5):
        self.sp_api = sp_api
        self.tracker = tracker
        self.processor = processor
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        self.poll_interval = poll_interval

    def run(self):
        print("[Watcher] Monitoring SharePoint library...")
        while True:
            try:
                files = self.sp_api.list_files()
                for item in files:
                    file_name = item.get("FileLeafRef")
                    file_url = item.get("FileRef")
                    if not file_name or not file_url:
                        continue

                    if not self.tracker.has_seen(file_url):
                        try:
                            local_path = self.download_dir / file_name
                            self.sp_api.download_file(file_url, str(local_path))
                            self.processor.process_file(local_path)
                            self.tracker.mark_seen(file_url, file_name)
                        except Exception as e:
                            print(f"[Watcher] Failed {file_name}: {e}")
                            self.tracker.mark_seen(file_url, file_name)

                time.sleep(self.poll_interval)
            except Exception as e:
                print(f"[Watcher] Fatal loop error: {e}")
                time.sleep(self.poll_interval)
