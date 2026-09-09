#data loading
import os

base_path = r"C:\Users\nidhi\Agentic Multi-Format Document Intelligence System\data\raw\CUAD_v1\CUAD_v1"

for root, dirs, files in os.walk(base_path):
    level = root.replace(base_path, "").count(os.sep)
    indent = "  " * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = "  " * (level + 1)
    for f in files[:5]:
        print(f"{subindent}{f}")
    if len(files) > 5:
        print(f"{subindent}... and {len(files)-5} more files")