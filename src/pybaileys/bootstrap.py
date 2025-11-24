import os
import sys
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NODE_ENV_DIR = os.path.join(BASE_DIR, 'node_env')

SYSTEM_NODE = shutil.which("node")
LOCAL_NODE_BIN = os.path.join(NODE_ENV_DIR, 'bin', 'node') if os.name != 'nt' else os.path.join(NODE_ENV_DIR, 'Scripts', 'node.exe')

def get_node_executable():
    """Returns path to node."""
    if os.path.exists(LOCAL_NODE_BIN):
        return LOCAL_NODE_BIN
    if SYSTEM_NODE:
        return SYSTEM_NODE
    return None

def install_node_if_needed():
    """Installs portable Node.js if system node is missing."""
    if get_node_executable():
        return

    print("[PyBaileys] System Node.js not found. Installing portable version...")
    try:
        import nodeenv
        # Install Node 18
        nodeenv.create_environment(env_dir=NODE_ENV_DIR, node_ver="18.16.0", quiet=False)
    except Exception as e:
        raise RuntimeError(f"Failed to install Node.js: {e}\nPlease install Node.js manually.")

def setup():
    """Only ensures Node binary exists. Modules are already pre-packaged."""
    install_node_if_needed()
    return get_node_executable()