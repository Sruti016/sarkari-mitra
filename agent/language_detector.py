# agent/language_detector.py
# ─────────────────────────────────────────────────────────
# PURPOSE: Detect if user typed in Hindi, English, or Hinglish
# ─────────────────────────────────────────────────────────

from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import SUPPORTED_LANGS, DEFAULT_LANG

# Makes langdetect results consistent (it's random by default)
DetectorFactory.seed = 0

# Hinglish keywords — Hindi words written in Roman script
HINGLISH_KEYWORDS = [
    "mujhe", "batao", "kya", "hai", "nahi", "hoga", "kaun",
    "kaise", "kab", "kyun", "mera", "tera", "aap", "tum",
    "yojana", "kisan", "sarkari", "paisa", "rupay",
    "apply", "karna", "chahiye", "milega", "milta",
    "scheme ke", "bhai", "yaar", "kitna", "kuch", "bahut",
    "accha", "theek", "pata", "lagta", "bolte", "rehta",
    "eligible", "matlab", "samjho", "batana", "chahta",
    "mere", "tumhara", "apna", "unka", "inke", "unhe"
]


def detect_language(text: str) -> str:
    """
    Detect language of input text.
    Returns:
        "hi"       → Pure Hindi (Devanagari script)
        "hinglish" → Mixed Hindi+English in Roman script
        "en"       → English
    Falls back to DEFAULT_LANG if detection fails.
    """
    if not text or len(text.strip()) < 3:
        return DEFAULT_LANG

    text_lower = text.lower()

    # ── Check for Hinglish FIRST ──────────────────────────
    # Count how many Hinglish keywords appear in the text
    hinglish_count = sum(1 for kw in HINGLISH_KEYWORDS if kw in text_lower)

    # If 2 or more Hinglish keywords found → classify as Hinglish
    if hinglish_count >= 2:
        return "hinglish"

    # ── Check for pure Hindi (Devanagari characters) ───────
    # Devanagari Unicode range: \u0900 to \u097F
    devanagari_chars = sum(1 for ch in text if '\u0900' <= ch <= '\u097F')
    if devanagari_chars > 3:                # More than 3 Devanagari chars = Hindi
        return "hi"

    # ── Fall back to langdetect for everything else ────────
    try:
        lang = detect(text)
        if lang in SUPPORTED_LANGS:
            return lang
        return DEFAULT_LANG

    except LangDetectException:
        return DEFAULT_LANG


def get_language_label(lang_code: str) -> str:
    """
    Convert language code to human-readable label.
    Used in prompts to tell LLM which language to reply in.
    """
    labels = {
        "en"      : "English",
        "hi"      : "Hindi (Devanagari script)",
        "hinglish": "Hinglish (casual mixed Hindi-English in Roman script)"
    }
    return labels.get(lang_code, "English")


# ── Quick test ──────────────────────────────────────────
# Run: python agent/language_detector.py
if __name__ == "__main__":
    test_inputs = [
        "What schemes are available for farmers?",
        "मुझे किसान योजना के बारे में बताएं",
        "मेरी आय 2 लाख रुपये है",
        "How do I apply for Ayushman Bharat?",
        "pm kisan ke liye eligible kaun hai",
        "bhai mujhe batao kitna paisa milega PM Kisan mein",
        "yaar kya main eligible hoon ayushman bharat ke liye",
        "scheme ke baare mein kuch batao please"
    ]

    print("=" * 55)
    print("LANGUAGE DETECTION TEST")
    print("=" * 55)
    for text in test_inputs:
        lang  = detect_language(text)
        label = get_language_label(lang)
        print(f"Input   : {text}")
        print(f"Detected: {lang} → {label}")
        print("-" * 55)