import os

root = "."
for path, dirs, files in os.walk(root):
    level = path.replace(root, "").count(os.sep)
    indent = " " * 4 * level
    print(f"{indent}{os.path.basename(path)}/")
    subindent = " " * 4 * (level + 1)
    for f in files:
        print(f"{subindent}{f}")
