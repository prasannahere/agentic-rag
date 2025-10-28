import json
from pathlib import Path

class FileTracker:
    def __init__(self, storage_file: Path):
        self.storage_file = storage_file
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        self.seen_files = self._load_seen_files()

    def _load_seen_files(self):
        if self.storage_file.exists():
            try:
                with open(self.storage_file, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def mark_seen(self, file_url: str, file_name: str):
        self.seen_files[file_url] = {"file_name": file_name}
        self._save()

    def has_seen(self, file_url: str) -> bool:
        return file_url in self.seen_files

    def _save(self):
        with open(self.storage_file, "w") as f:
            json.dump(self.seen_files, f, indent=2)
