"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
from typing import Any

import pytest

from oracle.oci_pricing_mcp_server.tests._support import PricingTestCase

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(os.getenv("OCI_PRICING_LIVE_TESTS") != "1", reason="Set OCI_PRICING_LIVE_TESTS=1 to contact the public Price List API"),
]


class TestPublicPriceList(PricingTestCase):
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
