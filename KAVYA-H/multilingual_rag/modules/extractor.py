import os
from pypdf import PdfReader
from docx import Document


def extract_text(file_path: str, original_filename: str) -> list[dict]:
    """
    Returns list of dicts:
    {
        "text": str,
        "source": str,          # original filename
        "page": int | None      # page number for PDF, None otherwise
    }
    """
    ext = os.path.splitext(original_filename)[1].lower()
    results = []

    if ext == ".pdf":
        reader = PdfReader(file_path)
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = text.strip()
            if text:
                results.append({
                    "text": text,
                    "source": original_filename,
                    "page": i
                })
    elif ext == ".docx":
        doc = Document(file_path)
        full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        if full_text.strip():
            results.append({
                "text": full_text.strip(),
                "source": original_filename,
                "page": None
            })
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read().strip()
        if text:
            results.append({
                "text": text,
                "source": original_filename,
                "page": None
            })
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    return results
