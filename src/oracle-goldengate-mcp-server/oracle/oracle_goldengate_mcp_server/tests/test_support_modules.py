"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import base64
import http.client
import json
from pathlib import Path

import pytest
import requests

from oracle.oracle_goldengate_mcp_server import (
    config,
    extract_config,
    http_client,
    map_statement,
    replicat_config,
    table_statement,
)


def test_map_statement_normalize_and_build() -> None:
    assert map_statement.normalize_map_statement("S.T, TARGET D.T") == "MAP S.T, TARGET D.T;"
    assert map_statement.normalize_map_statement("MAP S.T, TARGET D.T;") == "MAP S.T, TARGET D.T;"

    minimal = map_statement.build_map_statement(
        {"source": {"schema": "S", "table": "T", "targetTable": "D.T"}}
    )
    assert minimal == "MAP S.T, TARGET D.T;"

    built = map_statement.build_map_statement(
        {
            "source": {
                "container": "PDB1",
                "schema": "S",
                "table": "T",
                "targetTable": "D.T",
                "partitionObjIds": [1, 2],
            },
            "options": {
                "modCompareCols": "(c1)",
                "colMap": "USEDEFAULTS",
                "compareCols": "ON UPDATE ALL",
                "coordinated": True,
                "def": "DEF1",
                "exceptionsOnly": True,
                "exitParam": "it's ok",
                "eventActions": "IGNORE",
                "filter": "id > 1",
                "handleCollisions": False,
                "insertAllRecords": True,
                "insertAppend": True,
                "keyCols": ["ID", "CODE"],
                "mapAllColumns": False,
                "mapException": "TARGET D.ERR",
                "mapInvisibleColumns": True,
                "repError": "DEFAULT, ABEND",
                "resolveConflict": "UPDATEROWEXISTS",
                "sqlExec": "ID SP1",
                "thread": 4,
                "threadRange": "(1-8)",
                "trimSpaces": True,
                "trimVarSpaces": False,
                "where": "ID > 0",
            },
        }
    )
    assert built.startswith("MAP PDB1.S.T PARTITIONOBJID 1, 2, TARGET D.T")
    assert "EXITPARAM 'it''s ok'" in built
    assert ", HANDLECOLLISIONS" not in built
    assert "NOHANDLECOLLISIONS" in built
    assert built.endswith(";")

    alternatives = map_statement.build_map_statement(
        {
            "source": {"schema": "S", "table": "T", "targetTable": "D.T"},
            "options": {
                "targetDef": "target.def",
                "handleCollisions": True,
                "insertAppend": False,
                "mapAllColumns": True,
                "mapInvisibleColumns": False,
                "trimSpaces": False,
                "trimVarSpaces": True,
            },
        }
    )
    assert "TARGETDEF target.def" in alternatives
    assert "HANDLECOLLISIONS" in alternatives
    assert "NOINSERTAPPEND" in alternatives
    assert "MAPALLCOLUMNS" in alternatives
    assert "NOMAPINVISIBLECOLUMNS" in alternatives
    assert "NOTRIMSPACES" in alternatives
    assert "TRIMVARSPACES" in alternatives


@pytest.mark.parametrize(
    "payload,error",
    [
        ({"source": None}, "source is required"),
        ({"source": {"table": "T", "targetTable": "X"}}, "source.schema is required"),
        ({"source": {"schema": "S", "targetTable": "X"}}, "source.table is required"),
        ({"source": {"schema": "S", "table": "T"}}, "source.targetTable is required"),
        (
            {"source": {"schema": "S", "table": "T", "targetTable": "X"}, "options": {"def": "A", "targetDef": "B"}},
            "mutually exclusive",
        ),
    ],
)
def test_map_statement_validation_errors(payload: dict, error: str) -> None:
    with pytest.raises(ValueError, match=error):
        map_statement.build_map_statement(payload)


def test_table_statement_normalize_and_build() -> None:
    assert table_statement.normalize_table_statement("S.T") == "TABLE S.T;"
    assert table_statement.normalize_table_statement("TABLE S.T;") == "TABLE S.T;"

    minimal = table_statement.build_table_statement({"source": {"schema": "S", "table": "T"}})
    assert minimal == "TABLE S.T;"

    built = table_statement.build_table_statement(
        {
            "source": {
                "container": "PDB1",
                "schema": "S",
                "table": "T",
                "partitionObjIds": [7],
                "targetTable": "D.T",
            },
            "options": {
                "attrCharset": "AL32UTF8",
                "charset": "UTF-8",
                "colCharset": "UTF-8",
                "colMap": "USEDEFAULTS",
                "cols": ["ID", "NAME"],
                "def": "DEF1",
                "eventActions": "IGNORE",
                "exitParam": "a'b",
                "fetchCols": ["ID"],
                "fetchColsExcept": ["C2"],
                "fetchModCols": ["M1"],
                "fetchModColsExcept": ["M2"],
                "fetchBeforeFilter": True,
                "filter": "ID > 1",
                "getBeforeCols": "ALL",
                "keyCols": ["ID"],
                "sqlExec": "ID SP",
                "sqlPredicate": "ID = 1",
                "tokens": {"APP": "ERP", "ENV": "PROD"},
                "trimSpaces": False,
                "trimVarSpaces": True,
                "where": "ID > 0",
            },
        }
    )
    assert built.startswith("TABLE PDB1.S.T PARTITIONOBJID 7, TARGET D.T")
    assert "SQLPREDICATE 'WHERE ID = 1'" in built
    assert "NOTRIMSPACES" in built
    assert "TRIMVARSPACES" in built

    alternatives = table_statement.build_table_statement(
        {
            "source": {"schema": "S", "table": "T"},
            "options": {
                "colsExcept": ["SECRET"],
                "targetDef": "target.def",
                "getBeforeCols": ["ID", "NAME"],
                "trimSpaces": True,
                "trimVarSpaces": False,
            },
        }
    )
    assert "COLSEXCEPT (SECRET)" in alternatives
    assert "TARGETDEF target.def" in alternatives
    assert "GETBEFORECOLS (ID, NAME)" in alternatives
    assert "TRIMSPACES" in alternatives
    assert "NOTRIMVARSPACES" in alternatives


@pytest.mark.parametrize(
    "payload,error",
    [
        ({"source": None}, "source is required"),
        ({"source": {"table": "T"}}, "source.schema is required"),
        ({"source": {"schema": "S"}}, "source.table is required"),
        ({"source": {"schema": "S", "table": "T"}, "options": {"cols": ["A"], "colsExcept": ["B"]}}, "mutually exclusive"),
        ({"source": {"schema": "S", "table": "T"}, "options": {"def": "A", "targetDef": "B"}}, "mutually exclusive"),
    ],
)
def test_table_statement_validation_errors(payload: dict, error: str) -> None:
    with pytest.raises(ValueError, match=error):
        table_statement.build_table_statement(payload)


def test_extract_config_builders() -> None:
    assert extract_config._normalize_boolean(False) == "FALSE"
    assert extract_config._normalize_boolean(0) == "0"
    assert extract_config._build_integrated_params_clause(None) is None
    assert extract_config._build_integrated_params_clause(" parallelism 2 ") == "INTEGRATEDPARAMS (parallelism 2)"
    assert extract_config._build_integrated_params_clause([" wait ", " "]) == "INTEGRATEDPARAMS (wait)"
    assert extract_config._build_integrated_params_clause({"keyValues": {"trace": False}}) == "INTEGRATEDPARAMS (trace FALSE)"
    assert extract_config._build_tranlog_options_clause(None) is None
    assert extract_config._build_tranlog_options_clause(" archivedlogonly ") == "TRANLOGOPTIONS archivedlogonly"
    assert extract_config._build_tranlog_options_clause([" alt ", " "]) == "TRANLOGOPTIONS alt"
    assert extract_config._build_report_count_clause({"every": " 5 MINUTES "}) == "REPORTCOUNT EVERY 5 MINUTES"
    assert extract_config._build_report_count_clause({}) is None
    assert extract_config._build_bounded_recovery_clause({}) is None
    assert extract_config._build_db_options_clause(" integratedparams ") == "DBOPTIONS integratedparams"
    assert extract_config._build_db_options_clause([" a ", " "]) == "DBOPTIONS a"
    assert extract_config._build_db_options_clause({}) is None

    lines = extract_config.build_advanced_extract_parameters(
        {
            "disableHeartbeatTable": True,
            "tranlogOptions": {
                "clauses": ["DBLOGREADER"],
                "integratedParams": {"entries": ["parallelism 4"], "keyValues": {"trace": True}},
                "additional": ["ALT"],
            },
            "reportCount": {"every": {"value": 10, "unit": "MINUTES"}, "records": 100, "rate": True, "additional": ["RESET"]},
            "boundedRecovery": {"interval": "30MIN", "dir": "./br", "additional": ["NOW"]},
            "dbOptions": {"entries": ["FETCHBATCHSIZE 5000"], "additional": ["X 1"]},
            "sourceCatalog": "PDB1",
            "ddl": ["INCLUDE MAPPED", "EXCLUDE ALL"],
            "additionalParameters": ["DYNAMICRESOLUTION"],
        }
    )
    assert "DISABLE_HEARTBEAT_TABLE" in lines
    assert any(line.startswith("TRANLOGOPTIONS DBLOGREADER") for line in lines)
    assert any("INTEGRATEDPARAMS" in line for line in lines)
    assert any(line.startswith("REPORTCOUNT") for line in lines)
    assert any(line.startswith("BR ") for line in lines)
    assert "SOURCECATALOG PDB1" in lines
    assert "DDL INCLUDE MAPPED" in lines
    assert "DYNAMICRESOLUTION" in lines

    assert extract_config.build_advanced_extract_parameters(None) == []
    assert extract_config.build_advanced_extract_parameters({"ddl": "INCLUDE ALL"}) == ["DDL INCLUDE ALL"]


def test_replicat_config_builders_and_errors() -> None:
    assert replicat_config._build_db_options(None) is None
    assert replicat_config._build_db_options(" allowduptargetmap ") == "DBOPTIONS allowduptargetmap"
    assert replicat_config._build_db_options([" a ", " "]) == "DBOPTIONS a"
    assert replicat_config._build_db_options({"entries": [" one "], "additional": [" two "]}) == "DBOPTIONS one, two"
    assert replicat_config._build_batch_sql(None) == []
    assert replicat_config._build_batch_sql(" mode ops ") == ["BATCHSQL mode ops"]
    assert replicat_config.build_advanced_replicat_parameters(None) == {
        "lines": [],
        "mode": {"type": "nonintegrated", "parallel": True},
    }

    payload = {
        "credential": ["USERIDALIAS C DOMAIN D"],
        "applyParallelism": 3,
        "dbOptions": ["LIMITROWS 10"],
        "batchSql": ["MODE OPS"],
        "ddlError": "DEFAULT, ABEND",
        "repError": "DEFAULT, ABEND",
        "ddlOptions": "ADDTRANDATA",
        "sourceCatalog": "PDB1",
        "obey": "file.prm",
        "mapParallelism": 8,
        "splitTransRecs": 100,
        "lookAheadTransactions": 50,
        "chunkSize": 1000,
        "additionalParameters": ["ASSUMETARGETDEFS"],
        "checkpointTable": "SCH.CHK",
        "modeType": "integrated",
        "modeParallel": False,
    }
    built = replicat_config.build_advanced_replicat_parameters(payload)
    assert built["credentialLines"] == ["USERIDALIAS C DOMAIN D"]
    assert built["mode"] == {"type": "integrated", "parallel": False}
    assert built["checkpointTable"] == "SCH.CHK"
    assert any(line.startswith("DBOPTIONS") for line in built["lines"])
    assert any(line.startswith("BATCHSQL") for line in built["lines"])

    with pytest.raises(ValueError, match="mutually exclusive"):
        replicat_config.build_advanced_replicat_parameters(
            {"applyParallelism": 2, "minApplyParallelism": 1}
        )
    with pytest.raises(ValueError, match="mapParallelism"):
        replicat_config.build_advanced_replicat_parameters(
            {"modeType": "parallel", "mapParallelism": 4}
        )


def test_config_read_from_password_env_and_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for key in [
        "OGG_BASE_URL",
        "OGG_USERNAME",
        "OGG_PASSWORD",
        "OGG_PASSWORD_FILE",
        "OGG_PASSWORD_SECRET_OCID",
        "OCI_REGION",
        "OCI_TENANCY_OCID",
        "OCI_USER_OCID",
        "OCI_KEY_FINGERPRINT",
        "OCI_PRIVATE_KEY_FILE",
    ]:
        monkeypatch.delenv(key, raising=False)

    monkeypatch.setenv("OGG_BASE_URL", "https://example.com")
    monkeypatch.setenv("OGG_USERNAME", "'user'")
    monkeypatch.setenv("OGG_PASSWORD", '"pass"')
    cfg = config.read_config()
    assert cfg["username"] == "user"
    assert cfg["password"] == "pass"

    pwd_file = tmp_path / "pwd.txt"
    pwd_file.write_text("filepass\n", encoding="utf-8")
    monkeypatch.setenv("OGG_PASSWORD_FILE", str(pwd_file))
    monkeypatch.delenv("OGG_PASSWORD", raising=False)
    cfg2 = config.read_config()
    assert cfg2["password"] == "filepass"


def test_config_read_from_secret_ocid(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    key_file = tmp_path / "oci.pem"
    key_file.write_text("-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----", encoding="utf-8")

    monkeypatch.setenv("OGG_BASE_URL", "https://example.com")
    monkeypatch.setenv("OGG_USERNAME", "user")
    monkeypatch.setenv("OGG_PASSWORD_SECRET_OCID", "ocid1.secret.oc1..x")
    monkeypatch.setenv("OCI_REGION", "us-phoenix-1")
    monkeypatch.setenv("OCI_TENANCY_OCID", "ocid1.tenancy.oc1..x")
    monkeypatch.setenv("OCI_USER_OCID", "ocid1.user.oc1..x")
    monkeypatch.setenv("OCI_KEY_FINGERPRINT", "aa:bb")
    monkeypatch.setenv("OCI_PRIVATE_KEY_FILE", str(key_file))

    monkeypatch.setattr(
        config,
        "_signed_get",
        lambda *_: {"secretBundleContent": {"content": base64.b64encode(b"secretpass").decode("utf-8")}},
    )

    cfg = config.read_config()
    assert cfg["password"] == "secretpass"


def test_password_file_decoding_and_errors(tmp_path: Path) -> None:
    utf16_file = tmp_path / "pwd-utf16.txt"
    utf16_file.write_bytes(b"\xff\xfe" + " secret ".encode("utf-16-le"))
    assert config._read_password_from_file(str(utf16_file)) == "secret"

    invalid_file = tmp_path / "invalid.txt"
    invalid_file.write_bytes(b"\xff")
    with pytest.raises(ValueError, match="Unable to decode"):
        config._read_password_from_file(str(invalid_file))

    with pytest.raises(ValueError, match="Unable to read"):
        config._read_password_from_file(str(tmp_path / "missing.txt"))


def test_signed_get_success_and_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "sign_oci_request", lambda *_args, **_kwargs: {"authorization": "sig"})

    class _Response:
        def __init__(self, status: int, body: str):
            self.status = status
            self._body = body

        def read(self):
            return self._body.encode("utf-8")

    class _Connection:
        next_response = _Response(200, '{"ok": true}')
        requests = []

        def __init__(self, hostname: str):
            self.hostname = hostname

        def request(self, method: str, path: str, headers: dict):
            self.requests.append((self.hostname, method, path, headers))

        def getresponse(self):
            return self.next_response

    monkeypatch.setattr(http.client, "HTTPSConnection", _Connection)

    assert config._signed_get({}, "secrets.example.com", "/secret") == {"ok": True}
    assert _Connection.requests == [
        ("secrets.example.com", "GET", "/secret", {"authorization": "sig"})
    ]

    _Connection.next_response = _Response(404, "missing")
    with pytest.raises(RuntimeError, match="HTTP 404: missing"):
        config._signed_get({}, "secrets.example.com", "/missing")


def test_config_validation_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OGG_BASE_URL", raising=False)
    with pytest.raises(ValueError, match="OGG_BASE_URL"):
        config.read_config()

    monkeypatch.setenv("OGG_BASE_URL", "https://example.com")
    monkeypatch.delenv("OGG_USERNAME", raising=False)
    monkeypatch.delenv("OGG_PASSWORD", raising=False)
    monkeypatch.delenv("OGG_PASSWORD_FILE", raising=False)
    monkeypatch.delenv("OGG_PASSWORD_SECRET_OCID", raising=False)
    with pytest.raises(ValueError, match="Basic auth requires"):
        config.read_config()

    monkeypatch.setenv("OGG_USERNAME", "user")
    monkeypatch.setenv("OGG_PASSWORD_SECRET_OCID", "ocid1.secret.oc1..x")
    with pytest.raises(ValueError, match="OCI_REGION"):
        config.read_config()

    monkeypatch.setenv("OCI_REGION", "us-phoenix-1")
    with pytest.raises(ValueError, match="OCI signer credentials"):
        config.read_config()


def test_http_client_helpers_and_request_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    assert http_client._classify_request_error(requests.exceptions.ConnectTimeout()) == "Connection timed out"
    assert http_client._classify_request_error(requests.exceptions.ReadTimeout()) == "Request timed out while waiting for response"
    assert http_client._classify_request_error(requests.exceptions.ConnectionError("connection refused")) == "Connection refused"
    assert http_client._classify_request_error(requests.exceptions.ConnectionError("other")) == "Network connection error"
    assert http_client._classify_request_error(requests.exceptions.InvalidURL()) == "Invalid deployment URL"
    assert http_client._classify_request_error(requests.exceptions.RequestException()) == "HTTP request failed"

    with pytest.raises(ValueError, match="OCI signer is not fully configured"):
        http_client.sign_oci_request({}, "GET", "/x", "example.com")

    monkeypatch.setattr(http_client, "load_pem_private_key", lambda *args, **kwargs: object())
    with pytest.raises(ValueError, match="RSA private key"):
        http_client.sign_oci_request(
            {
                "tenancyOCID": "tenancy",
                "userOCID": "user",
                "keyFingerprint": "fp",
                "privateKeyPEM": "pem",
            },
            "GET",
            "/x",
            "example.com",
        )

    class _FakeKey:
        def sign(self, *_args, **_kwargs):
            return b"sig"

    monkeypatch.setattr(http_client, "RSAPrivateKey", _FakeKey)
    monkeypatch.setattr(http_client, "load_pem_private_key", lambda *args, **kwargs: _FakeKey())

    headers = http_client.sign_oci_request(
        {
            "tenancyOCID": "tenancy",
            "userOCID": "user",
            "keyFingerprint": "fp",
            "privateKeyPEM": "pem",
            "passphrase": "",
        },
        "GET",
        "/x",
        "example.com",
        body=json.dumps({"x": 1}),
    )
    assert headers["host"] == "example.com"
    assert "authorization" in headers
    assert headers["content-type"] == "application/json"

    headers_without_body = http_client.sign_oci_request(
        {
            "tenancyOCID": "tenancy",
            "userOCID": "user",
            "keyFingerprint": "fp",
            "privateKeyPEM": "pem",
            "passphrase": "",
        },
        "GET",
        "/x",
        "example.com",
    )
    assert "content-length" not in headers_without_body

    class _Resp:
        def __init__(self, status_code: int, text: str, json_payload=None):
            self.status_code = status_code
            self.text = text
            self._json_payload = json_payload

        def json(self):
            if isinstance(self._json_payload, Exception):
                raise self._json_payload
            return self._json_payload

    class _Session:
        def __init__(self):
            self.next = _Resp(200, "ok", {"ok": True})

        def request(self, **_kwargs):
            if isinstance(self.next, Exception):
                raise self.next
            return self.next

    client = http_client.HttpClient({"baseUrl": "https://example.com", "authMode": "basic", "username": "u", "password": "p"})
    fake = _Session()
    client.session = fake

    assert client.get("/ok") == {"ok": True}

    fake.next = _Resp(200, "plain", ValueError("not json"))
    assert client.get("/text") == "plain"

    fake.next = _Resp(200, "yaml", {"unused": 1})
    assert client.get("/yaml", response_text=True) == "yaml"

    fake.next = _Resp(500, "boom", None)
    with pytest.raises(RuntimeError, match="500"):
        client.get("/fail")

    fake.next = requests.exceptions.ConnectionError("name or service not known")
    with pytest.raises(RuntimeError, match="DNS resolution failed"):
        client.get("/conn")

    captured = []

    class _CapturingSession:
        def request(self, **kwargs):
            captured.append(kwargs)
            return _Resp(200, "ok", {"ok": True})

    client = http_client.HttpClient({"baseUrl": "https://example.com/", "authMode": "none"})
    client.session = _CapturingSession()

    assert client.get("https://override.example.com/ok", headers={"X-Test": "1"}) == {"ok": True}
    assert captured[-1]["url"] == "https://override.example.com/ok"
    assert captured[-1]["headers"]["X-Test"] == "1"
    assert captured[-1]["auth"] is None

    assert client.post("/post", {"x": 1}) == {"ok": True}
    assert captured[-1]["method"] == "POST"
    assert captured[-1]["data"] == '{"x": 1}'

    assert client.patch("/patch", {"y": 2}) == {"ok": True}
    assert captured[-1]["method"] == "PATCH"

    assert client.delete("/delete") == {"ok": True}
    assert captured[-1]["method"] == "DELETE"
