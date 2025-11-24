# scripts/convert_notebook.py
# Usage: python scripts/convert_notebook.py notebook.ipynb
import sys
import nbformat
from pathlib import Path

def convert_first_cell_to_markdown(nb_path):
    nb_path = Path(nb_path)
    if not nb_path.exists():
        print("Not found:", nb_path)
        return 1
    nb = nbformat.read(str(nb_path), as_version=4)
    if not nb['cells']:
        print("No cells found in notebook")
        return 1
    nb['cells'][0]['cell_type'] = 'markdown'
    # if the cell had 'outputs' or execution_count, clear them
    nb['cells'][0].pop('outputs', None)
    nb['cells'][0].pop('execution_count', None)
    nbformat.write(nb, str(nb_path))
    print("Converted first cell to markdown:", nb_path)
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/convert_notebook.py path/to/notebook.ipynb")
        sys.exit(1)
    sys.exit(convert_first_cell_to_markdown(sys.argv[1]))
