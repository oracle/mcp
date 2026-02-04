"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
import sys

from flask import Flask, jsonify, request

app = Flask(__name__)


# Generates OCI-like responses
def oci_res(data):
    return jsonify(data)


# Catch all for debugging
@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "DELETE"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def catch_all(path):
    print(f"MISSING MOCK: {request.method} to /{path}")
    print(f"Query Args: {request.args}")
    return jsonify({"error": "Endpoint not mocked", "path": path}), 404


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200


# Dynamically load and register blueprints from services/
services_dir = os.path.join(os.path.dirname(__file__), "services")
if os.path.exists(services_dir):
    sys.path.insert(0, services_dir)
    for filename in os.listdir(services_dir):
        if filename.endswith("_routes.py") and not filename.startswith("_"):
            module_name = filename[:-3]  # Remove '.py'
            bp_name = filename.replace("_routes.py", "")
            try:
                module = __import__(module_name)
                bp_var = f"{bp_name}_bp"
                if hasattr(module, bp_var):
                    bp = getattr(module, bp_var)
                    app.register_blueprint(bp)
                    print(f"Registered blueprint: {bp_var} from {filename}")
                else:
                    print(f"Warning: Blueprint {bp_var} not found in {filename}")
            except ImportError as e:
                print(f"Error importing {filename}: {e}")
else:
    print("Warning: services directory not found")

if __name__ == "__main__":
    print("Starting OCI mock server...")
    app.run(host="127.0.0.1", port=5001, debug=False, threaded=True)
