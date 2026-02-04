"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from pathlib import Path

SCRIPTS_DIRECTORY = Path(__file__).parent / "scripts"

MQL_QUERY_DOC = "MQL_QUERY.md"


def get_script_content(script_name: str) -> str:
    file_path = SCRIPTS_DIRECTORY / script_name
    with open(file_path, "r") as f:
        return f.read()
