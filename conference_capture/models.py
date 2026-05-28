from pydantic import BaseModel


class ConversationRecord(BaseModel):
    date: str
    name: str
    company: str
    role: str
    conference: str
    topics: str
    action_items: str
    notes: str
    transcript: str
    gmail_draft_id: str | None = None
    gmail_draft_url: str | None = None
