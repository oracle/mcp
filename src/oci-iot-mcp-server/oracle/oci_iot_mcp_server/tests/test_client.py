from types import SimpleNamespace

import pytest

from oracle.oci_iot_mcp_server import client
from oracle.oci_iot_mcp_server import __project__, __version__


def test_get_iot_client_caches_per_profile(monkeypatch, tmp_path):
    key_file = tmp_path / "key.pem"
    token_file = tmp_path / "token.txt"
    key_file.write_text("private-key")
    token_file.write_text("security-token")

    def fake_from_file(*, profile_name):
        return {
            "profile_name": profile_name,
            "key_file": str(key_file),
            "security_token_file": str(token_file),
        }

    expected_user_agent = f"{__project__.split('oracle.', 1)[1].split('-server', 1)[0]}/{__version__}"

    monkeypatch.setattr(client.oci.config, "from_file", fake_from_file)
    monkeypatch.setattr(
        client.oci.signer,
        "load_private_key_from_file",
        lambda path, pass_phrase=None: f"pk:{path}",
    )
    monkeypatch.setattr(client.oci.auth.signers, "SecurityTokenSigner", lambda token, key: (token, key))
    monkeypatch.setattr(
        client.oci.iot,
        "IotClient",
        lambda config, signer=None: {
            "profile": config["profile_name"],
            "signer": signer,
            "user_agent": config.get("additional_user_agent"),
        },
    )

    client.clear_iot_client_cache()

    default_client = client.get_iot_client("DEFAULT")
    alt_client = client.get_iot_client("ALT")

    assert default_client["profile"] == "DEFAULT"
    assert alt_client["profile"] == "ALT"
    assert default_client["user_agent"] == expected_user_agent
    assert alt_client["user_agent"] == expected_user_agent
    assert default_client is not alt_client


def test_get_iot_client_auto_falls_back_to_api_key_when_no_security_token(monkeypatch):
    expected_user_agent = f"{__project__.split('oracle.', 1)[1].split('-server', 1)[0]}/{__version__}"

    monkeypatch.setenv("OCI_IOT_AUTH_TYPE", "auto")
    monkeypatch.setattr(
        client.oci.config,
        "from_file",
        lambda *, profile_name: {
            "profile_name": profile_name,
            "tenancy": "ocid1.tenancy.oc1..aaaa",
            "user": "ocid1.user.oc1..aaaa",
            "fingerprint": "aa:bb",
            "key_file": "/tmp/api-key.pem",
            "region": "us-ashburn-1",
        },
    )
    monkeypatch.setattr(
        client.oci.signer,
        "Signer",
        lambda **kwargs: {"kind": "api_key", "kwargs": kwargs},
    )
    monkeypatch.setattr(
        client.oci.iot,
        "IotClient",
        lambda config, signer=None: {"config": config, "signer": signer},
    )

    client.clear_iot_client_cache()

    built_client = client.get_iot_client("DEFAULT")

    assert built_client["signer"]["kind"] == "api_key"
    assert built_client["config"]["additional_user_agent"] == expected_user_agent


def test_get_iot_client_security_token_uses_private_key_pass_phrase(monkeypatch, tmp_path):
    observed = {}
    token_file = tmp_path / "token.txt"
    token_file.write_text("security-token")

    monkeypatch.setenv("OCI_IOT_AUTH_TYPE", "security_token")
    monkeypatch.setattr(
        client.oci.config,
        "from_file",
        lambda *, profile_name: {
            "profile_name": profile_name,
            "key_file": "/tmp/encrypted-key.pem",
            "security_token_file": str(token_file),
            "pass_phrase": "top-secret",
        },
    )

    def fake_load_private_key(path, pass_phrase=None):
        observed["path"] = path
        observed["pass_phrase"] = pass_phrase
        return f"pk:{path}:{pass_phrase}"

    monkeypatch.setattr(client.oci.signer, "load_private_key_from_file", fake_load_private_key)
    monkeypatch.setattr(client.oci.auth.signers, "SecurityTokenSigner", lambda token, key: (token, key))
    monkeypatch.setattr(
        client.oci.iot,
        "IotClient",
        lambda config, signer=None: {"config": config, "signer": signer},
    )

    client.clear_iot_client_cache()

    built_client = client.get_iot_client("DEFAULT")

    assert observed == {"path": "/tmp/encrypted-key.pem", "pass_phrase": "top-secret"}
    assert built_client["signer"] == ("security-token", "pk:/tmp/encrypted-key.pem:top-secret")


def test_get_iot_client_uses_instance_principal_when_configured(monkeypatch):
    signer = SimpleNamespace(
        kind="instance_principal",
        tenancy_id="ocid1.tenancy.oc1..aaaa",
        region="us-phoenix-1",
    )

    monkeypatch.setenv("OCI_IOT_AUTH_TYPE", "instance_principal")
    monkeypatch.setattr(
        client.oci.auth.signers,
        "InstancePrincipalsSecurityTokenSigner",
        lambda: signer,
    )
    monkeypatch.setattr(
        client.oci.iot,
        "IotClient",
        lambda config, signer=None: {"config": config, "signer": signer},
    )

    client.clear_iot_client_cache()

    built_client = client.get_iot_client()

    assert built_client["signer"] is signer
    assert built_client["config"]["region"] == "us-phoenix-1"
    assert built_client["config"]["additional_user_agent"].endswith(f"/{__version__}")


def test_get_iot_client_uses_resource_principal_when_configured(monkeypatch):
    signer = SimpleNamespace(
        kind="resource_principal",
        tenancy_id="ocid1.tenancy.oc1..bbbb",
        region="us-chicago-1",
    )

    monkeypatch.setenv("OCI_IOT_AUTH_TYPE", "resource_principal")
    monkeypatch.setattr(
        client.oci.auth.signers,
        "get_resource_principals_signer",
        lambda: signer,
    )
    monkeypatch.setattr(
        client.oci.iot,
        "IotClient",
        lambda config, signer=None: {"config": config, "signer": signer},
    )

    client.clear_iot_client_cache()

    built_client = client.get_iot_client()

    assert built_client["signer"] is signer
    assert built_client["config"]["region"] == "us-chicago-1"
    assert built_client["config"]["additional_user_agent"].endswith(f"/{__version__}")


def test_get_iot_client_uses_instance_principal_delegation_when_configured(monkeypatch):
    observed = {}
    signer = SimpleNamespace(
        kind="instance_principal_delegation",
        tenancy_id="ocid1.tenancy.oc1..delegation1",
        region="us-ashburn-1",
    )

    monkeypatch.setenv("OCI_IOT_AUTH_TYPE", "instance_principal_delegation")
    monkeypatch.setenv("OCI_IOT_DELEGATION_TOKEN", "delegation-token-123")

    def fake_instance_delegation_signer(**kwargs):
        observed.update(kwargs)
        return signer

    monkeypatch.setattr(
        client.oci.auth.signers,
        "InstancePrincipalsDelegationTokenSigner",
        fake_instance_delegation_signer,
    )
    monkeypatch.setattr(
        client.oci.iot,
        "IotClient",
        lambda config, signer=None: {"config": config, "signer": signer},
    )

    client.clear_iot_client_cache()

    built_client = client.get_iot_client()

    assert observed == {"delegation_token": "delegation-token-123"}
    assert built_client["signer"] is signer
    assert built_client["config"]["region"] == "us-ashburn-1"


def test_get_iot_client_uses_resource_principal_delegation_when_configured(monkeypatch):
    observed = {}
    signer = SimpleNamespace(
        kind="resource_principal_delegation",
        tenancy_id="ocid1.tenancy.oc1..delegation2",
        region="us-sanjose-1",
    )

    monkeypatch.setenv("OCI_IOT_AUTH_TYPE", "resource_principal_delegation")
    monkeypatch.setenv("OCI_IOT_DELEGATION_TOKEN", "delegation-token-456")

    def fake_resource_delegation_signer(*, delegation_token, resource_principal_token_path_provider=None):
        observed["delegation_token"] = delegation_token
        observed["path_provider"] = resource_principal_token_path_provider
        return signer

    monkeypatch.setattr(
        client.oci.auth.signers,
        "get_resource_principal_delegation_token_signer",
        fake_resource_delegation_signer,
    )
    monkeypatch.setattr(
        client.oci.iot,
        "IotClient",
        lambda config, signer=None: {"config": config, "signer": signer},
    )

    client.clear_iot_client_cache()

    built_client = client.get_iot_client()

    assert observed == {"delegation_token": "delegation-token-456", "path_provider": None}
    assert built_client["signer"] is signer
    assert built_client["config"]["region"] == "us-sanjose-1"


def test_get_iot_client_uses_oke_workload_identity_when_configured(monkeypatch):
    observed = {}
    signer = SimpleNamespace(
        kind="oke_workload_identity",
        region="us-phoenix-1",
    )

    monkeypatch.setenv("OCI_IOT_AUTH_TYPE", "oke_workload_identity")
    monkeypatch.setenv("OCI_IOT_OKE_SERVICE_ACCOUNT_TOKEN_PATH", "/tmp/serviceaccount/token")
    monkeypatch.setenv("OCI_IOT_OKE_SERVICE_ACCOUNT_TOKEN", "inline-token")

    def fake_oke_signer(service_account_token_path=None, service_account_token=None, **kwargs):
        observed["service_account_token_path"] = service_account_token_path
        observed["service_account_token"] = service_account_token
        observed["kwargs"] = kwargs
        return signer

    monkeypatch.setattr(
        client.oci.auth.signers,
        "get_oke_workload_identity_resource_principal_signer",
        fake_oke_signer,
    )
    monkeypatch.setattr(
        client.oci.iot,
        "IotClient",
        lambda config, signer=None: {"config": config, "signer": signer},
    )

    client.clear_iot_client_cache()

    built_client = client.get_iot_client()

    assert observed == {
        "service_account_token_path": None,
        "service_account_token": "inline-token",
        "kwargs": {},
    }
    assert built_client["signer"] is signer
    assert built_client["config"]["region"] == "us-phoenix-1"


@pytest.mark.parametrize(
    "auth_type",
    [
        "instance_principal_delegation",
        "resource_principal_delegation",
    ],
)
def test_get_iot_client_requires_delegation_token_for_delegation_modes(monkeypatch, auth_type):
    monkeypatch.setenv("OCI_IOT_AUTH_TYPE", auth_type)
    monkeypatch.delenv("OCI_IOT_DELEGATION_TOKEN", raising=False)
    client.clear_iot_client_cache()

    with pytest.raises(ValueError, match="OCI_IOT_DELEGATION_TOKEN"):
        client.get_iot_client()


def test_get_iot_client_rejects_unknown_auth_type(monkeypatch):
    monkeypatch.setenv("OCI_IOT_AUTH_TYPE", "not-a-real-auth-mode")
    client.clear_iot_client_cache()

    with pytest.raises(ValueError, match="OCI_IOT_AUTH_TYPE"):
        client.get_iot_client("DEFAULT")
