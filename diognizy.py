import subprocess
import os
import sys

print("--- DIAGNOSTIC TOOL ---")

# 1. Check Paths
base_path = os.path.abspath("src/pybaileys/engine")
bridge_path = os.path.join(base_path, "bridge.js")
node_modules_path = os.path.join(base_path, "node_modules")
baileys_lib_path = os.path.join(base_path, "vendor", "baileys-main", "lib", "index.js")

print(f"Checking paths in: {base_path}")

if not os.path.exists(bridge_path):
    print(f"[FAIL] bridge.js not found at {bridge_path}")
    sys.exit(1)
print("[PASS] bridge.js found")

if not os.path.exists(node_modules_path):
    print(f"[FAIL] node_modules not found. Run 'npm install' in {base_path}")
    sys.exit(1)
print("[PASS] node_modules found")

if not os.path.exists(baileys_lib_path):
    print(f"[FAIL] Baileys lib not found at {baileys_lib_path}")
    print("       Did you run 'npx tsc' inside the baileys-main folder?")
    sys.exit(1)
print("[PASS] Baileys lib found")

# 2. Test Node Execution
print("\nAttempting to run bridge.js manually...")
try:
    process = subprocess.Popen(
        ["node", "bridge.js"],
        cwd=base_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Read first few lines
    print("Reading output (timeout 5s)...")
    try:
        outs, errs = process.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        outs, errs = process.communicate()
        print("[PASS] Process started and timed out (this is good, it means it's running)")
        print("Output captured:")
        print(outs)
        if "PORT:" in outs:
            print("\n[SUCCESS] The bridge is working correctly!")
        else:
            print("\n[FAIL] Bridge started but did not print PORT.")
    
    if errs:
        print(f"\n[STDERR LOGS]:\n{errs}")

except FileNotFoundError:
    print("[FAIL] 'node' command not found. Is Node.js installed?")

print("\n--- END DIAGNOSIS ---")