import base64
from email.mime.text import MIMEText

from .auth import gmail_service
from .models import ConversationRecord

_BODY_TEMPLATE = """\
Hi {name},

It was great meeting you at {conference}! I really enjoyed our conversation about {topics}.

{action_items_section}Looking forward to staying in touch.

Best regards
"""


def create_draft(record: ConversationRecord) -> tuple[str, str]:
    """Returns (draft_id, draft_url)."""
    service = gmail_service()

    action_items_section = ""
    if record.action_items.strip():
        items = record.action_items.strip().splitlines()
        formatted = "\n".join(f"- {item.strip()}" for item in items if item.strip())
        action_items_section = f"As a follow-up from our chat:\n{formatted}\n\n"

    first_name = record.name.split()[0] if record.name not in ("", "Unknown") else "there"
    body = _BODY_TEMPLATE.format(
        name=first_name,
        conference=record.conference,
        topics=record.topics,
        action_items_section=action_items_section,
    )

    subject = f"Great meeting you at {record.conference} – {record.name}"
    message = MIMEText(body)
    message["subject"] = subject
    encoded = base64.urlsafe_b64encode(message.as_bytes()).decode()

    draft = service.users().drafts().create(
        userId="me",
        body={"message": {"raw": encoded}},
    ).execute()

    draft_id = draft["id"]
    draft_url = f"https://mail.google.com/mail/#drafts/{draft_id}"
    return draft_id, draft_url
