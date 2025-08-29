import os
import subprocess
import sys

def pip_install_deps():
    req_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_path])
    except Exception as e:
        print(f"Failed to install dependencies: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    pip_install_deps()
    # Now run the real server
    server_path = os.path.join(os.path.dirname(__file__), "kube-mcp-server.py")
    # Replace this process with the server (pass through args)
    os.execv(sys.executable, [sys.executable, server_path] + sys.argv[1:])

if __name__ == "__main__":
    main()
