from .tool_models import ToolErrorPayload


def error_result(
    *,
    code: str,
    message: str,
    resource_type: str | None = None,
    retry_hint: str | None = None,
    details: dict | None = None,
) -> dict:
    return {
        "ok": False,
        "error": ToolErrorPayload(
            code=code,
            message=message,
            resource_type=resource_type,
            retry_hint=retry_hint,
            details=details or {},
        ).model_dump(exclude_none=True),
    }


def ambiguity_error(
    *,
    resource_type: str,
    message: str,
    input_payload: dict,
    candidates: list[dict],
) -> dict:
    return error_result(
        code="ambiguous_identifier",
        message=message,
        resource_type=resource_type,
        retry_hint="Retry with the OCID of the intended resource.",
        details={"input": input_payload, "candidates": candidates},
    )


def invalid_input_error(
    *,
    resource_type: str,
    message: str,
    input_payload: dict,
    retry_hint: str | None = None,
) -> dict:
    return error_result(
        code="invalid_input",
        message=message,
        resource_type=resource_type,
        retry_hint=retry_hint,
        details={"input": input_payload},
    )


def not_found_error(
    *,
    resource_type: str,
    message: str,
    input_payload: dict,
    retry_hint: str | None = None,
) -> dict:
    return error_result(
        code="resource_not_found",
        message=message,
        resource_type=resource_type,
        retry_hint=retry_hint,
        details={"input": input_payload},
    )
