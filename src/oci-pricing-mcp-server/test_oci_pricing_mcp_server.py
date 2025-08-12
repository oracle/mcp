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


class TestOciPricingMcpServer(unittest.TestCase):
    """
    Functional tests for oci-pricing-mcp-server.py.

    Strategy:
      - Mirror the reference test style: dynamic import, verbose logging, and
        functional calls into the module under test.
      - Hide @mcp.tool wrappers' differences: support both FunctionTool.run(arguments)
        and direct function invocation transparently.
      - Robustly unwrap FastMCP ToolResult: content(List[TextContent]) → text (JSON)
        → native dict/list types.
      - Be resilient to the public price list "subset" nature of cetools:
        transient emptiness and currency differences are handled via skips.
    """

    @classmethod
    def setUpClass(cls):
        # Silence the known DeprecationWarning noise from dependencies, if any.
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
        cls.probe_sku_ok = os.getenv("PROBE_SKU_OK", "B93113")
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

        # 3) Reluctantly accept __call__
        call_cand = getattr(obj, "__call__", None)
        if callable(call_cand):
            return "plain", call_cand

        # 4) Final fallback
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
        self.assertIsNotNone(out.get("model"))
        self.assertIsNotNone(out.get("value"))
        self.assertGreater(float(out.get("value", 0)), 0.0)

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
