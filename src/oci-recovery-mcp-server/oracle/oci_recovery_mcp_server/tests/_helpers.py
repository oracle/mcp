"""
Copyright (c) 2025, 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Shared fakes for the recovery server tests. Not named test_* so pytest does not
collect it; the tests directory is on sys.path, so `from _helpers import ...`
resolves for every test module beside it.
"""

from types import SimpleNamespace


def _response(data, *, has_next_page=False, next_page=None):
    """An OCI SDK response envelope with just the fields the server reads."""
    return SimpleNamespace(
        data=data,
        has_next_page=has_next_page,
        next_page=next_page,
        status=200,
        headers={},
        request_id="request-id",
        opc_request_id="opc-request-id",
    )


def _raise(error):
    """Raise from inside a lambda or a mock side effect."""
    raise error
