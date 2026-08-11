import json

with open("kaggle_resolution_control.ipynb", "r") as f:
    nb = json.load(f)

with open("kaggle_pilot_only.ipynb", "r") as f:
    pilot = json.load(f)
    pilot_cell_1 = pilot["cells"][1]["source"] # Download
    pilot_cell_3 = pilot["cells"][3]["source"] # Robust Extract

seeds_11 = "42,100,1234,2025,9999,7,17,314,2718,4242,7777"

new_cells = []
for idx, cell in enumerate(nb["cells"]):

        
    if cell["cell_type"] == "code":
        if idx == 1:
            cell["source"] = pilot_cell_1
        elif idx == 2:
            cell["source"] = pilot_cell_3
            
        source = cell["source"]
        new_source = []
        for line_num, line in enumerate(source):
            if idx == 0 and line_num == 4:
                new_source.append('import os\n')
                new_source.append('if not os.path.exists("/kaggle/working/bubbleml-submission"):\n')
                new_source.append('    os.system("git clone https://github.com/RealmeBTI/bubbleml-submission.git /kaggle/working/bubbleml-submission")\n')

            line = line.replace('96x96', '48x48')
            line = line.replace('96', '48')
            
            if 'SEEDS  = "' in line:
                line = f'SEEDS  = "{seeds_11}"\n'
                
            if 'assert len(saved) == 7' in line:
                line = line.replace('assert len(saved) == 7', 'assert len(saved) == 11')
            if 'Expected 7' in line:
                line = line.replace('Expected 7', 'Expected 11')
            if '(%d/7)' in line:
                line = line.replace('(%d/7)', '(%d/11)')
            if '7 seeds' in line:
                line = line.replace('7 seeds', '11 seeds')
            if '14 checkpoints' in line:
                line = line.replace('14 checkpoints', '22 checkpoints')
            if '== 14' in line:
                line = line.replace('== 14', '== 22')

            if 'EXPECTED_HEAD   =' in line or 'EXPECTED_BRANCH =' in line or 'assert head ==' in line or 'assert branch ==' in line:
                line = "# " + line
                
            # Block GITHUB_PAT and the trailing parenthesis
            if any(x in line for x in ['pat =', 'if not pat:', 'raise RuntimeError', '"GITHUB_PAT not found', '"(Add-ons -> Secrets)', '    )\n', 'remote_url =', 'remote", "set-url"']):
                # Only comment if we are in cell 0
                if idx == 0:
                    line = "# " + line

            new_source.append(line)
        cell["source"] = new_source
    
    new_cells.append(cell)

nb["cells"] = new_cells

with open("kaggle_48x48/kaggle_resolution_48x48.ipynb", "w") as f:
    json.dump(nb, f, indent=1)
