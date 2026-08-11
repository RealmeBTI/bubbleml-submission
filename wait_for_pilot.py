import subprocess
import time

kernel = "sbmahafujbondhon/accelerator-test"
while True:
    res = subprocess.run(["python3", "-m", "kaggle", "kernels", "status", kernel], capture_output=True, text=True)
    status = res.stdout
    if "complete" in status.lower() or "error" in status.lower():
        print("Kernel finished:", status)
        break
    time.sleep(30)

subprocess.run(["rm", "-rf", "/tmp/pilot_out"])
subprocess.run(["mkdir", "-p", "/tmp/pilot_out"])
subprocess.run(["python3", "-m", "kaggle", "kernels", "output", kernel, "-p", "/tmp/pilot_out"])
print("Output downloaded.")
