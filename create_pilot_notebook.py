import json

with open("kaggle_resolution_control.ipynb", "r") as f:
    nb = json.load(f)

# Create the verification cell
verify_source = [
    "import torch, sys, time\n",
    "print('PyTorch version:', torch.__version__)\n",
    "print('CUDA available:', torch.cuda.is_available())\n",
    "if torch.cuda.is_available():\n",
    "    print('GPU:', torch.cuda.get_device_name(0))\n",
    "    print('CUDA Capability:', torch.cuda.get_device_capability(0))\n",
    "else:\n",
    "    print('No GPU available!')\n",
    "    sys.exit(1)\n"
]

verify_cell = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": verify_source
}

# The pilot cell needs to measure time
# We can just wrap the subprocess.run call with time.time()
pilot_source = nb["cells"][2]["source"]
new_pilot_source = []
for line in pilot_source:
    if "import subprocess" in line:
        line = line.replace("import subprocess", "import subprocess, time")
    if "subprocess.run([" in line:
        new_pilot_source.append("start_time = time.time()\n")
    new_pilot_source.append(line)
    if "cwd=str(REPO), check=True)" in line:
        new_pilot_source.append("end_time = time.time()\n")
        new_pilot_source.append("total_time = end_time - start_time\n")
        new_pilot_source.append("print(f'Total pilot time: {total_time:.2f} seconds')\n")
        new_pilot_source.append("print(f'Training time per epoch: {total_time/5:.2f} seconds')\n")
        new_pilot_source.append("print(f'Checkpoint path: {PILOT_CKPT}/tfno_seed_42.pt')\n")
        new_pilot_source.append("print(f'Final status: SUCCESS')\n")

nb["cells"][2]["source"] = new_pilot_source

# We only want cell 0, 1, 2, and the verify cell (which goes after cell 1)
# Cell 0: pip install
# Cell 1: download dataset
# Cell 2: Pilot
new_cells = [
    nb["cells"][0],
    nb["cells"][1],
    verify_cell,
    nb["cells"][2]
]

nb["cells"] = new_cells

with open("kaggle_pilot_only.ipynb", "w") as f:
    json.dump(nb, f, indent=1)

