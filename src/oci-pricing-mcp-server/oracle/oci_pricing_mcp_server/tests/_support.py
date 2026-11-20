"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import asyncio
import inspect
import os
import unittest

from oracle.oci_pricing_mcp_server import server


class PricingTestCase(unittest.TestCase):
    module = server
    probe_sku_ok = os.getenv("PROBE_SKU_OK", "B93113")
    probe_sku_missing = os.getenv("PROBE_SKU_MISSING", "B88298")
    ccy_jpy = os.getenv("PROBE_CCY", "JPY")
    query_compute = os.getenv("PROBE_QUERY", "Compute")

    def _call(self, name, **kwargs):
        result = getattr(self.module, name)(**kwargs)
        return asyncio.run(result) if inspect.isawaitable(result) else result
