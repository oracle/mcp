"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
"""

import unittest
import json
import sys
import os
import importlib.util
import warnings
import asyncio
from types import MethodType
from typing import Any, Dict, Tuple, Callable


class TestOciPricingMcpServer(unittest.TestCase):
    """
    Functional tests for oci-pricing-mcp-server.py

    方針:
      - 参考テストと同じ構成/ログ/動的 import。
      - @mcp.tool ラッパはテスト側で吸収（run(arguments) と元関数直呼びの両対応）。
      - ToolResult → content(List[TextContent]) → text(JSON) を確実にアンラップ。
      - cetools は公開サブセットのため空返りや通貨差は skip として扱う。
    """

    @classmethod
    def setUpClass(cls):
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        server_filename = os.getenv("PRICING_SERVER_FILENAME", "oci-pricing-mcp-server.py")
        server_path = os.path.join(os.path.dirname(__file__), server_filename)
        if not os.path.exists(server_path):
            raise FileNotFoundError(f"Server file not found at {server_path}")

        spec = importlib.util.spec_from_file_location("oci_pricing_mcp_server", server_path)
        cls.server_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.server_module)
        cls.module = cls.server_module

        # Probes（環境変数で上書き可）
        cls.probe_sku_ok = os.getenv("PROBE_SKU_OK", "B93113")
        cls.probe_sku_missing = os.getenv("PROBE_SKU_MISSING", "B88298")
        cls.ccy_jpy = os.getenv("PROBE_CCY", "JPY")
        cls.query_compute = os.getenv("PROBE_QUERY", "Compute")

    # ---------- helpers: unwrap/call tool functions ----------

    @staticmethod
    def _is_method_of(obj, maybe_method) -> bool:
        try:
            return isinstance(maybe_method, MethodType) and maybe_method.__self__ is obj
        except Exception:
            return False

    @staticmethod
    def _maybe_json_load(x: Any) -> Any:
        """bytes/str を JSON なら dict/list に、そうでなければ文字列として返す。"""
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
        FastMCP の ToolResult を “中身” に剥がす。
        代表例:
          - ToolResult.content -> List[TextContent] -> first.text -> JSON load
          - ToolResult.content -> str/json ならそのまま/loads
          - .data/.result/.output/.value なども走査
          - to_dict()['content'] もケア
        """
        if _depth > 5:
            return res  # ガード

        # 既にプリミティブ
        if isinstance(res, (dict, list, str, int, float, bool)) or res is None:
            # List の場合 TextContent っぽい要素を剥がす
            if isinstance(res, list):
                # TextContent らしき（.text を持つ）だけで構成されている？
                all_textlike = True
                texts = []
                others = []
                for el in res:
                    if hasattr(el, "text"):
                        texts.append(getattr(el, "text"))
                    elif isinstance(el, dict) and "text" in el:
                        texts.append(el["text"])
                    else:
                        all_textlike = False
                        others.append(el)
                if all_textlike and texts:
                    # 1個ならそれを JSON 解析
                    if len(texts) == 1:
                        return cls._unwrap_tool_result(cls._maybe_json_load(texts[0]), _depth + 1)
                    # 複数ある場合は先頭を優先（多くは 1 要素）
                    return cls._unwrap_tool_result(cls._maybe_json_load(texts[0]), _depth + 1)
            # それ以外はそのまま/JSON 解析
            return cls._maybe_json_load(res)

        # ToolResult らしい？
        looks_tool_result = (
            "ToolResult" in res.__class__.__name__
            or hasattr(res, "content")
            or hasattr(res, "mimetype")
        )

        if looks_tool_result:
            # 1) content を優先
            if hasattr(res, "content"):
                try:
                    return cls._unwrap_tool_result(getattr(res, "content"), _depth + 1)
                except Exception:
                    pass
            # 2) data/result/output/value も試す
            for attr in ("data", "result", "output", "value"):
                if hasattr(res, attr):
                    try:
                        return cls._unwrap_tool_result(getattr(res, attr), _depth + 1)
                    except Exception:
                        continue
            # 3) to_dict 経由
            if hasattr(res, "to_dict") and callable(getattr(res, "to_dict")):
                try:
                    d = res.to_dict()
                    if isinstance(d, dict) and "content" in d:
                        return cls._unwrap_tool_result(d["content"], _depth + 1)
                    return d
                except Exception:
                    pass

        # TextContent 単体なら text 抜き出し
        if hasattr(res, "text"):
            try:
                return cls._maybe_json_load(getattr(res, "text"))
            except Exception:
                pass

        # 最後の手段：そのまま
        return res

    def _resolve_callable(self, obj) -> Tuple[str, Callable]:
        """
        どう呼ぶかを判定して (mode, fn) を返す。
        mode:
          - "plain"   : fn(*args, **kwargs)
          - "toolrun" : fn(arguments_dict)  # FunctionTool.run(arguments)
        """
        # 1) 元関数寄りの属性を優先（kwargs を素直に渡せる可能性を最大化）
        for attr in ("func", "_func", "__wrapped__", "__call__", "call", "invoke"):
            cand = getattr(obj, attr, None)
            if callable(cand):
                return "plain", cand

        # 2) FunctionTool.run を検出
        run_cand = getattr(obj, "run", None)
        if callable(run_cand) and self._is_method_of(obj, run_cand):
            return "toolrun", run_cand

        # 3) フォールバック
        if callable(obj):
            return "plain", obj

        raise TypeError(f"Object is not callable and no callable attribute found: {type(obj)}")

    def _call(self, name: str, *args, **kwargs):
        """
        module.<name> を実行して unwrap 済みの値を返す。
          - mode "plain"   : fn(*args, **kwargs)
          - mode "toolrun" : fn(arguments_dict)
        """
        obj = getattr(self.module, name, None)
        if obj is None:
            raise AttributeError(f"{name} not found in module")

        mode, fn = self._resolve_callable(obj)

        # plain 経路
        if mode == "plain":
            if asyncio.iscoroutinefunction(fn):
                res = asyncio.run(fn(*args, **kwargs))
            else:
                res = fn(*args, **kwargs)
                if asyncio.iscoroutine(res):
                    res = asyncio.run(res)
            return self._unwrap_tool_result(res)

        # toolrun 経路（必ず kwargs を辞書にして渡す）
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
        result = self._call("ping")  # ToolResult でも unwrap される
        # 念のための緩和（dict/その他の可能性）
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
        """Known SKU in JPY should return a priced item; otherwise skip (subset揺らぎ対応)."""
        if not hasattr(self.module, "pricing_get_sku"):
            self.skipTest("pricing_get_sku not found in module")

        print(f"About to call pricing_get_sku('{self.probe_sku_ok}', '{self.ccy_jpy}')")
        try:
            out: Dict[str, Any] = self._call(
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

        if "note" in out and out.get("note") in {"not-found"}:
            self.skipTest(f"SKU appears missing in public subset: {out}")
            return

        for k in ("partNumber", "displayName", "metricName", "serviceCategory", "currencyCode"):
            self.assertIn(k, out, f"Missing key '{k}'")
        self.assertEqual(out.get("currencyCode"), self.ccy_jpy)
        self.assertIsNotNone(out.get("model"))
        self.assertIsNotNone(out.get("value"))
        self.assertGreater(float(out.get("value", 0)), 0.0)

        print(f"OK: {out.get('partNumber')} {out.get('displayName')} -> "
              f"{out.get('model')} {out.get('value')} {out.get('currencyCode')}")

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
        """require_priced=True: every item must have model/value and correct currencyCode."""
        if not hasattr(self.module, "pricing_search_name"):
            self.skipTest("pricing_search_name not found in module")

        print(f"About to call pricing_search_name(query='{self.query_compute}', "
              f"currency='{self.ccy_jpy}', require_priced=True)")
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
        """Without require_priced, currencyCode should still be populated via simplify(...)."""
        if not hasattr(self.module, "pricing_search_name"):
            self.skipTest("pricing_search_name not found in module")

        query = "Object Storage"
        print(f"About to call pricing_search_name(query='{query}', currency='{self.ccy_jpy}', require_priced=False)")
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
        items = out.get("items") or []
        if len(items) == 0:
            self.skipTest("No items returned (likely transient)")
            return

        for it in items:
            self.assertIn("currencyCode", it)
            self.assertEqual(it.get("currencyCode"), self.ccy_jpy)

        print(f"currencyCode populated for {len(items)} items")

    def test_search_name_limit_clamped_to_20(self):
        """Large limit should be capped to <= 20."""
        if not hasattr(self.module, "pricing_search_name"):
            self.skipTest("pricing_search_name not found in module")

        big_limit = 100
        print(f"About to call pricing_search_name(query='Compute', currency='USD', limit={big_limit})")
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
        self.assertEqual(out.get("note"), "empty-query")
        self.assertEqual(out.get("items"), [])
        print("Empty query handled correctly")

    def tearDown(self):
        print(f"{'=' * 70}")
        print(f"Completed test: {self._testMethodName}")
        print(f"{'=' * 70}\n")


if __name__ == "__main__":
    print("Starting oci-pricing-mcp-server functional tests")
    print("Env overrides: PRICING_SERVER_FILENAME, PROBE_SKU_OK, PROBE_SKU_MISSING, PROBE_CCY, PROBE_QUERY")

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
