import os
from datetime import UTC, datetime

from .control_plane import (
    get_digital_twin_adapter_record,
    get_digital_twin_instance_record,
    get_digital_twin_model_record,
    get_iot_domain_group_record,
    get_iot_domain_record,
    list_digital_twin_instances_page_record,
)
from .data_plane import (
    DataApiTokenError,
    build_ords_base_url,
    get_cached_data_api_token,
    list_historized_records,
    list_raw_command_records,
    list_rejected_data_records,
    list_snapshot_records,
    require_token_credentials,
)
from .errors import error_result
from .domain_context import derive_domain_context
from .resolvers import resolve_twin_for_tool


def _is_error(payload) -> bool:
    return isinstance(payload, dict) and payload.get("ok") is False


def _latest_by_field(rows: list[dict], field_name: str) -> dict | None:
    if not rows:
        return None
    return max(rows, key=lambda row: row.get(field_name) or "")


def resolve_twin_bundle(
    *,
    digital_twin_instance_id: str | None = None,
    digital_twin_instance_name: str | None = None,
    iot_domain_id: str | None = None,
    iot_domain_display_name: str | None = None,
    domain_short_id: str | None = None,
    compartment_id: str | None = None,
):
    twin = resolve_twin_for_tool(
        digital_twin_instance_id=digital_twin_instance_id,
        digital_twin_instance_name=digital_twin_instance_name,
        iot_domain_id=iot_domain_id,
        iot_domain_display_name=iot_domain_display_name,
        domain_short_id=domain_short_id,
        compartment_id=compartment_id,
    )
    if _is_error(twin):
        return twin

    domain = get_iot_domain_record(twin["iot_domain_id"])
    domain_group = get_iot_domain_group_record(domain["iot_domain_group_id"])
    domain_context = derive_domain_context(
        iot_domain=domain,
        iot_domain_group=domain_group,
    ).model_dump()

    adapter = None
    model = None
    if twin.get("digital_twin_adapter_id"):
        adapter = get_digital_twin_adapter_record(twin["digital_twin_adapter_id"])
        model_id = adapter.get("digital_twin_model_id")
        if model_id:
            model = get_digital_twin_model_record(model_id)

    return {
        "twin": twin,
        "domain": domain,
        "domain_group": domain_group,
        "domain_context": domain_context,
        "adapter": adapter,
        "model": model,
    }


def resolve_twin_bundle_with_token(
    *,
    digital_twin_instance_id: str | None = None,
    digital_twin_instance_name: str | None = None,
    iot_domain_id: str | None = None,
    iot_domain_display_name: str | None = None,
    domain_short_id: str | None = None,
    compartment_id: str | None = None,
):
    bundle = resolve_twin_bundle(
        digital_twin_instance_id=digital_twin_instance_id,
        digital_twin_instance_name=digital_twin_instance_name,
        iot_domain_id=iot_domain_id,
        iot_domain_display_name=iot_domain_display_name,
        domain_short_id=domain_short_id,
        compartment_id=compartment_id,
    )
    if _is_error(bundle):
        return bundle

    credentials = require_token_credentials(os.environ)
    if _is_error(credentials):
        return credentials

    try:
        token = get_cached_data_api_token(
            domain_context=bundle["domain_context"],
            env=os.environ,
            now=lambda: datetime.now(UTC),
        )
    except DataApiTokenError as exc:
        return error_result(
            code=exc.code,
            message=str(exc),
            retry_hint=exc.retry_hint,
            details=exc.details,
        )
    except Exception as exc:
        return error_result(
            code="data_plane_error",
            message="Failed to mint an IoT Data API bearer token.",
            retry_hint="Verify the ORDS credentials and domain access, then retry.",
            details={"reason": str(exc)},
        )
    return bundle, token


def _summarize_checks(checks: list[dict]) -> str:
    if any(check.get("status") == "error" for check in checks):
        return "error"
    if any(check.get("status") == "warning" for check in checks):
        return "warning"
    return "ok"


def _build_check(name: str, status: str, details: dict | None = None) -> dict:
    return {"name": name, "status": status, "details": details or {}}


def _safe_exception_payload(message: str, exc: Exception) -> dict:
    return {"message": message, "error_type": exc.__class__.__name__}


def resolve_gateway_topology(bundle: dict, *, gateway_children_limit: int = 100) -> dict:
    twin = bundle["twin"]
    connectivity_type = twin.get("connectivity_type")
    gateway_ids = twin.get("gateways") or []
    topology = {
        "connectivity_type": connectivity_type,
        "gateways": gateway_ids,
        "gateway_twins": [],
        "gateway_resolution_errors": [],
        "child_discovery_errors": [],
        "child_discovery_truncated": False,
        "indirect_children": [],
        "warnings": [],
    }

    if connectivity_type == "INDIRECT":
        if not gateway_ids:
            topology["warnings"].append("Indirect twin has no gateway references.")
            return topology
        for gateway_id in gateway_ids:
            try:
                gateway = get_digital_twin_instance_record(gateway_id)
            except Exception as exc:
                topology["gateway_resolution_errors"].append(
                    {
                        "gateway_id": gateway_id,
                        **_safe_exception_payload("Gateway twin could not be resolved.", exc),
                    }
                )
                continue
            if _is_error(gateway):
                topology["gateway_resolution_errors"].append(
                    {"gateway_id": gateway_id, "error": gateway["error"]}
                )
            else:
                topology["gateway_twins"].append(gateway)
        if topology["gateway_resolution_errors"]:
            topology["warnings"].append("One or more gateway twins could not be resolved.")
        return topology

    if connectivity_type == "GATEWAY":
        iot_domain_id = twin.get("iot_domain_id")
        if not iot_domain_id:
            topology["warnings"].append("Gateway child discovery requires the twin iot_domain_id.")
            return topology
        try:
            child_page = list_digital_twin_instances_page_record(
                iot_domain_id=iot_domain_id,
                connectivity_type="INDIRECT",
                limit=gateway_children_limit,
            )
        except Exception as exc:
            topology["child_discovery_errors"].append(
                _safe_exception_payload("Unable to discover indirect child twins for gateway.", exc)
            )
            topology["warnings"].append("Indirect child discovery failed; gateway topology may be incomplete.")
            return topology
        topology["indirect_children"] = [
            child for child in child_page["items"] if twin["id"] in (child.get("gateways") or [])
        ]
        topology["child_discovery_truncated"] = bool(child_page.get("opc_next_page"))
        if topology["child_discovery_truncated"]:
            topology["warnings"].append(
                "Indirect child discovery is bounded to one SDK list call and may not include every child twin."
            )
        return topology

    return topology


def _gateway_topology_check(topology: dict) -> dict:
    connectivity_type = topology.get("connectivity_type")
    if connectivity_type == "INDIRECT" and not topology.get("gateways"):
        return _build_check(
            "gateway_topology",
            "warning",
            {
                "connectivity_type": connectivity_type,
                "message": "Indirect twin has no gateway references.",
            },
        )
    if topology.get("gateway_resolution_errors"):
        return _build_check(
            "gateway_topology",
            "warning",
            {
                "connectivity_type": connectivity_type,
                "gateway_resolution_errors": topology["gateway_resolution_errors"],
            },
        )
    if topology.get("child_discovery_errors"):
        return _build_check(
            "gateway_topology",
            "warning",
            {
                "connectivity_type": connectivity_type,
                "child_discovery_errors": topology["child_discovery_errors"],
            },
        )
    if topology.get("child_discovery_truncated"):
        return _build_check(
            "gateway_topology",
            "warning",
            {
                "connectivity_type": connectivity_type,
                "child_discovery_truncated": True,
                "indirect_child_count": len(topology.get("indirect_children") or []),
                "warnings": topology.get("warnings") or [],
            },
        )
    return _build_check(
        "gateway_topology",
        "ok",
        {
            "connectivity_type": connectivity_type,
            "gateway_count": len(topology.get("gateway_twins") or []),
            "indirect_child_count": len(topology.get("indirect_children") or []),
            "warnings": topology.get("warnings") or [],
        },
    )


def validate_twin_readiness_impl(
    *,
    digital_twin_instance_id: str | None = None,
    digital_twin_instance_name: str | None = None,
    iot_domain_id: str | None = None,
    iot_domain_display_name: str | None = None,
    domain_short_id: str | None = None,
    compartment_id: str | None = None,
):
    resolved = resolve_twin_bundle_with_token(
        digital_twin_instance_id=digital_twin_instance_id,
        digital_twin_instance_name=digital_twin_instance_name,
        iot_domain_id=iot_domain_id,
        iot_domain_display_name=iot_domain_display_name,
        domain_short_id=domain_short_id,
        compartment_id=compartment_id,
    )
    if _is_error(resolved):
        return resolved

    bundle, token = resolved
    twin = bundle["twin"]
    domain_context = bundle["domain_context"]
    base_url = build_ords_base_url(domain_context)
    credential_check = require_token_credentials(os.environ)
    if _is_error(credential_check):
        return credential_check

    snapshot_rows = list_snapshot_records(
        base_url=base_url,
        token=token.access_token,
        digital_twin_instance_id=twin["id"],
        target_count=10,
    )

    checks = [
        _build_check(
            "selector_resolution",
            "ok",
            {"twin_id": twin["id"], "twin_name": twin.get("name")},
        ),
        _build_check(
            "domain_context",
            "ok",
            {
                "region": domain_context.get("region"),
                "domain_short_id": domain_context.get("domain_short_id"),
            },
        ),
        _build_check(
            "ords_credentials",
            "ok",
            credential_check["data"],
        ),
        _build_check(
            "token_mint",
            "ok",
            {"expires_at": getattr(token, "expires_at", None)},
        ),
        _build_check(
            "snapshot_read",
            "ok" if snapshot_rows else "warning",
            {
                "count": len(snapshot_rows),
                "message": "No snapshot records found" if not snapshot_rows else None,
            },
        ),
    ]
    gateway_topology = bundle.get("gateway_topology") or resolve_gateway_topology(bundle)
    checks.append(_gateway_topology_check(gateway_topology))

    overall_status = _summarize_checks(checks)
    return {
        "overall_status": overall_status,
        "twin": twin,
        "gateway_topology": gateway_topology,
        "checks": checks,
    }


def get_twin_platform_context_impl(
    *,
    digital_twin_instance_id: str | None = None,
    digital_twin_instance_name: str | None = None,
    iot_domain_id: str | None = None,
    iot_domain_display_name: str | None = None,
    domain_short_id: str | None = None,
    compartment_id: str | None = None,
):
    bundle = resolve_twin_bundle(
        digital_twin_instance_id=digital_twin_instance_id,
        digital_twin_instance_name=digital_twin_instance_name,
        iot_domain_id=iot_domain_id,
        iot_domain_display_name=iot_domain_display_name,
        domain_short_id=domain_short_id,
        compartment_id=compartment_id,
    )
    if _is_error(bundle):
        return bundle
    bundle["gateway_topology"] = resolve_gateway_topology(bundle)
    return bundle


def get_latest_twin_state_impl(
    *,
    digital_twin_instance_id: str | None = None,
    digital_twin_instance_name: str | None = None,
    iot_domain_id: str | None = None,
    iot_domain_display_name: str | None = None,
    domain_short_id: str | None = None,
    compartment_id: str | None = None,
):
    resolved = resolve_twin_bundle_with_token(
        digital_twin_instance_id=digital_twin_instance_id,
        digital_twin_instance_name=digital_twin_instance_name,
        iot_domain_id=iot_domain_id,
        iot_domain_display_name=iot_domain_display_name,
        domain_short_id=domain_short_id,
        compartment_id=compartment_id,
    )
    if _is_error(resolved):
        return resolved

    bundle, token = resolved
    base_url = build_ords_base_url(bundle["domain_context"])
    twin_id = bundle["twin"]["id"]
    snapshot_rows = list_snapshot_records(
        base_url=base_url,
        token=token.access_token,
        digital_twin_instance_id=twin_id,
        target_count=20,
    )
    historized_rows = list_historized_records(
        base_url=base_url,
        token=token.access_token,
        digital_twin_instance_id=twin_id,
        target_count=20,
    )
    raw_command_rows = list_raw_command_records(
        base_url=base_url,
        token=token.access_token,
        digital_twin_instance_id=twin_id,
        target_count=20,
    )
    rejected_rows = list_rejected_data_records(
        base_url=base_url,
        token=token.access_token,
        digital_twin_instance_id=twin_id,
        target_count=20,
    )

    latest_snapshot = _latest_by_field(snapshot_rows, "time_created")
    latest_historized = _latest_by_field(historized_rows, "time_created")
    latest_raw_command = _latest_by_field(raw_command_rows, "time_created")
    latest_rejected = _latest_by_field(rejected_rows, "time_received")

    return {
        "twin": bundle["twin"],
        "latest_snapshot": latest_snapshot,
        "latest_historized": latest_historized,
        "latest_raw_command": latest_raw_command,
        "latest_rejected_data": latest_rejected,
        "observed_timestamps": {
            "snapshot": latest_snapshot.get("time_created") if latest_snapshot else None,
            "historized": latest_historized.get("time_created") if latest_historized else None,
            "raw_command": latest_raw_command.get("time_created") if latest_raw_command else None,
            "rejected_data": latest_rejected.get("time_received") if latest_rejected else None,
        },
    }
