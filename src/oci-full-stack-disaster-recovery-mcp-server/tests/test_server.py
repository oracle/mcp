"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Tests for MCP server helper behavior and tool schema metadata.
"""

from __future__ import annotations

import inspect

import pytest
from pydantic.fields import FieldInfo

from oracle.oci_fsdr_mcp_server import server
from oracle.oci_fsdr_mcp_server.consts import ALLOWED_FSDR_OPERATIONS


def test_tool_parameters_use_pydantic_field_metadata():
    signature = inspect.signature(server.list_dr_protection_groups)
    compartment_id = signature.parameters["compartment_id"].default
    limit = signature.parameters["limit"].default

    assert isinstance(compartment_id, FieldInfo)
    assert compartment_id.description
    assert isinstance(limit, FieldInfo)
    assert limit.description


def test_raw_call_rejects_unknown_operation_before_creating_client():
    with pytest.raises(ValueError, match="Unsupported operation"):
        server.fsdr_raw_call(operation="not_a_real_operation", parameters={})


def test_allowed_operation_literal_matches_allow_list():
    operation = inspect.signature(server.fsdr_raw_call).parameters["operation"].default
    assert isinstance(operation, FieldInfo)
    assert "create_dr_plan_execution" in ALLOWED_FSDR_OPERATIONS


def test_resolve_model_instantiates_polymorphic_oci_model():
    model = server._resolve_model(
        {
            "_type": "CreateObjectStorageLogLocationDetails",
            "bucket": "dr-logs",
            "namespace": "mytenancy",
        }
    )

    assert model.bucket == "dr-logs"
    assert model.namespace == "mytenancy"


def test_main_runs_stdio_without_banner(monkeypatch):
    run_kwargs = {}

    def fake_run(**kwargs):
        run_kwargs.update(kwargs)

    monkeypatch.setattr(server.mcp, "run", fake_run)

    server.main()

    assert run_kwargs == {"show_banner": False}
