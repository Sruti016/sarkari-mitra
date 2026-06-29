# rag/embeddings.py
# ─────────────────────────────────────────────────────────
# PURPOSE: Step 3 — Convert chunks to vectors
# UPDATED: Matches your exact embed settings from embedder.py
# - batch_size=32 (your original value)
# - faiss.normalize_L2 applied here (same as your embedder)
# - convert_to_numpy=True (your original setting)
# ─────────────────────────────────────────────────────────

import os
import sys
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import EMBED_MODEL, EMBED_DIM

# Load model once at module level — prevents reloading on every call
print(f"[embeddings] Loading model: {EMBED_MODEL}")
_model = SentenceTransformer(EMBED_MODEL)
print(f"[embeddings] Model ready. Output dim: {EMBED_DIM}")


def embed_chunks(chunks: list[dict], batch_size: int = 32) -> np.ndarray:
    """
    Convert chunk list to embedding vectors.

    MATCHES YOUR ORIGINAL embedder.py exactly:
    - batch_size=32
    - show_progress_bar=True
    - convert_to_numpy=True
    - faiss.normalize_L2 applied before returning

    Args:
        chunks    : List of chunk dicts with "text" key
        batch_size: 32 matches your original (reduce to 16 if RAM issues)

    Returns:
        Normalized numpy array shape (num_chunks, EMBED_DIM)
        Already normalized — ready to add directly into FAISS
    """
    if not chunks:
        print("[embeddings] No chunks to embed")
        return np.array([])

    texts = [chunk["text"] for chunk in chunks]

    print(f"[embeddings] Embedding {len(texts)} chunks...")

    embeddings = _model.encode(
        texts,
        batch_size        = batch_size,     # Your original value
        show_progress_bar = True,           # Your original setting
        convert_to_numpy  = True            # Your original setting
    )

    # Normalize BEFORE returning — same as your embedder.py line:
    # faiss.normalize_L2(embeddings)
    embeddings = embeddings.astype(np.float32)
    faiss.normalize_L2(embeddings)

    print(f"[embeddings] Done. Shape: {embeddings.shape}")
    return embeddings


def embed_single_query(query: str) -> np.ndarray:
    """
    Embed one search query at retrieval time.
    Must use the exact same model as embed_chunks().

    Returns:
        numpy array shape (1, EMBED_DIM) — NOT normalized yet
        Normalization happens in retriever.py before search
    """
    vector = _model.encode(
        [query],
        convert_to_numpy=True
    )
    return vector.astype(np.float32)


def embed_new_chunks(new_chunks: list[dict]) -> np.ndarray:
    """
    Embed only NEW chunks from a newly uploaded PDF.
    Called by FastAPI update endpoint.
    Returns normalized vectors ready for FAISS.
    """
    print(f"[embeddings] Embedding {len(new_chunks)} new chunks...")
    return embed_chunks(new_chunks)     # normalize_L2 already applied inside


# ── Quick test ──────────────────────────────────────────
# Run: python rag/embeddings.py
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from rag.load_pdf  import load_all_pdfs
    from rag.chunking  import chunk_all_documents

    print("=" * 55)
    print("EMBEDDINGS TEST")
    print("=" * 55)

    pdf_results = load_all_pdfs()
    all_chunks  = chunk_all_documents(pdf_results)
    vectors     = embed_chunks(all_chunks)

    print(f"\nResults:")
    print(f"  Chunks   : {len(all_chunks)}")
    print(f"  Shape    : {vectors.shape}")
    print(f"  Sample   : {vectors[0][:5]}...")