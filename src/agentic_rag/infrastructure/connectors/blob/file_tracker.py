import json
from pathlib import Path
from datetime import datetime

class FileTracker:
    def __init__(self, storage_file: Path):
        self.storage_file = storage_file
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        self.seen_files = self._load_seen_files()

    def _load_seen_files(self):
        if self.storage_file.exists():
            try:
                with open(self.storage_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def mark_seen(self, file_id: str, file_name: str = None, modified_time: str = None):
        """Mark file as seen with optional name and last modified time."""
        if file_name or modified_time:
            self.seen_files[file_id] = {
                "file_name": file_name,
                "modified_time": modified_time,
                "seen_at": datetime.now().isoformat()
            }
        else:
            # Simple tracking for blob storage (etag only)
            self.seen_files[file_id] = {"seen_at": datetime.now().isoformat()}
        self._save_seen_files()

    def has_seen(self, file_id: str, modified_time: str = None):
        """Return True if file_id is seen and modified time hasn't changed (if provided)."""
        info = self.seen_files.get(file_id)
        if info is None:
            return False
        if modified_time is not None:
            return info.get("modified_time") == modified_time
        return True

    def _save_seen_files(self):
        with open(self.storage_file, 'w') as f:
            json.dump(self.seen_files, f, indent=2)
