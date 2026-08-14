# rag/load_pdf.py
# ─────────────────────────────────────────────────────────
# PURPOSE: Step 1 — Extract raw text from PDFs
# Mirrors your original extract_text_from_pdf() logic exactly
# ─────────────────────────────────────────────────────────

import os
import sys
from pathlib import Path
from PyPDF2 import PdfReader

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import PDF_DIR


def load_single_pdf(pdf_path: str) -> dict:
    """
    Extract all text from a single PDF file.
    Skips pages that fail — same logic as your original embedder.

    Returns:
    {
        "filename" : "pm_kisan.pdf",
        "filepath" : "/full/path/pm_kisan.pdf",
        "pages"    : 12,
        "text"     : "full extracted text...",
        "success"  : True/False,
        "error"    : None or "error message"
    }
    """
    result = {
        "filename" : Path(pdf_path).name,
        "filepath" : pdf_path,
        "pages"    : 0,
        "text"     : "",
        "success"  : False,
        "error"    : None
    }

    try:
        reader = PdfReader(pdf_path)
        result["pages"] = len(reader.pages)
        full_text = ""

        for page_num, page in enumerate(reader.pages):
            try:
                text = page.extract_text()
                if text:                        # Skip image-only pages
                    full_text += text + "\n"    # Exact same as your embedder
            except Exception as e:
                print(f"  [WARN] Skipping page {page_num} in {result['filename']}: {e}")
                continue

        if not full_text.strip():
            result["error"] = "No text extracted — PDF may be scanned/image-based"
            return result

        result["text"]    = full_text
        result["success"] = True
        return result

    except Exception as e:
        result["error"] = str(e)
        return result


def load_all_pdfs(pdf_dir: str = None) -> list[dict]:
    """
    Load ALL PDFs from pdf directory.
    Mirrors your original loop in build_index().

    Args:
        pdf_dir: Override default PDF_DIR from config (optional)
    """
    directory = pdf_dir or PDF_DIR
    pdf_files = list(Path(directory).glob("*.pdf"))

    if not pdf_files:
        print(f"[ERROR] No PDF files found in {directory}")
        print("        Please add government scheme PDFs and run again.")
        return []

    print(f"[load_pdf] Found {len(pdf_files)} PDF(s). Processing...")

    results = []
    for pdf_path in pdf_files:
        print(f"  → Loading: {pdf_path.name} ...", end=" ")
        result = load_single_pdf(str(pdf_path))

        if result["success"]:
            word_count = len(result["text"].split())
            print(f"✓ ({result['pages']} pages, ~{word_count} words)")
        else:
            print(f"✗ FAILED: {result['error']}")

        results.append(result)

    success = sum(1 for r in results if r["success"])
    failed  = len(results) - success
    print(f"\n[load_pdf] Done — {success} success, {failed} failed")
    return results


def load_new_pdf(pdf_path: str) -> dict:
    """
    Load a single NEW pdf just added by user.
    Called by FastAPI update endpoint.
    """
    if not os.path.exists(pdf_path):
        return {
            "filename": Path(pdf_path).name,
            "filepath": pdf_path,
            "pages"   : 0,
            "text"    : "",
            "success" : False,
            "error"   : f"File not found: {pdf_path}"
        }

    print(f"[load_pdf] Loading new PDF: {Path(pdf_path).name}")
    result = load_single_pdf(pdf_path)

    if result["success"]:
        print(f"  ✓ Loaded {result['pages']} pages successfully")
    else:
        print(f"  ✗ Failed: {result['error']}")

    return result


# ── Quick test ──────────────────────────────────────────
# Run: python rag/load_pdf.py
if __name__ == "__main__":
    results = load_all_pdfs()
    print("\nSample text from first successful PDF:")
    print("-" * 55)
    for r in results:
        if r["success"]:
            print(f"File : {r['filename']}")
            print(r["text"][:500])
            break