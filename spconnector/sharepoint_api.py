import requests
from pathlib import Path


class SharePointAPI:
    def __init__(self, client_id: str, client_secret: str, tenant: str, realm: str, site_url: str, library_name: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant = tenant
        self.realm = realm
        self.site_url = site_url
        self.library_name = library_name
        self.access_token = self._get_access_token()

    def _get_access_token(self) -> str:
        """Obtain an OAuth access token for SharePoint."""
        token_url = f"https://accounts.accesscontrol.windows.net/{self.realm}/tokens/OAuth/2"

        payload = {
            'grant_type': 'client_credentials',
            'client_id': f'{self.client_id}@{self.realm}',
            'client_secret': self.client_secret,
            'resource': f'00000003-0000-0ff1-ce00-000000000000/{self.tenant}.sharepoint.com@{self.realm}'
        }

        response = requests.post(token_url, data=payload)
        response.raise_for_status()

        token_json = response.json()
        token = token_json.get('access_token')

        if not token:
            raise Exception("Failed to obtain access token")

        return token

    def _headers(self):
        """Return authorization headers."""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json;odata=verbose'
        }

    def list_files(self):
        """List files from the given SharePoint document library."""
        url = f"{self.site_url}/_api/web/lists/GetByTitle('{self.library_name}')/items?$select=FileLeafRef,FileRef,Modified"
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()
        return response.json()['d']['results']

    def download_file(self, file_url: str, file_path: Path):
        """Download a file from SharePoint by its relative URL."""
        download_url = f"{self.site_url}/_api/web/getfilebyserverrelativeurl('{file_url}')/$value"
        response = requests.get(download_url, headers=self._headers(), stream=True)
        response.raise_for_status()

        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return file_path
