from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

from loader import load_cuad_txt_contracts
from chunker import chunk_contracts


class SemanticRetriever:
    def __init__(self, chunks, model_name="all-MiniLM-L6-v2"):
        self.chunks = chunks
        print(f"Loading embedding model: {model_name} ...")
        self.model = SentenceTransformer(model_name)

        print(f"Embedding {len(chunks)} chunks...")
        texts = [c["text"] for c in chunks]
        embeddings = self.model.encode(texts, show_progress_bar=True)

        # FAISS needs float32 numpy arrays
        embeddings = np.array(embeddings).astype("float32")

        # Normalize vectors so inner product = cosine similarity
        faiss.normalize_L2(embeddings)

        self.dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(self.dimension)  # IP = inner product
        self.index.add(embeddings)

        print(f"Index built. Dimension: {self.dimension}, Total vectors: {self.index.ntotal}")

    def search(self, query, top_k=5):
        query_embedding = self.model.encode([query]).astype("float32")
        faiss.normalize_L2(query_embedding)

        scores, indices = self.index.search(query_embedding, top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            chunk = self.chunks[idx]
            results.append({
                "chunk_id": chunk["chunk_id"],
                "filename": chunk["filename"],
                "text": chunk["text"],
                "score": float(score)
            })
        return results


if __name__ == "__main__":
    txt_folder = r"C:\Users\nidhi\Agentic Multi-Format Document Intelligence System\data\raw\CUAD_v1\CUAD_v1\full_contract_txt"

    contracts = load_cuad_txt_contracts(txt_folder, limit=5)
    chunks = chunk_contracts(contracts)

    retriever = SemanticRetriever(chunks)

    query = "termination of agreement notice period"
    results = retriever.search(query, top_k=5)

    print(f"\nQuery: '{query}'\n")
    for i, r in enumerate(results, 1):
        print(f"Rank {i} | Score: {r['score']:.3f} | {r['filename']}")
        print(r["text"][:250].replace("\n", " "))
        print("-" * 80)