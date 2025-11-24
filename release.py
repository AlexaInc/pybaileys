import os
import sys

print("--- FIXING PACKAGE ---")

# 1. Ensure bootstrap.py exists with correct content
BOOTSTRAP_CONTENT = r"""import os
import subprocess
import sys
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENGINE_DIR = os.path.join(BASE_DIR, 'engine')
VENDOR_DIR = os.path.join(ENGINE_DIR, 'vendor', 'baileys-main')
NODE_ENV_DIR = os.path.join(BASE_DIR, 'node_env')

SYSTEM_NODE = shutil.which("node")
LOCAL_NODE_BIN = os.path.join(NODE_ENV_DIR, 'bin', 'node') if os.name != 'nt' else os.path.join(NODE_ENV_DIR, 'Scripts', 'node.exe')

def get_node_executable():
    if os.path.exists(LOCAL_NODE_BIN): return LOCAL_NODE_BIN
    if SYSTEM_NODE: return SYSTEM_NODE
    return None

def get_npm_path(node_exec):
    if node_exec == LOCAL_NODE_BIN:
        if os.name == 'nt': return os.path.join(os.path.dirname(node_exec), 'npm.cmd')
        return os.path.join(os.path.dirname(node_exec), 'npm')
    return shutil.which("npm")

def get_npx_path(node_exec):
    bin_dir = os.path.dirname(node_exec)
    if os.name == 'nt': return os.path.join(bin_dir, 'npx.cmd')
    return os.path.join(bin_dir, 'npx')

def install_node_if_needed():
    if get_node_executable(): return
    print("[PyBaileys] Installing isolated Node.js environment...")
    try:
        import nodeenv
        nodeenv.create_environment(env_dir=NODE_ENV_DIR, node_ver="18.16.0", quiet=False)
    except Exception as e:
        raise RuntimeError(f"Failed to install Node.js: {e}")

def build_engine_if_needed():
    node_exec = get_node_executable()
    npm_exec = get_npm_path(node_exec)
    npx_exec = get_npx_path(node_exec)

    if not os.path.exists(os.path.join(ENGINE_DIR, 'node_modules')):
        print("[PyBaileys] Installing engine dependencies...")
        subprocess.check_call([node_exec, npm_exec, 'install'], cwd=ENGINE_DIR)

    lib_path = os.path.join(VENDOR_DIR, 'lib')
    if not os.path.exists(lib_path):
        print("[PyBaileys] Compiling Baileys TypeScript...")
        if not os.path.exists(os.path.join(VENDOR_DIR, 'node_modules')):
            subprocess.check_call([node_exec, npm_exec, 'install'], cwd=VENDOR_DIR)
        subprocess.check_call([node_exec, npx_exec, 'tsc'], cwd=VENDOR_DIR)

def setup():
    install_node_if_needed()
    build_engine_if_needed()
    return get_node_executable()
"""

with open("src/pybaileys/bootstrap.py", "w") as f:
    f.write(BOOTSTRAP_CONTENT)
print("[OK] Recreated src/pybaileys/bootstrap.py")

# 2. Update MANIFEST.in to explicitly include .py files
MANIFEST_CONTENT = r"""recursive-include src/pybaileys/engine *
include src/pybaileys/engine/package.json
global-include *.py
"""
with open("MANIFEST.in", "w") as f:
    f.write(MANIFEST_CONTENT)
print("[OK] Updated MANIFEST.in to include all Python files")

# 3. Update pyproject.toml to Version 1.0.2
TOML_CONTENT = r"""[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "pybaileys"
version = "1.0.2"
description = "A Python wrapper for the Baileys WhatsApp Library"
readme = "README.md"
authors = [{ name = "Hansaka", email = "your@email.com" }]
license = { text = "MIT" }
requires-python = ">=3.7"
dependencies = [
    "websocket-client>=1.5.0",
    "qrcode>=7.0",
    "nodeenv>=1.8.0"
]

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
pybaileys = ["engine/**/*"]
"""
with open("pyproject.toml", "w") as f:
    f.write(TOML_CONTENT)
print("[OK] Bumped version to 1.0.2 in pyproject.toml")

print("\n--- READY TO BUILD ---")
print("Run the following commands:")
print("1. pip uninstall pybaileys -y")
print("2. rm -rf dist build")
print("3. python -m build")
print("4. pip install dist/pybaileys-1.0.2-py3-none-any.whl")
print("5. python testaaa/aa.py")
print("If step 5 works, then run: python -m twine upload dist/*")