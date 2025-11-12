import json
from pathlib import Path

from agentic_rag.domain.utils import PathConfig
from .drive_api import DriveAPI
from .file_tracker import FileTracker
from .drive_watcher import DriveWatcher
from .processor import Processor

# Use PathConfig to get project root
BASE_DIR = PathConfig.PROJECT_ROOT
CONFIG_PATH = BASE_DIR / "config" / "config.json"

# Load config
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

# 🔑 Always resolve paths relative to BASE_DIR
service_account_file = BASE_DIR / config["service_account_file"]
seen_files_path = BASE_DIR / config["seen_files_path"]
download_dir = BASE_DIR / config["download_dir"]

drive_api = DriveAPI(str(service_account_file), config["scopes"])
tracker = FileTracker(seen_files_path)
processor = Processor()

folder_id = config["folder_id_to_watch"]
poll_interval = config.get("poll_interval", 2)

watcher = DriveWatcher(drive_api, tracker, processor, folder_id, download_dir, poll_interval)
#watcher.run()
