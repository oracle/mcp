"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations


_REGISTERED = False


def register_tools() -> None:
    """Import tool modules once so their decorators register with FastMCP."""
    global _REGISTERED
    if _REGISTERED:
        return

    from .vision_api_tools import analyze_image  # noqa: F401
    from .vision_api_tools import parallel_analyze_image  # noqa: F401
    from .vision_api_tools import classify_image  # noqa: F401
    from .vision_api_tools import detect_objects  # noqa: F401
    from .vision_api_tools import detect_faces  # noqa: F401
    from .vision_api_tools import detect_text  # noqa: F401
    from .vision_api_tools import image_jobs  # noqa: F401
    from .object_storage_tools import upload_image_to_object_storage  # noqa: F401
    from .object_storage_tools import list_object_storage_objects  # noqa: F401
    from .object_storage_tools import fetch_object_storage_object  # noqa: F401
    from .support_tools import get_config_status  # noqa: F401
    from .support_tools import get_analysis_result  # noqa: F401

    _REGISTERED = True
