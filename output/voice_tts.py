# output/voice_tts.py
# ─────────────────────────────────────────────────────────
# PURPOSE: Convert text to speech and save as MP3
# Called by POST /voice FastAPI endpoint
# Uses gTTS (Google Text-to-Speech) — free, no API key needed
# ─────────────────────────────────────────────────────────

import os
import sys
import uuid
import hashlib

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import AUDIO_DIR

# Ensure audio folder exists
os.makedirs(AUDIO_DIR, exist_ok=True)


def _get_gtts_lang(language: str) -> str:
    """
    Convert our language label to gTTS language code.

    gTTS codes:
    - "hi" → Hindi
    - "en" → English
    Hinglish has no native TTS → use Hindi for better pronunciation
    """
    lang_map = {
        "Hindi (Devanagari script)"                           : "hi",
        "Hinglish (casual mixed Hindi-English in Roman script)": "hi",
        "English"                                             : "en",
        "hi"                                                  : "hi",
        "en"                                                  : "en",
        "hinglish"                                            : "hi",
    }
    return lang_map.get(language, "en")


def _make_filename(text: str) -> str:
    """
    Generate a unique filename based on text hash.
    Same text = same filename = cached file (no re-generation).
    Format: audio_<8char_hash>.mp3
    """
    text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
    return f"audio_{text_hash}.mp3"


def generate_voice(text: str, language: str = "en") -> dict:
    """
    Convert text to speech and save as MP3.
    Returns info dict with file path and URL.

    Args:
        text    : Text to convert to speech
        language: Language label from detector or "hi"/"en" code

    Returns:
        {
            "success"  : True/False,
            "filename" : "audio_abc12345.mp3",
            "filepath" : "/full/path/audio_abc12345.mp3",
            "audio_url": "/audio/audio_abc12345.mp3",
            "language" : "hi",
            "error"    : None or "error message"
        }
    """
    try:
        from gtts import gTTS
    except ImportError:
        return {
            "success"  : False,
            "filename" : None,
            "filepath" : None,
            "audio_url": None,
            "language" : None,
            "error"    : "gTTS not installed. Run: pip install gtts"
        }

    # Clean text — remove markdown symbols that sound bad in TTS
    clean = text
    for symbol in ["*", "#", "_", "`", "•", "→", "←", "✅", "❌", "⚠️", "🎯", "😊"]:
        clean = clean.replace(symbol, "")
    clean = " ".join(clean.split())     # Normalize whitespace

    # Truncate very long text — gTTS has limits
    # 500 chars is enough for one response
    if len(clean) > 500:
        clean = clean[:500] + "..."

    if not clean.strip():
        return {
            "success"  : False,
            "filename" : None,
            "filepath" : None,
            "audio_url": None,
            "language" : None,
            "error"    : "Empty text after cleaning"
        }

    # Get gTTS language code
    gtts_lang = _get_gtts_lang(language)

    # Generate filename — cached if same text requested again
    filename = _make_filename(clean + gtts_lang)
    filepath = os.path.join(AUDIO_DIR, filename)

    # If file already exists → return cached version
    if os.path.exists(filepath):
        return {
            "success"  : True,
            "filename" : filename,
            "filepath" : filepath,
            "audio_url": f"/audio/{filename}",
            "language" : gtts_lang,
            "error"    : None,
            "cached"   : True
        }

    # Generate new audio file
    try:
        tts = gTTS(text=clean, lang=gtts_lang, slow=False)
        tts.save(filepath)

        return {
            "success"  : True,
            "filename" : filename,
            "filepath" : filepath,
            "audio_url": f"/audio/{filename}",
            "language" : gtts_lang,
            "error"    : None,
            "cached"   : False
        }

    except Exception as e:
        return {
            "success"  : False,
            "filename" : None,
            "filepath" : None,
            "audio_url": None,
            "language" : gtts_lang,
            "error"    : str(e)
        }


def cleanup_old_audio(max_files: int = 100):
    """
    Delete oldest audio files if folder has more than max_files.
    Call this periodically to prevent disk fill-up.
    Called automatically by FastAPI startup.
    """
    try:
        files = [
            os.path.join(AUDIO_DIR, f)
            for f in os.listdir(AUDIO_DIR)
            if f.endswith(".mp3")
        ]

        if len(files) <= max_files:
            return

        # Sort by creation time — delete oldest first
        files.sort(key=os.path.getctime)
        to_delete = files[:len(files) - max_files]

        for f in to_delete:
            os.remove(f)

        print(f"[voice_tts] Cleaned up {len(to_delete)} old audio files")

    except Exception as e:
        print(f"[voice_tts] Cleanup error: {e}")


# ── Quick test ──────────────────────────────────────────
# Run: python output/voice_tts.py
if __name__ == "__main__":
    print("Testing voice TTS...")

    tests = [
        ("PM Kisan scheme gives Rs.6000 per year to farmers.", "en"),
        ("पीएम किसान योजना में किसानों को 6000 रुपये मिलते हैं।", "hi"),
        ("Yaar, PM Kisan mein 6000 rupaye milte hain per year!", "hinglish"),
    ]

    for text, lang in tests:
        print(f"\nText    : {text[:50]}...")
        print(f"Language: {lang}")
        result = generate_voice(text, lang)
        if result["success"]:
            print(f"✓ Saved : {result['filename']}")
            print(f"  URL   : {result['audio_url']}")
            print(f"  Cached: {result.get('cached', False)}")
        else:
            print(f"✗ Error : {result['error']}")