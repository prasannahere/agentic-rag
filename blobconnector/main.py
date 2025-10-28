from pathlib import Path
from azure.storage.blob import BlobServiceClient
import sys

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import PathConfig

# Support both direct execution and module import
try:
    from .azure_blob_api import AzureBlobAPI
    from .azure_blob_watcher import AzureBlobWatcher
    from .file_tracker import FileTracker
    from .processor import Processor
except ImportError:
    from blobconnector.azure_blob_api import AzureBlobAPI
    from blobconnector.azure_blob_watcher import AzureBlobWatcher
    from blobconnector.file_tracker import FileTracker
    from blobconnector.processor import Processor

# ==== Replace with your details ====
STORAGE_ACCOUNT_NAME = "nttdatahugo---"
STORAGE_ACCESS_KEY = "longlongkey"  # a.k.a primary admin key
CONTAINER_NAME = "hugossssop"

# ...s
DOWNLOAD_DIR = PathConfig.BLOB_DOWNLOADED_FILES
# ===================================

# Init API
api = AzureBlobAPI(STORAGE_ACCOUNT_NAME, STORAGE_ACCESS_KEY, CONTAINER_NAME)

# Optional: list containers for sanity check
service = BlobServiceClient(
    account_url=f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net",
    credential=STORAGE_ACCESS_KEY
)
print("Available containers:")
for container in service.list_containers():
    print("-", container["name"])


# Setup configuration paths
TRACKER_FILE = PathConfig.BLOB_SEEN_FILES
TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Initialize tracker and processor
tracker = FileTracker(TRACKER_FILE)
processor = Processor()

# Run watcher (continuously downloads new/changed blobs)
watcher = AzureBlobWatcher(
    api,
    tracker,
    processor,
    prefix="",  # optional blob folder filter
    download_dir=DOWNLOAD_DIR,
    poll_interval=5
)

watcher.run()
