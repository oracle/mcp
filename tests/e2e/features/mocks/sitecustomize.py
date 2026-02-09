import os
import sys

import oci.identity

# Use this file to perform patches for individual servers that ignore HTTP/HTTPS proxy settings
# E.g. the OCI identity service has one global endpoint that ignores proxies.
# You can patch the identity client's init function to shove the mocked endpoint in there.

original_init = oci.identity.IdentityClient.__init__


def patched_init(self, config, **kwargs):
    # Change http to https so the Shim triggers the SSL logic
    kwargs["service_endpoint"] = "https://iaas.us-mock-1.oraclecloud.com"
    kwargs["verify"] = False
    return original_init(self, config, **kwargs)


oci.identity.IdentityClient.__init__ = patched_init

# IMPORTANT: Use stderr for logging
sys.stderr.write("!!! IDENTITY PATCH INJECTED VIA SITECUSTOMIZE !!!\n")

config_env = os.environ.get("OCI_CONFIG_FILE", "NOT SET (Using default ~/.oci/config)")
sys.stderr.write(f"!!! DEBUG: Identity Server using config: {config_env} !!!\n")
