import nbformat

p = "notebook.ipynb"
nb = nbformat.read(p, as_version=4)
nb['cells'][0]['cell_type'] = 'markdown'
nbformat.write(nb, p)

print("Converted first cell to markdown. Now open notebook.ipynb → Run All → Save.")
