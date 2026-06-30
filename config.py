# config.py
import os
from dotenv import load_dotenv

import os


if os.path.exists(".env") and not os.getenv("RAILWAY_ENVIRONMENT"):
    try:
        with open(".env", "rb") as f:
            content = f.read()

        if content.startswith(b'\xef\xbb\xbf'):
            content = content[3:]
        for line in content.decode('utf-8', errors='ignore').splitlines():
            if '=' in line and not line.strip().startswith('#'):
                key, val = line.split('=', 1)
                os.environ[key.strip()] = val.strip()
    except Exception as e:
        print(f"Warning: .env load failed: {e}")  
          
# ── LLM Settings ──────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = "llama-3.3-70b-versatile"  # ← FIXED (was llama3-70b-8192, decommissioned)
MAX_TOKENS   = 1024
TEMPERATURE  = 0.7

# ── Embedding Settings ─────────────────────────
EMBED_MODEL   = "all-MiniLM-L6-v2"
EMBED_DIM     = 384
CHUNK_SIZE    = 300
CHUNK_OVERLAP = 75

# ── Paths ──────────────────────────────────────
BASE_DIR         = os.path.dirname(__file__)
PDF_DIR          = os.path.join(BASE_DIR, "knowledge_base", "raw_pdfs")
CHUNKS_DIR       = os.path.join(BASE_DIR, "knowledge_base", "processed_chunks")
FAISS_INDEX_DIR  = os.path.join(BASE_DIR, "rag", "faiss_index")
FAISS_INDEX_PATH = os.path.join(FAISS_INDEX_DIR, "index.faiss")
METADATA_PATH    = os.path.join(FAISS_INDEX_DIR, "metadata.json")

# ── Memory / Session ───────────────────────────
DB_PATH     = os.path.join(BASE_DIR, "memory", "sessions.db")
MAX_HISTORY = 10

# ── Language ───────────────────────────────────
SUPPORTED_LANGS = ["en", "hi"]
DEFAULT_LANG    = "en"

# ── RAG Retrieval ──────────────────────────────
TOP_K = 5

# ── Voice / Audio ──────────────────────────────────────────  ← NEW
AUDIO_DIR = os.path.join(BASE_DIR, "output", "audio")          # ← NEW
os.makedirs(AUDIO_DIR, exist_ok=True)                          # ← NEW auto-create

# ── Startup validation ─────────────────────────
# This runs when any file imports config — catches missing key immediately
if not GROQ_API_KEY:
    raise EnvironmentError(
        "\n[ERROR] GROQ_API_KEY not found!\n"
        "Add this to your .env file:\n"
        "GROQ_API_KEY=your_key_here\n"
        "Get a free key at: https://console.groq.com"
    )