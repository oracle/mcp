# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

"""essbase_tools response contracts, failures, and SDK dispatch."""

import json

import pytest

from oracle.data_studio_mcp_server.tools import essbase_tools
from .test_unit import ESS_DISPATCH_CASES
from .tool_assertions import (
    assert_composite_response, assert_confirmation_required, assert_sdk_failure, assert_tools_require_connection,
)


SERVICE = 'essbase'
TOOL_MODULE = essbase_tools


def test_tools_without_connection_return_setup_error(tools):
    assert_tools_require_connection(tools)


_failure_cases = list({tool: (tool, kwargs, path)
                       for tool, kwargs, path in reversed(ESS_DISPATCH_CASES)}.values())


@pytest.mark.parametrize("tool,kwargs,path", _failure_cases)
def test_sdk_failure_is_reported_and_redacted(tools, clients, tool, kwargs, path):
    ctx, sdk, _ = clients
    assert_sdk_failure(tools[tool].fn, ctx, sdk, kwargs, path)


COMPOSITES = [
    ('essbase_describe_database', {'app_name': 'A', 'db_name': 'D'}, [
        ('applications.get_database', 'database'), ('dimensions.list_dimensions', 'dimensions'),
        ('database_settings.get_settings', 'settings'), ('database_settings.get_statistics', 'statistics'),
        ('database_settings.get_storage_statistics', 'storage'),
        ('variables.list_db_variables', 'variables'),
    ]),
    ('essbase_get_script', {'app_name': 'A', 'db_name': 'D', 'script_name': 'S'}, [
        ('scripts.get_script_content', 'content'), ('scripts.validate_script', 'validation'),
    ]),
    ('essbase_manage_security', {'username': 'u'}, [
        ('users.get_user', 'user'), ('users.get_user_provisioning_report', 'provisioning'),
    ]),
    ('essbase_manage_security', {'group_name': 'g'}, [
        ('groups.get_group', 'group'), ('groups.get_group_provisioning_report', 'provisioning'),
        ('groups.get_group_members', 'members'),
    ]),
    ('essbase_server_health', {}, [
        ('about.get', 'about'), ('about.get_instance', 'instance'), ('sessions.list_sessions', 'sessions'),
    ]),
    ('essbase_manage_locks', {'app_name': 'A', 'db_name': 'D'}, [
        ('locks.list_locks', 'locks'), ('locks.list_locked_objects', 'locked_objects'),
        ('locks.list_locked_blocks', 'locked_blocks'),
    ]),
    ('essbase_manage_filters', {'action': 'get', 'app_name': 'A', 'db_name': 'D', 'filter_name': 'F'}, [
        ('filters.get_filter', 'filter'), ('filters.get_filter_rows', 'rows'),
        ('filters.get_permissions', 'permissions'),
    ]),
    ('essbase_manage_groups', {'action': 'get', 'group_id': 'G'}, [
        ('groups.get_group', 'group'), ('groups.get_members', 'members'),
        ('groups.get_provisioning_report', 'provisioning'),
    ]),
    ('essbase_outline_metadata', {'app_name': 'A', 'db_name': 'D', 'category': 'all'}, [
        ('dimensions.list_dimensions', 'dimensions'), ('dimensions.get_smart_lists', 'smart_lists'),
        ('dimensions.get_outline_settings', 'outline_settings'),
        ('dimensions.get_attribute_settings', 'attribute_settings'),
    ]),
    ('essbase_manage_db_settings', {'app_name': 'A', 'db_name': 'D'}, [
        ('database_settings.get_settings', 'settings'),
        ('database_settings.get_startup_settings', 'startup'),
        ('database_settings.get_calculation_settings', 'calculation'),
        ('database_settings.get_cache_settings', 'cache'),
        ('database_settings.get_buffer_settings', 'buffer'),
        ('database_settings.get_compression_settings', 'compression'),
        ('database_settings.get_transaction_settings', 'transactions'),
    ]),
]


@pytest.mark.parametrize("tool,kwargs,steps", COMPOSITES)
@pytest.mark.parametrize("fail_step", ["none", "first", "all"])
def test_composites_preserve_successful_sections_on_partial_failure(
        tools, clients, tool, kwargs, steps, fail_step):
    ctx, sdk, _ = clients
    unwrap = ("variables",) if tool == "essbase_outline_metadata" else ("dimensions", "variables")
    assert_composite_response(tools[tool].fn, ctx, sdk, kwargs, steps, fail_step,
                              envelopes=("dimensions", "variables"), unwrap=unwrap)


_destructive = [(tool, kwargs, path) for tool, kwargs, path in ESS_DISPATCH_CASES if "confirm" in kwargs]


@pytest.mark.parametrize("tool,kwargs,path", _destructive)
@pytest.mark.parametrize("confirm", [None, "wrong-resource"])
def test_destructive_actions_require_matching_confirmation(tools, clients, tool, kwargs, path, confirm):
    ctx, sdk, _ = clients
    assert_confirmation_required(tools[tool].fn, ctx, sdk, kwargs, path, confirm)


@pytest.mark.parametrize("scope,prefix,args", [
    ("server", "server", ()), ("application", "app", ("A",)), ("database", "db", ("A", "D")),
])
@pytest.mark.parametrize("action", ["get", "set", "delete"])
def test_essbase_variable_scopes(tools, clients, scope, prefix, args, action):
    ctx, essbase, _ = clients
    method = getattr(essbase.variables, f'{"update" if action == "set" else action}_{prefix}_variable')
    method.return_value = {"name": "V", "value": "2026"}
    result = json.loads(tools["essbase_manage_variables"].fn(
        action=action, scope=scope, app_name="A", db_name="D", variable_name="V", value="2026",
        confirm="V", ctx=ctx))
    if action == "set":
        method.assert_called_once_with(*args, "V", {"name": "V", "value": "2026"})
    else:
        method.assert_called_once_with(*args, "V")
    assert result == ({"status": "deleted", "variable": "V"} if action == "delete"
                      else {"name": "V", "value": "2026"})


@pytest.mark.parametrize("scope,prefix,args", [
    ("application", "app", ("A",)), ("database", "db", ("A", "D")),
])
def test_essbase_missing_variable_is_created(tools, clients, scope, prefix, args):
    ctx, essbase, _ = clients
    getattr(essbase.variables, f"update_{prefix}_variable").side_effect = RuntimeError("not found")
    create = getattr(essbase.variables, f"create_{prefix}_variable")
    create.return_value = {"name": "V", "value": "2026"}
    result = json.loads(tools["essbase_manage_variables"].fn(
        action="set", scope=scope, app_name="A", db_name="D", variable_name="V", value="2026", ctx=ctx))
    create.assert_called_once_with(*args, {"name": "V", "value": "2026"})
    assert result == {"name": "V", "value": "2026"}


def test_failed_calculation_returns_bounded_log_excerpt(tools, clients):
    ctx, essbase, _ = clients
    essbase.jobs.execute.return_value = {"jobID": 17}
    essbase.jobs.wait_for_completion.return_value = {"statusCode": 400}
    essbase.applications.get_latest_log.return_value = b"x" * 2100 + b"failed"
    result = json.loads(tools["essbase_run_calculation"].fn(
        app_name="A", db_name="D", script_name="CalcAll", ctx=ctx))
    essbase.jobs.wait_for_completion.assert_called_once_with(17)
    assert result == {"statusCode": 400, "log_excerpt": "x" * 1994 + "failed"}
