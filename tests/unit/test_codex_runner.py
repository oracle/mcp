"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import json
import runpy
from types import SimpleNamespace
import os
from pathlib import Path
import signal
import select
import subprocess
import sys
import threading
import tomllib
import time

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e2e" / "features"))
from codex_runner import (  # noqa: E402
    CodexError,
    isolated_session,
    parse_events,
    prepare_environments,
    run_process,
    translate_hosts,
)


@pytest.fixture(autouse=True)
def offline_executable(monkeypatch):
    # Config/result tests must run on machines without Codex or inference credentials.
    monkeypatch.setenv("CODEX_E2E_EXECUTABLE", sys.executable)
    monkeypatch.setenv("CODEX_API_KEY", "this-is-not-the-secret")


def host_file(tmp_path, servers):
    path = tmp_path / "hosts.json"
    path.write_text(json.dumps({"mcpServers": servers}))
    return path


def test_translation_preserves_cwd_substitutions_and_disabled_servers(tmp_path):
    path = host_file(
        tmp_path,
        {
            "compute": {
                "command": sys.executable,
                "args": ["../server.py"],
                "env": {"OCI_CONFIG_FILE": "${env:OCI_CONFIG_FILE}", "PYTHONPATH": "../src:mocks"},
                "timeout": 42,
            },
            "disabled": {"disabled": True},
        },
    )
    servers = translate_hosts(path, tmp_path / "mock-config", tmp_path / "home")
    assert list(servers) == ["compute"]
    server = servers["compute"]
    assert server["cwd"] == str(tmp_path)
    assert server["required"] is True
    assert server["startup_timeout_sec"] == server["tool_timeout_sec"] == 42
    assert server["args"][0] == "-i"
    assert f"OCI_CONFIG_FILE={tmp_path / 'mock-config'}" in server["args"]
    assert "PYTHONPATH=../src:mocks" in server["args"]
    assert server["args"][-2:] == [sys.executable, "../server.py"]


@pytest.mark.parametrize(
    "settings",
    [
        {"url": "https://example.invalid"},
        {"type": "http"},
        {"timeout": 0},
        {"disabled": "false"},
        {"env": {"TOKEN": "${env:PERSONAL_SECRET}"}},
        {"args": "--not-an-array"},
        {"env": {"OCI_CONFIG_FILE": "/real/credentials"}},
        {"args": [42]},
        {"cwd": "missing"},
        {"env": []},
        {"env": {"BAD-NAME": "value"}},
        {"disabled": True},
    ],
)
def test_translation_rejects_unsupported_or_unsafe_settings(tmp_path, settings):
    path = host_file(tmp_path, {"compute": {"command": sys.executable, **settings}})
    with pytest.raises(CodexError):
        translate_hosts(path, tmp_path / "mock-config", tmp_path / "home")


@pytest.mark.parametrize("servers", [{}, {"bad name": {}}, {"invalid": "settings"}])
def test_translation_rejects_empty_or_invalid_inventory(tmp_path, servers):
    with pytest.raises(CodexError):
        translate_hosts(host_file(tmp_path, servers), tmp_path / "mock", tmp_path / "home")


def test_bad_host_shape_is_reported(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"unexpected":{}}')
    with pytest.raises(CodexError, match="mcpServers"):
        translate_hosts(path, tmp_path / "mock", tmp_path / "home")


def test_mcp_child_does_not_inherit_provider_or_oci_credentials(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_API_KEY", "this-is-not-the-secret")
    monkeypatch.setenv("OCI_PRIVATE_KEY", "this-is-not-the-secret")
    code = "import os,json; print(json.dumps(dict(os.environ)))"
    path = host_file(tmp_path, {"compute": {"command": sys.executable, "args": ["-c", code]}})
    server = translate_hosts(path, tmp_path / "mock-config", tmp_path / "home")["compute"]
    result = subprocess.run([server["command"], *server["args"]], capture_output=True, check=True)
    env = json.loads(result.stdout)
    assert "CODEX_API_KEY" not in env
    assert "OCI_PRIVATE_KEY" not in env
    assert env["HOME"] == str(tmp_path / "home")
    assert env["OCI_CONFIG_FILE"] == str(tmp_path / "mock-config")


def test_session_has_only_test_config_and_cleans_up_auth(tmp_path, monkeypatch):
    source = tmp_path / "personal"
    source.mkdir()
    (source / "auth.json").write_text('{"tokens":{"access_token":"this-is-not-the-secret"}}')
    (source / "config.toml").write_text('[mcp_servers.personal]\ncommand="unwanted"')
    monkeypatch.setenv("CODEX_HOME", str(source))
    monkeypatch.delenv("CODEX_API_KEY", raising=False)
    monkeypatch.setenv("OCI_CONFIG_FILE", "/personal/config")
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:5000")
    path = host_file(tmp_path, {"compute": {"command": sys.executable}})
    with isolated_session(path, tmp_path / "mock-config", "test-model") as session:
        env, command = session.env, session.command
        home = Path(env["CODEX_HOME"])
        config = tomllib.loads((home / "config.toml").read_text())
        assert set(config["mcp_servers"]) == {"compute"}
        assert config["features"]["shell_tool"] is False
        assert config["features"]["view_image"] is False
        assert config["web_search"] == "disabled"
        assert "OCI_CONFIG_FILE" not in env
        assert "HTTPS_PROXY" not in env
        assert home != source
        assert (home / "auth.json").stat().st_mode & 0o777 == 0o600
        assert "--json" in command and command[-1] == "-"
        assert not any("bypass" in arg for arg in command)
    assert not home.exists()
    assert (source / "auth.json").exists()


def test_missing_auth_and_executable_fail_without_touching_personal_state(tmp_path, monkeypatch):
    monkeypatch.delenv("CODEX_API_KEY", raising=False)
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "empty"))
    path = host_file(tmp_path, {"test": {"command": sys.executable}})
    with pytest.raises(CodexError, match="codex login"):
        with isolated_session(path, tmp_path / "mock", "test-model"):
            pass
    monkeypatch.setenv("CODEX_API_KEY", "this-is-not-the-secret")
    monkeypatch.setenv("CODEX_E2E_EXECUTABLE", str(tmp_path / "missing"))
    with pytest.raises(CodexError, match="executable"):
        with isolated_session(path, tmp_path / "mock", "test-model"):
            pass


def events(*items):
    return (
        "\n".join(
            json.dumps(e)
            for e in [
                {"type": "thread.started", "thread_id": "thread-test"},
                {"type": "turn.started"},
                *[{"type": "item.completed", "item": {"id": str(i), **item}} for i, item in enumerate(items)],
                {"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 2}},
            ]
        )
        + "\n"
    )


def call(tool="list_instances", arguments=None, result=None, **kwargs):
    return {
        "type": "mcp_tool_call",
        "server": "compute",
        "tool": tool,
        "arguments": arguments or {},
        "status": "completed",
        "error": None,
        "result": result or {"content": [{"type": "text", "text": '{"id":"ocid1.instance.mock"}'}]},
        **kwargs,
    }


MESSAGE = {"type": "agent_message", "text": "ocid1.instance.mock"}


def test_result_retains_successful_mcp_evidence_and_usage():
    result = parse_events(events(call(), MESSAGE), {"compute"})
    assert result.text == "ocid1.instance.mock"
    assert result.thread_id == "thread-test"
    assert result.usage["input_tokens"] == 10
    assert result.require_call("list_instances")["server"] == "compute"


def test_cli_startup_warning_is_retained_but_does_not_replace_mcp_evidence():
    warning = {
        "type": "item.completed",
        "item": {"id": "warning", "type": "error", "message": "policy fallback"},
    }
    output = events(call(), MESSAGE).replace(
        '{"type": "turn.started"}', json.dumps(warning) + '\n{"type": "turn.started"}'
    )
    result = parse_events(output, {"compute"})
    assert result.warnings == ["policy fallback"]
    result.require_call("list_instances")
    with pytest.raises(CodexError):
        parse_events(events({"type": "error", "message": "runtime error"}, MESSAGE), {"compute"})


@pytest.mark.parametrize(
    "output",
    [
        "not-json\n",
        "{}\n",
        "[]\n",
        events(MESSAGE)[:-3],
        events(MESSAGE).replace('"turn.completed"', '"turn.failed"'),
        events(MESSAGE).replace('"turn.completed"', '"error"'),
        events(),
        events(call(status="in_progress"), MESSAGE),
        events(call(error={"message": 7}), MESSAGE),
        events({"type": "command_execution", "status": "completed"}, MESSAGE),
        events({"type": "web_search"}, MESSAGE),
        events(call(server="personal"), MESSAGE),
        events(MESSAGE).replace('"thread-test"', '""'),
        events(MESSAGE).replace('"text": "ocid1.instance.mock"', '"text": 5'),
        events(MESSAGE).replace('"usage": {"input_tokens": 10, "output_tokens": 2}', '"usage": null'),
        events(MESSAGE) + '{"type":"turn.started"}\n',
    ],
)
def test_invalid_failed_or_shortcut_events_cannot_pass(output):
    with pytest.raises(CodexError):
        parse_events(output, {"compute"})


def test_plausible_answer_does_not_prove_a_call():
    result = parse_events(events(MESSAGE), {"compute"})
    with pytest.raises(AssertionError, match="list_instances"):
        result.require_call("list_instances")


def test_codex_resource_discovery_is_separate_from_operation_evidence():
    discovery = call("list_mcp_resources", server="codex")
    guide = call("read_mcp_resource", {"server": "compute", "uri": "guide://mql"})
    result = parse_events(events(discovery, guide, call("get_metrics_data"), MESSAGE), {"compute"})
    assert [item["tool"] for item in result.calls] == ["get_metrics_data"]
    assert [item["tool"] for item in result.resource_calls] == ["list_mcp_resources", "read_mcp_resource"]
    inventory = parse_events(events(discovery, MESSAGE), {"compute"})
    assert not inventory.calls
    with pytest.raises(AssertionError, match="get_metrics_data"):
        inventory.require_call("get_metrics_data")


@pytest.mark.parametrize("tool", ["list_mcp_resources", "list_mcp_resource_templates"])
def test_native_null_arguments_are_valid_only_for_aggregate_discovery(tool):
    item = call(tool, server="codex")
    item["arguments"] = None  # Native CLI resource helpers serialize absent arguments as JSON null.
    result = parse_events(events(item, MESSAGE), {"compute"})
    assert result.resource_calls[0]["arguments"] is None
    assert not result.calls
    item = call("get_metrics_data")
    item["arguments"] = None
    with pytest.raises(CodexError):
        parse_events(events(item, MESSAGE), {"compute"})


@pytest.mark.parametrize("target,server", [("", "codex"), ("  ", "codex"), (" compute ", "compute")])
def test_resource_discovery_matches_cli_target_normalization(target, server):
    item = call("list_mcp_resources", {"server": target}, server=server)
    result = parse_events(events(item, MESSAGE), {"compute"})
    assert result.resource_calls[0]["arguments"] == {"server": target}
    assert not result.calls


@pytest.mark.parametrize(
    "item",
    [
        call("get_metrics_data", server="codex"),
        call("read_mcp_resource", server="personal"),
        call("list_mcp_resources", {"server": "personal"}, server="codex"),
        call("list_mcp_resources", {"server": 7}, server="codex"),
    ],
)
def test_resource_helpers_cannot_authorize_foreign_servers_or_operations(item):
    with pytest.raises(CodexError):
        parse_events(events(item, MESSAGE), {"compute"})


def test_chained_lookup_requires_an_id_from_the_preceding_result():
    good = call("get_instance", {"instance_id": "ocid1.instance.mock"})
    result = parse_events(events(call(), good, MESSAGE), {"compute"})
    result.require_chain("list_instances", "get_instance", "instance_id")
    bad = call("get_instance", {"instance_id": "ocid1.instance.invented"})
    result = parse_events(events(call(), bad, MESSAGE), {"compute"})
    with pytest.raises(AssertionError, match="returned"):
        result.require_chain("list_instances", "get_instance", "instance_id")


def test_chained_lookup_rejects_a_prefix_of_a_returned_id():
    result = parse_events(
        events(call(), call("get_instance", {"instance_id": "ocid1.instance"}), MESSAGE), {"compute"}
    )
    with pytest.raises(AssertionError, match="returned"):
        result.require_chain("list_instances", "get_instance", "instance_id")


def test_unfinished_mcp_call_cannot_pass_as_an_inventory():
    output = events(MESSAGE)
    pending = json.dumps({"type": "item.started", "item": {"id": "pending", **call()}}) + "\n"
    output = output.replace('{"type": "item.completed"', pending + '{"type": "item.completed"')
    with pytest.raises(CodexError, match="incomplete"):
        parse_events(output, {"compute"})


def test_empty_mcp_result_cannot_prove_success():
    output = events(call(), MESSAGE).replace(
        '"content": [{"type": "text", "text": "{\\"id\\":\\"ocid1.instance.mock\\"}"}]', '"unexpected": true'
    )
    with pytest.raises(CodexError, match="Invalid completed"):
        parse_events(output, {"compute"})


def test_mock_proxy_is_substituted_only_into_mcp_environment(tmp_path):
    path = host_file(
        tmp_path, {"compute": {"command": sys.executable, "env": {"HTTPS_PROXY": "${env:MOCK_OCI_PROXY}"}}}
    )
    server = translate_hosts(path, tmp_path / "mock", tmp_path / "home", "http://127.0.0.1:12345")["compute"]
    assert "HTTPS_PROXY=http://127.0.0.1:12345" in server["args"]


def test_normal_inference_proxy_is_preserved(tmp_path, monkeypatch):
    source = tmp_path / "auth"
    source.mkdir()
    (source / "auth.json").write_text("{}")
    monkeypatch.setenv("CODEX_HOME", str(source))
    monkeypatch.setenv("HTTPS_PROXY", "http://corporate-proxy.example:3128")
    path = host_file(tmp_path, {"compute": {"command": sys.executable}})
    with isolated_session(path, tmp_path / "mock", "test-model") as session:
        assert session.env["HTTPS_PROXY"] == "http://corporate-proxy.example:3128"


def test_scenarios_keep_all_enabled_servers_for_cross_service_prompts(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_API_KEY", "this-is-not-the-secret")
    path = host_file(
        tmp_path,
        {
            "oracle-compute": {"command": sys.executable},
            "oracle-storage": {"command": sys.executable},
            "oracle-disabled": {"disabled": True},
        },
    )
    with isolated_session(path, tmp_path / "mock", "test-model") as session:
        assert set(session.servers) == {"oracle-compute", "oracle-storage"}


def test_prepare_installs_inventory_projects_without_mock_proxy(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    launcher = tmp_path / "uv"
    record = tmp_path / "record"
    launcher.write_text(
        f"#!{sys.executable}\nimport sys,os,json\n"
        f"open({str(record)!r},'w').write(json.dumps([sys.argv[1:],os.environ.get('HTTPS_PROXY')]))\n"
    )
    launcher.chmod(0o700)
    monkeypatch.setenv("HTTPS_PROXY", "http://normal-network.example:3128")
    path = host_file(
        tmp_path,
        {
            "compute": {
                "command": str(launcher),
                "args": ["run", "--project", "project", "--locked", "--no-dev", "server"],
            },
            "disabled": {"disabled": True},
        },
    )
    prepare_environments(path)
    args, proxy = json.loads(record.read_text())
    assert args == ["sync", "--project", str(project), "--locked", "--no-dev"]
    assert proxy == "http://normal-network.example:3128"


def test_prepare_resolves_project_from_the_launch_cwd(tmp_path):
    work = tmp_path / "work"
    (work / "project").mkdir(parents=True)
    launcher = tmp_path / "uv"
    record = tmp_path / "record"
    launcher.write_text(f"#!{sys.executable}\nimport sys\nopen({str(record)!r},'w').write(sys.argv[3])\n")
    launcher.chmod(0o700)
    path = host_file(
        tmp_path,
        {
            "test": {
                "command": str(launcher),
                "cwd": "work",
                "args": ["run", "--project", "project", "--locked", "--no-dev", "entrypoint"],
            }
        },
    )
    prepare_environments(path)
    assert record.read_text() == str(work / "project")


def test_sigterm_cleans_process_group_and_session_directory(tmp_path):
    ready, session_path, fifo = tmp_path / "ready", tmp_path / "session", tmp_path / "pipe"
    os.mkfifo(fifo)
    reader = os.open(fifo, os.O_RDONLY | os.O_NONBLOCK)
    hosts = host_file(tmp_path, {"test": {"command": sys.executable}})
    child = (
        "import os,time;from pathlib import Path;"
        f"fd=os.open({str(fifo)!r},os.O_WRONLY);Path({str(ready)!r}).write_text(str(os.getpid()));time.sleep(60)"
    )
    driver = (
        "import sys;from pathlib import Path;"
        f"sys.path.insert(0,{str(Path(__file__).resolve().parents[1] / 'e2e/features')!r});"
        "from codex_runner import isolated_session,run_process\n"
        f"with isolated_session({str(hosts)!r},{str(tmp_path / 'mock')!r},'test-model') as s:\n"
        f" Path({str(session_path)!r}).write_text(str(s.cwd.parent))\n"
        f" run_process([sys.executable,'-c',{child!r}], '', s.env, s.cwd,timeout=15)\n"
    )
    proc = subprocess.Popen(
        [sys.executable, "-c", driver], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    try:
        deadline = time.monotonic() + 5
        while not ready.exists() and proc.poll() is None and time.monotonic() < deadline:
            time.sleep(0.01)
        assert ready.exists(), "Controlled descendant did not become ready"
        proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=5)
        assert select.select([reader], [], [], 3)[0], "SIGTERM leaked the owned child"
        assert os.read(reader, 1) == b""
        assert not Path(session_path.read_text()).exists(), "SIGTERM leaked session auth/config"
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
        if ready.exists() and ready.read_text():
            try:
                os.killpg(int(ready.read_text()), signal.SIGKILL)
            except ProcessLookupError:
                pass
        os.close(reader)


def test_process_uses_stdin_and_bounds_output(tmp_path):
    result = run_process(
        [sys.executable, "-c", "import sys;print(sys.stdin.read())"],
        "literal $(exit 42)",
        os.environ.copy(),
        tmp_path,
        timeout=5,
    )
    assert result == "literal $(exit 42)\n"
    with pytest.raises(CodexError, match="output"):
        run_process(
            [sys.executable, "-c", "print('x'*100000)"],
            "",
            os.environ.copy(),
            tmp_path,
            timeout=5,
            max_output=100,
        )
    with pytest.raises(CodexError, match="exit 7"):
        run_process([sys.executable, "-c", "raise SystemExit(7)"], "", os.environ.copy(), tmp_path, timeout=5)
    with pytest.raises(CodexError, match="start"):
        run_process([str(tmp_path / "missing")], "", os.environ.copy(), tmp_path, timeout=5)
    with pytest.raises(CodexError, match="UTF-8"):
        run_process(
            [sys.executable, "-c", "import sys;sys.stdout.buffer.write(b'\\xff')"],
            "",
            os.environ.copy(),
            tmp_path,
            timeout=5,
        )
    with pytest.raises(CodexError, match="timeout"):
        run_process([sys.executable], "", os.environ.copy(), tmp_path, timeout=0)


@pytest.mark.parametrize("cancel", [False, True])
def test_timeout_and_cancellation_kill_owned_descendants(tmp_path, cancel):
    # The descendant ignores TERM; checking its actual death catches incomplete group cleanup.
    pid_path, fifo = tmp_path / "pid", tmp_path / "liveness"
    os.mkfifo(fifo)
    reader = os.open(fifo, os.O_RDONLY | os.O_NONBLOCK)
    child = (
        "import os,signal,time;from pathlib import Path;"
        "signal.signal(signal.SIGTERM,signal.SIG_IGN);"
        f"fd=os.open({str(fifo)!r},os.O_WRONLY);"
        f"Path({str(pid_path)!r}).write_text(str(os.getpid()));time.sleep(60)"
    )
    parent = (
        "import subprocess,sys,time;from pathlib import Path;"
        f"p=subprocess.Popen([sys.executable,'-c',{child!r}]);time.sleep(60)"
    )
    timer = threading.Timer(1, lambda: os.kill(os.getpid(), signal.SIGINT)) if cancel else None
    if timer:
        timer.start()
    try:
        with pytest.raises(KeyboardInterrupt if cancel else CodexError):
            run_process(
                [sys.executable, "-c", parent], "", os.environ.copy(), tmp_path, timeout=10 if cancel else 1
            )
    finally:
        if timer:
            timer.cancel()
    try:
        assert pid_path.exists(), "Descendant did not start"
        # EOF proves no live descendant retains the writer, without OS-specific ps/zombie checks.
        assert select.select([reader], [], [], 3)[0], "Descendant retained the pipe after cleanup"
        assert os.read(reader, 1) == b""
    finally:
        os.close(reader)


# Literal outcome contracts: a successful unrelated lookup must not mask a failed operation.
OPERATION_CHECKS = [
    ("cloud-guard", "step_impl_list_problems", "list_problems"),
    ("cloud-guard", "step_impl_get_problem_details", "get_problem_details"),
    (
        "compute-instance-agent",
        "step_impl_list_agent_command_executions",
        "list_instance_agent_command_executions",
    ),
    ("compute-instance-agent", "step_impl_get_agent_command_execution_details", "run_instance_agent_command"),
    ("compute", "step_impl_list_instances", "list_instances"),
    ("compute", "step_impl_get_instance", "get_instance"),
    ("compute", "step_impl_list_images", "list_images"),
    ("compute", "step_impl_get_image", "get_image"),
    ("compute", "step_impl_list_vnic_attachments", "list_vnic_attachments"),
    ("compute", "step_impl_get_vnic_attachment", "get_vnic_attachment"),
    ("faaas", "step_impl_list_families", "list_fusion_environment_families"),
    ("faaas", "step_impl_list_environments", "list_fusion_environments"),
    ("faaas", "step_impl_get_environment", "get_fusion_environment"),
    ("faaas", "step_impl_get_environment_status", "get_fusion_environment_status"),
    ("identity", "step_impl_list_compartments", "list_compartments"),
    ("identity", "step_impl_get_tenancy", "get_tenancy"),
    ("identity", "step_impl_list_ads", "list_availability_domains"),
    ("identity", "step_impl_get_user", "get_current_user"),
    ("identity", "step_impl_list_regions", "list_subscribed_regions"),
    ("logging", "step_impl_list_log_groups", "list_log_groups"),
    ("logging", "step_impl_get_log_group", "get_log_group"),
    ("logging", "step_impl_list_logs", "list_logs"),
    ("logging", "step_impl_get_log", "get_log"),
    ("migration", "step_impl_list_migrations", "list_migrations"),
    ("migration", "step_impl_get_migration", "get_migration"),
    ("monitoring", "step_impl_list_alarms", "list_alarms"),
    ("monitoring", "step_impl_list_metric_definitions", "list_metric_definitions"),
    ("monitoring", "step_impl_get_metrics_data", "get_metrics_data"),
    ("network-load-balancer", "step_impl_list_nlbs", "list_network_load_balancers"),
    ("network-load-balancer", "step_impl_get_nlb", "get_network_load_balancer"),
    ("network-load-balancer", "step_impl_list_listeners", "list_network_load_balancer_listeners"),
    ("network-load-balancer", "step_impl_get_listener", "get_network_load_balancer_listener"),
    ("network-load-balancer", "step_impl_list_backend_sets", "list_network_load_balancer_backend_sets"),
    ("network-load-balancer", "step_impl_get_backend_set", "get_network_load_balancer_backend_set"),
    ("network-load-balancer", "step_impl_list_backends", "list_network_load_balancer_backends"),
    ("networking", "step_impl_list_vcns", "list_vcns"),
    ("networking", "step_impl_get_vcn", "get_vcn"),
    ("networking", "step_impl_list_subnets", "list_subnets"),
    ("networking", "step_impl_get_subnet", "get_subnet"),
    ("networking", "step_impl_list_security_lists", "list_security_lists"),
    ("networking", "step_impl_get_security_list", "get_security_list"),
    ("networking", "step_impl_list_nsgs", "list_network_security_groups"),
    ("networking", "step_impl_get_nsg", "get_network_security_group"),
    ("networking", "step_impl_get_vnic", "get_vnic"),
    ("object-storage", "step_impl_namespace", "get_namespace"),
    ("object-storage", "step_impl_list_buckets", "list_buckets"),
    ("object-storage", "step_impl_bucket_details", "get_bucket_details"),
    ("object-storage", "step_impl_list_objects", "list_objects"),
    ("object-storage", "step_impl_list_object_versions", "list_object_versions"),
    ("registry", "step_impl_list_container_repositories", "list_container_repositories"),
    ("registry", "step_impl_get_container_repository", "get_container_repository"),
    ("resource-search", "step_impl_list_resource_types", "list_resource_types"),
    ("resource-search", "step_impl_list_resources", "list_all_resources"),
    ("resource-search", "step_impl_search_by_display_name", "search_resources"),
    ("resource-search", "step_impl_search_free_text", "search_resources_free_form"),
    ("resource-search", "step_impl_search_by_type", "search_resources_by_type"),
    ("usage", "step_impl_get_summarized_usage", "get_summarized_usage"),
]


@pytest.fixture(scope="module")
def operation_steps():
    directory = Path(__file__).resolve().parents[1] / "e2e/features/steps"
    return {
        server: runpy.run_path(str(directory / f"oci-{server}-mcp-server-steps.py"))
        for server in {row[0] for row in OPERATION_CHECKS}
    }


@pytest.mark.parametrize("server,function,tool", OPERATION_CHECKS)
def test_operation_outcomes_reject_unrelated_success(operation_steps, server, function, tool):
    result = parse_events(events(call("unrelated_lookup"), MESSAGE), {"compute"})
    with pytest.raises(AssertionError, match=tool):
        operation_steps[server][function](SimpleNamespace(result=result))


@pytest.mark.parametrize(
    "status,error",
    [("failed", {"message": "transient service failure"}), ("completed", {"message": "tool error"})],
)
def test_failed_attempt_is_retained_and_successful_retry_can_satisfy_operation(status, error):
    attempt = call(status=status, error=error)
    attempt["result"] = None
    result = parse_events(events(attempt, call(), MESSAGE), {"compute"})
    assert result.failed_calls == [{"id": "0", **attempt}]
    assert len(result.calls) == 1
    result.require_call("list_instances")


def test_failed_discovery_does_not_override_successful_requested_operation(operation_steps):
    failure = call("list_metric_definitions", status="failed", error={"message": "Endpoint not mocked"})
    failure["result"] = None
    output = events(
        failure, call("get_metrics_data"), {"type": "agent_message", "text": "CpuUtilization: 45.5"}
    )
    result = parse_events(output, {"compute"})
    operation_steps["monitoring"]["step_impl_get_metrics_data"](SimpleNamespace(result=result))
    assert result.failed_calls[0]["tool"] == "list_metric_definitions"


def test_failed_requested_operation_cannot_be_replaced_by_unrelated_success(operation_steps):
    failure = call("get_metrics_data", status="failed", error={"message": "service failure"})
    failure["result"] = None
    output = events(call("list_alarms"), failure, {"type": "agent_message", "text": "CpuUtilization: 45.5"})
    result = parse_events(output, {"compute"})
    with pytest.raises(AssertionError, match="get_metrics_data"):
        operation_steps["monitoring"]["step_impl_get_metrics_data"](SimpleNamespace(result=result))


@pytest.mark.parametrize("tool", ["get_tenancy", "get_current_tenancy"])
def test_tenancy_outcome_accepts_equivalent_successful_operations(operation_steps, tool):
    server = "oracle-oci-identity-mcp-server"
    response = {"content": [{"type": "text", "text": '{"id":"ocid1.tenancy.mock"}'}]}
    result = parse_events(
        events(
            call(tool, server=server, result=response),
            {"type": "agent_message", "text": "ocid1.tenancy.mock"},
        ),
        {server},
    )
    operation_steps["identity"]["step_impl_get_tenancy"](SimpleNamespace(result=result))


@pytest.mark.parametrize("kind", ["failed", "isError"])
def test_failed_only_response_has_no_successful_operation_evidence(kind):
    item = call()
    if kind == "failed":
        item["status"] = "failed"
        item["result"] = None
        item["error"] = {"message": "mock failure"}
    else:
        item["result"]["isError"] = True
    result = parse_events(events(item, MESSAGE), {"compute"})
    assert len(result.failed_calls) == 1
    assert not result.calls
    with pytest.raises(AssertionError, match="list_instances"):
        result.require_call("list_instances")


@pytest.mark.parametrize("field,value", [("error", []), ("result", []), ("arguments", None)])
def test_recovery_does_not_accept_malformed_failed_calls(field, value):
    item = call(status="failed", error={"message": "failure"})
    item[field] = value
    with pytest.raises(CodexError, match="Invalid completed"):
        parse_events(events(item, call(), MESSAGE), {"compute"})


def test_success_requires_a_result_and_chain_requires_a_successful_listing():
    item = call()
    item["result"] = None
    with pytest.raises(CodexError, match="Missing successful"):
        parse_events(events(item, MESSAGE), {"compute"})
    result = parse_events(
        events(call(status="failed"), call("get_instance", {"instance_id": "ocid1.instance.mock"}), MESSAGE),
        {"compute"},
    )
    with pytest.raises(AssertionError, match="returned by list_instances"):
        result.require_chain("list_instances", "get_instance", "instance_id")
