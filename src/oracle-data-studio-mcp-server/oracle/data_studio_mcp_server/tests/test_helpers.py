# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

"""Output bounding and trust metadata in tools._helpers."""

import pytest

from oracle.data_studio_mcp_server.tools._helpers import ai_chat_envelope


@pytest.mark.parametrize("key", ["items", "data", "rows"])
def test_select_ai_bounds_enveloped_rows_and_preserves_metadata(key):
    original = {key: [1, 2, 3], "summary": "generated text"}
    result = ai_chat_envelope(original, mode="chat_with_db", max_rows=1)
    assert result == {"source": "select_ai", "mode": "chat_with_db", "untrusted": True,
                      "result": {key: [1], "summary": "generated text", "truncated": True,
                                 "original_row_count": 3, "max_rows": 1}}
    assert original[key] == [1, 2, 3]
