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


def list_digital_twin_adapters_records(*, iot_domain_id: str) -> list[dict]:
    return _map_many("list_digital_twin_adapters", map_digital_twin_adapter, iot_domain_id=iot_domain_id)


def list_digital_twin_models_records(*, iot_domain_id: str) -> list[dict]:
    return _map_many("list_digital_twin_models", map_digital_twin_model_summary, iot_domain_id=iot_domain_id)


def list_digital_twin_instances_records(*, iot_domain_id: str, limit: int = 1000) -> list[dict]:
    return _map_many(
        "list_digital_twin_instances",
        map_digital_twin_instance,
        iot_domain_id=iot_domain_id,
        limit=limit,
    )


def list_digital_twin_relationships_records(*, iot_domain_id: str) -> list[dict]:
    return _map_many(
        "list_digital_twin_relationships",
        map_digital_twin_relationship,
        iot_domain_id=iot_domain_id,
    )


def list_iot_domain_groups_records(*, compartment_id: str) -> list[dict]:
    return _map_many("list_iot_domain_groups", map_iot_domain_group, compartment_id=compartment_id)


def list_iot_domains_records(*, compartment_id: str) -> list[dict]:
    return _map_many("list_iot_domains", map_iot_domain, compartment_id=compartment_id)


def list_work_request_errors_records(*, work_request_id: str) -> list[dict]:
    return _map_many("list_work_request_errors", map_work_request_error, work_request_id=work_request_id)


def list_work_request_logs_records(*, work_request_id: str) -> list[dict]:
    return _map_many("list_work_request_logs", map_work_request_log, work_request_id=work_request_id)


def list_work_requests_records(*, compartment_id: str) -> list[dict]:
    return _map_many("list_work_requests", map_work_request, compartment_id=compartment_id)


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
