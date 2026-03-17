"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
import sys

import oci

# Use this file to perform patches for individual servers that ignore HTTP/HTTPS proxy settings
# E.g. the OCI identity service has one global endpoint that ignores proxies.
# You can patch the identity client's init function to shove the mocked endpoint in there.

# Identity
original_identity_init = oci.identity.IdentityClient.__init__


def patched_identity_init(self, config, **kwargs):
    # Change http to https so the Shim triggers the SSL logic
    kwargs["service_endpoint"] = "https://iaas.us-mock-1.oraclecloud.com"
    kwargs["verify"] = False
    return original_identity_init(self, config, **kwargs)


oci.identity.IdentityClient.__init__ = patched_identity_init
sys.stderr.write("!!! IDENTITY PATCH INJECTED VIA SITECUSTOMIZE !!!\n")


# Network load balancer search
original_network_load_balancer_init = (
    oci.network_load_balancer.NetworkLoadBalancerClient.__init__
)


def patched_network_load_balancer_init(self, config, **kwargs):
    # Change http to https so the Shim triggers the SSL logic
    kwargs["service_endpoint"] = "https://iaas.us-mock-1.oraclecloud.com"
    kwargs["verify"] = False
    return original_network_load_balancer_init(self, config, **kwargs)


oci.network_load_balancer.NetworkLoadBalancerClient.__init__ = (
    patched_network_load_balancer_init
)
sys.stderr.write("!!! NLB PATCH INJECTED VIA SITECUSTOMIZE !!!\n")


# Object storage
original_object_storage_init = oci.object_storage.ObjectStorageClient.__init__


def patched_object_storage_init(self, config, **kwargs):
    # Change http to https so the Shim triggers the SSL logic
    kwargs["service_endpoint"] = "https://iaas.us-mock-1.oraclecloud.com"
    kwargs["verify"] = False
    return original_object_storage_init(self, config, **kwargs)


oci.object_storage.ObjectStorageClient.__init__ = patched_object_storage_init
sys.stderr.write("!!! OBJECT STORAGE PATCH INJECTED VIA SITECUSTOMIZE !!!\n")


# Usage
original_usage_init = oci.usage_api.UsageapiClient.__init__


def patched_usage_init(self, config, **kwargs):
    # Change http to https so the Shim triggers the SSL logic
    kwargs["service_endpoint"] = "https://iaas.us-mock-1.oraclecloud.com"
    kwargs["verify"] = False
    return original_usage_init(self, config, **kwargs)


oci.usage_api.UsageapiClient.__init__ = patched_usage_init
sys.stderr.write("!!! USAGE PATCH INJECTED VIA SITECUSTOMIZE !!!\n")


# Resource search
original_resource_search_init = oci.resource_search.ResourceSearchClient.__init__


def patched_resource_search_init(self, config, **kwargs):
    # Change http to https so the Shim triggers the SSL logic
    kwargs["service_endpoint"] = "https://iaas.us-mock-1.oraclecloud.com"
    kwargs["verify"] = False
    return original_resource_search_init(self, config, **kwargs)


oci.resource_search.ResourceSearchClient.__init__ = patched_resource_search_init
sys.stderr.write("!!! RESOURCE SEARCH PATCH INJECTED VIA SITECUSTOMIZE !!!\n")


config_env = os.environ.get("OCI_CONFIG_FILE", "NOT SET (Using default ~/.oci/config)")
sys.stderr.write(f"!!! DEBUG: MCP server using config: {config_env} !!!\n")
