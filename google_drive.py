import os

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def drive_client():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds = InstalledAppFlow.from_client_secrets_file(
                "client_secret.json", SCOPES
            ).run_local_server(port=0)

        with open("token.json", "w", encoding="utf-8") as f:
            f.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


def create_folder(name: str, parent_folder_id: str):
    drive = drive_client()

    folder_metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_folder_id],
    }

    folder = drive.files().create(body=folder_metadata, fields="id").execute()
    return folder["id"]


def upload_file(file: str, folder_id: str):
    drive = drive_client()

    media = MediaFileUpload(file, resumable=True)
    body = {"name": Path(file).name, "parents": [folder_id]}

    f = drive.files().create(
        body=body,
        media_body=media,
        fields="webViewLink",
    ).execute()
    return f.get("webViewLink")

