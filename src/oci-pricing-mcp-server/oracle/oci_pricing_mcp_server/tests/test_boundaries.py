"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import asyncio
import json
import subprocess
import sys

import httpx
import pytest

from oracle.oci_pricing_mcp_server import server


def test_optional_enrichment_cannot_swallow_the_offline_guard(monkeypatch):
    monkeypatch.setattr(server, "ALT_CCY", "EUR")

    async def enrich():
        async with httpx.AsyncClient() as client:
            await server._enrich_with_alt_currency_if_zero(client, {"value": None}, "B123", "JPY")

    with pytest.raises(pytest.fail.Exception, match="Live HTTP is forbidden"):
        asyncio.run(enrich())


def test_environment_defaults_are_read_in_a_fresh_process(monkeypatch, tmp_path):
    for name, value in {
        "OCI_PRICING_DEFAULT_CCY": " jpy ",
        "OCI_PRICING_MAX_PAGES": "3",
        "OCI_PRICING_HTTP_TIMEOUT": "7.5",
        "OCI_PRICING_RETRIES": "4",
        "OCI_PRICING_BACKOFF": "0.25",
        "OCI_PRICING_ALT_CCY": " eur ",
    }.items():
        monkeypatch.setenv(name, value)
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import json; from oracle.oci_pricing_mcp_server import server as s; "
            "print(json.dumps([s.DEFAULT_CCY, s.DEFAULT_MAX_PAGES, s.DEFAULT_TIMEOUT, "
            "s._RETRIES, s._BACKOFF_BASE, s.ALT_CCY]))",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    assert json.loads(result.stdout) == ["JPY", 3, 7.5, 4, 0.25, "EUR"]


@pytest.mark.parametrize("currency", [None, " jPy "])
def test_sku_uses_default_or_normalized_currency_at_http_boundary(monkeypatch, currency):
    monkeypatch.setattr(server, "DEFAULT_CCY", "JPY")
    monkeypatch.setattr(server, "ALT_CCY", None)

    async def get(client, url, *, params, headers):
        assert url == "https://apexapps.oracle.com/pls/apex/cetools/api/v1/products/"
        assert params == {"partNumber": "B123", "currencyCode": "JPY"}
        return httpx.Response(
            200,
            json={
                "items": [
                    {
                        "partNumber": "B123",
                        "prices": [
                            {"currencyCode": "JPY", "prices": [{"model": "PAYG", "value": 200}]}
                        ],
                    }
                ]
            },
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", get)
    result = asyncio.run(server.pricing_get_sku(" B123 ", currency=currency))
    assert result == {
        "kind": "sku",
        "partNumber": "B123",
        "displayName": None,
        "metricName": None,
        "serviceCategory": None,
        "currencyCode": "JPY",
        "model": "PAYG",
        "value": 200,
    }


def test_page_limit_stops_a_continuing_listing(monkeypatch):
    calls = []

    async def get(client, url, *, params, headers):
        calls.append(url)
        return httpx.Response(
            200,
            json={
                "items": [{"partNumber": f"P{len(calls)}"}],
                "links": [{"rel": "next", "href": f"?offset={len(calls)}"}],
            },
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", get)

    async def collect():
        async with httpx.AsyncClient() as client:
            return [item async for item in server.iter_all(client, "USD", 2)]

    assert asyncio.run(collect()) == [{"partNumber": "P1"}, {"partNumber": "P2"}]
    assert len(calls) == 2


@pytest.mark.parametrize("currency,limit,expected", [(None, 100, 20), (" jpy ", 0, 1)])
def test_search_normalizes_currency_and_clamps_result_count(monkeypatch, currency, limit, expected):
    monkeypatch.setattr(server, "DEFAULT_CCY", "JPY")
    monkeypatch.setattr(server, "ALT_CCY", None)
    items = [
        {
            "partNumber": f"P{index:02}",
            "displayName": f"Compute Shape {index}",
            "prices": [{"currencyCode": "JPY", "prices": [{"model": "PAYG", "value": 200}]}],
        }
        for index in range(25)
    ]

    async def get(client, url, *, params, headers):
        assert params["currencyCode"] == "JPY"
        found = items
        if "partNumber" in params:
            found = [item for item in items if item["partNumber"] == params["partNumber"]]
        return httpx.Response(200, json={"items": found}, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", get)
    result = asyncio.run(server.pricing_search_name("Compute", currency=currency, limit=limit))
    assert result["kind"] == "search"
    assert result["currency"] == "JPY"
    assert result["returned"] == expected
    assert [item["partNumber"] for item in result["items"]] == [
        f"P{index:02}" for index in range(expected)
    ]
    assert all(item["currencyCode"] == "JPY" and item["value"] == 200 for item in result["items"])


@pytest.mark.parametrize(
    "href",
    [
        "http://apexapps.oracle.com/next",
        "https://evil.example/next",
        "//evil.example/next",
        "https://apexapps.oracle.com:444/next",
        "https://user@apexapps.oracle.com/next",
    ],
)
def test_continuation_rejects_untrusted_destinations(href):
    assert server._safe_next_url(href, server.API) is None
