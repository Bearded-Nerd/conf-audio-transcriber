import json
import os
from datetime import date

import anthropic

from .models import ConversationRecord

_PROMPT = """\
You are a helpful assistant. A user recorded a voice memo after a conference conversation.
Analyze the transcript below and extract the following information as JSON with these exact keys:
- name: full name of the person they spoke with (string, "Unknown" if not found)
- company: their company or organization (string, "Unknown" if not found)
- role: their job title or role (string, "Unknown" if not found)
- conference: name of the conference or event (string, use the hint if provided)
- topics: comma-separated list of key topics discussed (string)
- action_items: newline-separated list of follow-up action items (string)
- notes: a 2-3 sentence summary of the conversation (string)

Return ONLY valid JSON, no markdown fences, no extra text.

Conference hint: {conference_hint}

Transcript:
{transcript}
"""


def analyze(transcript: str, conference_hint: str = "") -> ConversationRecord:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    prompt = _PROMPT.format(
        conference_hint=conference_hint or "not provided",
        transcript=transcript,
    )

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    # Strip markdown fences if model included them despite instructions
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    data = json.loads(raw)

    return ConversationRecord(
        date=date.today().isoformat(),
        transcript=transcript,
        **data,
    )
