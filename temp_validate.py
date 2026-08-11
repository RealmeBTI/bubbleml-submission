import json, ast

with open("kaggle_48x48/kaggle_resolution_48x48.ipynb", "r") as f:
    nb = json.load(f)

for idx, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        source = "".join(cell["source"])
        try:
            ast.parse(source)
            print(f"Cell {idx}: syntax OK")
        except SyntaxError as e:
            print(f"Cell {idx}: SyntaxError: {e}")
