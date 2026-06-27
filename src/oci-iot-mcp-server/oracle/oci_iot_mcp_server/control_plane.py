import base64
from typing import Any, Callable

from oci.iot.models import (
    InvokeRawBinaryCommandDetails,
    InvokeRawJsonCommandDetails,
    InvokeRawTextCommandDetails,
)

from .client import get_iot_client
from .models import (
    DigitalTwinAdapterModel,
    DigitalTwinInstanceModel,
    DigitalTwinModelModel,
    DigitalTwinModelSummaryModel,
    DigitalTwinRelationshipModel,
    ErrorModel,
    IoTDomainGroupModel,
    IoTDomainModel,
    LogModel,
    WorkRequestModel,
)

MAX_RELATIONSHIP_LIST_ITEMS = 1000
MAX_RELATIONSHIP_PAGE_SIZE = 1000
MAX_RELATIONSHIP_PAGES = 100


def _normalize_items(data: Any) -> list[Any]:
    if hasattr(data, "items"):
        return list(data.items)
    if isinstance(data, (list, tuple)):
        return list(data)
    if data is None:
        return []
    return [data]


def _map_one(method_name: str, mapper: Callable[[Any], dict], **kwargs) -> dict:
    response = getattr(get_iot_client(), method_name)(**kwargs)
    return mapper(response.data)


def _map_many(method_name: str, mapper: Callable[[Any], dict], **kwargs) -> list[dict]:
    response = getattr(get_iot_client(), method_name)(**kwargs)
    return [mapper(item) for item in _normalize_items(response.data)]


def _header_value(headers: Any, name: str):
    if not headers:
        return None
    value = headers.get(name) if hasattr(headers, "get") else None
    if value is not None:
        return value
    if hasattr(headers, "items"):
        lowered = name.lower()
        for key, candidate in headers.items():
            if str(key).lower() == lowered:
                return candidate
    return None


def _map_page(method_name: str, mapper: Callable[[Any], dict], **kwargs) -> dict:
    response = getattr(get_iot_client(), method_name)(**kwargs)
    headers = getattr(response, "headers", {}) or {}
    opc_next_page = _header_value(headers, "opc-next-page")
    opc_request_id = getattr(response, "request_id", None) or _header_value(headers, "opc-request-id")
    return {
        "items": [mapper(item) for item in _normalize_items(response.data)],
        "opc_next_page": opc_next_page,
        "opc_request_id": opc_request_id,
        "page": kwargs.get("page"),
        "limit": kwargs.get("limit"),
        "has_more": bool(opc_next_page),
    }


def map_digital_twin_adapter(model: Any) -> dict:
    return DigitalTwinAdapterModel.from_oci_model(model).model_dump()


def map_digital_twin_instance(model: Any) -> dict:
    return DigitalTwinInstanceModel.from_oci_model(model).model_dump()


def map_digital_twin_model(model: Any) -> dict:
    return DigitalTwinModelModel.from_oci_model(model).model_dump()


def map_digital_twin_model_summary(model: Any) -> dict:
    return DigitalTwinModelSummaryModel.from_oci_model(model).model_dump()


def map_digital_twin_relationship(model: Any) -> dict:
    return DigitalTwinRelationshipModel.from_oci_model(model).model_dump()


def map_iot_domain(model: Any) -> dict:
    return IoTDomainModel.from_oci_model(model).model_dump()


def map_iot_domain_group(model: Any) -> dict:
    return IoTDomainGroupModel.from_oci_model(model).model_dump()


def map_work_request(model: Any) -> dict:
    return WorkRequestModel.from_oci_model(model).model_dump()


def map_work_request_error(model: Any) -> dict:
    return ErrorModel.from_oci_model(model).model_dump()


def map_work_request_log(model: Any) -> dict:
    return LogModel.from_oci_model(model).model_dump()


def get_digital_twin_adapter_record(digital_twin_adapter_id: str) -> dict:
    return _map_one(
        "get_digital_twin_adapter",
        map_digital_twin_adapter,
        digital_twin_adapter_id=digital_twin_adapter_id,
    )


def get_digital_twin_instance_record(digital_twin_instance_id: str) -> dict:
    return _map_one(
        "get_digital_twin_instance",
        map_digital_twin_instance,
        digital_twin_instance_id=digital_twin_instance_id,
    )


def get_digital_twin_instance_content_record(digital_twin_instance_id: str):
    response = get_iot_client().get_digital_twin_instance_content(
        digital_twin_instance_id=digital_twin_instance_id
    )
    return response.data


def get_digital_twin_model_record(digital_twin_model_id: str) -> dict:
    return _map_one(
        "get_digital_twin_model",
        map_digital_twin_model,
        digital_twin_model_id=digital_twin_model_id,
    )


def get_digital_twin_model_spec_record(digital_twin_model_id: str):
    response = get_iot_client().get_digital_twin_model_spec(digital_twin_model_id=digital_twin_model_id)
    return response.data


def get_digital_twin_relationship_record(digital_twin_relationship_id: str) -> dict:
    return _map_one(
        "get_digital_twin_relationship",
        map_digital_twin_relationship,
        digital_twin_relationship_id=digital_twin_relationship_id,
    )


def get_iot_domain_record(iot_domain_id: str) -> dict:
    return _map_one("get_iot_domain", map_iot_domain, iot_domain_id=iot_domain_id)


def get_iot_domain_group_record(iot_domain_group_id: str) -> dict:
    return _map_one(
        "get_iot_domain_group",
        map_iot_domain_group,
        iot_domain_group_id=iot_domain_group_id,
    )


def get_work_request_record(work_request_id: str) -> dict:
    return _map_one("get_work_request", map_work_request, work_request_id=work_request_id)


def _digital_twin_adapters_list_kwargs(
    *,
    iot_domain_id: str,
    id: str | None = None,
    digital_twin_model_spec_uri: str | None = None,
    digital_twin_model_id: str | None = None,
    display_name: str | None = None,
    lifecycle_state: str | None = None,
    page: str | None = None,
    limit: int | None = None,
    sort_order: str | None = None,
    sort_by: str | None = None,
    opc_request_id: str | None = None,
) -> dict:
    kwargs = {
        "iot_domain_id": iot_domain_id,
        "id": id,
        "digital_twin_model_spec_uri": digital_twin_model_spec_uri,
        "digital_twin_model_id": digital_twin_model_id,
        "display_name": display_name,
        "lifecycle_state": lifecycle_state,
        "page": page,
        "limit": limit,
        "sort_order": sort_order,
        "sort_by": sort_by,
        "opc_request_id": opc_request_id,
    }
    return {key: value for key, value in kwargs.items() if value is not None}


def list_digital_twin_adapters_records(
    *,
    iot_domain_id: str,
    id: str | None = None,
    digital_twin_model_spec_uri: str | None = None,
    digital_twin_model_id: str | None = None,
    display_name: str | None = None,
    lifecycle_state: str | None = None,
    page: str | None = None,
    limit: int | None = None,
    sort_order: str | None = None,
    sort_by: str | None = None,
    opc_request_id: str | None = None,
) -> list[dict]:
    return _map_many(
        "list_digital_twin_adapters",
        map_digital_twin_adapter,
        **_digital_twin_adapters_list_kwargs(
            iot_domain_id=iot_domain_id,
            id=id,
            digital_twin_model_spec_uri=digital_twin_model_spec_uri,
            digital_twin_model_id=digital_twin_model_id,
            display_name=display_name,
            lifecycle_state=lifecycle_state,
            page=page,
            limit=limit,
            sort_order=sort_order,
            sort_by=sort_by,
            opc_request_id=opc_request_id,
        ),
    )


def list_digital_twin_adapters_page_record(
    *,
    iot_domain_id: str,
    id: str | None = None,
    digital_twin_model_spec_uri: str | None = None,
    digital_twin_model_id: str | None = None,
    display_name: str | None = None,
    lifecycle_state: str | None = None,
    page: str | None = None,
    limit: int | None = None,
    sort_order: str | None = None,
    sort_by: str | None = None,
    opc_request_id: str | None = None,
) -> dict:
    return _map_page(
        "list_digital_twin_adapters",
        map_digital_twin_adapter,
        **_digital_twin_adapters_list_kwargs(
            iot_domain_id=iot_domain_id,
            id=id,
            digital_twin_model_spec_uri=digital_twin_model_spec_uri,
            digital_twin_model_id=digital_twin_model_id,
            display_name=display_name,
            lifecycle_state=lifecycle_state,
            page=page,
            limit=limit,
            sort_order=sort_order,
            sort_by=sort_by,
            opc_request_id=opc_request_id,
        ),
    )


def _digital_twin_models_list_kwargs(
    *,
    iot_domain_id: str,
    id: str | None = None,
    display_name: str | None = None,
    spec_uri_starts_with: str | None = None,
    lifecycle_state: str | None = None,
    page: str | None = None,
    limit: int | None = None,
    sort_order: str | None = None,
    sort_by: str | None = None,
    opc_request_id: str | None = None,
) -> dict:
    kwargs = {
        "iot_domain_id": iot_domain_id,
        "id": id,
        "display_name": display_name,
        "spec_uri_starts_with": spec_uri_starts_with,
        "lifecycle_state": lifecycle_state,
        "page": page,
        "limit": limit,
        "sort_order": sort_order,
        "sort_by": sort_by,
        "opc_request_id": opc_request_id,
    }
    return {key: value for key, value in kwargs.items() if value is not None}


def list_digital_twin_models_records(
    *,
    iot_domain_id: str,
    id: str | None = None,
    display_name: str | None = None,
    spec_uri_starts_with: str | None = None,
    lifecycle_state: str | None = None,
    page: str | None = None,
    limit: int | None = None,
    sort_order: str | None = None,
    sort_by: str | None = None,
    opc_request_id: str | None = None,
) -> list[dict]:
    return _map_many(
        "list_digital_twin_models",
        map_digital_twin_model_summary,
        **_digital_twin_models_list_kwargs(
            iot_domain_id=iot_domain_id,
            id=id,
            display_name=display_name,
            spec_uri_starts_with=spec_uri_starts_with,
            lifecycle_state=lifecycle_state,
            page=page,
            limit=limit,
            sort_order=sort_order,
            sort_by=sort_by,
            opc_request_id=opc_request_id,
        ),
    )


def list_digital_twin_models_page_record(
    *,
    iot_domain_id: str,
    id: str | None = None,
    display_name: str | None = None,
    spec_uri_starts_with: str | None = None,
    lifecycle_state: str | None = None,
    page: str | None = None,
    limit: int | None = None,
    sort_order: str | None = None,
    sort_by: str | None = None,
    opc_request_id: str | None = None,
) -> dict:
    return _map_page(
        "list_digital_twin_models",
        map_digital_twin_model_summary,
        **_digital_twin_models_list_kwargs(
            iot_domain_id=iot_domain_id,
            id=id,
            display_name=display_name,
            spec_uri_starts_with=spec_uri_starts_with,
            lifecycle_state=lifecycle_state,
            page=page,
            limit=limit,
            sort_order=sort_order,
            sort_by=sort_by,
            opc_request_id=opc_request_id,
        ),
    )


def _digital_twin_instances_list_kwargs(
    *,
    iot_domain_id: str,
    display_name: str | None = None,
    page: str | None = None,
    lifecycle_state: str | None = None,
    sort_order: str | None = None,
    sort_by: str | None = None,
    opc_request_id: str | None = None,
    digital_twin_model_id: str | None = None,
    digital_twin_model_spec_uri: str | None = None,
    connectivity_type: str | None = None,
    id: str | None = None,
    limit: int = 1000,
) -> dict:
    kwargs = {
        "iot_domain_id": iot_domain_id,
        "display_name": display_name,
        "page": page,
        "lifecycle_state": lifecycle_state,
        "sort_order": sort_order,
        "sort_by": sort_by,
        "opc_request_id": opc_request_id,
        "digital_twin_model_id": digital_twin_model_id,
        "digital_twin_model_spec_uri": digital_twin_model_spec_uri,
        "connectivity_type": connectivity_type,
        "id": id,
        "limit": limit,
    }
    return {key: value for key, value in kwargs.items() if value is not None}


def list_digital_twin_instances_records(
    *,
    iot_domain_id: str,
    display_name: str | None = None,
    page: str | None = None,
    lifecycle_state: str | None = None,
    sort_order: str | None = None,
    sort_by: str | None = None,
    opc_request_id: str | None = None,
    digital_twin_model_id: str | None = None,
    digital_twin_model_spec_uri: str | None = None,
    connectivity_type: str | None = None,
    id: str | None = None,
    limit: int = 1000,
) -> list[dict]:
    return _map_many(
        "list_digital_twin_instances",
        map_digital_twin_instance,
        **_digital_twin_instances_list_kwargs(
            iot_domain_id=iot_domain_id,
            display_name=display_name,
            page=page,
            lifecycle_state=lifecycle_state,
            sort_order=sort_order,
            sort_by=sort_by,
            opc_request_id=opc_request_id,
            digital_twin_model_id=digital_twin_model_id,
            digital_twin_model_spec_uri=digital_twin_model_spec_uri,
            connectivity_type=connectivity_type,
            id=id,
            limit=limit,
        ),
    )


def list_digital_twin_instances_page_record(
    *,
    iot_domain_id: str,
    display_name: str | None = None,
    page: str | None = None,
    lifecycle_state: str | None = None,
    sort_order: str | None = None,
    sort_by: str | None = None,
    opc_request_id: str | None = None,
    digital_twin_model_id: str | None = None,
    digital_twin_model_spec_uri: str | None = None,
    connectivity_type: str | None = None,
    id: str | None = None,
    limit: int = 1000,
) -> dict:
    return _map_page(
        "list_digital_twin_instances",
        map_digital_twin_instance,
        **_digital_twin_instances_list_kwargs(
            iot_domain_id=iot_domain_id,
            display_name=display_name,
            page=page,
            lifecycle_state=lifecycle_state,
            sort_order=sort_order,
            sort_by=sort_by,
            opc_request_id=opc_request_id,
            digital_twin_model_id=digital_twin_model_id,
            digital_twin_model_spec_uri=digital_twin_model_spec_uri,
            connectivity_type=connectivity_type,
            id=id,
            limit=limit,
        ),
    )


def _digital_twin_relationships_list_kwargs(
    *,
    iot_domain_id: str,
    display_name: str | None = None,
    content_path: str | None = None,
    source_digital_twin_instance_id: str | None = None,
    target_digital_twin_instance_id: str | None = None,
    lifecycle_state: str | None = None,
    page: str | None = None,
    sort_order: str | None = None,
    sort_by: str | None = None,
    opc_request_id: str | None = None,
    id: str | None = None,
    limit: int | None = 1000,
) -> dict:
    kwargs = {
        "iot_domain_id": iot_domain_id,
        "display_name": display_name,
        "content_path": content_path,
        "source_digital_twin_instance_id": source_digital_twin_instance_id,
        "target_digital_twin_instance_id": target_digital_twin_instance_id,
        "lifecycle_state": lifecycle_state,
        "page": page,
        "sort_order": sort_order,
        "sort_by": sort_by,
        "opc_request_id": opc_request_id,
        "id": id,
        "limit": limit,
    }
    return {key: value for key, value in kwargs.items() if value is not None}


def list_digital_twin_relationships_records(
    *,
    iot_domain_id: str,
    display_name: str | None = None,
    content_path: str | None = None,
    source_digital_twin_instance_id: str | None = None,
    target_digital_twin_instance_id: str | None = None,
    lifecycle_state: str | None = None,
    page: str | None = None,
    sort_order: str | None = None,
    sort_by: str | None = None,
    opc_request_id: str | None = None,
    id: str | None = None,
    limit: int = 1000,
) -> list[dict]:
    return _map_many(
        "list_digital_twin_relationships",
        map_digital_twin_relationship,
        **_digital_twin_relationships_list_kwargs(
            iot_domain_id=iot_domain_id,
            display_name=display_name,
            content_path=content_path,
            source_digital_twin_instance_id=source_digital_twin_instance_id,
            target_digital_twin_instance_id=target_digital_twin_instance_id,
            lifecycle_state=lifecycle_state,
            page=page,
            sort_order=sort_order,
            sort_by=sort_by,
            opc_request_id=opc_request_id,
            id=id,
            limit=limit,
        ),
    )


def list_digital_twin_relationships_page_record(
    *,
    iot_domain_id: str,
    display_name: str | None = None,
    content_path: str | None = None,
    source_digital_twin_instance_id: str | None = None,
    target_digital_twin_instance_id: str | None = None,
    lifecycle_state: str | None = None,
    page: str | None = None,
    sort_order: str | None = None,
    sort_by: str | None = None,
    opc_request_id: str | None = None,
    id: str | None = None,
    limit: int = 1000,
) -> dict:
    return _map_page(
        "list_digital_twin_relationships",
        map_digital_twin_relationship,
        **_digital_twin_relationships_list_kwargs(
            iot_domain_id=iot_domain_id,
            display_name=display_name,
            content_path=content_path,
            source_digital_twin_instance_id=source_digital_twin_instance_id,
            target_digital_twin_instance_id=target_digital_twin_instance_id,
            lifecycle_state=lifecycle_state,
            page=page,
            sort_order=sort_order,
            sort_by=sort_by,
            opc_request_id=opc_request_id,
            id=id,
            limit=limit,
        ),
    )


def list_all_digital_twin_relationships_records(
    *,
    iot_domain_id: str,
    display_name: str | None = None,
    content_path: str | None = None,
    source_digital_twin_instance_id: str | None = None,
    target_digital_twin_instance_id: str | None = None,
    lifecycle_state: str | None = None,
    sort_order: str | None = None,
    sort_by: str | None = None,
    opc_request_id: str | None = None,
    id: str | None = None,
    max_items: int = 1000,
    page_size: int = 100,
) -> dict:
    if not 1 <= max_items <= MAX_RELATIONSHIP_LIST_ITEMS:
        raise ValueError(f"max_items must be between 1 and {MAX_RELATIONSHIP_LIST_ITEMS}")
    if not 1 <= page_size <= MAX_RELATIONSHIP_PAGE_SIZE:
        raise ValueError(f"page_size must be between 1 and {MAX_RELATIONSHIP_PAGE_SIZE}")

    items = []
    page = None
    pages_fetched = 0
    opc_next_page = None
    opc_request_id_value = None
    pagination_warning = None
    requested_pages = {page}

    while len(items) < max_items and pages_fetched < MAX_RELATIONSHIP_PAGES:
        remaining = max_items - len(items)
        page_payload = list_digital_twin_relationships_page_record(
            iot_domain_id=iot_domain_id,
            display_name=display_name,
            content_path=content_path,
            source_digital_twin_instance_id=source_digital_twin_instance_id,
            target_digital_twin_instance_id=target_digital_twin_instance_id,
            lifecycle_state=lifecycle_state,
            page=page,
            sort_order=sort_order,
            sort_by=sort_by,
            opc_request_id=opc_request_id,
            id=id,
            limit=min(page_size, remaining),
        )
        pages_fetched += 1
        page_items = page_payload["items"]
        items.extend(page_items[:remaining])
        opc_next_page = page_payload.get("opc_next_page")
        opc_request_id_value = page_payload.get("opc_request_id")
        if not opc_next_page:
            break
        if opc_next_page in requested_pages:
            pagination_warning = "Stopped relationship pagination because OCI returned a repeated opc-next-page token."
            break
        page = opc_next_page
        requested_pages.add(page)

    if (
        not pagination_warning
        and opc_next_page
        and len(items) < max_items
        and pages_fetched >= MAX_RELATIONSHIP_PAGES
    ):
        pagination_warning = (
            f"Stopped relationship pagination after reaching the maximum of {MAX_RELATIONSHIP_PAGES} SDK pages."
        )

    result = {
        "items": items,
        "count": len(items),
        "max_items": max_items,
        "page_size": page_size,
        "pages_fetched": pages_fetched,
        "opc_next_page": opc_next_page,
        "opc_request_id": opc_request_id_value,
        "has_more": bool(opc_next_page),
        "truncated": bool(opc_next_page),
    }
    if pagination_warning:
        result["pagination_warning"] = pagination_warning
    return result


def list_iot_domain_groups_records(
    *,
    compartment_id: str,
    id: str | None = None,
    display_name: str | None = None,
    lifecycle_state: str | None = None,
    type: str | None = None,
    page: str | None = None,
    limit: int | None = None,
    sort_order: str | None = None,
    sort_by: str | None = None,
    opc_request_id: str | None = None,
) -> list[dict]:
    kwargs = {
        "compartment_id": compartment_id,
        "id": id,
        "display_name": display_name,
        "lifecycle_state": lifecycle_state,
        "type": type,
        "page": page,
        "limit": limit,
        "sort_order": sort_order,
        "sort_by": sort_by,
        "opc_request_id": opc_request_id,
    }
    return _map_many(
        "list_iot_domain_groups",
        map_iot_domain_group,
        **{key: value for key, value in kwargs.items() if value is not None},
    )


def list_iot_domains_records(
    *,
    compartment_id: str,
    id: str | None = None,
    iot_domain_group_id: str | None = None,
    display_name: str | None = None,
    lifecycle_state: str | None = None,
    page: str | None = None,
    limit: int | None = None,
    sort_order: str | None = None,
    sort_by: str | None = None,
    opc_request_id: str | None = None,
) -> list[dict]:
    kwargs = {
        "compartment_id": compartment_id,
        "id": id,
        "iot_domain_group_id": iot_domain_group_id,
        "display_name": display_name,
        "lifecycle_state": lifecycle_state,
        "page": page,
        "limit": limit,
        "sort_order": sort_order,
        "sort_by": sort_by,
        "opc_request_id": opc_request_id,
    }
    return _map_many(
        "list_iot_domains",
        map_iot_domain,
        **{key: value for key, value in kwargs.items() if value is not None},
    )


def list_work_request_errors_records(*, work_request_id: str) -> list[dict]:
    return _map_many("list_work_request_errors", map_work_request_error, work_request_id=work_request_id)


def list_work_request_logs_records(*, work_request_id: str) -> list[dict]:
    return _map_many("list_work_request_logs", map_work_request_log, work_request_id=work_request_id)


def list_work_requests_records(
    *,
    compartment_id: str,
    id: str | None = None,
    status: str | None = None,
    resource_id: str | None = None,
    page: str | None = None,
    limit: int | None = None,
    sort_order: str | None = None,
    sort_by: str | None = None,
    opc_request_id: str | None = None,
) -> list[dict]:
    kwargs = {
        "compartment_id": compartment_id,
        "id": id,
        "status": status,
        "resource_id": resource_id,
        "page": page,
        "limit": limit,
        "sort_order": sort_order,
        "sort_by": sort_by,
        "opc_request_id": opc_request_id,
    }
    return _map_many(
        "list_work_requests",
        map_work_request,
        **{key: value for key, value in kwargs.items() if value is not None},
    )


def build_invoke_raw_command_details(
    *,
    request_endpoint: str,
    request_data_format: str,
    request_data: object,
    response_endpoint: str | None = None,
    request_duration: str | None = None,
    response_duration: str | None = None,
):
    common = {
        "request_endpoint": request_endpoint,
        "response_endpoint": response_endpoint,
        "request_duration": request_duration,
        "response_duration": response_duration,
    }
    format_name = request_data_format.upper()

    if format_name == "TEXT":
        if not isinstance(request_data, str):
            raise ValueError("TEXT request_data must be a string.")
        return InvokeRawTextCommandDetails(
            **common,
            request_data_content_type="text/plain",
            request_data=request_data,
        )

    if format_name == "JSON":
        if not isinstance(request_data, dict):
            raise ValueError("JSON request_data must be an object.")
        return InvokeRawJsonCommandDetails(
            **common,
            request_data_content_type="application/json",
            request_data=request_data,
        )

    if format_name == "BINARY":
        if not isinstance(request_data, str):
            raise ValueError("BINARY request_data must be a base64-encoded string.")
        base64.b64decode(request_data, validate=True)
        return InvokeRawBinaryCommandDetails(
            **common,
            request_data_content_type="application/octet-stream",
            request_data=request_data,
        )

    raise ValueError("request_data_format must be one of TEXT, JSON, or BINARY.")


def invoke_raw_command(
    *,
    digital_twin_instance_id: str,
    request_endpoint: str,
    request_data_format: str,
    request_data: object,
    response_endpoint: str | None = None,
    request_duration: str | None = None,
    response_duration: str | None = None,
) -> dict:
    details = build_invoke_raw_command_details(
        request_endpoint=request_endpoint,
        request_data_format=request_data_format,
        request_data=request_data,
        response_endpoint=response_endpoint,
        request_duration=request_duration,
        response_duration=response_duration,
    )
    response = get_iot_client().invoke_raw_command(
        digital_twin_instance_id=digital_twin_instance_id,
        invoke_raw_command_details=details,
    )
    headers = getattr(response, "headers", {}) or {}
    return {
        "status_code": getattr(response, "status", None),
        "opc_request_id": headers.get("opc-request-id"),
    }
