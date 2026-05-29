import json
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

    token_json = os.environ.get("GOOGLE_TOKEN_JSON")
    if token_json:
        creds = Credentials.from_authorized_user_info(json.loads(token_json), _SCOPES)
    elif os.path.exists(_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(_TOKEN_PATH, _SCOPES)

    if creds and not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise RuntimeError(
                "Google token is expired and has no refresh token. "
                "Re-run the OAuth flow locally: "
                "python -c \"from conference_capture.auth import run_local_flow; run_local_flow()\""
            )

    if not creds:
        raise RuntimeError(
            "No Google credentials found. "
            "Set GOOGLE_TOKEN_JSON env var (Railway) or place token.json in the project root (local)."
        )

    return creds


def run_local_flow() -> None:
    """Run the OAuth consent flow locally to generate a fresh token.json with a refresh token."""
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        flow = InstalledAppFlow.from_client_config(json.loads(creds_json), _SCOPES)
    else:
        creds_file = os.environ.get("GOOGLE_CREDENTIALS_FILE", "credentials.json")
        flow = InstalledAppFlow.from_client_secrets_file(creds_file, _SCOPES)

    creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")
    with open(_TOKEN_PATH, "w") as f:
        f.write(creds.to_json())
    print(f"\ntoken.json written. Copy this into GOOGLE_TOKEN_JSON on Railway:\n\n{creds.to_json()}\n")


def sheets_service():
    return build("sheets", "v4", credentials=get_credentials())


def gmail_service():
    return build("gmail", "v1", credentials=get_credentials())
