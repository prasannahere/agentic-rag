from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.service_account import Credentials
from pathlib import Path
import io

class DriveAPI:
    def __init__(self, service_account_file: str, scopes: list):
        credentials = Credentials.from_service_account_file(
            service_account_file, scopes=scopes
        )
        self.service = build('drive', 'v3', credentials=credentials)

    def list_files(self, folder_id: str, page_size: int = 1000):
        response = self.service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="files(id, name, mimeType, modifiedTime)",
            pageSize=page_size
        ).execute()
        return response.get('files', [])

    def download_file(self, file_id: str, file_path: Path):
        request = self.service.files().get_media(fileId=file_id)
        with io.FileIO(file_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
        return file_path