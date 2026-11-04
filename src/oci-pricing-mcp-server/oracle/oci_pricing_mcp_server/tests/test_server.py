"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import asyncio
from unittest import mock

from ._support import PricingTestCase


class TestOciPricingMcpServer(PricingTestCase):
    def test_ping(self):
        """Health check tool returns 'ok'."""
        if not hasattr(self.module, "ping"):
            self.skipTest("ping not found in module")
        result = self._call("ping")  # Unwrapping also handles ToolResult
        # Relax if a dict-like value is returned
        if not isinstance(result, str):
            try:
                _d = dict(result)
                result = _d.get("result", _d.get("status", result))
            except Exception:
                pass
        self.assertEqual(result, "ok")
        print("ping() -> ok")

    def test_get_sku_rejects_invalid_currency(self):
        """Invalid currency formats must return kind=error, note=invalid-currency-format."""
        if not hasattr(self.module, "pricing_get_sku"):
            self.skipTest("pricing_get_sku not found in module")

        # NOTE: case-mixed/lowercase are now accepted (auto-uppercased). Exclude them.
        bad_list = ["USDT", "12$", "JP", "EUR1", ""]
        for bad in bad_list:
            out = self._call(
                "pricing_get_sku",
                part_number=self.probe_sku_ok,
                currency=bad,
            )
            self.assertIsInstance(out, dict)
            self.assertEqual(out.get("kind"), "error")
            self.assertEqual(out.get("note"), "invalid-currency-format")
            self.assertEqual(out.get("input"), bad)

    def test_search_name_rejects_invalid_currency(self):
        """Invalid currency formats must return kind=error, note=invalid-currency-format."""
        if not hasattr(self.module, "pricing_search_name"):
            self.skipTest("pricing_search_name not found in module")

        # NOTE: case-mixed/lowercase are now accepted (auto-uppercased). Exclude them.
        bad_list = ["USDT", "12$", "JP", "EUR1", ""]
        for bad in bad_list:
            out = self._call(
                "pricing_search_name",
                query=self.query_compute,
                currency=bad,
                limit=3,
                max_pages=2,
            )
            self.assertIsInstance(out, dict)
            self.assertEqual(out.get("kind"), "error")
            self.assertEqual(out.get("note"), "invalid-currency-format")
            self.assertEqual(out.get("input"), bad)

    def test_empty_query_returns_empty_query_note(self):
        """Empty query should return note='empty-query' and items=[]."""
        if not hasattr(self.module, "pricing_search_name"):
            self.skipTest("pricing_search_name not found in module")

        print("Calling pricing_search_name(query='', currency='USD')")
        out = self._call(
            "pricing_search_name",
            query="",
            currency="USD",
        )
        self.assertIsInstance(out, dict)
        # Expect kind == error, if present
        if "kind" in out:
            self.assertEqual(out["kind"], "error")
        self.assertEqual(out.get("note"), "empty-query")
        self.assertEqual(out.get("items"), [])
        print("Empty query handled correctly")

    def test_iter_all_rejects_untrusted_absolute_next_link(self):
        calls = []

        async def fake_fetch(_client, url, params):
            calls.append((url, params))
            return {
                "items": [{"partNumber": "B123"}],
                "links": [{"rel": "next", "href": "http://169.254.169.254/opc/v2/instance/"}],
            }

        original_fetch = self.module.fetch
        self.module.fetch = fake_fetch
        try:
            async def collect():
                return [item async for item in self.module.iter_all(object(), currency="USD", max_pages=2)]

            items = asyncio.run(collect())
        finally:
            self.module.fetch = original_fetch

        self.assertEqual(items, [{"partNumber": "B123"}])
        self.assertEqual(calls, [(self.module.API, {"currencyCode": "USD"})])

    def test_price_block_helpers_and_simplify_notes(self):
        item = {
            "partNumber": "PN1",
            "displayName": "Compute",
            "metricName": "OCPU",
            "serviceCategory": "Compute",
            "prices": [{"currencyCode": "USD", "prices": [{"model": "PAYG", "value": 1.25}]}],
            "currencyCodeLocalizations": [
                {"currencyCode": "JPY", "prices": [{"model": "PAYG", "value": 200.0}]}
            ],
        }

        blocks = self.module._iter_price_blocks(item)
        self.assertEqual([block["currencyCode"] for block in blocks], ["USD", "JPY"])
        self.assertEqual(self.module._pick_price(item, "JPY"), ("PAYG", 200.0, "JPY"))
        self.assertEqual(self.module._pick_price(item, "EUR"), ("PAYG", 1.25, "USD"))

        missing = self.module.simplify({"partNumber": "PN2"}, "USD")
        self.assertEqual(missing["currencyCode"], "USD")
        self.assertEqual(missing["note"], "no-unit-price-in-public-subset-or-currency")

        zero = self.module.simplify(
            {"prices": [{"currencyCode": "USD", "prices": [{"model": "PAYG", "value": 0}]}]},
            "USD",
        )
        self.assertEqual(zero["note"], "zero-price-or-free-tier-only")

        nonnumeric = self.module.simplify(
            {
                "prices": [
                    {
                        "currencyCode": "USD",
                        "prices": [{"model": "PAYG", "value": "free"}],
                    }
                ]
            },
            "USD",
        )
        self.assertEqual(
            nonnumeric["note"], "no-unit-price-in-public-subset-or-currency"
        )

    def test_fetch_retries_transient_errors_and_handles_bad_json(self):
        module = self.module

        class FakeResponse:
            def __init__(self, status_code, payload=None, json_error=None):
                self.status_code = status_code
                self.request = mock.Mock()
                self._payload = payload
                self._json_error = json_error

            def raise_for_status(self):
                if self.status_code >= 400:
                    raise module.httpx.HTTPStatusError(
                        "bad status", request=self.request, response=self
                    )

            def json(self):
                if self._json_error:
                    raise self._json_error
                return self._payload

        class FakeClient:
            def __init__(self):
                self.responses = [
                    FakeResponse(500),
                    FakeResponse(200, json_error=ValueError("not json")),
                ]

            async def get(self, url, params=None, headers=None):
                return self.responses.pop(0)

        async def no_sleep(_seconds):
            return None

        async def run_fetch():
            with mock.patch.object(module, "_RETRIES", 1), mock.patch.object(
                module, "_BACKOFF_BASE", 0
            ), mock.patch.object(module.asyncio, "sleep", no_sleep):
                return await module.fetch(FakeClient(), "https://example.com")

        self.assertEqual(asyncio.run(run_fetch()), {})

        class FailingClient:
            async def get(self, url, params=None, headers=None):
                raise module.httpx.ReadTimeout("timeout")

        async def run_exhausted_fetch():
            with mock.patch.object(module, "_RETRIES", 0):
                return await module.fetch(FailingClient(), "https://example.com")

        with self.assertRaises(module.httpx.ReadTimeout):
            asyncio.run(run_exhausted_fetch())

    def test_iter_all_follows_relative_next_links(self):
        module = self.module
        calls = []

        async def fake_fetch(_client, url, params=None):
            calls.append((url, params))
            if len(calls) == 1:
                return {
                    "items": [{"partNumber": "PN1"}],
                    "links": [{"rel": "next", "href": "/next-page"}],
                }
            return {"items": [{"partNumber": "PN2"}], "links": []}

        async def collect_items():
            with mock.patch.object(module, "fetch", fake_fetch):
                return [item async for item in module.iter_all(object(), "USD", 3)]

        items = asyncio.run(collect_items())

        self.assertEqual([item["partNumber"] for item in items], ["PN1", "PN2"])
        self.assertEqual(calls[0], (module.API, {"currencyCode": "USD"}))
        self.assertEqual(calls[1], ("https://apexapps.oracle.com/next-page", None))

    def test_iter_all_follows_query_relative_next_and_rejects_off_host(self):
        module = self.module
        calls = []
        expected_second = (
            "https://apexapps.oracle.com/pls/apex/cetools/api/v1/products/"
            "?offset=25&currencyCode=EUR"
        )

        async def fake_fetch(_client, url, params=None):
            calls.append((url, params))
            if len(calls) == 1:
                return {
                    "items": [{"partNumber": "PN1"}],
                    "links": [{"rel": "next", "href": "?offset=25&currencyCode=EUR"}],
                }
            if url == expected_second:
                return {
                    "items": [{"partNumber": "PN2"}],
                    "links": [{"rel": "next", "href": "https://evil.example/steal"}],
                }
            return {"items": [{"partNumber": "SHOULD-NOT-FETCH"}], "links": []}

        async def collect_items():
            with mock.patch.object(module, "fetch", fake_fetch):
                return [item async for item in module.iter_all(object(), "EUR", 4)]

        items = asyncio.run(collect_items())

        self.assertEqual([item["partNumber"] for item in items], ["PN1", "PN2"])
        self.assertEqual(calls[0], (module.API, {"currencyCode": "EUR"}))
        self.assertEqual(calls[1], (expected_second, None))
        self.assertEqual(len(calls), 2)

    def test_search_items_aliases_adb_intent_and_deduplication(self):
        items = [
            {
                "partNumber": "ADB1",
                "displayName": "Autonomous Database Shared",
                "metricName": "OCPU",
                "prices": [{"currencyCode": "USD", "prices": [{"model": "PAYG", "value": 1}]}],
            },
            {
                "partNumber": "DB1",
                "displayName": "Database Backup",
                "metricName": "Storage",
                "prices": [{"currencyCode": "USD", "prices": [{"model": "PAYG", "value": 1}]}],
            },
            {
                "partNumber": "ADB1",
                "displayName": "Autonomous Database Shared",
                "metricName": "OCPU",
                "prices": [{"currencyCode": "USD", "prices": [{"model": "PAYG", "value": 1}]}],
            },
        ]

        adb_hits = self.module.search_items(items, "ADB", prefer_currency="USD")

        self.assertEqual(len(adb_hits), 1)
        self.assertEqual(adb_hits[0]["partNumber"], "ADB1")
        self.assertEqual(self.module.acronym("Autonomous Database"), "ad")
        self.assertEqual(self.module.nospace("load balancer"), "loadbalancer")

    def test_currency_helpers_cover_fallbacks(self):
        module = self.module

        self.assertEqual(module._clamp("bad", 1, 10, 6), 6)
        self.assertEqual(module._clamp(99, 1, 10, 6), 10)
        self.assertEqual(module._norm_currency(" usd "), "USD")

        with mock.patch.object(module, "_HAS_BABEL", False), mock.patch.object(
            module, "_HAS_PYCOUNTRY", False
        ):
            module._is_valid_iso4217.cache_clear()
            self.assertTrue(module._is_valid_iso4217("ZZZ"))
            self.assertFalse(module._is_valid_iso4217("USDT"))

        raising_pycountry = mock.Mock()
        raising_pycountry.currencies.get.side_effect = RuntimeError("offline")
        with mock.patch.object(module, "_HAS_BABEL", True), mock.patch.object(
            module, "get_currency_name", side_effect=RuntimeError("unknown")
        ), mock.patch.object(module, "_HAS_PYCOUNTRY", True), mock.patch.object(
            module, "pycountry", raising_pycountry
        ):
            module._is_valid_iso4217.cache_clear()
            self.assertTrue(module._is_valid_iso4217("ZZZ"))

        with mock.patch.object(module, "_is_valid_iso4217", return_value=False):
            self.assertEqual(
                module._norm_currency_strict(None, default="BAD"),
                ("BAD", "invalid-default-currency"),
            )

    def test_alt_currency_enrichment_adds_reference_or_returns_original(self):
        module = self.module

        async def fake_fetch(_client, _url, params=None):
            self.assertEqual(params["currencyCode"], "EUR")
            return {
                "items": [
                    {
                        "prices": [
                            {
                                "currencyCode": "EUR",
                                "prices": [{"model": "PAYG", "value": 9.5}],
                            }
                        ]
                    }
                ]
            }

        async def enrich():
            item = {"value": 0, "model": "PAYG"}
            with mock.patch.object(module, "ALT_CCY", "EUR"), mock.patch.object(
                module, "fetch", fake_fetch
            ):
                return await module._enrich_with_alt_currency_if_zero(
                    object(), item, "PN1", "USD"
                )

        enriched = asyncio.run(enrich())
        self.assertEqual(enriched["altCurrencyCode"], "EUR")
        self.assertEqual(enriched["altValue"], 9.5)

        async def failing_fetch(*_args, **_kwargs):
            raise RuntimeError("alt failed")

        async def enrich_failure():
            item = {"value": None}
            with mock.patch.object(module, "ALT_CCY", "EUR"), mock.patch.object(
                module, "fetch", failing_fetch
            ):
                return await module._enrich_with_alt_currency_if_zero(
                    object(), item, "PN1", "USD"
                )

        self.assertEqual(asyncio.run(enrich_failure()), {"value": None})

        async def empty_alt_fetch(*_args, **_kwargs):
            return {"items": []}

        async def enrich_no_alt_items():
            item = {"value": "free", "model": "PAYG"}
            with mock.patch.object(module, "ALT_CCY", "EUR"), mock.patch.object(
                module, "fetch", empty_alt_fetch
            ):
                return await module._enrich_with_alt_currency_if_zero(
                    object(), item, "PN1", "USD"
                )

        self.assertEqual(
            asyncio.run(enrich_no_alt_items()), {"value": "free", "model": "PAYG"}
        )

        async def alt_without_value_fetch(*_args, **_kwargs):
            return {"items": [{"partNumber": "ALT"}]}

        async def enrich_alt_without_value():
            item = {"value": 0, "model": "PAYG"}
            with mock.patch.object(module, "ALT_CCY", "EUR"), mock.patch.object(
                module, "fetch", alt_without_value_fetch
            ):
                return await module._enrich_with_alt_currency_if_zero(
                    object(), item, "PN1", "USD"
                )

        self.assertEqual(
            asyncio.run(enrich_alt_without_value()), {"value": 0, "model": "PAYG"}
        )

    def test_pricing_get_sku_impl_direct_fallback_and_http_error(self):
        module = self.module

        class FakeAsyncClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

        async def identity_enrich(_client, item, _part_number, _currency):
            return item

        async def direct_fetch(_client, _url, _params=None):
            return {
                "items": [
                    {
                        "partNumber": "PN1",
                        "displayName": "Compute",
                        "prices": [
                            {
                                "currencyCode": "USD",
                                "prices": [{"model": "PAYG", "value": 1.0}],
                            }
                        ],
                    }
                ]
            }

        async def run_direct():
            with mock.patch.object(module.httpx, "AsyncClient", FakeAsyncClient), mock.patch.object(
                module, "fetch", direct_fetch
            ), mock.patch.object(module, "_enrich_with_alt_currency_if_zero", identity_enrich):
                return await module.pricing_get_sku_impl("PN1", "usd")

        direct = asyncio.run(run_direct())
        self.assertEqual(direct["kind"], "sku")
        self.assertEqual(direct["currencyCode"], "USD")

        async def empty_fetch(_client, _url, _params=None):
            return {"items": []}

        async def fake_iter_all(_client, _currency, _pages):
            yield {"partNumber": "PN2"}

        async def run_fallback():
            with mock.patch.object(module.httpx, "AsyncClient", FakeAsyncClient), mock.patch.object(
                module, "fetch", empty_fetch
            ), mock.patch.object(module, "iter_all", fake_iter_all), mock.patch.object(
                module,
                "search_items",
                return_value=[{"partNumber": "PN2", "currencyCode": "USD"}],
            ):
                return await module.pricing_get_sku_impl("Compute", "USD", max_pages=99)

        fallback = asyncio.run(run_fallback())
        self.assertEqual(fallback["kind"], "search")
        self.assertEqual(fallback["note"], "matched-by-name")
        self.assertEqual(fallback["returned"], 1)

        async def failing_fetch(_client, _url, _params=None):
            raise module.httpx.ConnectError("network down")

        async def run_error():
            with mock.patch.object(module.httpx, "AsyncClient", FakeAsyncClient), mock.patch.object(
                module, "fetch", failing_fetch
            ):
                return await module.pricing_get_sku_impl("PN1", "USD")

        error = asyncio.run(run_error())
        self.assertEqual(error["kind"], "error")
        self.assertEqual(error["note"], "http-error")

        self.assertEqual(
            asyncio.run(module.pricing_get_sku_impl("", "USD")),
            {"kind": "error", "note": "empty-part-number", "items": []},
        )

        async def run_missing_currency_from_simplify():
            with mock.patch.object(module.httpx, "AsyncClient", FakeAsyncClient), mock.patch.object(
                module, "fetch", direct_fetch
            ), mock.patch.object(
                module,
                "simplify",
                return_value={"partNumber": "PN1", "currencyCode": None},
            ), mock.patch.object(module, "_enrich_with_alt_currency_if_zero", identity_enrich):
                return await module.pricing_get_sku_impl("PN1", "USD")

        self.assertEqual(
            asyncio.run(run_missing_currency_from_simplify())["currencyCode"], "USD"
        )

    def test_pricing_search_name_impl_enriches_and_filters_priced_items(self):
        module = self.module

        class FakeAsyncClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

        async def fake_iter_all(_client, _currency, _pages):
            yield {"partNumber": "PN1"}
            yield {"partNumber": "PN2"}

        async def detail_fetch(_client, _url, params=None):
            value = 2.5 if params["partNumber"] == "PN1" else 0
            return {
                "items": [
                    {
                        "partNumber": params["partNumber"],
                        "prices": [
                            {
                                "currencyCode": params["currencyCode"],
                                "prices": [{"model": "PAYG", "value": value}],
                            }
                        ],
                    }
                ]
            }

        async def identity_enrich(_client, item, _part_number, _currency):
            return item

        async def run_search():
            with mock.patch.object(module.httpx, "AsyncClient", FakeAsyncClient), mock.patch.object(
                module, "iter_all", fake_iter_all
            ), mock.patch.object(
                module,
                "search_items",
                return_value=[
                    {"partNumber": "PN1", "currencyCode": "USD"},
                    {"partNumber": "PN2", "currencyCode": "USD"},
                    {"displayName": "No SKU", "model": "PAYG", "value": "not-number"},
                ],
            ), mock.patch.object(module, "fetch", detail_fetch), mock.patch.object(
                module, "_enrich_with_alt_currency_if_zero", identity_enrich
            ):
                return await module.pricing_search_name_impl(
                    "Compute", "USD", limit=100, max_pages=100, require_priced=True
                )

        result = asyncio.run(run_search())
        self.assertEqual(result["kind"], "search")
        self.assertEqual(result["returned"], 1)
        self.assertEqual(result["items"][0]["partNumber"], "PN1")

        async def run_missing_currency_from_detail():
            with mock.patch.object(module.httpx, "AsyncClient", FakeAsyncClient), mock.patch.object(
                module, "iter_all", fake_iter_all
            ), mock.patch.object(
                module,
                "search_items",
                return_value=[{"partNumber": "PN1", "currencyCode": "USD"}],
            ), mock.patch.object(module, "fetch", detail_fetch), mock.patch.object(
                module,
                "simplify",
                return_value={
                    "partNumber": "PN1",
                    "currencyCode": None,
                    "model": "PAYG",
                    "value": 1,
                },
            ), mock.patch.object(module, "_enrich_with_alt_currency_if_zero", identity_enrich):
                return await module.pricing_search_name_impl(
                    "Compute", "USD", require_priced=False
                )

        self.assertEqual(
            asyncio.run(run_missing_currency_from_detail())["items"][0]["currencyCode"],
            "USD",
        )

    def test_pricing_search_name_impl_http_error_and_wrappers(self):
        module = self.module

        class FakeAsyncClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

        async def failing_iter_all(_client, _currency, _pages):
            raise module.httpx.ReadTimeout("timeout")
            yield

        async def run_error():
            with mock.patch.object(module.httpx, "AsyncClient", FakeAsyncClient), mock.patch.object(
                module, "iter_all", failing_iter_all
            ):
                return await module.pricing_search_name_impl("Compute", "USD")

        self.assertEqual(asyncio.run(run_error())["note"], "http-error")

        async def fake_get_sku_impl(**kwargs):
            return {"kind": "sku", "partNumber": kwargs["part_number"]}

        async def fake_search_impl(**kwargs):
            return {"kind": "search", "query": kwargs["query"]}

        with mock.patch.object(module, "pricing_get_sku_impl", fake_get_sku_impl):
            self.assertEqual(
                self._call("pricing_get_sku", part_number="PN1")["partNumber"], "PN1"
            )

        with mock.patch.object(module, "pricing_search_name_impl", fake_search_impl):
            self.assertEqual(
                self._call("pricing_search_name", query="Compute")["query"], "Compute"
            )

        self.assertEqual(module.ping(), "ok")
        with mock.patch.object(module.mcp, "run") as run_mock:
            module.main()
        run_mock.assert_called_once_with()
