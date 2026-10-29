from .control_plane import (
    get_digital_twin_instance_record,
    list_digital_twin_instances_page_record,
    list_iot_domains_page_record,
)
from .errors import (
    ambiguity_error,
    invalid_input_error,
    not_found_error,
    error_result,
)
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
    input_payload = {
        "iot_domain_display_name": iot_domain_display_name,
        "domain_short_id": domain_short_id,
        "compartment_id": compartment_id,
    }

    # An explicit OCID takes precedence over friendly selectors.
    if iot_domain_id:
        return success_result({"id": iot_domain_id})

    if not iot_domain_display_name and not domain_short_id:
        return invalid_input_error(
            resource_type="iot_domain",
            message="An IoT domain ID, display name, or short ID is required.",
            input_payload=input_payload,
            retry_hint=(
                "Retry with iot_domain_id, or provide a domain display name "
                "or short ID together with compartment_id."
            ),
        )

    if not compartment_id:
        return invalid_input_error(
            resource_type="iot_domain",
            message="Friendly IoT domain lookup requires compartment_id.",
            input_payload=input_payload,
            retry_hint="Retry with iot_domain_id or include compartment_id.",
        )

    matches = []
    page = None
    seen_tokens = set()

    while True:
        try:
            response = list_iot_domains_page_record(
                compartment_id=compartment_id,
                page=page,
                limit=1000,
            )
        except Exception as exc:
            return error_result(
                code="domain_search_failed",
                message="Failed to search IoT domains.",
                resource_type="iot_domain",
                retry_hint=(
                    "Retry the request. If the issue persists, "
                    "check service availability."
                ),
                details={"reason": str(exc)},
            )

        for row in response["items"]:
            name_matches = (
                bool(iot_domain_display_name)
                and row.get("name") == iot_domain_display_name
            )
            short_id_matches = (
                bool(domain_short_id)
                and _first_label(row.get("device_host")) == domain_short_id
            )

            # Preserve the existing OR semantics when both selectors are given.
            if name_matches or short_id_matches:
                matches.append(row)

        next_page = response.get("opc_next_page")

        if not next_page:
            break

        if next_page in seen_tokens:
            return error_result(
                code="pagination_error",
                message="Repeated pagination token while searching IoT domains.",
                resource_type="iot_domain",
                retry_hint=(
                    "Retry the request. If the issue persists, "
                    "check service pagination behavior."
                ),
                details={
                    "page": page,
                    "next_page": next_page,
                },
            )

        seen_tokens.add(next_page)
        page = next_page

    # Deduplicate records matched by both selectors or repeated across pages.
    unique_matches = {}

    for row in matches:
        domain_id = row.get("id")

        if not domain_id:
            return error_result(
                code="invalid_domain_record",
                message="A matching IoT domain record is missing its ID.",
                resource_type="iot_domain",
                details={"record": row},
            )

        unique_matches[domain_id] = row

    matches = list(unique_matches.values())

    if not matches:
        return not_found_error(
            resource_type="iot_domain",
            message="No IoT domain matched the provided selector.",
            input_payload=input_payload,
        )

    if len(matches) > 1:
        return ambiguity_error(
            resource_type="iot_domain",
            message="Multiple IoT domains matched the provided selector.",
            input_payload=input_payload,
            candidates=[
                {
                    "id": row["id"],
                    "display_name": row.get("name"),
                }
                for row in matches
            ],
        )

    return success_result(matches[0])

def resolve_twin_selector(
    *,
    digital_twin_instance_id: str | None = None,
    digital_twin_instance_name: str | None = None,
    iot_domain_id: str | None = None,
) -> dict:
    input_payload = {
        "digital_twin_instance_id": digital_twin_instance_id,
        "digital_twin_instance_name": digital_twin_instance_name,
        "iot_domain_id": iot_domain_id,
    }

    # An explicit ID takes precedence over friendly-name lookup.
    if digital_twin_instance_id:
        try:
            record = get_digital_twin_instance_record(
                digital_twin_instance_id=digital_twin_instance_id
            )
        except Exception as exc:
            return error_result(
                code="twin_lookup_failed",
                message="Failed to retrieve the digital twin instance.",
                resource_type="digital_twin_instance",
                retry_hint=(
                    "Retry the request. If the issue persists, "
                    "check service availability and the supplied ID."
                ),
                details={"reason": str(exc)},
            )

        return success_result(record)

    if not digital_twin_instance_name:
        return invalid_input_error(
            resource_type="digital_twin_instance",
            message="A digital twin instance ID or name is required.",
            input_payload=input_payload,
            retry_hint=(
                "Retry with digital_twin_instance_id or provide "
                "digital_twin_instance_name and iot_domain_id."
            ),
        )

    if not iot_domain_id:
        return invalid_input_error(
            resource_type="digital_twin_instance",
            message="Friendly digital twin lookup requires an IoT domain ID.",
            input_payload=input_payload,
            retry_hint=(
                "Retry with digital_twin_instance_id or include iot_domain_id."
            ),
        )

    matches = []
    page = None
    seen_tokens = set()

    while True:
        try:
            response = list_digital_twin_instances_page_record(
                iot_domain_id=iot_domain_id,
                page=page,
                limit=1000,
            )
        except Exception as exc:
            return error_result(
                code="twin_search_failed",
                message="Failed to search digital twin instances.",
                resource_type="digital_twin_instance",
                retry_hint=(
                    "Retry the request. If the issue persists, "
                    "check service availability."
                ),
                details={"reason": str(exc)},
            )

        for row in response["items"]:
            if row.get("name") == digital_twin_instance_name:
                matches.append(row)

        next_page = response.get("opc_next_page")

        if not next_page:
            break

        if next_page in seen_tokens:
            return error_result(
                code="pagination_error",
                message=(
                    "Repeated pagination token while searching "
                    "digital twin instances."
                ),
                resource_type="digital_twin_instance",
                retry_hint=(
                    "Retry the request. If the issue persists, "
                    "check service pagination behavior."
                ),
                details={
                    "page": page,
                    "next_page": next_page,
                },
            )

        seen_tokens.add(next_page)
        page = next_page

    # Deduplicate by twin ID before checking for ambiguity.
    unique_matches = {}

    for row in matches:
        twin_id = row.get("id")

        if not twin_id:
            return error_result(
                code="invalid_twin_record",
                message="A matching digital twin record is missing its ID.",
                resource_type="digital_twin_instance",
                details={"record": row},
            )

        unique_matches[twin_id] = row

    matches = list(unique_matches.values())

    if not matches:
        return not_found_error(
            resource_type="digital_twin_instance",
            message="No digital twin instance matched the provided selector.",
            input_payload=input_payload,
        )

    if len(matches) > 1:
        return ambiguity_error(
            resource_type="digital_twin_instance",
            message=(
                f"Multiple digital twin instances matched display name "
                f"'{digital_twin_instance_name}'."
            ),
            input_payload=input_payload,
            candidates=[
                {
                    "id": row["id"],
                    "display_name": row.get("name"),
                }
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
