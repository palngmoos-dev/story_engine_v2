import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.file']

class GoogleDriveConnector:
    def __init__(self, secrets_dir="secrets"):
        self.secrets_dir = secrets_dir
        self.creds = None
        self.service = None
        
        if not os.path.exists(self.secrets_dir):
            os.makedirs(self.secrets_dir)
            
        self.token_path = os.path.join(self.secrets_dir, 'token.pickle')
        self.creds_path = os.path.join(self.secrets_dir, 'credentials.json')
        
        self._authenticate()

    def _authenticate(self):
        """Authenticates the user using token.pickle or credentials.json."""
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                self.creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not os.path.exists(self.creds_path):
                    print(f"[GOOGLE DRIVE] Error: {self.creds_path} not found. Please provide Google API credentials.")
                    return
                
                flow = InstalledAppFlow.from_client_secrets_file(self.creds_path, SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(self.token_path, 'wb') as token:
                pickle.dump(self.creds, token)

        if self.creds:
            self.service = build('drive', 'v3', credentials=self.creds)

    def upload_file(self, local_path, folder_id=None):
        """Uploads a file to Google Drive."""
        if not self.service:
            print("[GOOGLE DRIVE] Service not initialized. Skipping upload.")
            return None

        file_metadata = {'name': os.path.basename(local_path)}
        if folder_id:
            file_metadata['parents'] = [folder_id]
            
        media = MediaFileUpload(local_path, resumable=True)
        try:
            file = self.service.files().create(body=file_metadata,
                                                media_body=media,
                                                fields='id').execute()
            print(f'[GOOGLE DRIVE] File ID: {file.get("id")} uploaded.')
            return file.get('id')
        except Exception as e:
            print(f"[GOOGLE DRIVE] Upload failed: {e}")
            return None

    def backup_project(self, project_id: str, encrypted_blob: str):
        """Simulates or performs backup of the state. (Refined V2)"""
        # For now, we still save locally but try to sync if service is available
        temp_path = f"backups/{project_id}_state.json"
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(encrypted_blob)
        
        if self.service:
            self.upload_file(temp_path)
            print(f"[GOOGLE DRIVE] Syncing {project_id} to cloud...")

# Singleton instance
gdrive = GoogleDriveConnector()
