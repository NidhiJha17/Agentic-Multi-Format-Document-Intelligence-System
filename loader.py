import os
import glob

def load_cuad_txt_contracts(txt_folder_path, limit=None):
    """
    Loads CUAD full_contract_txt files.
    Returns a list of {filename, path, text} dicts.
    """
    txt_files = glob.glob(os.path.join(txt_folder_path, "**", "*.txt"), recursive=True)
    txt_files.sort()

    if limit:
        txt_files = txt_files[:limit]

    contracts = []
    for path in txt_files:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        contracts.append({
            "filename": os.path.basename(path),
            "path": path,
            "text": text
        })

    return contracts


if __name__ == "__main__":
    txt_folder = r"C:\Users\nidhi\Agentic Multi-Format Document Intelligence System\data\raw\CUAD_v1\CUAD_v1\full_contract_txt"

    contracts = load_cuad_txt_contracts(txt_folder, limit=5)

    print(f"Loaded {len(contracts)} contracts\n")
    for c in contracts:
        print(f"File: {c['filename']}")
        print(f"Length: {len(c['text'])} characters")
        print(c["text"][:300].replace("\n", " "))
        print("-" * 80)