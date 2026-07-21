"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import json
from typing import Any

import oci


def map_response_data(data: Any) -> Any:
    """Serialize OCI SDK response data into MCP-facing plain values."""

    if data is None:
        return data

    if isinstance(data, bytes | bytearray):
        data = data.decode("utf-8")

    if isinstance(data, str):
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return data

    try:
        return oci.util.to_dict(data)
    except Exception:
        if isinstance(data, list | tuple):
            return [map_response_data(item) for item in data]
        if isinstance(data, dict):
            return {key: map_response_data(value) for key, value in data.items()}
        return data
