"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from copy import deepcopy
from unittest.mock import Mock

import pytest

from oracle.oracle_goldengate_mcp_server import api, process_safety
from oracle.oracle_goldengate_mcp_server.http_client import GoldenGateHTTPError


@pytest.fixture
def responses():
    return {
        api.get_extract_status("E_INIT"): {"response": {
            "status": "stopped", "processId": 123, "lastStarted": "2026-10-23T10:00:01Z",
        }},
        api.get_extract_details("E_INIT"): {"response": {"source": "tables", "config": ["EXTFILE ./dirdat/I1, PURGE"]}},
        api.get_replicat_details("R_INIT"): {"response": {"source": {"name": "I1", "path": "dirdat"}, "config": ["REPLICAT R_INIT"]}},
        api.get_extract_history("E_INIT"): {"response": {"history": [{
            "started": "2026-10-23T10:00:00Z", "finished": "2026-10-23T10:01:00Z",
            "processId": 123, "status": "stopped", "exitCode": 0, "killedManually": False,
        }]}},
        api.get_extract_report("E_INIT"): {"response": {"lines": ["Process id: 123", "Initial load report"]}},
    }


def test_guard_checks_matching_file_and_current_successful_run(responses):
    client = Mock()
    client.get.side_effect = responses.__getitem__
    evidence = process_safety.validate_initial_load_start(client, "R_INIT", "E_INIT")
    assert evidence["sourceFile"] == "dirdat/I1"
    assert evidence["exitCode"] == 0
    assert evidence["processId"] == 123
    assert client.get.call_args_list[0] == client.get.call_args_list[-1]
    client.post.assert_not_called()


@pytest.mark.parametrize("path,key,value,error", [
    (api.get_extract_status("E_INIT"), "status", "running", "not confirmed STOPPED"),
    (api.get_extract_status("E_INIT"), "processId", None, "execution identity"),
    (api.get_extract_status("E_INIT"), "processId", True, "execution identity"),
    (api.get_extract_status("E_INIT"), "lastStarted", None, "timestamps"),
    (api.get_extract_status("E_INIT"), "lastStarted", "not-a-date", "timestamps"),
    (api.get_extract_status("E_INIT"), "lastStarted", "2026-10-23T10:00:00", "timezone"),
    (api.get_extract_status("E_INIT"), "lastStarted", "2026-10-23T11:00:00Z", "not confirmed successful"),
    (api.get_extract_details("E_INIT"), "source", "tranlogs", "not an Initial Load"),
    (api.get_extract_details("E_INIT"), "config", ["EXTFILE OTHER/I1, PURGE"], "does not match"),
    (api.get_extract_details("E_INIT"), "config", ["EXTTRAIL dirdat/I1"], "does not match"),
    (api.get_extract_details("E_INIT"), "config", None, "configuration is unavailable"),
    (api.get_extract_details("E_INIT"), "config", [123], "configuration is unavailable"),
    (api.get_replicat_details("R_INIT"), "source", "tables", "source is ambiguous"),
    (api.get_replicat_details("R_INIT"), "source", {"name": ""}, "source is ambiguous"),
    (api.get_replicat_details("R_INIT"), "source", {"name": "I1", "path": None}, "source is ambiguous"),
    (api.get_extract_history("E_INIT"), "history", None, "history is unavailable"),
    (api.get_extract_history("E_INIT"), "history", [], "No matching"),
    (api.get_extract_history("E_INIT"), "history", [{"processId": 999}], "No matching"),
])
def test_guard_refuses_missing_ambiguous_and_mismatched_evidence(responses, path, key, value, error):
    responses[path]["response"][key] = value
    client = Mock()
    client.get.side_effect = responses.__getitem__
    with pytest.raises(ValueError, match=error):
        process_safety.validate_initial_load_start(client, "R_INIT", "E_INIT")
    client.post.assert_not_called()


@pytest.mark.parametrize("key,value,error", [
    ("status", "abended", "not confirmed successful"),
    ("exitCode", 1, "not confirmed successful"),
    ("exitCode", None, "not confirmed successful"),
    ("exitCode", False, "not confirmed successful"),
    ("killedManually", True, "not confirmed successful"),
    ("finished", None, "timestamps"),
    ("finished", "2026-10-23T09:00:00Z", "not confirmed successful"),
    ("started", "2026-10-23T10:00:02Z", "not confirmed successful"),
])
def test_guard_rejects_unsuccessful_or_stale_run(responses, key, value, error):
    responses[api.get_extract_history("E_INIT")]["response"]["history"][0][key] = value
    client = Mock()
    client.get.side_effect = responses.__getitem__
    with pytest.raises(ValueError, match=error):
        process_safety.validate_initial_load_start(client, "R_INIT", "E_INIT")
    client.post.assert_not_called()


@pytest.mark.parametrize("report,error", [
    ("", "empty report"), (None, "empty report"),
    ({"response": {"lines": [123]}}, "empty report"),
    ("Extract starting up", "does not identify"),
    ("Process id: 999\nOld completed report", "does not identify"),
    ("Process id: 123\nProcess ABENDED", "failure indicator"),
    ("Process id: 123\nOGG-00990 Stop forced by user", "operator stop"),
    ("Process id: 123\nOGG-01021 Command received from REST API: STOP.", "operator stop"),
])
def test_guard_rejects_incomplete_failed_interrupted_and_old_reports(responses, report, error):
    responses[api.get_extract_report("E_INIT")] = report
    client = Mock()
    client.get.side_effect = responses.__getitem__
    with pytest.raises(ValueError, match=error):
        process_safety.validate_initial_load_start(client, "R_INIT", "E_INIT")
    client.post.assert_not_called()


def test_guard_rejects_a_restart_during_checks(responses):
    client = Mock()
    reads = 0

    def get(path):
        nonlocal reads
        if path == api.get_extract_status("E_INIT"):
            reads += 1
            if reads == 2:
                return {"status": "running", "processId": 456, "lastStarted": "2026-10-23T11:00:00Z"}
        return responses[path]

    client.get.side_effect = get
    with pytest.raises(ValueError, match="changed during inspection"):
        process_safety.validate_initial_load_start(client, "R_INIT", "E_INIT")
    client.post.assert_not_called()


def _generic_client(producer=None):
    producer = producer or {"source": {"tranlogs": "integrated"}, "config": ["EXTTRAIL dirdat/AA"]}
    responses = {
        api.get_replicat_details("R1"): {"source": {"name": "AA", "path": "dirdat"}, "config": ["REPLICAT R1"]},
        api.list_extracts(): {"items": [{"name": "E1"}]},
        api.get_extract_details("E1"): producer,
    }

    def get(path):
        if path == api.get_extract_details("R1"):
            raise GoldenGateHTTPError(404, "not found")
        return responses[path]

    client = Mock()
    client.get.side_effect = get
    return client, responses


def test_generic_start_allows_verified_cdc_producer():
    client, _ = _generic_client()
    process_safety.ensure_generic_start_allowed(client, "R1")
    client.post.assert_not_called()


@pytest.mark.parametrize("producer,error", [
    ({"source": "tables", "config": ["EXTFILE dirdat/AA, PURGE"]}, "start_initial_load_replicat"),
    ({"source": "tables", "config": ["EXTTRAIL dirdat/AA"]}, "No matching local CDC"),
    ({"source": "tranlogs", "config": ["EXTTRAIL other/AA"]}, "No matching local CDC"),
])
def test_generic_start_cannot_bypass_initial_load_guard(producer, error):
    client, _ = _generic_client(producer)
    with pytest.raises(ValueError, match=error):
        process_safety.ensure_generic_start_allowed(client, "R1")
    client.post.assert_not_called()


@pytest.mark.parametrize("collection", [
    {"items": None}, {"items": [{"name": "A!"}]}, {"items": [None]},
    {"items": [], "links": None}, {"items": [], "links": [None]},
    {"items": [{"name": "E1"}] * 129},
    {"items": [], "links": [{"rel": "next", "href": "https://example.invalid/next"}]},
])
def test_generic_start_refuses_ambiguous_or_incomplete_discovery(collection):
    client, responses = _generic_client()
    responses[api.list_extracts()] = collection
    with pytest.raises(ValueError, match="process start was refused"):
        process_safety.ensure_generic_start_allowed(client, "R1")
    client.post.assert_not_called()


@pytest.mark.parametrize("replicat", [
    {"source": "tables", "config": []},
    {"source": {"filename": "dirdat/AA"}, "config": ["SPECIALRUN"]},
])
def test_generic_start_refuses_explicit_initial_load(replicat):
    client, responses = _generic_client()
    responses[api.get_replicat_details("R1")] = replicat
    with pytest.raises(ValueError, match="start_initial_load_replicat"):
        process_safety.ensure_generic_start_allowed(client, "R1")
    client.post.assert_not_called()


def test_generic_start_does_not_treat_auth_failure_as_not_found():
    client = Mock()
    client.get.side_effect = GoldenGateHTTPError(403, "forbidden")
    with pytest.raises(GoldenGateHTTPError):
        process_safety.ensure_generic_start_allowed(client, "R1")
    assert client.get.call_count == 1
    client.post.assert_not_called()


@pytest.mark.parametrize("response", [None, [], {"response": []}, {}])
def test_generic_start_refuses_unrecognized_extract_details(response):
    client = Mock()
    client.get.return_value = response
    with pytest.raises(ValueError, match="process start was refused"):
        process_safety.ensure_generic_start_allowed(client, "E1")
    client.post.assert_not_called()


def test_guard_rejects_newer_incomplete_history_even_with_an_old_success(responses):
    runs = responses[api.get_extract_history("E_INIT")]["response"]["history"]
    newer = deepcopy(runs[0])
    newer.update(started="2026-10-23T11:00:00Z", finished=None)
    runs.append(newer)
    client = Mock()
    client.get.side_effect = responses.__getitem__
    with pytest.raises(ValueError, match="not confirmed successful"):
        process_safety.validate_initial_load_start(client, "R_INIT", "E_INIT")
    client.post.assert_not_called()
