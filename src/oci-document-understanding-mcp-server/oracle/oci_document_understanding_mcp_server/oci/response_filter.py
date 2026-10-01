"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from typing import Any


def without_confidence(payload: Any) -> Any:
    """Returns a copy of a provider payload with all confidence fields removed."""
    if isinstance(payload, dict):
        return {key: without_confidence(value) for key, value in payload.items() if key != "confidence"}
    if isinstance(payload, list):
        return [without_confidence(value) for value in payload]
    return payload
