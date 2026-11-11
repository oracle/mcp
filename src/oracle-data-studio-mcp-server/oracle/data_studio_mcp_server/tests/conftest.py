# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

"""Shared SDK mocks and MCP registration for service tool tests."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from mcp.server.fastmcp import FastMCP

from .test_unit import ESS_DISPATCH_CASES, _walk


@pytest.fixture(scope="module")
def tools(request):
    server = FastMCP("tool-tests")
    request.module.TOOL_MODULE.register_tools(server)
    return server._tool_manager._tools


@pytest.fixture
def clients(request):
    sdk, workbench = MagicMock(), MagicMock()
    service = request.module.SERVICE
    if service == "adp":
        sdk.rest.expired = None
        sdk.rest.username = "ADMIN"
        sdk.Ingest.get_credential_list.return_value = []
        sdk.Ingest.get_consumer_groups.return_value = []
    elif service == "essbase":
        for _, _, path in ESS_DISPATCH_CASES:
            _walk(sdk, path).return_value = {}
    else:
        sdk.list_connections.return_value = []
        sdk.list_projects.return_value = []
        sdk.list_schedules.return_value = []
        sdk.check_if_project_exists.return_value = "project-123"
        sdk.check_if_dataload_exists.return_value = (False, None)
        sdk.check_if_workflow_exists.return_value = (False, None)
        sdk.check_if_df_exists.return_value = (False, None)
        sdk.check_if_schedule_exists.return_value = (False, None)
    connection = {"client": sdk, "workbench": workbench} if service == "datatransforms" else sdk
    ctx = SimpleNamespace(request_context=SimpleNamespace(lifespan_context={service: connection}))
    return ctx, sdk, workbench
