"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import ast
from types import SimpleNamespace

import oci
import pytest

import oracle.oci_python_mcp_server.server as server
from oracle.oci_python_mcp_server.server import (
    CLIENTS,
    OciCodeError,
    Pending,
    _materialize,
    _run,
    oci_discover,
    oci_exec,
)


def run(code):
    """Run a script with a recording dispatcher and no OCI credentials."""
    calls = []

    def dispatch(service, client, operation, args, kwargs):
        calls.append(
            {
                "service": service,
                "client": client,
                "operation": operation,
                "args": args,
                "kwargs": kwargs,
            }
        )
        if operation == "get_namespace":
            return "my-namespace"
        if operation == "list_instances":
            return [{"id": "ocid1.instance.oc1..xyz", "display_name": "web-1"}]
        return {"stub": operation}

    result = _run(code, dispatch)
    return calls, result


def test_registry_discovered():
    assert ("core", "ComputeClient") in CLIENTS


def test_service_inferred_from_client():
    result = oci_discover("ComputeClient", "list_instances")
    assert result["service"] == "core"
    assert "compartment_id" in (result["doc"] or "")


def test_discover_lists_clients_by_service():
    assert "ComputeClient" in oci_discover()["core"]


def test_single_call():
    calls, _ = run("ComputeClient.list_instances(compartment_id='ocid1.compartment')")
    assert calls[0]["operation"] == "list_instances"
    assert calls[0]["kwargs"]["compartment_id"] == "ocid1.compartment"


def test_multiline_builds_and_threads_model_variable():
    code = (
        "shape = LaunchInstanceShapeConfigDetails(ocpus=2, memory_in_gbs=16)\n"
        "details = LaunchInstanceDetails(compartment_id='x', shape='VM.Standard.E4.Flex',\n"
        "                                shape_config=shape)\n"
        "ComputeClient.launch_instance(details)\n"
    )
    calls, _ = run(code)
    body = calls[0]["args"][0]
    assert type(body).__name__ == "LaunchInstanceDetails"
    assert type(body.shape_config).__name__ == "LaunchInstanceShapeConfigDetails"
    assert body.shape_config.ocpus == 2


def test_result_of_one_call_feeds_another():
    code = (
        "ns = ObjectStorageClient.get_namespace()\n"
        "ObjectStorageClient.list_buckets(namespace_name=ns, compartment_id='ocid1...')\n"
    )
    calls, _ = run(code)
    assert calls[1]["kwargs"]["namespace_name"] == "my-namespace"


def test_subscript_into_returned_data():
    code = (
        "insts = ComputeClient.list_instances(compartment_id='x')\n"
        "ComputeClient.get_instance(instance_id=insts[0]['id'])\n"
    )
    calls, _ = run(code)
    assert calls[1]["kwargs"]["instance_id"] == "ocid1.instance.oc1..xyz"


def test_bare_ambiguous_model_resolves_via_call_service():
    code = (
        "d = LaunchInstanceDetails(compartment_id='x', shape='VM.Standard.E4.Flex')\n"
        "ComputeClient.launch_instance(d)\n"
    )
    calls, _ = run(code)
    assert calls[0]["args"][0].__class__.__module__.startswith("oci.core.models")


def test_reject_import_statement():
    with pytest.raises(OciCodeError):
        run("import os\nComputeClient.list_instances(compartment_id='x')")


def test_reject_for_loop():
    with pytest.raises(OciCodeError):
        run("for i in []:\n    ComputeClient.list_instances(compartment_id='x')")


def test_reject_undefined_variable():
    with pytest.raises(OciCodeError) as exc_info:
        run("ComputeClient.list_instances(compartment_id=secret)")
    assert exc_info.value.kind == "NameError"


def test_reject_dunder_attribute():
    with pytest.raises(OciCodeError):
        run("ComputeClient.list_instances(compartment_id=(1).__class__)")


def test_reject_arithmetic_bomb():
    with pytest.raises(OciCodeError):
        run("ComputeClient.list_instances(compartment_id=9**9**9)")


def test_reject_shell_via_import_call():
    with pytest.raises(OciCodeError):
        run("__import__('os').system('echo hi')")


def test_unknown_client_suggests():
    with pytest.raises(OciCodeError) as exc_info:
        run("ComputeClinet.list_instances(compartment_id='x')")
    assert exc_info.value.kind == "UnknownClient"
    assert "ComputeClient" in exc_info.value.extra["did_you_mean"]


def test_unknown_operation_suggests():
    with pytest.raises(OciCodeError) as exc_info:
        run("ComputeClient.list_instance(compartment_id='x')")
    assert exc_info.value.kind == "UnknownOperation"
    assert "list_instances" in exc_info.value.extra["did_you_mean"]


def test_unknown_model_rejected():
    with pytest.raises(OciCodeError) as exc_info:
        run("ComputeClient.launch_instance(EvilDetails(x=1))")
    assert exc_info.value.kind == "UnknownModel"


def test_exec_write_gated_by_default(monkeypatch):
    monkeypatch.delenv("OCI_MCP_ENABLE_MUTATIONS", raising=False)
    result = oci_exec("ComputeClient.terminate_instance(instance_id='x')")
    assert result["error"] == "MutationsDisabled"


def test_discover_skips_modules_that_fail_to_import(monkeypatch):
    monkeypatch.setattr(
        server.pkgutil,
        "iter_modules",
        lambda path: [SimpleNamespace(name="bad_service")],
    )

    def fail_import(_name):
        raise RuntimeError("boom")

    monkeypatch.setattr(server.importlib, "import_module", fail_import)

    assert server._discover() == ({}, {})


def test_auth_prefers_instance_principals(monkeypatch):
    monkeypatch.setattr(
        server.oci.auth.signers,
        "InstancePrincipalsSecurityTokenSigner",
        lambda: "signer",
    )

    assert server._auth() == ({}, {"signer": "signer"})


def test_auth_falls_back_to_config_file(monkeypatch):
    def fail_signer():
        raise RuntimeError("not on an instance")

    monkeypatch.setattr(
        server.oci.auth.signers,
        "InstancePrincipalsSecurityTokenSigner",
        fail_signer,
    )
    monkeypatch.setattr(server.oci.config, "from_file", lambda: {"region": "us-ashburn-1"})

    assert server._auth() == ({"region": "us-ashburn-1"}, {})


def test_client_cache_uses_discovered_client(monkeypatch):
    class FakeClient:
        def __init__(self, config, **kwargs):
            self.config = config
            self.kwargs = kwargs

    key = ("fake_service", "FakeClient")
    monkeypatch.setitem(server.CLIENTS, key, FakeClient)
    monkeypatch.setattr(server, "_auth", lambda: ({"region": "r1"}, {"signer": "s"}))
    server._cache.pop(key, None)

    first = server._client(*key)
    second = server._client(*key)

    assert first is second
    assert first.config == {"region": "r1"}
    assert first.kwargs == {"signer": "s"}


def test_resolve_service_hint_success_and_failure():
    key, err = server._resolve("ComputeClient", "core")
    assert err is None
    assert key == ("core", "ComputeClient")

    key, err = server._resolve("ComputeClient", "missing")
    assert key is None
    assert err["error"] == "UnknownClient"


def test_resolve_ambiguous_client(monkeypatch):
    monkeypatch.setitem(server.BY_CLIENT, "SharedClient", ["svc_a", "svc_b"])

    key, err = server._resolve("SharedClient", None)

    assert key is None
    assert err["error"] == "AmbiguousClient"
    assert err["services"] == ["svc_a", "svc_b"]


def test_resolve_client_expr_with_non_dotted_node():
    node = ast.parse("(1).x()", mode="exec").body[0].value.func.value
    assert server._resolve_client_expr(node) == (None, None)


def test_eval_containers_unary_and_subscript():
    _, result = run("x = [1, 2]\ny = (3, 4)\nz = {'a': -1, 'b': +2, 'c': x[1]}\nz")
    assert result == {"a": -1, "b": 2, "c": 2}


def test_reject_invalid_unary_operand():
    with pytest.raises(OciCodeError) as exc_info:
        run("x = -'not-a-number'\nx")
    assert exc_info.value.kind == "DisallowedCode"


def test_reject_bad_subscript():
    with pytest.raises(OciCodeError) as exc_info:
        run("x = []\nx[0]")
    assert exc_info.value.kind == "IndexError"


def test_qualified_model_constructor():
    code = (
        "details = oci.core.models.LaunchInstanceDetails("
        "compartment_id='x', shape='VM.Standard.E4.Flex')\n"
        "ComputeClient.launch_instance(details)\n"
    )

    calls, _ = run(code)

    assert calls[0]["args"][0].__class__.__module__.startswith("oci.core.models")


def test_unknown_qualified_model_rejected():
    with pytest.raises(OciCodeError) as exc_info:
        run("oci.core.models.NotARealModel(x=1)")
    assert exc_info.value.kind == "UnknownModel"


def test_reject_bare_private_name():
    with pytest.raises(OciCodeError) as exc_info:
        run("_PrivateModel(x=1)")
    assert exc_info.value.kind == "DisallowedCode"


def test_reject_private_dotted_attribute():
    with pytest.raises(OciCodeError) as exc_info:
        run("oci.core.models._PrivateModel(x=1)")
    assert exc_info.value.kind == "DisallowedCode"


def test_reject_private_operation():
    with pytest.raises(OciCodeError) as exc_info:
        run("ComputeClient._private()")
    assert exc_info.value.kind == "DisallowedCode"


def test_reject_call_that_is_not_model_or_dispatch():
    with pytest.raises(OciCodeError) as exc_info:
        run("ComputeClient()()")
    assert exc_info.value.kind == "DisallowedCode"


def test_reject_dispatch_kwargs_unpacking():
    with pytest.raises(OciCodeError) as exc_info:
        run("ComputeClient.list_instances(**{})")
    assert exc_info.value.kind == "DisallowedCode"


def test_reject_model_positional_args():
    with pytest.raises(OciCodeError) as exc_info:
        run("LaunchInstanceDetails('x')")
    assert exc_info.value.kind == "DisallowedCode"


def test_reject_model_kwargs_unpacking():
    with pytest.raises(OciCodeError) as exc_info:
        run("LaunchInstanceDetails(**{})")
    assert exc_info.value.kind == "DisallowedCode"


def test_bad_model_field_rejected():
    with pytest.raises(OciCodeError) as exc_info:
        run("d = LaunchInstanceDetails(not_a_field=1)\nComputeClient.launch_instance(d)")
    assert exc_info.value.kind == "BadModelField"


def test_materialize_nested_containers():
    pending = Pending(
        "LaunchInstanceDetails",
        {"compartment_id": "x", "shape": "VM.Standard.E4.Flex"},
        None,
    )

    result = _materialize({"items": [pending], "again": (pending,)}, "core")

    assert result["items"][0].__class__.__name__ == "LaunchInstanceDetails"
    assert result["again"][0].shape == "VM.Standard.E4.Flex"


def test_materialize_unknown_model_rejected():
    with pytest.raises(OciCodeError) as exc_info:
        _materialize(Pending("NotARealModel", {}, None), "core")
    assert exc_info.value.kind == "UnknownModel"


def test_run_rejects_too_long_code(monkeypatch):
    monkeypatch.setattr(server, "MAX_CODE", 3)
    with pytest.raises(OciCodeError) as exc_info:
        run("x = 1")
    assert exc_info.value.kind == "TooLong"


def test_run_rejects_syntax_error():
    with pytest.raises(OciCodeError) as exc_info:
        run("x =")
    assert exc_info.value.kind == "SyntaxError"


def test_run_rejects_too_many_statements(monkeypatch):
    monkeypatch.setattr(server, "MAX_STMTS", 1)
    with pytest.raises(OciCodeError) as exc_info:
        run("x = 1\nx")
    assert exc_info.value.kind == "TooLong"


def test_run_rejects_non_name_assignment():
    with pytest.raises(OciCodeError) as exc_info:
        run("x.y = 1\nx")
    assert exc_info.value.kind == "DisallowedCode"


def test_run_rejects_no_result():
    with pytest.raises(OciCodeError) as exc_info:
        run("x = 1")
    assert exc_info.value.kind == "NoResult"


def test_run_rejects_pending_final_result():
    with pytest.raises(OciCodeError) as exc_info:
        run("LaunchInstanceDetails(compartment_id='x', shape='VM.Standard.E4.Flex')")
    assert exc_info.value.kind == "NoResult"


def test_oci_exec_successful_read_call(monkeypatch):
    class FakeClient:
        def get_instance(self, **kwargs):
            return SimpleNamespace(data=oci.core.models.Instance(id=kwargs["instance_id"]))

    monkeypatch.setattr(server, "_client", lambda service, client: FakeClient())

    result = oci_exec("ComputeClient.get_instance(instance_id='instance1')")

    assert result["data"]["id"] == "instance1"


def test_oci_exec_list_call_uses_pagination(monkeypatch):
    class FakeClient:
        def list_instances(self, **_kwargs):
            raise AssertionError("pagination helper should call this")

    def fake_list_all(method, *args, **kwargs):
        assert method.__name__ == "list_instances"
        assert kwargs["compartment_id"] == "x"
        return SimpleNamespace(data=[oci.core.models.Instance(id="instance1")])

    monkeypatch.setattr(server, "_client", lambda service, client: FakeClient())
    monkeypatch.setattr(server.oci.pagination, "list_call_get_all_results", fake_list_all)

    result = oci_exec("ComputeClient.list_instances(compartment_id='x')")

    assert result["data"][0]["id"] == "instance1"


def test_oci_exec_limits_call_count(monkeypatch):
    class FakeClient:
        def get_instance(self, **_kwargs):
            return SimpleNamespace(data=oci.core.models.Instance(id="instance1"))

    monkeypatch.setattr(server, "_client", lambda service, client: FakeClient())
    code = "\n".join(
        "ComputeClient.get_instance(instance_id='instance1')"
        for _ in range(server.MAX_CALLS + 1)
    )

    result = oci_exec(code)

    assert result["error"] == "TooManyCalls"


def test_oci_exec_wraps_service_error(monkeypatch):
    def raise_service_error(_code, _dispatch):
        raise oci.exceptions.ServiceError(
            status=404,
            code="NotAuthorizedOrNotFound",
            headers={},
            message="missing",
            opc_request_id="request1",
        )

    monkeypatch.setattr(server, "_run", raise_service_error)

    result = oci_exec("ComputeClient.get_instance(instance_id='x')")

    assert result["error"] == "ServiceError"
    assert result["status"] == 404


def test_oci_exec_wraps_type_error(monkeypatch):
    monkeypatch.setattr(
        server,
        "_run",
        lambda _code, _dispatch: (_ for _ in ()).throw(TypeError("bad type")),
    )

    result = oci_exec("ComputeClient.get_instance(instance_id='x')")

    assert result == {"error": "TypeError", "message": "bad type"}


def test_oci_exec_wraps_unexpected_error(monkeypatch):
    monkeypatch.setattr(
        server,
        "_run",
        lambda _code, _dispatch: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    result = oci_exec("ComputeClient.get_instance(instance_id='x')")

    assert result == {"error": "RuntimeError", "message": "boom"}


def test_oci_discover_with_client_only():
    result = oci_discover("ComputeClient")

    assert result["service"] == "core"
    assert "list_instances" in result["operations"]
    assert "launch_instance" in result["write_ops"]


def test_oci_discover_unknown_client_with_service_hint():
    result = oci_discover("NotAClient", service="core")

    assert result["error"] == "UnknownClient"


def test_oci_discover_unknown_operation():
    result = oci_discover("ComputeClient", "list_instance")

    assert result["error"] == "UnknownOperation"
    assert "list_instances" in result["did_you_mean"]


def test_main_runs_mcp(monkeypatch):
    called = []
    monkeypatch.setattr(server.mcp, "run", lambda: called.append(True))

    server.main()

    assert called == [True]
