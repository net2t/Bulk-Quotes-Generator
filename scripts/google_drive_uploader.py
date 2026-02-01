#!/usr/bin/env python3
"""
Google Drive Uploader
Uploads images to Google Drive and returns shareable links
"""

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from pathlib import Path

class DriveUploader:
    def __init__(self, credentials_path="credentials.json"):
        """Initialize with Google credentials"""
        self.credentials_path = credentials_path
        self.service = None
        self.root_folder_id = None
        
    def connect(self):
        """Connect to Google Drive API"""
        try:
            scopes = ['https://www.googleapis.com/auth/drive.file']
            creds = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=scopes
            )
            self.service = build('drive', 'v3', credentials=creds)
            return True
        except Exception as e:
            print(f"Error connecting to Google Drive: {e}")
            return False
    
    def create_folder(self, folder_name, parent_id=None):
        """Create a folder in Drive"""
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_id:
                file_metadata['parents'] = [parent_id]
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            return folder.get('id')
            
        except Exception as e:
            print(f"Error creating folder: {e}")
            return None
    
    def find_folder(self, folder_name, parent_id=None):
        """Find a folder by name"""
        try:
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            if parent_id:
                query += f" and '{parent_id}' in parents"
            
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            items = results.get('files', [])
            if items:
                return items[0]['id']
            return None
            
        except Exception as e:
            print(f"Error finding folder: {e}")
            return None
    
    def get_or_create_folder(self, folder_name, parent_id=None):
        """Get existing folder or create new one"""
        folder_id = self.find_folder(folder_name, parent_id)
        if folder_id:
            return folder_id
        return self.create_folder(folder_name, parent_id)
    
    def upload_image(self, image_path, topic=None):
        """Upload an image to Drive"""
        if not self.service:
            if not self.connect():
                return None
        
        try:
            # Ensure root folder exists
            if not self.root_folder_id:
                self.root_folder_id = self.get_or_create_folder("Quote Images")
            
            # Create topic folder if specified
            parent_id = self.root_folder_id
            if topic:
                parent_id = self.get_or_create_folder(topic, self.root_folder_id)
            
            # Upload file
            image_path = Path(image_path)
            file_metadata = {
                'name': image_path.name,
                'parents': [parent_id]
            }
            
            media = MediaFileUpload(
                str(image_path),
                mimetype='image/png',
                resumable=True
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink, webContentLink'
            ).execute()
            
            # Make file publicly accessible
            self.service.permissions().create(
                fileId=file.get('id'),
                body={'type': 'anyone', 'role': 'reader'}
            ).execute()
            
            # Return shareable link
            return file.get('webViewLink')
            
        except Exception as e:
            print(f"Error uploading image: {e}")
            return None
    
    def batch_upload(self, image_paths, topic=None):
        """Upload multiple images"""
        links = []
        for image_path in image_paths:
            link = self.upload_image(image_path, topic)
            if link:
                links.append(link)
        return links

# Standalone function
def upload_to_drive(image_path, topic=None, credentials_path="credentials.json"):
    """Quick function to upload an image"""
    uploader = DriveUploader(credentials_path)
    return uploader.upload_image(image_path, topic)
