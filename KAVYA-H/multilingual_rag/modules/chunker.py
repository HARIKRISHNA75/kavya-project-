def chunk_text(documents: list[dict], chunk_size: int = 500, chunk_overlap: int = 80) -> list[dict]:
    """
    Simple character-based chunking that preserves source & page.
    """
    chunks = []
    for doc in documents:
        text = doc["text"]
        source = doc["source"]
        page = doc["page"]
        document_id = doc.get("document_id")

        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end].strip()
            if chunk:
                chunk_data = {
                    "text": chunk,
                    "source": source,
                    "page": page
                }
                if document_id:
                    chunk_data["document_id"] = document_id
                chunks.append(chunk_data)
            start += chunk_size - chunk_overlap
    return chunks
