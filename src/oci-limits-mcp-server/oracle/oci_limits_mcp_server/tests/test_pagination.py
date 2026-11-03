"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastmcp import Client

from oracle.oci_limits_mcp_server import server, utils


@pytest.fixture(params=["services", "limit_definitions", "limit_values"])
def listing(request):
    name = request.param
    args = {"compartment_id": "test-compartment"}
    if name != "services":
        args.update(service_name="test-service", name="test-limit")
    if name == "limit_values":
        args.update(scope_type="GLOBAL", availability_domain="test-ad")
    return name, args


@pytest.mark.parametrize(
    "limit,expected_count,request_limits,token",
    [
        (2, 2, [2], "page-2"),
        (3, 3, [3, 1], "page-3"),
        (None, 6, [None, None, None], None),
    ],
)
def test_total_limit_and_remaining_page_size(listing, limit, expected_count, request_limits, token):
    name, args = listing
    client = MagicMock()
    method = getattr(client, f"list_{name}")
    items = [SimpleNamespace(name=f"item-{i}") for i in range(6)]
    offset = 0

    def fetch(**kwargs):
        nonlocal offset
        count = min(kwargs["limit"] or 2, 2)
        data = items[offset : offset + count]
        offset += len(data)
        next_page = f"page-{method.call_count + 1}" if offset < 6 else None
        return SimpleNamespace(data=data, has_next_page=next_page is not None, next_page=next_page)

    method.side_effect = fetch
    result = getattr(utils, f"list_{name}_with_pagination")(client, **args, limit=limit)

    assert result == (items[:expected_count], token)
    assert [call.kwargs["limit"] for call in method.call_args_list] == request_limits
    assert [call.kwargs["page"] for call in method.call_args_list] == [None, "page-2", "page-3"][
        : len(request_limits)
    ]
    for call in method.call_args_list:
        assert all(call.kwargs[key] == value for key, value in args.items())


def test_empty_intermediate_page_does_not_stop_aggregation(listing):
    name, args = listing
    client = MagicMock()
    method = getattr(client, f"list_{name}")
    item = SimpleNamespace(name="item")
    method.side_effect = [
        SimpleNamespace(data=None, has_next_page=True, next_page="page-2"),
        SimpleNamespace(data=[item], has_next_page=False, next_page=None),
    ]
    assert getattr(utils, f"list_{name}_with_pagination")(client, **args, limit=2) == ([item], None)
    assert method.call_count == 2


@pytest.mark.asyncio
async def test_mcp_resume_tokens_reach_last_page(listing):
    name, args = listing
    tool_name = "list_limit_value" if name == "limit_values" else f"list_{name}"
    mock_client = MagicMock()
    method = getattr(mock_client, f"list_{name}")
    method.side_effect = [
        SimpleNamespace(data=[SimpleNamespace(name="first")], has_next_page=True, next_page="page-2"),
        SimpleNamespace(data=[SimpleNamespace(name="second")], has_next_page=True, next_page="page-3"),
        SimpleNamespace(data=[SimpleNamespace(name="third")], has_next_page=False, next_page=None),
    ]
    with patch.object(server, "get_limits_client", return_value=mock_client):
        async with Client(server.mcp) as client:
            page = None
            for expected_name, expected_token in [("first", "page-2"), ("second", "page-3"), ("third", None)]:
                result = (
                    await client.call_tool(tool_name, {**args, "limit": 1, "page": page})
                ).structured_content
                assert result["items"][0]["name"] == expected_name
                assert result["next_page"] == expected_token
                page = result["next_page"]
    assert method.call_count == 3
    assert [call.kwargs["page"] for call in method.call_args_list] == [None, "page-2", "page-3"]


@pytest.mark.parametrize("limit", [None, 2])
def test_explicit_page_fetches_only_one_page(listing, limit):
    name, args = listing
    client = MagicMock()
    method = getattr(client, f"list_{name}")
    method.return_value = SimpleNamespace(data=[], has_next_page=True, next_page="page-3")
    assert getattr(utils, f"list_{name}_with_pagination")(client, **args, page="page-2", limit=limit) == (
        [],
        "page-3",
    )
    method.assert_called_once()
    assert method.call_args.kwargs["page"] == "page-2"
