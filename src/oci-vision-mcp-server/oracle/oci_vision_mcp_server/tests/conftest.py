"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
for path in (ROOT,):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


@pytest.fixture(autouse=True)
def provide_required_mcp_env(monkeypatch, tmp_path):
    monkeypatch.setenv("OCI_CONFIG_PROFILE", "OC1_ASH")
    monkeypatch.setenv("OCI_REGION", "us-ashburn-1")
    monkeypatch.setenv(
        "OCI_VISION_DEFAULT_COMPARTMENT_ID",
        "ocid1.compartment.oc1..example",
    )
    monkeypatch.setenv("OCI_VISION_RESULT_STORE_DIR", str(tmp_path / "results"))
