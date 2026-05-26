"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
"""

import asyncio
import importlib.util
import json
import os
import sys
import unittest
import warnings
from collections.abc import Callable
from types import MethodType
from typing import Any
from unittest import mock


class TestOciPricingMcpServer(unittest.TestCase):
    """
    Functional tests for oci-pricing-mcp-server.py.

    Strategy:
      - Dynamic import the target server module to stay close to runtime usage.
      - Support both direct function invocation and FunctionTool.run(arguments) wrappers.
      - Unwrap FastMCP ToolResult → content(List[TextContent]) → text(JSON) → native types.
      - Be resilient to "public subset" nature of cetools (skip when results legitimately empty/zero).
    """

    @classmethod
    def setUpClass(cls):
        # Silence noisy warnings from dependencies if any.
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        server_filename = os.getenv("PRICING_SERVER_FILENAME", "oci-pricing-mcp-server.py")
        server_path = os.path.join(os.path.dirname(__file__), server_filename)
        if not os.path.exists(server_path):
            raise FileNotFoundError(f"Server file not found at {server_path}")

        spec = importlib.util.spec_from_file_location("oci_pricing_mcp_server", server_path)
        cls.server_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.server_module)
        cls.module = cls.server_module

        # Probe values (override via environment variables when needed)
        cls.probe_sku_ok = os.getenv("PROBE_SKU_OK", "B93113")       # Known-good-ish SKU for JPY
        cls.probe_sku_missing = os.getenv("PROBE_SKU_MISSING", "B88298")
        cls.ccy_jpy = os.getenv("PROBE_CCY", "JPY")
        cls.query_compute = os.getenv("PROBE_QUERY", "Compute")

    # ---------- helpers: unwrap/call tool functions ----------

    @staticmethod
    def _is_method_of(obj, maybe_method) -> bool:
        """Return True if maybe_method is a bound method of obj."""
        try:
            return isinstance(maybe_method, MethodType) and maybe_method.__self__ is obj
        except Exception:
            return False

    @staticmethod
    def _maybe_json_load(x: Any) -> Any:
        """
        If x is bytes/str containing JSON, decode/parse it; otherwise return x unchanged.
        Produces dict/list on success, or the original string on parse errors.
        """
        if isinstance(x, (bytes, bytearray)):
            try:
                x = x.decode("utf-8")
            except Exception:
                x = bytes(x).decode("utf-8", errors="ignore")
        if isinstance(x, str):
            s = x.strip()
            if s.startswith("{") or s.startswith("["):
                try:
                    return json.loads(s)
                except Exception:
                    return x
        return x

    @classmethod
    def _unwrap_tool_result(cls, res: Any, _depth: int = 0) -> Any:
        """
        Unwrap a FastMCP ToolResult-like object to its underlying value.

        Heuristics:
          - If primitive (dict/list/str/number/bool/None): maybe JSON-load strings.
          - If list of TextContent-like items: take the first .text and JSON-load it.
          - If it looks like a ToolResult: prefer .content; then try .data/.result/.output/.value;
            finally try .to_dict()['content'] if available.
          - If it is a TextContent-like object: use .text and maybe JSON-load.
          - Fallback: return as-is.

        Depth is limited to avoid infinite recursion.
        """
        if _depth > 5:
            return res  # guard against pathological cases

        # Already a primitive: try to JSON-load strings/lists of text-y items.
        if isinstance(res, (dict, list, str, int, float, bool)) or res is None:
            if isinstance(res, list):
                # If this is a list of objects with "text", extract the first.
                all_textlike = True
                texts = []
                others = []
                for el in res:
                    if hasattr(el, "text"):
                        texts.append(el.text)
                    elif isinstance(el, dict) and "text" in el:
                        texts.append(el["text"])
                    else:
                        all_textlike = False
                        others.append(el)
                if all_textlike and texts:
                    if len(texts) == 1:
                        return cls._unwrap_tool_result(
                            cls._maybe_json_load(texts[0]), _depth + 1
                        )
                    return cls._unwrap_tool_result(
                        cls._maybe_json_load(texts[0]), _depth + 1
                    )
            return cls._maybe_json_load(res)

        # ToolResult-like?
        looks_tool_result = (
            "ToolResult" in res.__class__.__name__
            or hasattr(res, "content")
            or hasattr(res, "mimetype")
        )

        if looks_tool_result:
            # 1) Prefer .content
            if hasattr(res, "content"):
                try:
                    return cls._unwrap_tool_result(res.content, _depth + 1)
                except Exception:
                    pass
            # 2) Try common payload attrs
            for attr in ("data", "result", "output", "value"):
                if hasattr(res, attr):
                    try:
                        return cls._unwrap_tool_result(getattr(res, attr), _depth + 1)
                    except Exception:
                        continue
            # 3) Try to_dict()['content']
            if hasattr(res, "to_dict") and callable(res.to_dict):
                try:
                    d = res.to_dict()
                    if isinstance(d, dict) and "content" in d:
                        return cls._unwrap_tool_result(d["content"], _depth + 1)
                    return d
                except Exception:
                    pass

        # Single TextContent-like object
        if hasattr(res, "text"):
            try:
                return cls._maybe_json_load(res.text)
            except Exception:
                pass

        # Fallback: return as-is
        return res

    def _resolve_callable(self, obj) -> tuple[str, Callable]:
        """
        Decide how to invoke a tool-like object and return (mode, fn).

        Modes:
          - "plain"   : call as fn(*args, **kwargs)  (direct function or friendly wrapper)
          - "toolrun" : call as fn(arguments_dict)   (FunctionTool.run(arguments))

        Priority:
          1) Prefer FunctionTool.run (reliable tool execution signature).
          2) Then try function-like references: func/_func/__wrapped__/call/invoke.
          3) Finally __call__ (often unfriendly for tools), then generic callable.
        """
        # 1) FunctionTool.run has priority
        run_cand = getattr(obj, "run", None)
        if callable(run_cand) and self._is_method_of(obj, run_cand):
            return "toolrun", run_cand

        # 2) Likely underlying function
        for attr in ("func", "_func", "__wrapped__", "call", "invoke"):
            cand = getattr(obj, attr, None)
            if callable(cand):
                return "plain", cand

        # 3) Final fallback
        if callable(obj):
            return "plain", obj

        raise TypeError(f"Object is not callable and no callable attribute found: {type(obj)}")

    def _call(self, name: str, *args, **kwargs):
        """
        Invoke module.<name> and return an unwrapped value.

        - If mode == "plain": fn(*args, **kwargs) (await if coroutine).
        - If mode == "toolrun": fn(arguments_dict) (await if coroutine).
        """
        obj = getattr(self.module, name, None)
        if obj is None:
            raise AttributeError(f"{name} not found in module")

        mode, fn = self._resolve_callable(obj)

        if mode == "plain":
            if asyncio.iscoroutinefunction(fn):
                res = asyncio.run(fn(*args, **kwargs))
            else:
                res = fn(*args, **kwargs)
                if asyncio.iscoroutine(res):
                    res = asyncio.run(res)
            return self._unwrap_tool_result(res)

        # toolrun path: require kwargs → arguments dict
        if args and not kwargs:
            raise AssertionError(
                f"{name} is a FunctionTool; call it with keyword args so we can pass an 'arguments' dict."
            )
        arguments = kwargs or {}
        res = fn(arguments)
        if asyncio.iscoroutine(res):
            res = asyncio.run(res)
        return self._unwrap_tool_result(res)

    def setUp(self):
        print(f"\n{'=' * 70}")
        print(f"Running test: {self._testMethodName}")
        print(f"{'=' * 70}")

    # ---------------------- basic health ----------------------

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

    # ---------------------- currency validation ----------------------

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

    def test_get_sku_accepts_case_insensitive_currency(self):
        """Case-insensitive currencies should auto-uppercase and NOT trigger invalid-currency-format."""
        if not hasattr(self.module, "pricing_get_sku"):
            self.skipTest("pricing_get_sku not found in module")

        cases = [("usd", "USD"), ("Usd", "USD"), ("jpy", "JPY"), ("JpY", "JPY")]
        for raw, upper in cases:
            try:
                out = self._call(
                    "pricing_get_sku",
                    part_number=self.probe_sku_ok,
                    currency=raw,
                )
            except Exception as e:
                self.skipTest(f"HTTP/Network error: {e}")
                continue

            self.assertIsInstance(out, dict)
            # Should not be rejected as invalid-currency-format
            self.assertNotEqual(out.get("note"), "invalid-currency-format")

            # If it's a SKU hit, currencyCode should be upper; if search, currency should be upper.
            kind = out.get("kind")
            if kind == "sku":
                self.assertEqual(out.get("currencyCode"), upper)
            elif kind == "search":
                self.assertEqual(out.get("currency"), upper)
            else:
                # error (e.g., http-error) is acceptable; just ensure note isn't invalid-currency-format
                pass

    def test_search_name_accepts_case_insensitive_currency(self):
        """Case-insensitive currencies should auto-uppercase and NOT trigger invalid-currency-format (search)."""
        if not hasattr(self.module, "pricing_search_name"):
            self.skipTest("pricing_search_name not found in module")

        cases = [("usd", "USD"), ("Usd", "USD"), ("jpy", "JPY"), ("JpY", "JPY")]
        for raw, upper in cases:
            try:
                out = self._call(
                    "pricing_search_name",
                    query=self.query_compute,
                    currency=raw,
                    limit=3,
                    max_pages=2,
                )
            except Exception as e:
                self.skipTest(f"HTTP/Network error: {e}")
                continue

            self.assertIsInstance(out, dict)
            self.assertNotEqual(out.get("note"), "invalid-currency-format")
            if out.get("kind") == "search":
                self.assertEqual(out.get("currency"), upper)

    def test_get_sku_uses_default_currency_when_omitted(self):
        """If currency is omitted (None), DEFAULT_CCY is used and validated."""
        if not hasattr(self.module, "pricing_get_sku"):
            self.skipTest("pricing_get_sku not found in module")

        default_ccy = getattr(self.module, "DEFAULT_CCY", "USD")

        print(f"About to call pricing_get_sku('{self.probe_sku_ok}', currency omitted)")
        try:
            # omit currency argument entirely
            out = self._call(
                "pricing_get_sku",
                part_number=self.probe_sku_ok,
            )
        except Exception as e:
            self.skipTest(f"HTTP/Network error calling pricing_get_sku: {e}")
            return

        self.assertIsInstance(out, dict)
        kind = out.get("kind")
        self.assertIn(kind, ("sku", "search", "error"))

        if kind == "sku":
            # currencyCode should be the module default
            self.assertEqual(out.get("currencyCode"), default_ccy)
        elif kind == "search":
            self.assertEqual(out.get("currency"), default_ccy)
        else:
            # if error due to public subset issues, still accept but print
            print("Received error (acceptable depending on dataset):", out)

    def test_search_name_uses_default_currency_when_omitted(self):
        """If currency is omitted (None), DEFAULT_CCY is used and validated in search."""
        if not hasattr(self.module, "pricing_search_name"):
            self.skipTest("pricing_search_name not found in module")

        default_ccy = getattr(self.module, "DEFAULT_CCY", "USD")

        try:
            out = self._call(
                "pricing_search_name",
                query=self.query_compute,
                # currency omitted
                limit=5,
                max_pages=2,
            )
        except Exception as e:
            self.skipTest(f"HTTP/Network error: {e}")
            return

        self.assertIsInstance(out, dict)
        if "kind" in out:
            self.assertEqual(out["kind"], "search")
        self.assertEqual(out.get("currency"), default_ccy)
        self.assertIn("items", out)
        self.assertIn("returned", out)

    # ---------------------- pricing_get_sku ----------------------

    def test_get_sku_known_price_jpy(self):
        """Known SKU in JPY should return a priced item; otherwise skip (public-subset variance)."""
        if not hasattr(self.module, "pricing_get_sku"):
            self.skipTest("pricing_get_sku not found in module")

        print(f"About to call pricing_get_sku('{self.probe_sku_ok}', '{self.ccy_jpy}')")
        try:
            out: dict[str, Any] = self._call(
                "pricing_get_sku",
                part_number=self.probe_sku_ok,
                currency=self.ccy_jpy,
            )
        except Exception as e:
            self.skipTest(f"HTTP/Network error calling pricing_get_sku: {e}")
            return

        if not isinstance(out, dict):
            self.skipTest(f"Unexpected response type: {type(out)}")
            return

        # If 'kind' is present, it should be one of the known markers.
        if "kind" in out:
            self.assertIn(out["kind"], ("sku", "search", "error"))

        if "note" in out and out.get("note") in {"not-found"}:
            self.skipTest(f"SKU appears missing in public subset: {out}")
            return

        for k in ("partNumber", "displayName", "metricName", "serviceCategory", "currencyCode"):
            self.assertIn(k, out, f"Missing key '{k}'")
        self.assertEqual(out.get("currencyCode"), self.ccy_jpy)

        # value/model が 0/欠落の揺らぎに備え、スキップ条件を追加
        if out.get("model") is None or out.get("value") is None:
            self.skipTest(f"Unit price missing in public subset: {out}")
            return
        try:
            if float(out.get("value", 0)) <= 0.0:
                self.skipTest(f"Unit price is zero in public subset: {out}")
                return
        except Exception:
            self.skipTest(f"Non-numeric unit price in public subset: {out}")
            return

        print(
            f"OK: {out.get('partNumber')} {out.get('displayName')} -> "
            f"{out.get('model')} {out.get('value')} {out.get('currencyCode')}"
        )

    def test_get_sku_missing_handles_not_found_or_name_fallback(self):
        """Missing SKU should return not-found or matched-by-name gracefully."""
        if not hasattr(self.module, "pricing_get_sku"):
            self.skipTest("pricing_get_sku not found in module")

        print(f"About to call pricing_get_sku('{self.probe_sku_missing}', '{self.ccy_jpy}')")
        try:
            out = self._call(
                "pricing_get_sku",
                part_number=self.probe_sku_missing,
                currency=self.ccy_jpy,
            )
        except Exception as e:
            self.skipTest(f"HTTP/Network error: {e}")
            return

        self.assertIsInstance(out, dict)
        # If 'kind' exists, it should reflect search/error/sku
        if "kind" in out:
            self.assertIn(out["kind"], ("search", "error", "sku"))

        note = out.get("note")
        if note is None and out.get("partNumber"):
            print("Direct SKU unexpectedly found (acceptable):", out)
            return

        self.assertIn(note, {"not-found", "matched-by-name"})
        if note == "matched-by-name":
            self.assertIn("items", out)
            self.assertIsInstance(out["items"], list)
        print(f"Handled with note={note}")

    # ---------------------- pricing_search_name ----------------------

    def test_search_name_require_priced_compute_jpy(self):
        """With require_priced=True, every item must have model/value and the requested currencyCode."""
        if not hasattr(self.module, "pricing_search_name"):
            self.skipTest("pricing_search_name not found in module")

        print(
            f"About to call pricing_search_name(query='{self.query_compute}', "
            f"currency='{self.ccy_jpy}', require_priced=True)"
        )
        try:
            out = self._call(
                "pricing_search_name",
                query=self.query_compute,
                currency=self.ccy_jpy,
                limit=12,
                max_pages=4,
                require_priced=True,
            )
        except Exception as e:
            self.skipTest(f"HTTP/Network error: {e}")
            return

        self.assertIsInstance(out, dict)
        if "kind" in out:
            self.assertEqual(out["kind"], "search")
        self.assertEqual(out.get("query"), self.query_compute)
        self.assertEqual(out.get("currency"), self.ccy_jpy)
        self.assertIn("items", out)
        self.assertIn("returned", out)

        items = out.get("items") or []
        if len(items) == 0:
            self.skipTest("No priced items returned (likely transient)")
            return

        for it in items:
            self.assertEqual(it.get("currencyCode"), self.ccy_jpy)
            self.assertIsNotNone(it.get("model"))
            self.assertIsNotNone(it.get("value"))
            self.assertGreater(float(it.get("value", 0)), 0.0)

        print(f"Got {len(items)} priced items; first={items[0].get('displayName')}")

    def test_search_name_currency_always_populated(self):
        """Without require_priced, currencyCode must still be set via simplify(...)."""
        if not hasattr(self.module, "pricing_search_name"):
            self.skipTest("pricing_search_name not found in module")

        query = "Object Storage"
        print(
            f"About to call pricing_search_name(query='{query}', currency='{self.ccy_jpy}', require_priced=False)"
        )
        try:
            out = self._call(
                "pricing_search_name",
                query=query,
                currency=self.ccy_jpy,
                limit=12,
                max_pages=3,
                require_priced=False,
            )
        except Exception as e:
            self.skipTest(f"HTTP/Network error: {e}")
            return

        self.assertIsInstance(out, dict)
        if "kind" in out:
            self.assertEqual(out["kind"], "search")

        items = out.get("items") or []
        if len(items) == 0:
            self.skipTest("No items returned (likely transient)")
            return

        for it in items:
            self.assertIn("currencyCode", it)
            self.assertEqual(it.get("currencyCode"), self.ccy_jpy)

        print(f"currencyCode populated for {len(items)} items")

    def test_search_name_limit_clamped_to_20(self):
        """A very large limit must be clamped to <= 20 in the result."""
        if not hasattr(self.module, "pricing_search_name"):
            self.skipTest("pricing_search_name not found in module")

        big_limit = 100
        print(
            f"About to call pricing_search_name(query='Compute', currency='USD', limit={big_limit})"
        )
        try:
            out = self._call(
                "pricing_search_name",
                query="Compute",
                currency="USD",
                limit=big_limit,
                max_pages=4,
                require_priced=False,
            )
        except Exception as e:
            self.skipTest(f"HTTP/Network error: {e}")
            return

        self.assertIsInstance(out, dict)
        if "kind" in out:
            self.assertEqual(out["kind"], "search")
        returned = int(out.get("returned", 0))
        self.assertLessEqual(returned, 20, f"returned should be <= 20 but was {returned}")
        print(f"Returned={returned} (<=20)")

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

    def test_search_name_adb_intent_does_not_error(self):
        """'ADB' intent path should not error and should return a valid search structure (smoke test)."""
        if not hasattr(self.module, "pricing_search_name"):
            self.skipTest("pricing_search_name not found in module")

        try:
            out = self._call(
                "pricing_search_name",
                query="ADB",
                currency="USD",
                limit=10,
                max_pages=3,
                require_priced=False,
            )
        except Exception as e:
            self.fail(f"pricing_search_name raised unexpectedly on ADB intent: {e}")

        self.assertIsInstance(out, dict)
        if "kind" in out:
            self.assertEqual(out["kind"], "search")
        self.assertIn("items", out)
        self.assertIn("returned", out)
        # No strict assertions on content due to public-subset variance.

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

    def tearDown(self):
        print(f"{'=' * 70}")
        print(f"Completed test: {self._testMethodName}")
        print(f"{'=' * 70}\n")


if __name__ == "__main__":
    print("Starting oci-pricing-mcp-server functional tests")
    print(
        "Env overrides: PRICING_SERVER_FILENAME, PROBE_SKU_OK, PROBE_SKU_MISSING, PROBE_CCY, PROBE_QUERY"
    )

    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        print(f"\nRunning specific test: {test_name}")
        suite = unittest.TestSuite()
        try:
            suite.addTest(TestOciPricingMcpServer(test_name))
            runner = unittest.TextTestRunner()
            runner.run(suite)
        except ValueError:
            print(f"Error: Test '{test_name}' not found. Available tests:")
            for name in unittest.defaultTestLoader.getTestCaseNames(TestOciPricingMcpServer):
                print(f"  - {name}")
    else:
        print("\nRunning all tests...")
        unittest.main()
