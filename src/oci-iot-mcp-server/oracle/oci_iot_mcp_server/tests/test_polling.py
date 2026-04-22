from oracle.oci_iot_mcp_server.polling import (
    wait_for_raw_command_terminal_state,
    wait_for_snapshot_update,
)


def test_wait_for_raw_command_terminal_state_returns_latest_record_on_timeout():
    observed = [
        {
            "id": "rc-1",
            "delivery_status": "PENDING",
            "time_updated": "2026-03-26T12:00:01Z",
        }
    ]
    ticks = iter([0.0, 1.1, 1.1])

    result = wait_for_raw_command_terminal_state(
        fetch_detail=lambda _: observed[-1],
        record_id="rc-1",
        timeout_seconds=1,
        sleep=lambda _: None,
        monotonic=lambda: next(ticks),
    )

    assert result["timed_out"] is True
    assert result["raw_command"]["id"] == "rc-1"


def test_wait_for_raw_command_terminal_state_returns_terminal_status_without_timeout():
    sleeps = []

    result = wait_for_raw_command_terminal_state(
        fetch_detail=lambda _: {"id": "rc-1", "delivery_status": "COMPLETED"},
        record_id="rc-1",
        timeout_seconds=5,
        sleep=lambda seconds: sleeps.append(seconds),
        monotonic=iter([0.0]).__next__,
    )

    assert result == {
        "timed_out": False,
        "raw_command": {"id": "rc-1", "delivery_status": "COMPLETED"},
    }
    assert sleeps == []


def test_wait_for_raw_command_terminal_state_sleeps_while_pending():
    details = iter(
        [
            {"id": "rc-1", "delivery_status": "PENDING"},
            {"id": "rc-1", "delivery_status": "REFUSED"},
        ]
    )
    ticks = iter([0.0, 0.1, 0.2]).__next__
    sleeps = []

    result = wait_for_raw_command_terminal_state(
        fetch_detail=lambda _: next(details),
        record_id="rc-1",
        timeout_seconds=5,
        sleep=lambda seconds: sleeps.append(seconds),
        monotonic=ticks,
    )

    assert result["timed_out"] is False
    assert result["raw_command"]["delivery_status"] == "REFUSED"
    assert sleeps == [2]


def test_wait_for_snapshot_update_returns_first_record_after_since():
    rows = iter(
        [
            [
                {
                    "digital_twin_instance_id": "ocid1.digitaltwininstance.oc1..aaaa",
                    "content_path": "temperature",
                    "value": 71,
                    "time_observed": "2026-03-26T11:59:59Z",
                }
            ],
            [
                {
                    "digital_twin_instance_id": "ocid1.digitaltwininstance.oc1..aaaa",
                    "content_path": "temperature",
                    "value": 72,
                    "time_observed": "2026-03-26T12:00:05Z",
                }
            ],
        ]
    )
    ticks = iter([0.0, 0.2, 0.4, 2.1])

    result = wait_for_snapshot_update(
        fetch_rows=lambda: next(rows),
        since="2026-03-26T12:00:00Z",
        timeout_seconds=2,
        sleep=lambda _: None,
        monotonic=lambda: next(ticks),
    )

    assert result["content_path"] == "temperature"
    assert result["value"] == 72


def test_wait_for_snapshot_update_times_out_when_no_rows_are_newer():
    rows = iter(
        [
            [
                {
                    "digital_twin_instance_id": "ocid1.digitaltwininstance.oc1..aaaa",
                    "content_path": "temperature",
                    "value": 71,
                    "time_observed": "2026-03-26T11:59:59Z",
                }
            ]
        ]
    )
    ticks = iter([0.0, 0.2, 2.1]).__next__
    sleeps = []

    result = wait_for_snapshot_update(
        fetch_rows=lambda: next(rows),
        since="2026-03-26T12:00:00Z",
        timeout_seconds=2,
        sleep=lambda seconds: sleeps.append(seconds),
        monotonic=ticks,
    )

    assert result == {"timed_out": True}
    assert sleeps == [2]


def test_wait_for_snapshot_update_skips_rows_missing_time_observed():
    rows = iter(
        [
            [
                {
                    "digital_twin_instance_id": "ocid1.digitaltwininstance.oc1..aaaa",
                    "content_path": "temperature",
                    "value": 71,
                }
            ],
            [
                {
                    "digital_twin_instance_id": "ocid1.digitaltwininstance.oc1..aaaa",
                    "content_path": "temperature",
                    "value": 72,
                    "time_observed": "2026-03-26T12:00:05Z",
                }
            ],
        ]
    )
    ticks = iter([0.0, 0.2, 0.4, 2.1])

    result = wait_for_snapshot_update(
        fetch_rows=lambda: next(rows),
        since="2026-03-26T12:00:00Z",
        timeout_seconds=2,
        sleep=lambda _: None,
        monotonic=lambda: next(ticks),
    )

    assert result["content_path"] == "temperature"
    assert result["value"] == 72
