"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Backend-derived prerequisites for starting GoldenGate processes.
"""

import posixpath
import re
from datetime import datetime
from typing import Any

from . import api
from .consts import PROCESS_NAME_PATTERN
from .http_client import GoldenGateHTTPError, HttpClient

MAX_START_CHECK_EXTRACTS = 128


def _payload(value: Any) -> dict:
    if not isinstance(value, dict):
        raise ValueError("Unrecognized GoldenGate response; process start was refused.")
    result = value.get("response", value)
    if not isinstance(result, dict):
        raise ValueError("Unrecognized GoldenGate response; process start was refused.")
    return result


def _config_text(details: dict) -> str:
    lines = details.get("config")
    if not isinstance(lines, list) or not all(isinstance(line, str) for line in lines):
        raise ValueError("Process configuration is unavailable; process start was refused.")
    return "\n".join(lines)


def _file_reference(value: str) -> str:
    # Compare complete paths rather than basenames; do not guess a deployment's
    # default directory or equate files on different paths.
    return posixpath.normpath(value.replace("\\", "/"))


def _parameter_files(config: str, parameter: str) -> set[str]:
    matches = re.finditer(
        rf"^\s*{parameter}\s+(?:\"([^\"]+)\"|'([^']+)'|([^,\s]+))\s*(?:,|$)",
        config,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    return {_file_reference(next(group for group in match.groups() if group)) for match in matches}


def _replicat_file(details: dict) -> str:
    source = details.get("source")
    if not isinstance(source, dict):
        raise ValueError("Replicat file or trail source is ambiguous; process start was refused.")
    name = source.get("filename") or source.get("name")
    path = source.get("path", "")
    if not isinstance(name, str) or not name.strip() or not isinstance(path, str):
        raise ValueError("Replicat file or trail source is ambiguous; process start was refused.")
    return _file_reference(posixpath.join(path, name))


def ensure_generic_start_allowed(client: HttpClient, process_name: str) -> None:
    """Allow Extracts and Replicats with a verifiable local CDC producer only."""
    try:
        extract = _payload(client.get(api.get_extract_details(process_name)))
    except GoldenGateHTTPError as exc:
        if exc.status_code != 404:
            raise
    else:
        if not extract.get("source"):
            raise ValueError("Extract source is ambiguous; process start was refused.")
        return

    replicat = _payload(client.get(api.get_replicat_details(process_name)))
    config = _config_text(replicat)
    if replicat.get("source") == "tables" or re.search(r"^\s*SPECIALRUN\b", config, re.IGNORECASE | re.MULTILINE):
        raise ValueError("Use start_initial_load_replicat for an Initial Load Replicat.")
    source_file = _replicat_file(replicat)
    collection = client.get(api.list_extracts())
    extracts = _payload(collection)
    items = extracts.get("items")
    links = []
    for envelope in (collection, extracts):
        page_links = envelope.get("links", [])
        if not isinstance(page_links, list) or not all(isinstance(link, dict) for link in page_links):
            raise ValueError("Extract collection links are ambiguous; process start was refused.")
        links.extend(page_links)
    if (
        not isinstance(items, list)
        or len(items) > MAX_START_CHECK_EXTRACTS
        or any(link.get("rel") == "next" for link in links)
    ):
        raise ValueError("Cannot inspect a complete, bounded Extract collection; process start was refused.")
    cdc_producer_found = False
    for item in items:
        name = item.get("name") if isinstance(item, dict) else None
        if not isinstance(name, str) or not re.fullmatch(PROCESS_NAME_PATTERN, name):
            raise ValueError("Extract identity is ambiguous; process start was refused.")
        producer = _payload(client.get(api.get_extract_details(name)))
        producer_config = _config_text(producer)
        if source_file in _parameter_files(producer_config, "EXTFILE"):
            raise ValueError("Use start_initial_load_replicat for a Replicat consuming an Initial Load EXTFILE.")
        producer_source = producer.get("source")
        is_cdc = producer_source == "tranlogs" or (
            isinstance(producer_source, dict) and bool(producer_source.get("tranlogs"))
        )
        if source_file in _parameter_files(producer_config, "EXTTRAIL") and is_cdc:
            cdc_producer_found = True
    if not cdc_producer_found:
        raise ValueError("No matching local CDC Extract could be verified; process start was refused.")


def _timestamp(value: Any) -> datetime:
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("Extract execution timestamps are missing or invalid; Replicat start was refused.") from exc
    if timestamp.tzinfo is None:
        raise ValueError("Extract execution timestamps require a timezone; Replicat start was refused.")
    return timestamp


def validate_initial_load_start(client: HttpClient, replicat_name: str, extract_name: str) -> dict:
    """Verify file association, latest successful execution and its report."""
    status = _payload(client.get(api.get_extract_status(extract_name)))
    if str(status.get("status", "unrecognized")).upper() != "STOPPED":
        raise ValueError("Initial Load Extract is not confirmed STOPPED; Replicat start was refused.")
    extract = _payload(client.get(api.get_extract_details(extract_name)))
    if extract.get("source") != "tables":
        raise ValueError("The selected Extract is not an Initial Load Extract; Replicat start was refused.")
    files = _parameter_files(_config_text(extract), "EXTFILE")
    replicat = _payload(client.get(api.get_replicat_details(replicat_name)))
    source_file = _replicat_file(replicat)
    if files != {source_file}:
        raise ValueError("Extract EXTFILE does not match the Replicat source; Replicat start was refused.")

    process_id = status.get("processId")
    if type(process_id) is not int or process_id < 1:
        raise ValueError("Extract execution identity is unavailable; Replicat start was refused.")
    last_started = _timestamp(status.get("lastStarted"))
    history = _payload(client.get(api.get_extract_history(extract_name))).get("history")
    if not isinstance(history, list):
        raise ValueError("Extract execution history is unavailable; Replicat start was refused.")
    runs = [run for run in history if isinstance(run, dict) and run.get("processId") == process_id]
    if not runs:
        raise ValueError("No matching Extract execution history; Replicat start was refused.")
    run = max(runs, key=lambda entry: _timestamp(entry.get("started")))
    if (
        str(run.get("status", "")).upper() != "STOPPED"
        or type(run.get("exitCode")) is not int
        or run["exitCode"] != 0
        or run.get("killedManually", False) is not False
        or not _timestamp(run.get("started")) <= last_started <= _timestamp(run.get("finished"))
    ):
        raise ValueError("Latest Extract execution is not confirmed successful; Replicat start was refused.")

    report = client.get(api.get_extract_report(extract_name))
    if isinstance(report, dict):
        lines = _payload(report).get("lines")
        report_text = "\n".join(lines) if isinstance(lines, list) and all(isinstance(line, str) for line in lines) else ""
    else:
        report_text = report if isinstance(report, str) else ""
    if not report_text.strip():
        raise ValueError("Initial Load Extract returned an empty report; Replicat start was refused.")
    if re.search(r"\b(ABENDED|ABENDING|TERMINATED\s+ABNORMALLY|FATAL|FAILED\s+TO)\b", report_text, re.IGNORECASE):
        raise ValueError("Extract report contains a failure indicator; Replicat start was refused.")
    if re.search(r"OGG-00990|Command received[^\r\n]*:\s*(?:STOP|KILL)\b", report_text, re.IGNORECASE):
        raise ValueError("Extract report indicates an operator stop; Replicat start was refused.")
    report_ids = set(re.findall(r"\bProcess\s+id\s*:\s*(\d+)\b", report_text, re.IGNORECASE))
    if report_ids != {str(process_id)}:
        raise ValueError("Extract report does not identify the latest execution; Replicat start was refused.")

    # Recheck the run after collecting prerequisites. A restart during inspection
    # invalidates the evidence; no automatic mutation retry is attempted.
    current = _payload(client.get(api.get_extract_status(extract_name)))
    if any(current.get(key) != status.get(key) for key in ("status", "lastStarted", "processId")):
        raise ValueError("Extract execution changed during inspection; Replicat start was refused.")
    return {
        "initialLoadExtractName": extract_name,
        "extractStatus": "STOPPED",
        "sourceFile": source_file,
        "processId": process_id,
        "lastStarted": status["lastStarted"],
        "exitCode": 0,
        "extractReportChecked": True,
        "strongFailureIndicatorFound": False,
    }
