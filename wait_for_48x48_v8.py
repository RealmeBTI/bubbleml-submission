import subprocess
import time
import sys

kernel = "sbmahafujbondhon/bubbleml-resolution-control-48x48"
print(f"Waiting for kernel {kernel} to complete...")
while True:
    res = subprocess.run(["python3", "-m", "kaggle", "kernels", "status", kernel], capture_output=True, text=True)
    status = res.stdout
    if "complete" in status.lower() or "KernelWorkerStatus.ERROR" in status:
        print("Kernel finished:", status)
        break
    time.sleep(60)

subprocess.run(["mkdir", "-p", "/tmp/kaggle_48x48_out8"])
subprocess.run(["python3", "-m", "kaggle", "kernels", "output", kernel, "-p", "/tmp/kaggle_48x48_out8"])
print("Output downloaded to /tmp/kaggle_48x48_out8.")
