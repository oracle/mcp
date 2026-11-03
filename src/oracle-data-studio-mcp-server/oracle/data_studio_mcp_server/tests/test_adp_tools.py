# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

"""adp_tools response contracts, failures, and SDK dispatch."""

import json

import pytest

from oracle.data_studio_mcp_server.tools import adp_tools
from .test_unit import ADP_DISPATCH_CASES
from .tool_assertions import (
    assert_composite_response, assert_confirmation_required, assert_sdk_failure, assert_tools_require_connection,
)


SERVICE = 'adp'
TOOL_MODULE = adp_tools


def test_tools_without_connection_return_setup_error(tools):
    assert_tools_require_connection(tools)


_failure_cases = list({tool: (tool, kwargs, path)
                       for tool, kwargs, path in reversed(ADP_DISPATCH_CASES)}.values())
_failure_cases += [case for case in ADP_DISPATCH_CASES if case[2] == "Ingest.cloud_progress_status"]


@pytest.mark.parametrize("tool,kwargs,path", _failure_cases)
def test_sdk_failure_is_reported_and_redacted(tools, clients, tool, kwargs, path):
    ctx, sdk, _ = clients
    assert_sdk_failure(tools[tool].fn, ctx, sdk, kwargs, path)


COMPOSITES = [
    ('adp_build_analytic_view', {'fact_table': 'SALES'}, [
        ('Analytics.compile', 'compile'), ('Analytics.get_metadata', 'metadata'),
        ('Analytics.get_data_preview', 'data_preview'),
    ]),
    ('adp_analyze_analytic_view', {'av_name': 'AV'}, [
        ('Analytics.get_metadata', 'metadata'), ('Analytics.get_measures_list', 'measures'),
        ('Analytics.get_dimension_names', 'dimensions'), ('Analytics.quality_report', 'quality_report'),
    ]),
]


@pytest.mark.parametrize("tool,kwargs,steps", COMPOSITES)
@pytest.mark.parametrize("fail_step", ["none", "first", "all"])
def test_composites_preserve_successful_sections_on_partial_failure(
        tools, clients, tool, kwargs, steps, fail_step):
    ctx, sdk, _ = clients
    sdk.Analytics.create_auto.return_value = {"name": "AV"}
    sdk.Analytics.is_exist.return_value = True
    assert_composite_response(tools[tool].fn, ctx, sdk, kwargs, steps, fail_step)


_destructive = [(tool, kwargs, path) for tool, kwargs, path in ADP_DISPATCH_CASES if "confirm" in kwargs]


@pytest.mark.parametrize("tool,kwargs,path", _destructive)
@pytest.mark.parametrize("confirm", [None, "wrong-resource"])
def test_destructive_actions_require_matching_confirmation(tools, clients, tool, kwargs, path, confirm):
    ctx, sdk, _ = clients
    assert_confirmation_required(tools[tool].fn, ctx, sdk, kwargs, path, confirm)


@pytest.mark.parametrize("payload,expected", [
    ('[{"AMOUNT": 1}, {"AMOUNT": 2}]', [{"AMOUNT": 1}]),
    ({"items": [{"AMOUNT": 1}, {"AMOUNT": 2}]}, [{"AMOUNT": 1}]),
    ({"rows": [{"AMOUNT": 1}, {"AMOUNT": 2}]}, [{"AMOUNT": 1}]),
])
def test_analytic_view_normalizes_and_bounds_rows(tools, clients, payload, expected):
    ctx, adp, _ = clients
    adp.Analytics.is_exist.return_value = True
    adp.Analytics.get_data_simple.return_value = payload
    result = json.loads(tools["adp_query_analytic_view"].fn(av_name="AV", owner="SALES", max_rows=1, ctx=ctx))
    assert result == {"rows": expected, "truncated": True, "original_row_count": 2, "max_rows": 1}
    adp.Analytics.get_data_simple.assert_called_once_with("AV", "SALES")


@pytest.mark.parametrize("raw", ["SELECT * FROM AV", {"sql": "SELECT * FROM AV"}])
def test_analytic_view_sql_mode_does_not_fetch_data(tools, clients, raw):
    ctx, adp, _ = clients
    adp.Analytics.is_exist.return_value = True
    adp.Analytics.get_sql_simple.return_value = raw
    result = tools["adp_query_analytic_view"].fn(av_name="AV", show_sql=True, ctx=ctx)
    if isinstance(raw, str):
        assert result == raw
    else:
        assert json.loads(result) == raw
    adp.Analytics.get_data_simple.assert_not_called()


def test_annotation_rows_and_literal_escaping(tools, clients):
    ctx, adp, _ = clients
    adp.Misc.run_query.return_value = {"rows": [
        ["SALES", "TABLE", None, "ADMIN", "DESCRIPTION", "Sales"],
        {"COLUMN_NAME": "AMOUNT", "ANNOTATION_NAME": "UNIT", "ANNOTATION_VALUE": "USD"},
        {"column_name": "IGNORED"}, ["short"], "invalid",
    ]}
    result = json.loads(tools["adp_get_annotations"].fn(
        object_name="O'SALES", object_type=None, annotation_owner="O'ADMIN", column_name="O'AMOUNT", ctx=ctx))
    sql = adp.Misc.run_query.call_args.args[0]
    assert "UPPER('O''SALES')" in sql
    assert "UPPER('O''ADMIN')" in sql
    assert "UPPER('O''AMOUNT')" in sql
    assert "UPPER(object_type)" not in sql
    assert result["annotation_count"] == 2
    assert result["annotations"] == {"table": {"DESCRIPTION": "Sales"}, "columns": {"AMOUNT": {"UNIT": "USD"}}}
