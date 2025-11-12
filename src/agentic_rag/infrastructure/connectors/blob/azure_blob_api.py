from azure.storage.blob import BlobServiceClient
from pathlib import Path

class AzureBlobAPI:
    def __init__(self, storage_account_name: str, storage_access_key: str, container_name: str):
        """Initialize Blob API with account credentials."""
        blob_url = f"https://{storage_account_name}.blob.core.windows.net"
        self.blob_service_client = BlobServiceClient(
            account_url=blob_url,
            credential=storage_access_key
        )
        self.container_client = self.blob_service_client.get_container_client(container_name)

    def list_files(self, prefix: str = ""):
        """List all blobs in the container (optionally filtered by prefix)."""
        return list(self.container_client.list_blobs(name_starts_with=prefix))

    def download_file(self, blob_name: str, local_path: Path):
        """Download a blob to a local path, preserving folder structure."""
        local_path.parent.mkdir(parents=True, exist_ok=True)
        with open(local_path, "wb") as f:
            stream = self.container_client.download_blob(blob_name)
            f.write(stream.readall())
        return local_path
