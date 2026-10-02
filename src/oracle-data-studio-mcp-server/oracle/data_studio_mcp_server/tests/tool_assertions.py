# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

"""Reusable assertions for service tool connection and response contracts."""

import inspect
import json
from types import SimpleNamespace

from .test_unit import _walk


def assert_tools_require_connection(tools):
    ctx = SimpleNamespace(request_context=SimpleNamespace(lifespan_context={}))
    for name, tool in tools.items():
        kwargs = {key: "example" for key, parameter in inspect.signature(tool.fn).parameters.items()
                  if parameter.default is inspect.Parameter.empty and key != "ctx"}
        result = json.loads(tool.fn(ctx=ctx, **kwargs))
        assert "not connected" in result["error"], name
        assert "Set " in result["error"], name


def assert_sdk_failure(fn, ctx, sdk, kwargs, path, *, fallback=None):
    method = _walk(sdk, path)
    method.side_effect = RuntimeError("SDK unavailable password=test-secret")
    if fallback:
        _walk(sdk, fallback).side_effect = method.side_effect
    result = json.loads(fn(ctx=ctx, **kwargs))
    method.assert_called_once()
    assert "SDK unavailable" in json.dumps(result)
    assert "test-secret" not in json.dumps(result)
    assert "error" in result or "_errors" in result


def assert_confirmation_required(fn, ctx, sdk, kwargs, path, confirm):
    result = json.loads(fn(ctx=ctx, **{**kwargs, "confirm": confirm}))
    assert "Refusing" in result["error"]
    _walk(sdk, path).assert_not_called()


def assert_composite_response(fn, ctx, sdk, kwargs, steps, fail_step, *, envelopes=(), unwrap=(), redacted=()):
    payloads = {}
    for path, key in steps:
        payload = {"name": "example"}
        if key in ("connections", "projects", "schedules", "sessions", "dataflows", "workflows", "dataloads",
                   "schemas", "measures", "dimensions", "variables", "quality_report", "data_preview"):
            payload = [payload]
        native = {"items": payload} if key in envelopes else payload
        payloads[key] = payload if key in unwrap else native
        _walk(sdk, path).return_value = native
    failed = steps if fail_step == "all" else steps[:1] if fail_step == "first" else []
    for path, _ in failed:
        _walk(sdk, path).side_effect = RuntimeError("section unavailable password=secret-value")
    result = json.loads(fn(ctx=ctx, **kwargs))
    for path, key in steps:
        _walk(sdk, path).assert_called_once()
        if (path, key) in failed:
            assert key not in result
        else:
            expected = payloads[key]
            if key in redacted:
                expected = ([{**item, "_redacted": True} for item in expected]
                            if isinstance(expected, list) else {**expected, "_redacted": True})
            assert result[key] == expected
    if failed:
        assert len(result["_errors"]) == len(failed)
        assert "section unavailable" in result["_errors"][0]
        assert "secret-value" not in json.dumps(result)
    else:
        assert "_errors" not in result
