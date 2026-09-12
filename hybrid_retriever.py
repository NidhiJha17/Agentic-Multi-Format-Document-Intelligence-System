from bm25_retriever import BM25Retriever
from semantic_retriever import SemanticRetriever
from loader import load_cuad_txt_contracts
from chunker import chunk_contracts


class HybridRetriever:
    def __init__(self, chunks, k=60):
        """
        k is the RRF constant (60 is the standard default from the original paper).
        """
        self.chunks = chunks
        self.k = k
        print("Building BM25 index...")
        self.bm25_retriever = BM25Retriever(chunks)
        print("Building semantic index...")
        self.semantic_retriever = SemanticRetriever(chunks)

    def search(self, query, top_k=5, candidate_pool=20):
        """
        candidate_pool: how many results to pull from EACH method before fusing.
        Should be >= top_k so fusion has enough candidates to work with.
        """
        bm25_results = self.bm25_retriever.search(query, top_k=candidate_pool)
        semantic_results = self.semantic_retriever.search(query, top_k=candidate_pool)

        # Build rank lookup: chunk_id -> rank position (1-indexed) per method
        bm25_ranks = {r["chunk_id"]: rank for rank, r in enumerate(bm25_results, 1)}
        semantic_ranks = {r["chunk_id"]: rank for rank, r in enumerate(semantic_results, 1)}

        # Union of all chunk_ids that appeared in either list
        all_chunk_ids = set(bm25_ranks.keys()) | set(semantic_ranks.keys())

        # Keep a lookup to the actual chunk data (text, filename) by chunk_id
        chunk_lookup = {r["chunk_id"]: r for r in bm25_results}
        chunk_lookup.update({r["chunk_id"]: r for r in semantic_results})

        fused_scores = []
        for chunk_id in all_chunk_ids:
            score = 0.0
            if chunk_id in bm25_ranks:
                score += 1 / (self.k + bm25_ranks[chunk_id])
            if chunk_id in semantic_ranks:
                score += 1 / (self.k + semantic_ranks[chunk_id])

            fused_scores.append({
                "chunk_id": chunk_id,
                "filename": chunk_lookup[chunk_id]["filename"],
                "text": chunk_lookup[chunk_id]["text"],
                "rrf_score": score,
                "bm25_rank": bm25_ranks.get(chunk_id, None),
                "semantic_rank": semantic_ranks.get(chunk_id, None),
            })

        fused_scores.sort(key=lambda x: x["rrf_score"], reverse=True)
        return fused_scores[:top_k]


if __name__ == "__main__":
    txt_folder = r"C:\Users\nidhi\Agentic Multi-Format Document Intelligence System\data\raw\CUAD_v1\CUAD_v1\full_contract_txt"

    contracts = load_cuad_txt_contracts(txt_folder, limit=5)
    chunks = chunk_contracts(contracts)

    retriever = HybridRetriever(chunks)

    query = "termination of agreement notice period"
    results = retriever.search(query, top_k=5)

    print(f"\nQuery: '{query}'\n")
    for i, r in enumerate(results, 1):
        print(f"Rank {i} | RRF: {r['rrf_score']:.4f} | BM25 rank: {r['bm25_rank']} | Semantic rank: {r['semantic_rank']} | {r['filename']}")
        print(r["text"][:250].replace("\n", " "))
        print("-" * 80)