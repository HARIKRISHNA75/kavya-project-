from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
import pickle
import os


class MultilingualEmbedder:
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.chunks = []          # list of dicts with text, source, page
        self.dimension = self.model.get_sentence_embedding_dimension()

    def build_index(self, chunks: list[dict]):
        self.chunks = chunks
        texts = [c["text"] for c in chunks]
        embeddings = self.model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
        embeddings = np.array(embeddings).astype("float32")

        self.index = faiss.IndexFlatIP(self.dimension)   # cosine via normalized vectors
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings)

    def save(self, folder: str = "vectorstore"):
        os.makedirs(folder, exist_ok=True)
        faiss.write_index(self.index, os.path.join(folder, "index.faiss"))
        with open(os.path.join(folder, "chunks.pkl"), "wb") as f:
            pickle.dump(self.chunks, f)

    def load(self, folder: str = "vectorstore"):
        self.index = faiss.read_index(os.path.join(folder, "index.faiss"))
        with open(os.path.join(folder, "chunks.pkl"), "rb") as f:
            self.chunks = pickle.load(f)

    def is_ready(self) -> bool:
        return self.index is not None and len(self.chunks) > 0
