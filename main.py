import os
import secrets
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles

from conference_capture.analyzer import analyze
from conference_capture.gmail_client import create_draft
from conference_capture.models import ConversationRecord
from conference_capture.sheets import append_row
from conference_capture.transcriber import transcribe

load_dotenv()

_api_key_header = APIKeyHeader(name="X-API-Key")


def _require_api_key(key: str = Depends(_api_key_header)):
    expected = os.environ.get("APP_API_KEY", "")
    if not expected or not secrets.compare_digest(key, expected):
        raise HTTPException(status_code=403, detail="Invalid API key")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _check_env()
    yield


def _check_env():
    required = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_SHEETS_ID", "APP_API_KEY"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        raise RuntimeError(f"Missing required env vars: {', '.join(missing)}")


app = FastAPI(title="Conference Capture", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def index():
    return FileResponse("static/index.html")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/conversations", response_model=ConversationRecord, dependencies=[Depends(_require_api_key)])
async def capture_conversation(
    audio: UploadFile = File(...),
    conference: str = Form(default=""),
):
    suffix = Path(audio.filename or "audio.webm").suffix or ".webm"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name

    try:
        transcript = transcribe(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Transcription failed: {e}")
    finally:
        os.unlink(tmp_path)

    try:
        record = analyze(transcript, conference_hint=conference)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Analysis failed: {e}")

    try:
        draft_id, draft_url = create_draft(record)
        record.gmail_draft_id = draft_id
        record.gmail_draft_url = draft_url
    except Exception as e:
        # Non-fatal: log and continue without draft
        print(f"[warn] Gmail draft failed: {e}")

    try:
        append_row(record)
    except Exception as e:
        print(f"[warn] Sheets append failed: {e}")

    return record
