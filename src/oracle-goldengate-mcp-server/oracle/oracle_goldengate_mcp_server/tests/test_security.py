"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import json
from unittest.mock import patch

import pytest

from oracle.oracle_goldengate_mcp_server import security
from oracle.oracle_goldengate_mcp_server.http_client import GoldenGateHTTPError, HttpClient


@pytest.mark.parametrize("text", [
    "USERID app, PASSWORD 'alpha beta-tail', OTHER option",
    'USERID app, PASSWORD "alpha beta-tail", OTHER option',
    "USERID app, PASSWORD 'alpha''quote beta-tail', OTHER option",
    'USERID app, PASSWORD "alpha\\\"quote beta-tail", OTHER option',
    "password='alpha beta-tail'",
    'connectionPassword="alpha beta-tail"',
    "{'password': 'alpha beta-tail', 'ok': True}",
    json.dumps({"password": 'alpha"quote beta-tail', "ok": True}),
    "PASSWORD 'alpha beta-tail",  # An incomplete quoted value must fail closed.
    "PASSWORD alpha-beta-tail",
    "Authorization: Bearer alpha-beta-tail",
    "privateKeyPEM=-----BEGIN PRIVATE KEY-----\nalpha\nbeta-tail\n-----END PRIVATE KEY-----",
    "-----BEGIN RSA PRIVATE KEY-----\nalpha\nbeta-tail\n-----END RSA PRIVATE KEY-----",
])
def test_redaction_consumes_complete_credentials(text):
    sanitized = security.redact_text(text)
    assert "[REDACTED]" in sanitized
    assert "alpha" not in sanitized
    assert "beta-tail" not in sanitized


def test_nested_reports_are_redacted_without_losing_safe_fields():
    value = {"reports": ["USERID app, PASSWORD 'alpha beta-tail'"], "rows": 42, "PASSWORD": "alpha beta-tail"}
    sanitized = security.sanitize_data(value)
    assert sanitized["rows"] == 42
    assert sanitized["PASSWORD"] == "[REDACTED]"
    assert "beta-tail" not in json.dumps(sanitized)
    assert value["PASSWORD"] == "alpha beta-tail"


def test_json_text_remains_valid_after_redaction():
    text = json.dumps({"password": 'alpha"quote beta-tail', "rows": 42})
    assert json.loads(security.redact_text(text)) == {"password": "[REDACTED]", "rows": 42}


def test_assigned_password_preserves_assignment_syntax():
    assert security.redact_text("PASSWORD = 'alpha beta-tail'") == "PASSWORD = '[REDACTED]'"


def test_http_errors_expose_status_without_leaking_quoted_password():
    client = HttpClient({"baseUrl": "https://example.invalid"})
    response = type("Response", (), {"status_code": 400, "text": "PASSWORD 'alpha beta-tail'"})()
    with patch.object(client.session, "request", return_value=response), pytest.raises(GoldenGateHTTPError) as error:
        client.post("/example", {})
    assert error.value.status_code == 400
    assert "beta-tail" not in str(error.value)
    client.close()
