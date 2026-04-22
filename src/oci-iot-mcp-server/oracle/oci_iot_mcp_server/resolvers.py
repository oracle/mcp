from .control_plane import (
    get_digital_twin_instance_record,
    list_digital_twin_instances_records,
    list_iot_domains_records,
)
from .errors import ambiguity_error, invalid_input_error, not_found_error
from .tool_models import success_result


def _first_label(host: str | None) -> str | None:
    return host.split(".", 1)[0] if host else None


def resolve_domain_selector(
    *,
    iot_domain_id: str | None = None,
    iot_domain_display_name: str | None = None,
    domain_short_id: str | None = None,
    compartment_id: str | None = None,
) -> dict:
    if iot_domain_id:
        return success_result({"id": iot_domain_id})

    if not compartment_id:
        return invalid_input_error(
            resource_type="iot_domain",
            message="Friendly IoT domain lookup requires compartment_id.",
            input_payload={
                "iot_domain_display_name": iot_domain_display_name,
                "domain_short_id": domain_short_id,
            },
            retry_hint="Retry with iot_domain_id or include compartment_id.",
        )

    matches = []
    for row in list_iot_domains_records(compartment_id=compartment_id):
        if iot_domain_display_name and row.get("name") == iot_domain_display_name:
            matches.append(row)
        if domain_short_id and _first_label(row.get("device_host")) == domain_short_id:
            matches.append(row)

    unique_matches = list({row["id"]: row for row in matches}.values())
    if not unique_matches:
        return not_found_error(
            resource_type="iot_domain",
            message="No IoT domain matched the provided selector.",
            input_payload={
                "iot_domain_display_name": iot_domain_display_name,
                "domain_short_id": domain_short_id,
                "compartment_id": compartment_id,
            },
        )

    if len(unique_matches) > 1:
        return ambiguity_error(
            resource_type="iot_domain",
            message="Multiple IoT domains matched the provided selector.",
            input_payload={
                "iot_domain_display_name": iot_domain_display_name,
                "domain_short_id": domain_short_id,
                "compartment_id": compartment_id,
            },
            candidates=[
                {"id": row["id"], "display_name": row.get("name")}
                for row in unique_matches
            ],
        )

    return success_result(unique_matches[0])


def resolve_twin_selector(
    *,
    digital_twin_instance_id: str | None = None,
    digital_twin_instance_name: str | None = None,
    iot_domain_id: str | None = None,
) -> dict:
    if digital_twin_instance_id:
        return success_result(
            get_digital_twin_instance_record(
                digital_twin_instance_id=digital_twin_instance_id
            )
        )

    if not iot_domain_id:
        return invalid_input_error(
            resource_type="digital_twin_instance",
            message="Friendly digital twin lookup requires an IoT domain selector.",
            input_payload={"digital_twin_instance_name": digital_twin_instance_name},
            retry_hint="Retry with digital_twin_instance_id or include iot_domain_id.",
        )

    matches = [
        row
        for row in list_digital_twin_instances_records(iot_domain_id=iot_domain_id)
        if row.get("name") == digital_twin_instance_name
    ]
    if not matches:
        return not_found_error(
            resource_type="digital_twin_instance",
            message="No digital twin instance matched the provided selector.",
            input_payload={
                "digital_twin_instance_name": digital_twin_instance_name,
                "iot_domain_id": iot_domain_id,
            },
        )

    if len(matches) > 1:
        return ambiguity_error(
            resource_type="digital_twin_instance",
            message=(
                f"Multiple digital twin instances matched display name "
                f"'{digital_twin_instance_name}'."
            ),
            input_payload={
                "digital_twin_instance_name": digital_twin_instance_name,
                "iot_domain_id": iot_domain_id,
            },
            candidates=[
                {"id": row["id"], "display_name": row.get("name")}
                for row in matches
            ],
        )

    return success_result(matches[0])


def resolve_twin_for_tool(
    *,
    digital_twin_instance_id: str | None = None,
    digital_twin_instance_name: str | None = None,
    iot_domain_id: str | None = None,
    iot_domain_display_name: str | None = None,
    domain_short_id: str | None = None,
    compartment_id: str | None = None,
) -> dict:
    if digital_twin_instance_id:
        result = resolve_twin_selector(digital_twin_instance_id=digital_twin_instance_id)
        return result["data"] if result["ok"] else result

    if not digital_twin_instance_name:
        return invalid_input_error(
            resource_type="digital_twin_instance",
            message="A digital twin selector is required.",
            input_payload={
                "digital_twin_instance_id": digital_twin_instance_id,
                "digital_twin_instance_name": digital_twin_instance_name,
            },
            retry_hint="Retry with digital_twin_instance_id or digital_twin_instance_name.",
        )

    domain_result = resolve_domain_selector(
        iot_domain_id=iot_domain_id,
        iot_domain_display_name=iot_domain_display_name,
        domain_short_id=domain_short_id,
        compartment_id=compartment_id,
    )
    if not domain_result["ok"]:
        return domain_result

    result = resolve_twin_selector(
        digital_twin_instance_name=digital_twin_instance_name,
        iot_domain_id=domain_result["data"]["id"],
    )
    return result["data"] if result["ok"] else result
