"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from unittest.mock import patch

from oracle.oci_identity_mcp_server import models as identity_models

# Tests targeting models.py (_oci_to_dict and fallbacks)


def test__oci_to_dict_none():
    assert identity_models._oci_to_dict(None) is None


def test__oci_to_dict_dict_passthrough():
    d = {"k": "v"}
    # Use equality (the implementation may return an equivalent dict rather than the same instance)
    assert identity_models._oci_to_dict(d) == d


@patch("oci.util.to_dict")
def test__oci_to_dict_oci_util_path(mock_to_dict):
    class Dummy:
        pass

    obj = Dummy()
    mock_to_dict.return_value = {"ok": True}
    assert identity_models._oci_to_dict(obj) == {"ok": True}
    mock_to_dict.assert_called()


@patch("oci.util.to_dict", side_effect=Exception("no util"))
def test__oci_to_dict_obj_dict_fallback_no_oci_util(mock_to_dict):
    class Dummy:
        def __init__(self):
            self.x = 1
            self._hidden = 2

    obj = Dummy()
    out = identity_models._oci_to_dict(obj)
    # Private attribute should be filtered out
    assert out == {"x": 1}
