import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/gmail.compose",
]
_TOKEN_PATH = "token.json"


def get_credentials() -> Credentials:
    creds = None
    creds_file = os.environ.get("GOOGLE_CREDENTIALS_FILE", "credentials.json")

    if os.path.exists(_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(_TOKEN_PATH, _SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, _SCOPES)
            creds = flow.run_local_server(port=0)
        with open(_TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return creds


def sheets_service():
    return build("sheets", "v4", credentials=get_credentials())


def gmail_service():
    return build("gmail", "v1", credentials=get_credentials())
