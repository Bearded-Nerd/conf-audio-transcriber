import os

from .auth import sheets_service
from .models import ConversationRecord

_HEADERS = [
    "Date", "Name", "Company", "Role", "Conference",
    "Topics", "Action Items", "Notes", "Transcript", "Gmail Draft URL",
]


def append_row(record: ConversationRecord) -> None:
    service = sheets_service()
    sheet_id = os.environ["GOOGLE_SHEETS_ID"]
    sheets = service.spreadsheets()

    result = sheets.values().get(
        spreadsheetId=sheet_id, range="A1:J1"
    ).execute()
    existing = result.get("values", [])

    rows = []
    if not existing:
        rows.append(_HEADERS)

    rows.append([
        record.date,
        record.name,
        record.company,
        record.role,
        record.conference,
        record.topics,
        record.action_items,
        record.notes,
        record.transcript,
        record.gmail_draft_url or "",
    ])

    sheets.values().append(
        spreadsheetId=sheet_id,
        range="A1",
        valueInputOption="RAW",
        body={"values": rows},
    ).execute()
