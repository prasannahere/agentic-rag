import json
from pathlib import Path

# Support both direct execution and module import
try:
    from .sharepoint_api import SharePointAPI
    from .file_tracker import FileTracker
    from .sharepoint_watcher import SharePointWatcher
    from .processor import Processor
except ImportError:
    from spconnector.sharepoint_api import SharePointAPI
    from spconnector.file_tracker import FileTracker
    from spconnector.sharepoint_watcher import SharePointWatcher
    from spconnector.processor import Processor
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "sp-config.json"

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