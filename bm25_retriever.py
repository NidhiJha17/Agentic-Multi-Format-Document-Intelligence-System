from rank_bm25 import BM25Okapi
import re

from loader import load_cuad_txt_contracts
from chunker import chunk_contracts


def simple_tokenize(text):
    text = text.lower()
    tokens = re.findall(r"\b[a-z0-9]+\b", text)
    return tokens


class BM25Retriever:
    def __init__(self, chunks):
        self.chunks = chunks
        self.tokenized_chunks = [simple_tokenize(c["text"]) for c in chunks]
        self.bm25 = BM25Okapi(self.tokenized_chunks)

    def search(self, query, top_k=5):
        query_tokens = simple_tokenize(query)
        scores = self.bm25.get_scores(query_tokens)

        scored_chunks = list(zip(self.chunks, scores))
        scored_chunks.sort(key=lambda x: x[1], reverse=True)

        results = []
        for chunk, score in scored_chunks[:top_k]:
            results.append({
                "chunk_id": chunk["chunk_id"],
                "filename": chunk["filename"],
                "text": chunk["text"],
                "score": score
            })
        return results


if __name__ == "__main__":
    txt_folder = r"C:\Users\nidhi\Agentic Multi-Format Document Intelligence System\data\raw\CUAD_v1\CUAD_v1\full_contract_txt"

    contracts = load_cuad_txt_contracts(txt_folder, limit=5)
    chunks = chunk_contracts(contracts)

    retriever = BM25Retriever(chunks)

    query = "termination of agreement notice period"
    results = retriever.search(query, top_k=5)

    print(f"Query: '{query}'\n")
    for i, r in enumerate(results, 1):
        print(f"Rank {i} | Score: {r['score']:.3f} | {r['filename']}")
        print(r["text"][:250].replace("\n", " "))
        print("-" * 80)