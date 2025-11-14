import json
from pathlib import Path

from agentic_rag.domain.utils import PathConfig
from .azure_blob_api import AzureBlobAPI
from .azure_blob_watcher import AzureBlobWatcher
from .file_tracker import FileTracker
from .processor import Processor

# Use PathConfig to get project root
BASE_DIR = PathConfig.PROJECT_ROOT
CONFIG_PATH = PathConfig.BLOB_CONFIG

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

api = AzureBlobAPI(
    storage_account_name=config["storage_account_name"],
    storage_access_key=config["storage_access_key"],
    container_name=config["container_name"]
)

tracker = FileTracker(BASE_DIR / config["seen_files_path"])
processor = Processor()

watcher = AzureBlobWatcher(
    api,
    tracker,
    processor,
    prefix=config.get("prefix", ""),
    download_dir=BASE_DIR / config["download_dir"],
    poll_interval=config.get("poll_interval", 5)
)

if __name__ == "__main__":
    watcher.run()
