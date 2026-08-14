# rag/chunking.py
# ─────────────────────────────────────────────────────────
# PURPOSE: Step 2 — Split text into chunks
# UPDATED: Matches your exact chunk_text() logic from embedder.py
# - Uses "chunk_str" variable name (your version)
# - Uses break (not continue) for small trailing chunks
# - No extra fields like word_count or start_word
# ─────────────────────────────────────────────────────────

import os
import sys
import json
import re
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import CHUNKS_DIR, CHUNK_SIZE, CHUNK_OVERLAP


def clean_text(text: str) -> str:
    """
    Clean raw PDF text before chunking.
    Removes garbage that hurts embedding quality.
    """
    # Remove 3+ consecutive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Remove page numbers like "Page 1 of 12" or "- 5 -"
    text = re.sub(r'[-–]\s*\d+\s*[-–]', '', text)
    text = re.sub(r'Page\s+\d+\s+of\s+\d+', '', text, flags=re.IGNORECASE)

    # Remove URLs
    text = re.sub(r'http[s]?://\S+', '', text)

    # Normalize multiple spaces
    text = re.sub(r' {2,}', ' ', text)

    # Strip each line
    lines = [line.strip() for line in text.splitlines()]
    text  = '\n'.join(line for line in lines if line)

    return text.strip()


def chunk_single_document(text: str, source_name: str) -> list[dict]:
    """
    Split one document into overlapping chunks.

    MATCHES YOUR ORIGINAL embedder.py logic exactly:
    - Splits by whitespace
    - Uses CHUNK_SIZE and CHUNK_OVERLAP from config
    - Skips chunks with < 20 words using break
    - Returns {text, source, chunk_id} — no extra fields

    Args:
        text       : Raw extracted text from PDF
        source_name: e.g. "pm_kisan.pdf"

    Returns:
        List of chunk dicts
    """
    cleaned  = clean_text(text)
    words    = cleaned.split()          # Split by whitespace — same as your version
    chunks   = []
    chunk_id = 0

    step = CHUNK_SIZE - CHUNK_OVERLAP   # Advance by this many words each iteration

    for i in range(0, len(words), step):
        chunk_words = words[i : i + CHUNK_SIZE]
        chunk_str   = " ".join(chunk_words)  # "chunk_str" — matches your variable name

        if len(chunk_words) < 20:       # Your original used break here
            break

        chunks.append({
            "text"    : chunk_str,      # Matches your original field names exactly
            "source"  : source_name,
            "chunk_id": chunk_id
        })
        chunk_id += 1

    return chunks


def chunk_all_documents(pdf_results: list[dict]) -> list[dict]:
    """
    Chunk ALL loaded PDF results.

    Args:
        pdf_results: Output from load_all_pdfs()

    Returns:
        Combined list of all chunks from all PDFs
    """
    os.makedirs(CHUNKS_DIR, exist_ok=True)

    all_chunks = []

    for pdf in pdf_results:
        if not pdf.get("success"):
            print(f"  [SKIP] {pdf['filename']} — load failed, skipping")
            continue

        print(f"  → Chunking: {pdf['filename']} ...", end=" ")
        chunks = chunk_single_document(pdf["text"], pdf["filename"])

        if not chunks:
            print("✗ No chunks created")
            continue

        all_chunks.extend(chunks)
        print(f"✓ {len(chunks)} chunks")

        # Save to disk for debugging
        save_chunks_to_disk(chunks, pdf["filename"])

    print(f"\n[chunking] Total: {len(all_chunks)} chunks from {len(pdf_results)} PDF(s)")
    return all_chunks


def chunk_single_new_document(pdf_result: dict) -> list[dict]:
    """
    Chunk a single NEW document.
    Called by FastAPI update endpoint after new PDF is uploaded.
    """
    if not pdf_result.get("success"):
        print(f"[chunking] Cannot chunk — PDF failed: {pdf_result.get('error')}")
        return []

    chunks = chunk_single_document(pdf_result["text"], pdf_result["filename"])
    print(f"[chunking] Created {len(chunks)} chunks for {pdf_result['filename']}")
    save_chunks_to_disk(chunks, pdf_result["filename"])
    return chunks


def save_chunks_to_disk(chunks: list[dict], filename: str):
    """
    Save chunks as JSON — same as your original embedder.py.
    Filename format: processed_chunks/pm_kisan_chunks.json
    """
    os.makedirs(CHUNKS_DIR, exist_ok=True)
    stem       = Path(filename).stem
    chunk_file = os.path.join(CHUNKS_DIR, f"{stem}_chunks.json")

    with open(chunk_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)


def load_chunks_from_disk(filename: str) -> list[dict]:
    """
    Load previously saved chunks from disk.
    Used when rebuilding index after a PDF deletion.
    """
    stem       = Path(filename).stem.replace("_chunks", "")
    chunk_file = os.path.join(CHUNKS_DIR, f"{stem}_chunks.json")

    if not os.path.exists(chunk_file):
        print(f"[chunking] Chunk file not found: {chunk_file}")
        return []

    with open(chunk_file, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Quick test ──────────────────────────────────────────
# Run: python rag/chunking.py
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from rag.load_pdf import load_all_pdfs

    print("=" * 55)
    print("CHUNKING TEST")
    print("=" * 55)

    pdf_results = load_all_pdfs()
    all_chunks  = chunk_all_documents(pdf_results)

    if all_chunks:
        print("\nSample chunk:")
        print("-" * 55)
        s = all_chunks[0]
        print(f"Source  : {s['source']}")
        print(f"Chunk ID: {s['chunk_id']}")
        print(f"Text    : {s['text'][:300]}...")