from datetime import datetime

RAW_COMMAND_TERMINAL_SUCCESS = {"COMPLETED"}
RAW_COMMAND_TERMINAL_FAILURE = {
    "REFUSED",
    "EXPIRED",
    "NOT_RESPONDED",
    "REJECTED",
    "BAD_RESPONSE",
}


def _parse_rfc3339(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def wait_for_raw_command_terminal_state(
    *,
    fetch_detail,
    record_id: str,
    timeout_seconds: int,
    sleep,
    monotonic,
) -> dict:
    deadline = monotonic() + timeout_seconds
    latest = None
    while True:
        latest = fetch_detail(record_id)
        status = latest["delivery_status"]
        if status in RAW_COMMAND_TERMINAL_SUCCESS | RAW_COMMAND_TERMINAL_FAILURE:
            return {"timed_out": False, "raw_command": latest}
        if monotonic() >= deadline:
            break
        sleep(2)

    return {"timed_out": True, "raw_command": latest}


def wait_for_snapshot_update(
    *,
    fetch_rows,
    since: str,
    timeout_seconds: int,
    sleep,
    monotonic,
) -> dict:
    deadline = monotonic() + timeout_seconds
    observed_after = _parse_rfc3339(since)
    while monotonic() < deadline:
        rows = fetch_rows()
        for row in rows:
            observed_at = row.get("time_observed")
            if not observed_at:
                continue
            try:
                observed_time = _parse_rfc3339(observed_at)
            except (TypeError, ValueError):
                continue
            if observed_time > observed_after:
                return row
        sleep(2)

    return {"timed_out": True}
