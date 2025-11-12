import json
from pathlib import Path

from agentic_rag.domain.utils import PathConfig
from .sharepoint_api import SharePointAPI
from .file_tracker import FileTracker
from .sharepoint_watcher import SharePointWatcher
from .processor import Processor

# Use PathConfig to get project root
BASE_DIR = PathConfig.PROJECT_ROOT
CONFIG_PATH = PathConfig.SP_CONFIG

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

sp_api = SharePointAPI(
    client_id=config["client_id"],
    client_secret=config["client_secret"],
    tenant=config["tenant"],
    realm=config["realm"],
    site_url=config["site_url"],
    library_name=config["library_name"]
)

tracker = FileTracker(BASE_DIR / config["seen_files_path"])
processor = Processor()

watcher = SharePointWatcher(
    sp_api,
    tracker,
    processor,
    BASE_DIR / config["download_dir"],
    config.get("poll_interval", 10)
)

if __name__=="__main__":

    watcher.run()