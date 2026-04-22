from oracle.oci_iot_mcp_server import server


def test_health_check_uses_imported_version_constant(monkeypatch):
    monkeypatch.setattr(server, "__version__", "9.9.9", raising=False)
    assert server.health_check()["version"] == "9.9.9"
