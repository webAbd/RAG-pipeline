# server.py
# ============================================================
# FastAPI Server — English RAG + Speech-to-Text + UI
#
# Start:  python server.py
# Docs:   http://localhost:8000/docs
# UI:     http://localhost:8000
# ============================================================

import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import tempfile, os, shutil
from pathlib import Path

from api.routes import router
from src.config import settings
from src.logger import setup_logger, logger


# ── STT helper (pluggable) ────────────────────────────────
def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe audio using YOUR STT model.

    PLUG YOUR MODEL IN HERE.
    Currently wired to Groq Whisper API as default.
    Replace the body of this function with your own STT call.

    Args:
        audio_path: Path to the saved audio file (webm/ogg/mp4).

    Returns:
        Transcript string.
    """
    # ── Option A: Groq Whisper (default) ──────────────────
    from groq import Groq
    client = Groq(api_key=settings.groq_api_key)
    with open(audio_path, "rb") as f:
        transcription = client.audio.transcriptions.create(
            model="whisper-large-v3-turbo",
            file=f,
            response_format="text",
            language="en",
        )
    return transcription if isinstance(transcription, str) else transcription.text

    # ── Option B: YOUR custom STT model ───────────────────
    # Uncomment and replace with your model's API:
    #
    # from your_stt_module import YourSTTModel
    # model = YourSTTModel()
    # return model.transcribe(audio_path)

    # ── Option C: OpenAI Whisper (local) ──────────────────
    # import whisper
    # model = whisper.load_model("base")
    # result = model.transcribe(audio_path)
    # return result["text"]


# ── Lifespan ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger(log_level=settings.log_level, log_file=settings.log_file)
    logger.info("=" * 55)
    logger.info("English RAG + STT API starting up")
    logger.info(f"Environment : {settings.app_env}")
    logger.info(f"LLM         : {settings.groq_model_name}")
    logger.info(f"Vector DB   : {settings.vectordb_path}")
    logger.info("=" * 55)

    try:
        from api.routes import _get_chain
        _get_chain()
        logger.info("RAG chain pre-loaded.")
    except Exception as e:
        logger.warning(f"RAG chain not pre-loaded: {e}")

    yield
    logger.info("Shutting down.")


# ── App ───────────────────────────────────────────────────
app = FastAPI(
    title="English RAG API",
    description="Grade 9 English Tutor — RAG + Speech to Text",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not settings.is_production else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files & templates
BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


# ── Routes ────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse, tags=["UI"])
async def serve_ui(request: Request):
    """Serve the chat UI."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/v1/transcribe", tags=["STT"])
async def transcribe(file: UploadFile = File(...)):
    """
    Transcribe an audio file to text using the STT model.

    Accepts: audio/webm, audio/ogg, audio/mp4, audio/wav
    Returns: { "transcript": "..." }
    """
    allowed_types = {"audio/webm", "audio/ogg", "audio/mp4", "audio/wav", "audio/mpeg"}
    if file.content_type and file.content_type not in allowed_types:
        # Be lenient — browsers sometimes send odd mime types
        logger.warning(f"Unexpected audio content-type: {file.content_type}")

    # Save to temp file
    suffix = Path(file.filename or "audio.webm").suffix or ".webm"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)

    try:
        shutil.copyfileobj(file.file, tmp)
        tmp.close()

        logger.info(f"Transcribing audio: {file.filename} ({os.path.getsize(tmp.name)} bytes)")
        transcript = transcribe_audio(tmp.name)
        logger.info(f"Transcript: {transcript[:80]}...")
        return {"transcript": transcript}

    except Exception as e:
        logger.exception(f"STT error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        os.unlink(tmp.name)


# RAG routes
app.include_router(router, prefix="/api/v1")


if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload and not settings.is_production,
        log_level=settings.api_log_level,
    )
