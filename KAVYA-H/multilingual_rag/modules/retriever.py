import numpy as np
import faiss
from modules.embedder import MultilingualEmbedder


def retrieve(
    embedder: MultilingualEmbedder,
    query: str,
    top_k: int = 5,
    document_id: str | None = None,
) -> list[dict]:
    if not embedder.is_ready():
        return []

    q_emb = embedder.model.encode([query], convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(q_emb)

    if document_id is not None:
        candidate_indices = [
            i for i, chunk in enumerate(embedder.chunks)
            if chunk.get("document_id", chunk["source"]) == document_id
        ]
        if not candidate_indices:
            return []

        candidate_vectors = np.vstack([
            embedder.index.reconstruct(int(i)) for i in candidate_indices
        ]).astype("float32")
        candidate_scores = (candidate_vectors @ q_emb[0]).flatten()
        ranked_positions = np.argsort(candidate_scores)[::-1][:top_k]
        return [
            {
                **embedder.chunks[candidate_indices[int(position)]].copy(),
                "score": float(candidate_scores[position]),
            }
            for position in ranked_positions
        ]

    scores, indices = embedder.index.search(q_emb, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0:
            continue
        chunk = embedder.chunks[idx].copy()
        chunk["score"] = float(score)
        results.append(chunk)
    return results
