"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from pathlib import Path

SCRIPTS_DIRECTORY = Path(__file__).parent / "scripts"

OPENSEARCH_API_GUIDE = "OPENSEARCH_API_GUIDE.md"
WORK_REQUEST_GUIDE = "WORK_REQUEST_GUIDE.md"
TOOL_SURFACE_SUMMARY = "TOOL_SURFACE_SUMMARY.md"


def get_script_content(script_name: str) -> str:
    file_path = SCRIPTS_DIRECTORY / script_name
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()
