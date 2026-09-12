def chunk_text(text, chunk_size=1500, overlap=200):
    # Split into paragraphs first (preserves natural structure)
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    chunks = []
    current_chunk = ""

    for para in paragraphs:
        # If adding this paragraph would exceed chunk_size, finalize current chunk
        if len(current_chunk) + len(para) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            # Start next chunk with overlap: take the tail end of the previous chunk
            overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
            current_chunk = overlap_text + " " + para
        else:
            current_chunk += " " + para

        # Handle paragraphs that are themselves longer than chunk_size
        while len(current_chunk) > chunk_size * 1.5:
            chunks.append(current_chunk[:chunk_size].strip())
            current_chunk = current_chunk[chunk_size - overlap:]

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def chunk_contracts(contracts, chunk_size=1500, overlap=200):
    """
    Takes the list of contract dicts from the loader and returns
    a list of chunk dicts, each tagged with its source contract.
    """
    all_chunks = []
    for contract in contracts:
        text_chunks = chunk_text(contract["text"], chunk_size, overlap)
        for i, chunk in enumerate(text_chunks):
            all_chunks.append({
                "chunk_id": f"{contract['filename']}::chunk_{i}",
                "filename": contract["filename"],
                "chunk_index": i,
                "text": chunk
            })
    return all_chunks


if __name__ == "__main__":
    from loader import load_cuad_txt_contracts
    from collections import defaultdict

    txt_folder = r"C:\Users\nidhi\Agentic Multi-Format Document Intelligence System\data\raw\CUAD_v1\CUAD_v1\full_contract_txt"
    contracts = load_cuad_txt_contracts(txt_folder, limit=5)

    chunks = chunk_contracts(contracts)

    print(f"Loaded {len(contracts)} contracts -> {len(chunks)} chunks\n")
    for c in chunks[:5]:
        print(f"Chunk ID: {c['chunk_id']}")
        print(f"Length: {len(c['text'])} characters")
        print(c["text"][:200].replace("\n", " "))
        print("-" * 80)

    counts = defaultdict(int)
    for c in chunks:
        counts[c["filename"]] += 1

    print("\nChunks per contract:")
    for fname, count in counts.items():
        print(f"  {count} chunks - {fname}")

    avg_len = sum(len(c["text"]) for c in chunks) / len(chunks)
    print(f"\nAverage chunk length: {avg_len:.0f} characters")