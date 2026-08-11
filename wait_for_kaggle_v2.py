import subprocess
import time
import sys
import shutil

kernel = "sbmahafujbondhon/bubbleml-resolution-control-96x96-missing"
while True:
    res = subprocess.run(["python3", "-m", "kaggle", "kernels", "status", kernel], capture_output=True, text=True)
    status = res.stdout
    if "complete" in status.lower() or "KernelWorkerStatus.ERROR" in status:
        print("Kernel finished:", status)
        break
    time.sleep(60)

subprocess.run(["rm", "-rf", "/tmp/kaggle_missing_out_v2"])
subprocess.run(["mkdir", "-p", "/tmp/kaggle_missing_out_v2"])
subprocess.run(["python3", "-m", "kaggle", "kernels", "output", kernel, "-p", "/tmp/kaggle_missing_out_v2"])
print("Output downloaded.")
