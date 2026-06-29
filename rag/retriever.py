# rag/retriever.py
# ─────────────────────────────────────────────────────────
# UPDATED: Now uses load_index() from update_index.py
# instead of loading FAISS directly.
# Everything else stays the same.
# ─────────────────────────────────────────────────────────

import os
import sys
try:
    import faiss
except ImportError:
    faiss = None
    
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import TOP_K

# Import shared loader — single source of truth for index loading
from rag.update_index import load_index
from rag.embeddings   import embed_single_query


class Retriever:
    """
    Loads FAISS index at startup using shared load_index().
    Exposes retrieve(query) → top-K relevant chunks.
    """

    def __init__(self):
        print("[Retriever] Loading index via update_index.load_index()...")

        # Use the shared loader — same function FastAPI will use at startup
        self.index, self.metadata = load_index()

        if self.index is None:
            raise RuntimeError(
                "FAISS index not found.\n"
                "Please run: python rag/update_index.py"
            )

        print(f"[Retriever] Ready — {self.index.ntotal} vectors loaded.")

    def reload(self):
        """
        Reload index from disk without restarting.
        Called automatically after a new PDF is added via API.
        """
        print("[Retriever] Reloading index from disk...")
        self.index, self.metadata = load_index()
        print(f"[Retriever] Reloaded — {self.index.ntotal} vectors now in index.")

    def retrieve(self, query: str, top_k: int = TOP_K) -> list[dict]:
        """
        Search FAISS index with user query.
        Returns top_k most relevant chunks.

        Args:
            query : User's question
            top_k : Number of results to return

        Returns:
            List of dicts: [{text, source, score}, ...]
        """
        if self.index is None or self.index.ntotal == 0:
            print("[Retriever] WARNING: Index is empty or not loaded")
            return []

        # Embed the query using shared embeddings module
        query_vec = embed_single_query(query).astype(np.float32)

        # Normalize for cosine similarity
        faiss.normalize_L2(query_vec)

        # Search — returns (scores, indices) arrays of shape (1, top_k)
        scores, indices = self.index.search(query_vec, top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:               # FAISS returns -1 if not enough results
                continue
            chunk = self.metadata[idx]
            results.append({
                "text"  : chunk["text"],
                "source": chunk["source"],
                "score" : float(score)
            })

        return results                  # Already sorted best-first by FAISS


# ── Quick test ──────────────────────────────────────────
# Run: python rag/retriever.py
if __name__ == "__main__":
    retriever = Retriever()

    test_queries = [
        "What is the eligibility for PM Kisan?",
        "How to apply for Ayushman Bharat?",
        "bhai kisan scheme mein kitna paisa milta hai"
    ]

    print("=" * 55)
    print("RETRIEVER TEST")
    print("=" * 55)

    for q in test_queries:
        print(f"\nQuery: {q}")
        print("-" * 55)
        results = retriever.retrieve(q, top_k=3)
        for i, r in enumerate(results, 1):
            print(f"[{i}] Score : {r['score']:.3f}")
            print(f"     Source: {r['source']}")
            print(f"     Text  : {r['text'][:150]}...")