"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import inspect
import oci
import pytest
from fastmcp import Client

from oracle.oci_cloud_mcp_server.server import (
    _extract_expected_kwargs_from_source,
    _supports_pagination,
    mcp,
)


def mock_execution(monkeypatch, sdk_class, operation, responses):
    """Replace execution only, retaining the installed SDK's accepted parameters."""
    captured = []
    sdk_method = getattr(sdk_class, operation)

    def execute(**kwargs):
        execute.__signature__.bind_partial(**kwargs)
        captured.append(kwargs)
        return responses[len(captured) - 1]

    signature = inspect.signature(sdk_method)
    parameters = [
        p for p in signature.parameters.values()
        if p.name != "self" and p.kind != inspect.Parameter.VAR_KEYWORD
    ]
    parameters.extend(
        inspect.Parameter(name, inspect.Parameter.KEYWORD_ONLY, default=None)
        for name in sorted(_extract_expected_kwargs_from_source(sdk_method) or [])
        if name not in signature.parameters
    )
    execute.__signature__ = inspect.Signature(parameters)
    fake_class = type(sdk_class.__name__, (), {operation: staticmethod(execute)})
    monkeypatch.setattr(
        "oracle.oci_cloud_mcp_server.server._import_client",
        lambda fqn: fake_class(),
    )
    return captured


def response(data, next_page=None):
    headers = {"opc-request-id": "mock-request"}
    if next_page is not None:
        headers["opc-next-page"] = next_page
    return oci.response.Response(200, headers, data, None)


async def invoke(sdk_class, operation, **kwargs):
    async with Client(mcp) as client:
        return (await client.call_tool("invoke_oci_api", {
            "client_fqn": f"{sdk_class.__module__.rsplit('.', 1)[0]}.{sdk_class.__name__}",
            "operation": operation,
            "result_mode": "full",
            **kwargs,
        })).data


@pytest.mark.parametrize("sdk_class,operation,expected", [
    (oci.generative_ai_inference.GenerativeAiInferenceClient, "summarize_text", False),
    (oci.core.VirtualNetworkClient, "list_ip_inventory", False),
    (oci.identity_domains.IdentityDomainsClient, "list_users", True),
    (oci.opsi.OperationsInsightsClient, "summarize_database_insight_resource_usage", True),
    (oci.object_storage.ObjectStorageClient, "list_objects", True),
    (oci.loggingsearch.LogSearchClient, "search_logs", True),
])
def test_installed_operation_contract(sdk_class, operation, expected):
    assert _supports_pagination(getattr(sdk_class, operation), operation) is expected


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["full", "summary", "auto"])
async def test_summarize_text_serializes_normally(monkeypatch, mode):
    sdk_class = oci.generative_ai_inference.GenerativeAiInferenceClient
    captured = mock_execution(monkeypatch, sdk_class, "summarize_text", [
        response(oci.generative_ai_inference.models.SummarizeTextResult(summary="valid summary"))
    ])
    result = await invoke(sdk_class, "summarize_text", result_mode=mode)
    assert "error" not in result
    data = result["data"] if mode == "full" else result["data"]["sample"]
    assert data["summary"] == "valid summary"
    assert result["result_meta"]["pagination_used"] is False
    assert captured == [{}]


@pytest.mark.asyncio
@pytest.mark.parametrize("offset_mode", [True, False])
async def test_users_native_continuation_and_metadata(monkeypatch, offset_mode):
    sdk_class = oci.identity_domains.IdentityDomainsClient
    models = oci.identity_domains.models
    pages = [
        response(models.Users(resources=[models.User(id="first")], total_results=2,
                              start_index=1, items_per_page=1, schemas=["scim-schema"]),
                 None if offset_mode else "second-page"),
        response(models.Users(resources=[models.User(id="second")], total_results=2,
                              start_index=2, items_per_page=1, schemas=["scim-schema"])),
    ]
    captured = mock_execution(monkeypatch, sdk_class, "list_users", pages)
    params = {"filter": 'userName sw "example"'}
    if offset_mode:
        params.update(start_index=1, count=1)
    result = await invoke(sdk_class, "list_users", params=params)
    assert "error" not in result
    assert [item["id"] for item in result["data"]["resources"]] == ["first", "second"]
    assert result["data"]["total_results"] == 2
    assert result["data"]["schemas"] == ["scim-schema"]
    assert result["data"]["items_per_page"] == 2
    assert captured == [params, {**params, **({"start_index": 2} if offset_mode else {"page": "second-page"})}]
    meta = result["result_meta"]
    assert meta["pagination_used"] is True
    assert meta["has_more_results"] is False
    assert [page["start_index"] for page in meta["page_metadata"]] == [1, 2]


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["full", "summary"])
async def test_users_cap_reports_truncation_without_skipping_records(monkeypatch, mode):
    sdk_class = oci.identity_domains.IdentityDomainsClient
    models = oci.identity_domains.models
    captured = mock_execution(monkeypatch, sdk_class, "list_users", [
        response(models.Users(resources=[models.User(id="first"), models.User(id="second")],
                              total_results=3, start_index=1, items_per_page=2)),
    ])
    result = await invoke(sdk_class, "list_users", max_results=1, result_mode=mode,
                          params={"count": 2})
    assert "error" not in result
    assert captured == [{"count": 1}]
    meta = result["result_meta"]
    assert meta["truncated"] is True
    assert meta["has_more_results"] is True
    assert "start_index" not in meta  # no lossless token for a cut page
    if mode == "full":
        assert [item["id"] for item in result["data"]["resources"]] == ["first"]


@pytest.mark.asyncio
async def test_declared_config_items_envelope_aggregates(monkeypatch):
    sdk_class = oci.opsi.OperationsInsightsClient
    models = oci.opsi.models
    captured = mock_execution(monkeypatch, sdk_class, "summarize_configuration_items", [
        response(models.ConfigurationItemsCollection(opsi_config_type="UX_CONFIGURATION",
                 config_items=[models.ConfigurationItemSummary()]), "second"),
        response(models.ConfigurationItemsCollection(opsi_config_type="UX_CONFIGURATION", config_items=[])),
    ])
    result = await invoke(sdk_class, "summarize_configuration_items")
    assert "error" not in result
    assert result["data"]["opsi_config_type"] == "UX_CONFIGURATION"
    assert len(result["data"]["config_items"]) == 1
    assert captured == [{}, {"page": "second"}]
    assert result["result_meta"]["page_metadata"] == [
        {"opsi_config_type": "UX_CONFIGURATION"}, {"opsi_config_type": "UX_CONFIGURATION"},
    ]


@pytest.mark.asyncio
async def test_non_collection_aggregate_preserves_payload_and_continuation(monkeypatch):
    sdk_class = oci.opsi.OperationsInsightsClient
    operation = "summarize_database_insight_resource_usage"
    captured = mock_execution(monkeypatch, sdk_class, operation, [response(
        oci.opsi.models.SummarizeDatabaseInsightResourceUsageAggregation(
            usage=4.5, capacity=10, usage_unit="GB", resource_metric="STORAGE"), "next"
    )])
    result = await invoke(sdk_class, operation)
    assert "error" not in result
    assert result["data"]["usage"] == 4.5
    assert result["data"]["capacity"] == 10
    assert result["data"]["usage_unit"] == "GB"
    assert captured == [{}]
    assert result["result_meta"]["pagination_used"] is False
    assert result["result_meta"]["next_page"] == "next"
    assert result["result_meta"]["has_more_results"] is True


@pytest.mark.asyncio
@pytest.mark.parametrize("empty", [False, True])
async def test_users_refuses_no_progress(monkeypatch, empty):
    sdk_class = oci.identity_domains.IdentityDomainsClient
    models = oci.identity_domains.models
    page = response(models.Users(resources=[] if empty else [models.User(id="first")],
                    start_index=1, items_per_page=0 if empty else 1, total_results=3))
    captured = mock_execution(monkeypatch, sdk_class, "list_users", [page, page])
    result = await invoke(sdk_class, "list_users", params={"count": 1})
    assert "error" in result
    assert ("no progress" if empty else "repeated continuation") in result["error"]
    assert len(captured) == (1 if empty else 2)


@pytest.mark.asyncio
async def test_multi_array_aggregate_is_not_flattened(monkeypatch):
    sdk_class = oci.opsi.OperationsInsightsClient
    models = oci.opsi.models
    operation = "summarize_database_insight_resource_forecast_trend"
    mock_execution(monkeypatch, sdk_class, operation, [response(
        models.SummarizeDatabaseInsightResourceForecastTrendAggregation(
            usage_unit="GB", historical_data=[models.HistoricalDataItem()],
            projected_data=[models.ProjectedDataItem()]), "next"
    )])
    result = await invoke(sdk_class, operation)
    assert "error" not in result
    assert result["data"]["usage_unit"] == "GB"
    assert len(result["data"]["historical_data"]) == 1
    assert len(result["data"]["projected_data"]) == 1
    assert result["result_meta"]["next_page"] == "next"


@pytest.mark.asyncio
async def test_real_logging_results_keep_search_metadata(monkeypatch):
    sdk_class = oci.loggingsearch.LogSearchClient
    models = oci.loggingsearch.models
    captured = mock_execution(monkeypatch, sdk_class, "search_logs", [
        response(models.SearchResponse(results=[models.SearchResult(data={"id": "first"})],
                                       summary=models.SearchResultSummary()), "second"),
        response(models.SearchResponse(results=[models.SearchResult(data={"id": "second"})],
                                       summary=models.SearchResultSummary())),
    ])
    result = await invoke(sdk_class, "search_logs")
    assert "error" not in result
    assert result["data"] == [{"data": {"id": "first"}}, {"data": {"id": "second"}}]
    assert captured == [{}, {"page": "second"}]
    assert len(result["result_meta"]["page_metadata"]) == 2
    assert "summary" in result["result_meta"]["page_metadata"][0]


@pytest.mark.asyncio
@pytest.mark.parametrize("empty_position", [0, 1])
async def test_logging_unset_results_are_empty_pages(monkeypatch, empty_position):
    sdk_class = oci.loggingsearch.LogSearchClient
    models = oci.loggingsearch.models
    pages = [
        models.SearchResponse(results=[models.SearchResult(data={"id": "record"})]),
        models.SearchResponse(summary=models.SearchResultSummary(result_count=0)),
    ]
    if empty_position == 0:
        pages.reverse()
    captured = mock_execution(monkeypatch, sdk_class, "search_logs", [
        response(pages[0], "second"), response(pages[1]),
    ])
    result = await invoke(sdk_class, "search_logs")
    assert "error" not in result
    assert result["data"] == [{"data": {"id": "record"}}]
    assert captured == [{}, {"page": "second"}]
    assert result["result_meta"]["has_more_results"] is False
    assert len(result["result_meta"]["page_metadata"]) == 2
    assert result["result_meta"]["page_metadata"][empty_position]["summary"]["result_count"] == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("dns", [False, True])
async def test_unset_items_keep_collection_shape(monkeypatch, dns):
    if dns:
        sdk_class = oci.dns.DnsClient
        operation = "get_zone_records"
        pages = [oci.dns.models.RecordCollection(), oci.dns.models.RecordCollection(
            items=[oci.dns.models.Record(domain="example.invalid")],
        )]
    else:
        sdk_class = oci.object_storage.ObjectStorageClient
        operation = "list_object_versions"
        pages = [oci.object_storage.models.ObjectVersionCollection(prefixes=["prefix/"]),
                 oci.object_storage.models.ObjectVersionCollection(items=[
                     oci.object_storage.models.ObjectVersionSummary(name="record"),
                 ])]
    captured = mock_execution(monkeypatch, sdk_class, operation, [
        response(pages[0], "second"), response(pages[1]),
    ])
    result = await invoke(sdk_class, operation)
    assert "error" not in result
    records = result["data"]["items"] if dns else result["data"]
    assert len(records) == 1
    assert records[0]["domain" if dns else "name"] == ("example.invalid" if dns else "record")
    assert captured == [{}, {"page": "second"}]
    assert result["result_meta"]["has_more_results"] is False
    if not dns:
        assert result["result_meta"]["page_metadata"][0]["prefixes"] == ["prefix/"]


@pytest.mark.asyncio
async def test_objects_prefix_only_page_still_continues(monkeypatch):
    sdk_class = oci.object_storage.ObjectStorageClient
    models = oci.object_storage.models
    captured = mock_execution(monkeypatch, sdk_class, "list_objects", [
        response(models.ListObjects(prefixes=["prefix/"], next_start_with="next-object")),
        response(models.ListObjects(objects=[models.ObjectSummary(name="record")])),
    ])
    result = await invoke(sdk_class, "list_objects")
    assert "error" not in result
    assert [item["name"] for item in result["data"]["objects"]] == ["record"]
    assert result["data"]["prefixes"] == ["prefix/"]
    assert captured == [{}, {"start": "next-object"}]
    assert result["result_meta"]["has_more_results"] is False


@pytest.mark.asyncio
async def test_real_objects_use_start_and_keep_prefixes(monkeypatch):
    sdk_class = oci.object_storage.ObjectStorageClient
    models = oci.object_storage.models
    captured = mock_execution(monkeypatch, sdk_class, "list_objects", [
        response(models.ListObjects(objects=[models.ObjectSummary(name="first")],
                                   prefixes=["prefix/"], next_start_with="next-object")),
        response(models.ListObjects(objects=[models.ObjectSummary(name="second")], prefixes=[])),
    ])
    result = await invoke(sdk_class, "list_objects")
    assert "error" not in result
    assert [item["name"] for item in result["data"]["objects"]] == ["first", "second"]
    assert result["data"]["prefixes"] == ["prefix/"]
    assert captured == [{}, {"start": "next-object"}]
    assert result["result_meta"]["has_more_results"] is False


@pytest.mark.asyncio
@pytest.mark.parametrize("exact_page", [False, True])
async def test_resource_cap_retains_only_lossless_continuation(monkeypatch, exact_page):
    sdk_class = oci.identity_domains.IdentityDomainsClient
    models = oci.identity_domains.models
    mock_execution(monkeypatch, sdk_class, "list_users", [response(models.Users(
        resources=[models.User(id="first")], total_results=2 if exact_page else 1,
        start_index=1, items_per_page=1,
    ))])
    result = await invoke(sdk_class, "list_users", max_results=1)
    assert "error" not in result
    assert result["result_meta"]["has_more_results"] is exact_page
    if exact_page:
        assert result["result_meta"]["start_index"] == 2
    else:
        assert "start_index" not in result["result_meta"]


@pytest.mark.asyncio
async def test_scim_count_zero_preserves_total_without_fetching(monkeypatch):
    sdk_class = oci.identity_domains.IdentityDomainsClient
    captured = mock_execution(monkeypatch, sdk_class, "list_users", [response(
        oci.identity_domains.models.Users(resources=[], total_results=10, start_index=1, items_per_page=0)
    )])
    result = await invoke(sdk_class, "list_users", params={"count": 0})
    assert "error" not in result
    assert result["data"]["total_results"] == 10
    assert result["data"]["resources"] == []
    assert result["result_meta"]["has_more_results"] is True
    assert captured == [{"count": 0}]


@pytest.mark.asyncio
async def test_later_page_shape_change_is_an_error_not_partial_success(monkeypatch):
    sdk_class = oci.identity_domains.IdentityDomainsClient
    captured = mock_execution(monkeypatch, sdk_class, "list_users", [
        response([], "next"), response({"unexpected": "object"}),
    ])
    result = await invoke(sdk_class, "list_users")
    assert "changed from a collection" in result["error"]
    assert captured == [{}, {"page": "next"}]


@pytest.mark.asyncio
@pytest.mark.parametrize("next_page", [None, "second-page"])
async def test_search_users_only_uses_supported_continuation(monkeypatch, next_page):
    sdk_class = oci.identity_domains.IdentityDomainsClient
    models = oci.identity_domains.models
    pages = [response(models.Users(resources=[models.User(id="first")],
                      start_index=1, items_per_page=1, total_results=2), next_page)]
    if next_page:
        pages.append(response(models.Users(resources=[models.User(id="second")],
                              start_index=2, items_per_page=1, total_results=2)))
    captured = mock_execution(monkeypatch, sdk_class, "search_users", pages)
    result = await invoke(sdk_class, "search_users", params={
        "user_search_request": {"start_index": 1, "count": 1},
    })
    assert "error" not in result
    assert [item["id"] for item in result["data"]["resources"]] == (
        ["first", "second"] if next_page else ["first"]
    )
    assert result["result_meta"]["has_more_results"] is (next_page is None)
    assert "start_index" not in result["result_meta"]
    assert all("start_index" not in call for call in captured)
    assert len(captured) == (2 if next_page else 1)


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["full", "summary", "auto"])
@pytest.mark.parametrize("cap", [1, 2, 3])
async def test_non_paginated_list_cap_reports_completeness(monkeypatch, mode, cap):
    sdk_class = oci.identity.IdentityClient
    mock_execution(monkeypatch, sdk_class, "list_regions", [response([
        oci.identity.models.Region(name="first"), oci.identity.models.Region(name="second"),
    ])])
    result = await invoke(sdk_class, "list_regions", result_mode=mode, max_results=cap)
    assert "error" not in result
    meta = result["result_meta"]
    assert meta["pagination_used"] is False
    assert meta["has_more_results"] is (cap < 2)
    assert meta.get("truncated", False) is (cap < 2)
    data = result["data"] if mode == "full" else result["data"]["sample"]
    assert len(data) == min(cap, 2)


@pytest.mark.asyncio
async def test_search_users_trimmed_page_remains_incomplete(monkeypatch):
    sdk_class = oci.identity_domains.IdentityDomainsClient
    models = oci.identity_domains.models
    mock_execution(monkeypatch, sdk_class, "search_users", [response(models.Users(
        resources=[models.User(id="first"), models.User(id="second")],
        start_index=1, items_per_page=2, total_results=2,
    ))])
    result = await invoke(sdk_class, "search_users", max_results=1,
                          params={"user_search_request": {"count": 2}})
    assert "error" not in result
    assert [item["id"] for item in result["data"]["resources"]] == ["first"]
    assert result["result_meta"]["has_more_results"] is True
    assert result["result_meta"]["truncated"] is True
