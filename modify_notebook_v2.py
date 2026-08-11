import json

with open("kaggle_resolution_control.ipynb", "r") as f:
    nb = json.load(f)

for cell in nb["cells"]:
    if cell["cell_type"] == "code":
        source = cell["source"]
        new_source = []
        for line in source:
            # Change SEEDS
            if 'SEEDS  = "42,100,1234,2025,9999,7,17"' in line:
                line = line.replace('42,100,1234,2025,9999,7,17', '314,2718,4242,7777')
            
            # Change asserts
            if 'assert len(saved) == 7' in line:
                line = line.replace('assert len(saved) == 7', 'assert len(saved) == 4')
            if 'Expected 7' in line:
                line = line.replace('Expected 7', 'Expected 4')
            
            # Change print statements that mention 7
            if '(%d/7)' in line:
                line = line.replace('(%d/7)', '(%d/4)')
            if '7 seeds' in line:
                line = line.replace('7 seeds', '4 seeds')
            if '14 checkpoints' in line:
                line = line.replace('14 checkpoints', '8 checkpoints')

            # Disable git operations in cell 07
            if 'subprocess.run(["git"' in line or "subprocess.run(['git'" in line:
                line = "# " + line
            
            new_source.append(line)
        cell["source"] = new_source

with open("kaggle_resolution_control_missing.ipynb", "w") as f:
    json.dump(nb, f, indent=1)
