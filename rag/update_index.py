# rag/update_index.py
# ─────────────────────────────────────────────────────────
# PURPOSE: Step 4 — Build, save, load, update FAISS index
# UPDATED: Metadata format matches your original embedder.py
# - Only saves {text, source} in metadata (your original format)
# - IndexFlatIP with normalize_L2 (your original index type)
# - Same file paths from config
# ─────────────────────────────────────────────────────────

import os
import sys
import json
import faiss
import numpy as np
from pathlib import Path
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import (
    FAISS_INDEX_PATH, METADATA_PATH,
    FAISS_INDEX_DIR, EMBED_DIM
)


# ── Internal helpers ─────────────────────────────────────

def _load_metadata() -> list[dict]:
    """Load metadata JSON. Returns empty list if not found."""
    if not os.path.exists(METADATA_PATH):
        return []
    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_metadata(metadata: list[dict]):
    """Save metadata list to disk."""
    os.makedirs(FAISS_INDEX_DIR, exist_ok=True)
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def _save_index(index: faiss.Index):
    """Save FAISS index to disk."""
    os.makedirs(FAISS_INDEX_DIR, exist_ok=True)
    faiss.write_index(index, FAISS_INDEX_PATH)


# ── Main pipeline functions ──────────────────────────────

def build_full_index(chunks: list[dict], vectors: np.ndarray) -> bool:
    """
    Build a brand new FAISS index from scratch.
    Run once during initial setup.

    MATCHES your original embedder.py build logic:
    - IndexFlatIP (your original index type)
    - Vectors already normalized (done in embeddings.py)
    - Metadata saves only {text, source} — your original format

    Args:
        chunks : All chunks from chunking.py
        vectors: Normalized embeddings from embeddings.py

    Returns:
        True if successful
    """
    if len(chunks) == 0 or len(vectors) == 0:
        print("[update_index] ERROR: No chunks or vectors")
        return False

    if len(chunks) != len(vectors):
        print(f"[update_index] ERROR: {len(chunks)} chunks vs {len(vectors)} vectors")
        return False

    print(f"[update_index] Building index with {len(chunks)} vectors...")

    try:
        # IndexFlatIP — your original index type from embedder.py
        index = faiss.IndexFlatIP(EMBED_DIM)
        index.add(vectors)              # Vectors already normalized by embeddings.py

        _save_index(index)
        print(f"[update_index] ✓ Index saved → {FAISS_INDEX_PATH}")
        print(f"               Vectors in index: {index.ntotal}")

        # Metadata format — matches your ORIGINAL embedder.py exactly:
        # {"text": c["text"], "source": c["source"]}
        # No chunk_id, no added_at — keeps it simple like your original
        metadata = [
            {"text": c["text"], "source": c["source"]}
            for c in chunks
        ]

        _save_metadata(metadata)
        print(f"[update_index] ✓ Metadata saved → {METADATA_PATH}")
        print(f"[update_index] ✓ Build complete!")
        return True

    except Exception as e:
        print(f"[update_index] ERROR: {e}")
        return False


def update_index(new_chunks: list[dict], new_vectors: np.ndarray) -> bool:
    """
    ADD new PDF chunks to existing index WITHOUT full rebuild.
    Called by FastAPI upload endpoint.

    Steps:
    1. Load existing index
    2. Add new normalized vectors
    3. Append new metadata entries
    4. Save everything to disk

    Args:
        new_chunks : Chunks from new PDF only
        new_vectors: Normalized embeddings for new chunks
    """
    if not os.path.exists(FAISS_INDEX_PATH):
        print("[update_index] No existing index — building fresh")
        return build_full_index(new_chunks, new_vectors)

    if not new_chunks:
        print("[update_index] No new chunks to add")
        return False

    try:
        # Load existing
        print("[update_index] Loading existing index...")
        index = faiss.read_index(FAISS_INDEX_PATH)
        print(f"               Before: {index.ntotal} vectors")

        # Add new vectors (already normalized by embeddings.py)
        index.add(new_vectors)
        print(f"               After : {index.ntotal} vectors")

        _save_index(index)

        # Append to metadata — same {text, source} format
        metadata = _load_metadata()
        for chunk in new_chunks:
            metadata.append({
                "text"  : chunk["text"],
                "source": chunk["source"]
            })
        _save_metadata(metadata)

        print(f"[update_index] ✓ Added {len(new_chunks)} new chunks")
        print(f"[update_index] ✓ Total metadata: {len(metadata)}")
        return True

    except Exception as e:
        print(f"[update_index] ERROR: {e}")
        return False


def load_index() -> tuple:
    """
    Load FAISS index + metadata from disk.
    Called ONCE at FastAPI startup.

    Returns:
        (index, metadata) — ready to use
        (None, [])        — if index not found
    """
    if not os.path.exists(FAISS_INDEX_PATH):
        print("[update_index] WARNING: No index found")
        print("               Run: python rag/update_index.py")
        return None, []

    print("[update_index] Loading index from disk...")
    index    = faiss.read_index(FAISS_INDEX_PATH)
    metadata = _load_metadata()
    print(f"[update_index] ✓ {index.ntotal} vectors, {len(metadata)} metadata entries")

    return index, metadata


def delete_from_index(source_filename: str) -> bool:
    """
    Remove all chunks of a specific PDF and rebuild index.
    FAISS doesn't support in-place deletion — must rebuild.

    Args:
        source_filename: e.g. "pm_kisan.pdf"
    """
    print(f"[update_index] Removing '{source_filename}'...")

    try:
        metadata       = _load_metadata()
        keep_metadata  = [m for m in metadata if m["source"] != source_filename]
        removed        = len(metadata) - len(keep_metadata)

        if removed == 0:
            print(f"[update_index] '{source_filename}' not found in index")
            return False

        print(f"[update_index] Removing {removed} chunks...")

        # Get remaining sources and rebuild
        from rag.chunking   import load_chunks_from_disk
        from rag.embeddings import embed_chunks

        keep_sources = list(set(m["source"] for m in keep_metadata))
        all_chunks   = []
        for source in keep_sources:
            all_chunks.extend(load_chunks_from_disk(source))

        if not all_chunks:
            index = faiss.IndexFlatIP(EMBED_DIM)
            _save_index(index)
            _save_metadata([])
            print("[update_index] ✓ Index cleared (no PDFs remaining)")
            return True

        vectors = embed_chunks(all_chunks)
        return build_full_index(all_chunks, vectors)

    except Exception as e:
        print(f"[update_index] ERROR: {e}")
        return False


def get_index_stats() -> dict:
    """
    Return current index stats.
    Used by FastAPI admin endpoint and frontend dashboard.
    """
    if not os.path.exists(FAISS_INDEX_PATH):
        return {"status": "no_index", "total_vectors": 0, "sources": []}

    index    = faiss.read_index(FAISS_INDEX_PATH)
    metadata = _load_metadata()

    source_counts = {}
    for m in metadata:
        src = m["source"]
        source_counts[src] = source_counts.get(src, 0) + 1

    return {
        "status"       : "ready",
        "total_vectors": index.ntotal,
        "total_chunks" : len(metadata),
        "sources"      : [
            {"filename": src, "chunks": count}
            for src, count in source_counts.items()
        ]
    }


# ── Full pipeline test ───────────────────────────────────
# Run: python rag/update_index.py
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

    from rag.load_pdf   import load_all_pdfs
    from rag.chunking   import chunk_all_documents
    from rag.embeddings import embed_chunks

    print("=" * 55)
    print("DYNAMIC KNOWLEDGE BASE — FULL PIPELINE TEST")
    print("=" * 55)

    # Step 1: Load PDFs
    pdf_results = load_all_pdfs()

    # Step 2: Chunk
    all_chunks = chunk_all_documents(pdf_results)

    # Step 3: Embed (normalize_L2 applied inside)
    vectors = embed_chunks(all_chunks)

    # Step 4: Build index
    success = build_full_index(all_chunks, vectors)

    if success:
        # Step 5: Simulate app startup
        index, metadata = load_index()

        # Step 6: Stats
        stats = get_index_stats()
        print("\n INDEX STATS:")
        print(f"  Status  : {stats['status']}")
        print(f"  Vectors : {stats['total_vectors']}")
        print(f"  Sources :")
        for s in stats["sources"]:
            print(f"    - {s['filename']}: {s['chunks']} chunks")