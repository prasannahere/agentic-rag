import time
from pathlib import Path

class DriveWatcher:
    def __init__(self, drive_api, tracker, processor, folder_id, download_dir: Path, poll_interval: int = 2):
        self.drive_api = drive_api
        self.tracker = tracker
        self.processor = processor
        self.folder_id = folder_id
        self.download_dir = download_dir
        self.download_dir.mkdir(exist_ok=True)
        self.poll_interval = poll_interval

    def run(self):
        print("[Watcher] Started monitoring Google Drive folder...")
        while True:
            try:
                files = self.drive_api.list_files(self.folder_id)
                for file in files:
                    file_id = file['id']
                    file_name = file['name']
                    modified_time = file.get('modifiedTime')

                    if file.get('mimeType') == 'application/vnd.google-apps.folder':
                        continue  # Skip subfolders

                    if not self.tracker.has_seen(file_id, modified_time):
                        local_path = self.download_dir / file_name
                        try:
                            self.drive_api.download_file(file_id, local_path)
                            self.processor.process_file(local_path)
                            self.tracker.mark_seen(file_id, file_name, modified_time)
                        except Exception as e:
                            print(f"[Watcher] Skipping {file_name} due to error \n")
                            self.tracker.mark_seen(file_id, file_name, modified_time)

                time.sleep(self.poll_interval)
            except Exception as e:
                print(f"[Watcher] Fatal error in loop: {e}")
                time.sleep(self.poll_interval)
