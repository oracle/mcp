"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Offline installed-artifact smoke; run with a fresh environment's Python.
"""

import argparse
import hashlib
from importlib import import_module
from importlib.resources import files
import json
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--forbid-root", type=Path, required=True, help="Checkout that must not supply imports")
    parser.add_argument("--catalog-sha256", help="Expected committed resource digest")
    args = parser.parse_args()
    prefix = Path(sys.prefix).resolve()
    forbidden = args.forbid_root.resolve()
    try:
        origins = {}
        for name in ("oracle.oci_cloud_mcp_server", "oracle.oci_cloud_mcp_server.sdk_catalog", "oci", "oracle_mcp_common"):
            module = import_module(name)
            origin = Path(module.__file__).resolve()
            if not origin.is_relative_to(prefix) or origin.is_relative_to(forbidden):
                raise ValueError(f"Unexpected installed module origin: {name}: {origin}")
            origins[name] = str(origin)
        from oracle.oci_cloud_mcp_server.sdk_catalog import load_catalog
        import oracle_mcp_common

        def no_auth(*args, **kwargs):
            raise AssertionError("Installed catalog smoke must not resolve credentials")
        oracle_mcp_common.build_auth_context = no_auth
        oracle_mcp_common.build_idcs_http_auth = no_auth
        catalog = load_catalog()
        resource = files("oracle.oci_cloud_mcp_server").joinpath("sdk_catalog.json").read_bytes()
        digest = hashlib.sha256(resource).hexdigest()
        if args.catalog_sha256 and digest != args.catalog_sha256:
            raise ValueError("Installed SDK catalog differs from the committed resource")
        client = catalog.client("oci.core.ComputeClient")
        assert catalog.client("oci.core.compute_client.ComputeClient") is client
        catalog.operation(client, "list_instances")
        assert catalog.load_client(client).__name__ == "ComputeClient"
        model = catalog.model("oci.core.models.LaunchInstanceDetails")
        assert catalog.model("oci.core.models.launch_instance_details.LaunchInstanceDetails") is model
        assert catalog.load_model(model).__name__ == "LaunchInstanceDetails"
        server = import_module("oracle.oci_cloud_mcp_server.server")
        assert server._catalog is catalog
        print(json.dumps({
            "sdk_version": json.loads(resource)["sdk_version"], "catalog_sha256": digest,
            "clients": len(catalog.clients), "models": len(catalog.models), "origins": origins,
        }, sort_keys=True))
        return 0
    except Exception as exc:
        print(f"Installed catalog smoke failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
