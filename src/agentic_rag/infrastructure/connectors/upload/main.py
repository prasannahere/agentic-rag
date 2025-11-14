import json
from pathlib import Path

from agentic_rag.domain.utils import PathConfig
from azure.storage.blob import BlobServiceClient

# Use PathConfig to get project root
BASE_DIR = PathConfig.PROJECT_ROOT
CONFIG_PATH = PathConfig.CONFIG_DIR / "blob-config.json"

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

class UploadConnector:
    def __init__(self, connection_string: str = None, container_name: str = None):
        connection_string = connection_string or config["connection_string"]
        container_name = container_name or config["container_name"]
        
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_client = self.blob_service_client.get_container_client(container_name)

        # Ensure container exists
        try:
            self.container_client.create_container()
        except Exception:
            pass  # Container already exists

    def upload_file(self, file_name: str, file_content):
        """
        Uploads a file to Azure Blob Storage.
        :param file_name: Name of the file in blob storage
        :param file_content: File-like object or bytes
        """
        blob_client = self.container_client.get_blob_client(file_name)
        blob_client.upload_blob(file_content, overwrite=True)

        return f"File '{file_name}' uploaded successfully."
