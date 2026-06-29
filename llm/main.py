# main.py
# ─────────────────────────────────────────────────────────
# PURPOSE: FastAPI backend — all API endpoints
# Connects React frontend to AI pipeline
# Run with: uvicorn main:app --reload --port 8000
# ─────────────────────────────────────────────────────────

import os
import sys
import shutil
from contextlib import asynccontextmanager
from pathlib import Path
from agent.language_detector import detect_language, get_language_label
from google_search import search_schemes, format_search_results, fetch_latest_schemes

from fastapi import (
    FastAPI, HTTPException, UploadFile,
    File, BackgroundTasks
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel

sys.path.append(os.path.dirname(__file__))

from config import PDF_DIR, AUDIO_DIR
from memory.chat_memory import (
    initialize_db, create_session,
    get_history, get_user_profile,
    clear_session, get_all_sessions,
    delete_session, session_exists
)
from llm.generator import Generator
from rag.update_index import (
    update_index, delete_from_index, get_index_stats
)
from rag.load_pdf    import load_new_pdf
from rag.chunking    import chunk_single_new_document
from rag.embeddings  import embed_new_chunks
from output.voice_tts import generate_voice, cleanup_old_audio


# ── Global generator instance ─────────────────────────────
# Loaded ONCE at startup — not per request
# This keeps FAISS index in memory for fast retrieval
generator: Generator = None


# ── Lifespan — runs at startup and shutdown ────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup: initialize DB + load AI models into memory
    Shutdown: cleanup tasks
    """
    global generator

    print("\n" + "="*55)
    print("  SARKARI-MITRA API — STARTING UP")
    print("="*55)

    # Step 1: Initialize SQLite database
    print("\n[startup] Initializing database...")
    initialize_db()

    # Step 2: Load AI generator (loads FAISS + Groq client)
    print("[startup] Loading AI generator...")
    generator = Generator()

    # Step 3: Clean old audio files
    print("[startup] Cleaning old audio files...")
    cleanup_old_audio(max_files=100)

    print("\n[startup] ✓ Sarkari-Mitra API is ready!")
    print("="*55 + "\n")

    yield   # App runs here

    # Shutdown
    print("\n[shutdown] Sarkari-Mitra API shutting down...")


# ── FastAPI app ────────────────────────────────────────────
app = FastAPI(
    title       = "Sarkari-Mitra API",
    description = "AI-powered Government Scheme Assistant for Indian Citizens",
    version     = "1.0.0",
    lifespan    = lifespan
)

# ── CORS — allow React (localhost:3000) to call this API ───
app.add_middleware(
    CORSMiddleware,
    allow_origins     = [
        "http://localhost:3000",    # React dev server
        "http://localhost:5173",    # Vite dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── Serve audio files as static ────────────────────────────
# React calls /audio/filename.mp3 to play voice
app.mount(
    "/audio",
    StaticFiles(directory=AUDIO_DIR),
    name="audio"
)


# ══════════════════════════════════════════════════════════
# REQUEST / RESPONSE MODELS
# ══════════════════════════════════════════════════════════

class ChatRequest(BaseModel):
    session_id: str
    message   : str

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "a3f2-bc91-...",
                "message"   : "bhai PM Kisan ke baare mein batao"
            }
        }


class VoiceRequest(BaseModel):
    text    : str
    language: str = "en"

    class Config:
        json_schema_extra = {
            "example": {
                "text"    : "PM Kisan mein 6000 rupaye milte hain",
                "language": "hinglish"
            }
        }


class ClearSessionRequest(BaseModel):
    session_id: str


# ══════════════════════════════════════════════════════════
# ENDPOINT 1 — HEALTH CHECK
# ══════════════════════════════════════════════════════════

@app.get("/health", tags=["System"])
async def health_check():
    """
    Check if API is running and models are loaded.
    React calls this on startup to verify backend is ready.
    """
    stats = get_index_stats()
    return {
        "status"        : "healthy",
        "index_loaded"  : stats["status"] == "ready",
        "total_vectors" : stats.get("total_vectors", 0),
        "model"         : "llama-3.3-70b-versatile",
        "version"       : "1.0.0"
    }


# ══════════════════════════════════════════════════════════
# ENDPOINT 2 — CREATE SESSION
# ══════════════════════════════════════════════════════════

@app.post("/session/new", tags=["Session"])
async def new_session():
    """
    Create a new chat session.
    Call when user opens the app or clicks 'New Chat'.
    Returns session_id — store this in React localStorage.
    """
    session_id = create_session()
    return {
        "session_id": session_id,
        "message"   : "Session created successfully"
    }


# ══════════════════════════════════════════════════════════
# ENDPOINT 3 — MAIN CHAT (Most Important)
# ══════════════════════════════════════════════════════════

@app.post("/chat", tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Main AI endpoint — send message, get structured response.

    Returns full JSON with:
    - AI response text
    - Scheme recommendations with eligibility
    - Updated user profile
    - Sources used from PDFs
    - Language detected

    React uses this to render:
    - Chat bubbles
    - Scheme cards
    - Profile sidebar
    """
    # Validate session exists in DB
    if not session_exists(request.session_id):
        raise HTTPException(
            status_code = 404,
            detail      = "Session not found. Call POST /session/new first."
        )

    # Validate message is not empty
    if not request.message.strip():
        raise HTTPException(
            status_code = 400,
            detail      = "Message cannot be empty."
        )

    try:
        # Google Search se extra context fetch karo
        try:
            search_results = search_schemes(request.message.strip())
            web_context = format_search_results(search_results)
            # NewsAPI se latest news fetch karo
            news_context = fetch_latest_schemes(request.message.strip())
            web_context = web_context + news_context
        
        except:
            web_context = ""
        # Call AI generator — returns structured JSON dict
        result = generator.generate(
            session_id   = request.session_id,
            user_message = request.message.strip(),
            web_context  = web_context
        )
        return result

    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail      = f"AI generation error: {str(e)}"
        )


# ══════════════════════════════════════════════════════════
# ENDPOINT 4 — GET CHAT HISTORY
# ══════════════════════════════════════════════════════════

@app.get("/session/{session_id}/history", tags=["Session"])
async def get_session_history(session_id: str):
    """
    Get full chat history for a session.
    Call when page loads to restore previous conversation.
    Returns messages in chronological order.
    """
    if not session_exists(session_id):
        raise HTTPException(
            status_code = 404,
            detail      = "Session not found."
        )

    history = get_history(session_id)
    return {
        "session_id"    : session_id,
        "history"       : history,
        "message_count" : len(history)
    }


# ══════════════════════════════════════════════════════════
# ENDPOINT 5 — GET USER PROFILE
# ══════════════════════════════════════════════════════════

@app.get("/session/{session_id}/profile", tags=["Session"])
async def get_session_profile(session_id: str):
    """
    Get collected user profile for a session.
    React uses this to render the profile sidebar.
    Shows which fields are filled and which are missing.
    """
    if not session_exists(session_id):
        raise HTTPException(
            status_code = 404,
            detail      = "Session not found."
        )

    profile  = get_user_profile(session_id)
    required = ["age", "income", "profession", "state"]
    missing  = [f for f in required if not profile.get(f)]

    return {
        "session_id"      : session_id,
        "profile"         : profile,
        "profile_complete": len(missing) == 0,
        "missing_fields"  : missing
    }


# ══════════════════════════════════════════════════════════
# ENDPOINT 6 — CLEAR SESSION CHAT
# ══════════════════════════════════════════════════════════

@app.post("/session/clear", tags=["Session"])
async def clear_chat(request: ClearSessionRequest):
    """
    Clear all messages for a session.
    Called by 'Clear Chat' button in React.
    Keeps session and profile — only deletes messages.
    """
    if not session_exists(request.session_id):
        raise HTTPException(
            status_code = 404,
            detail      = "Session not found."
        )

    clear_session(request.session_id)
    return {
        "session_id": request.session_id,
        "message"   : "Chat history cleared successfully"
    }


# ══════════════════════════════════════════════════════════
# ENDPOINT 7 — TEXT TO VOICE
# ══════════════════════════════════════════════════════════

@app.post("/voice", tags=["Voice"])
async def text_to_voice(request: VoiceRequest):
    """
    Convert text to speech MP3.
    React calls this when user clicks the speaker button.
    Returns URL to MP3 file served at /audio/filename.mp3
    """
    if not request.text.strip():
        raise HTTPException(
            status_code = 400,
            detail      = "Text cannot be empty."
        )

    # 🔥 AUTO DETECT LANGUAGE
    lang_code = detect_language(request.text)
    language  = get_language_label(lang_code)

    # 🔥 GENERATE VOICE WITH DETECTED LANGUAGE
    result = generate_voice(request.text, language)

    if not result["success"]:
        raise HTTPException(
            status_code = 500,
            detail      = f"TTS error: {result['error']}"
        )

    return {
        "audio_url"      : result["audio_url"],
        "filename"       : result["filename"],
        "language"       : result["language"],
        "cached"         : result.get("cached", False)
    }


# ══════════════════════════════════════════════════════════
# ENDPOINT 8 — UPLOAD NEW PDF (Admin)
# ══════════════════════════════════════════════════════════

@app.post("/upload-pdf", tags=["Admin"])
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file            : UploadFile = File(...)
):
    """
    Upload a new government scheme PDF.
    Automatically adds it to FAISS index without restart.

    Steps:
    1. Save PDF to knowledge_base/raw_pdfs/
    2. Extract text
    3. Chunk text
    4. Embed chunks
    5. Add to FAISS index
    6. Reload retriever so new queries use new data

    React admin panel uses this to add new PDFs.
    """
    # Validate file type
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code = 400,
            detail      = "Only PDF files are accepted."
        )

    # Save uploaded file to raw_pdfs directory
    save_path = os.path.join(PDF_DIR, file.filename)

    try:
        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        print(f"[upload] Saved: {file.filename}")
    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail      = f"Failed to save file: {str(e)}"
        )

    # Process PDF in background so API doesn't hang
    def process_pdf(pdf_path: str, filename: str):
        try:
            # Load → chunk → embed → update index
            pdf_result = load_new_pdf(pdf_path)
            if not pdf_result["success"]:
                print(f"[upload] Failed to load {filename}: {pdf_result['error']}")
                return

            new_chunks  = chunk_single_new_document(pdf_result)
            new_vectors = embed_new_chunks(new_chunks)
            success     = update_index(new_chunks, new_vectors)

            if success:
                # Reload retriever so new data is searchable immediately
                generator.retriever.reload()
                print(f"[upload] ✓ {filename} added to index and retriever reloaded")
            else:
                print(f"[upload] ✗ Failed to update index for {filename}")

        except Exception as e:
            print(f"[upload] Error processing {filename}: {e}")

    # Add to background tasks — returns response immediately
    background_tasks.add_task(process_pdf, save_path, file.filename)

    stats = get_index_stats()
    return {
        "filename"      : file.filename,
        "message"       : "PDF uploaded. Processing in background — will be searchable in ~30 seconds.",
        "current_vectors": stats.get("total_vectors", 0)
    }


# ══════════════════════════════════════════════════════════
# ENDPOINT 9 — DELETE PDF (Admin)
# ══════════════════════════════════════════════════════════

@app.delete("/pdf/{filename}", tags=["Admin"])
async def remove_pdf(filename: str):
    """
    Remove a PDF from knowledge base and FAISS index.
    Rebuilds index without that PDF.
    React admin panel uses this to remove outdated PDFs.
    """
    pdf_path = os.path.join(PDF_DIR, filename)

    # Check if PDF file exists
    if not os.path.exists(pdf_path):
        raise HTTPException(
            status_code = 404,
            detail      = f"PDF '{filename}' not found in knowledge base."
        )

    # Remove from FAISS index first
    success = delete_from_index(filename)

    # Delete physical file
    try:
        os.remove(pdf_path)
    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail      = f"Failed to delete file: {str(e)}"
        )

    if success:
        # Reload retriever with updated index
        generator.retriever.reload()

    stats = get_index_stats()
    return {
        "filename"               : filename,
        "message"                : f"'{filename}' removed successfully",
        "total_vectors_remaining": stats.get("total_vectors", 0)
    }


# ══════════════════════════════════════════════════════════
# ENDPOINT 10 — INDEX STATS (Admin)
# ══════════════════════════════════════════════════════════

@app.get("/index/stats", tags=["Admin"])
async def index_stats():
    """
    Get current knowledge base statistics.
    React admin dashboard uses this to show loaded PDFs.
    """
    return get_index_stats()


# ══════════════════════════════════════════════════════════
# ENDPOINT 11 — ALL SESSIONS (Admin)
# ══════════════════════════════════════════════════════════

@app.get("/admin/sessions", tags=["Admin"])
async def list_all_sessions():
    """
    List all chat sessions with message counts.
    Useful for admin monitoring dashboard.
    """
    sessions = get_all_sessions()
    return {
        "total_sessions": len(sessions),
        "sessions"      : sessions
    }


# ══════════════════════════════════════════════════════════
# ENDPOINT 12 — DELETE SESSION (Admin)
# ══════════════════════════════════════════════════════════

@app.delete("/admin/session/{session_id}", tags=["Admin"])
async def remove_session(session_id: str):
    """
    Delete a session and all its messages.
    Admin cleanup tool.
    """
    if not session_exists(session_id):
        raise HTTPException(
            status_code = 404,
            detail      = "Session not found."
        )

    delete_session(session_id)
    return {
        "session_id": session_id,
        "message"   : "Session deleted successfully"
    }


# ══════════════════════════════════════════════════════════
# RUN SERVER
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host    = "0.0.0.0",
        port    = 8000,
        reload  = True      # Auto-reload on code changes
    )