import os
import subprocess
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENGINE_DIR = os.path.join(BASE_DIR, 'src', 'pybaileys', 'engine')
VENDOR_DIR = os.path.join(ENGINE_DIR, 'vendor', 'baileys-main')

def run_command(cmd, cwd):
    print(f"[*] Running: {' '.join(cmd)} in {cwd}")
    # Use shell=True on Windows to find npm/npx
    shell = (os.name == 'nt')
    subprocess.check_call(cmd, cwd=cwd, shell=shell)

def pre_build():
    print("--- PRE-BUILDING ASSETS ---")
    
    # 1. Install Engine Dependencies
    print("1. Installing Engine Dependencies...")
    if os.path.exists(os.path.join(ENGINE_DIR, 'node_modules')):
        shutil.rmtree(os.path.join(ENGINE_DIR, 'node_modules'))
    run_command(['npm', 'install', '--production'], cwd=ENGINE_DIR)

    # 2. Install Vendor Dependencies
    print("2. Installing Vendor Dependencies...")
    if os.path.exists(os.path.join(VENDOR_DIR, 'node_modules')):
        shutil.rmtree(os.path.join(VENDOR_DIR, 'node_modules'))
    run_command(['npm', 'install'], cwd=VENDOR_DIR)

    # 3. Compile TypeScript
    print("3. Compiling Baileys TypeScript...")
    run_command(['npx', 'tsc'], cwd=VENDOR_DIR)

    # 4. Cleanup Vendor Dev Dependencies (Optional, to save space)
    # We re-install only production deps to keep package size down
    print("4. Pruning dev dependencies...")
    shutil.rmtree(os.path.join(VENDOR_DIR, 'node_modules'))
    run_command(['npm', 'install', '--production'], cwd=VENDOR_DIR)

    print("\n[SUCCESS] Assets pre-built! You can now run 'python -m build'")

if __name__ == "__main__":
    pre_build()