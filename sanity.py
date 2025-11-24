import subprocess
import os
import sys

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

print("--- SANITY CHECK START ---")
print("[1] Python print is working.")

try:
    node_v = subprocess.check_output(["node", "-v"], text=True).strip()
    print(f"[2] Node.js found: {node_v}")
except:
    print("[2] ERROR: Node.js not installed")

bridge = "src/pybaileys/engine/bridge.js"
if os.path.exists(bridge):
    print(f"[3] Bridge file found at: {bridge}")
else:
    print(f"[3] FAIL: Bridge file missing at: {bridge}")

print("--- SANITY CHECK END ---")
