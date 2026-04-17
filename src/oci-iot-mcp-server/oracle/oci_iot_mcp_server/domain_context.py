from .control_plane import get_iot_domain_group_record, get_iot_domain_record
from .errors import error_result, invalid_input_error
from .resolvers import resolve_domain_selector, resolve_twin_for_tool
from .tool_models import DomainContextModel


def _first_label(host: str) -> str:
    return host.split(".", 1)[0]


def _parse_region(host: str) -> str:
    return host.split(".iot.", 1)[1].split(".oci.oraclecloud.com", 1)[0]


def derive_domain_context(*, iot_domain: dict, iot_domain_group: dict) -> DomainContextModel:
    device_region = _parse_region(iot_domain["device_host"])
    data_region = _parse_region(iot_domain_group["data_host"])
    if device_region != data_region:
        raise ValueError("device_host and data_host must share the same OCI region.")

    return DomainContextModel(
        iot_domain_id=iot_domain["id"],
        iot_domain_display_name=iot_domain.get("name"),
        iot_domain_group_id=iot_domain_group["id"],
        iot_domain_group_display_name=iot_domain_group.get("name"),
        device_host=iot_domain["device_host"],
        data_host=iot_domain_group["data_host"],
        domain_short_id=_first_label(iot_domain["device_host"]),
        domain_group_short_id=_first_label(iot_domain_group["data_host"]),
        region=device_region,
        db_token_scope=iot_domain_group.get("db_token_scope"),
        db_allowed_identity_domain_host=iot_domain.get("db_allowed_identity_domain_host"),
    )


def resolve_domain_context_for_tool(
    *,
    iot_domain_id: str | None = None,
    iot_domain_display_name: str | None = None,
    domain_short_id: str | None = None,
    compartment_id: str | None = None,
    digital_twin_instance_id: str | None = None,
    digital_twin_instance_name: str | None = None,
) -> dict:
    if digital_twin_instance_id or digital_twin_instance_name:
        twin = resolve_twin_for_tool(
            digital_twin_instance_id=digital_twin_instance_id,
            digital_twin_instance_name=digital_twin_instance_name,
            iot_domain_id=iot_domain_id,
            iot_domain_display_name=iot_domain_display_name,
            domain_short_id=domain_short_id,
            compartment_id=compartment_id,
        )
        if isinstance(twin, dict) and twin.get("ok") is False:
            return twin
        domain_id = twin["iot_domain_id"]
    else:
        domain_result = resolve_domain_selector(
            iot_domain_id=iot_domain_id,
            iot_domain_display_name=iot_domain_display_name,
            domain_short_id=domain_short_id,
            compartment_id=compartment_id,
        )
        if not domain_result["ok"]:
            return domain_result
        domain_id = domain_result["data"]["id"]

    if not domain_id:
        return invalid_input_error(
            resource_type="iot_domain",
            message="An IoT domain selector is required.",
            input_payload={
                "iot_domain_id": iot_domain_id,
                "iot_domain_display_name": iot_domain_display_name,
                "domain_short_id": domain_short_id,
                "compartment_id": compartment_id,
                "digital_twin_instance_id": digital_twin_instance_id,
                "digital_twin_instance_name": digital_twin_instance_name,
            },
            retry_hint="Retry with an IoT domain selector or a digital twin selector.",
        )

    iot_domain = get_iot_domain_record(domain_id)
    group_id = iot_domain.get("iot_domain_group_id")
    if not group_id:
        return error_result(
            code="control_plane_error",
            message="The resolved IoT domain did not include an IoT domain group identifier.",
            resource_type="iot_domain",
            details={"iot_domain_id": domain_id},
        )

    iot_domain_group = get_iot_domain_group_record(group_id)
    return derive_domain_context(
        iot_domain=iot_domain,
        iot_domain_group=iot_domain_group,
    ).model_dump()
