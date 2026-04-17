"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Path builder helpers for GoldenGate REST API routes.
"""

from urllib.parse import quote


def _enc(value: str) -> str:
    """URL-encode a path segment safely."""
    return quote(value, safe="")


def list_domains() -> str:
    return "/services/v2/credentials"


def list_connections(domain: str) -> str:
    return f"/services/v2/credentials/{_enc(domain)}"


def list_checkpoint_tables(_domain_name: str, _connection_name: str) -> str:
    return "/services/v2/commands/execute"


def list_extracts() -> str:
    return "/services/v2/extracts"


def list_replicats() -> str:
    return "/services/v2/replicats"


def list_distribution_paths() -> str:
    return "/services/v2/sources"


def list_trails() -> str:
    return "/services/adminsrvr/v2/trails"


def get_extract_status(extract_name: str) -> str:
    return f"/services/v2/extracts/{_enc(extract_name)}/command"


def get_replicat_status(replicat_name: str) -> str:
    return f"/services/v2/replicats/{_enc(replicat_name)}/command"


def create_connection(domain: str, connection: str, _userid: str, _connection_password: str) -> str:
    return f"/services/v2/credentials/{_enc(domain)}/{_enc(connection)}"


def add_trandata_schema(domain: str, connection: str) -> str:
    return f"/services/v2/connections/{_enc(domain)}.{_enc(connection)}/trandata/schema"


def add_trandata_table(domain: str, connection: str) -> str:
    return f"/services/v2/connections/{_enc(domain)}.{_enc(connection)}/trandata/table"


def create_extract(extract_name: str) -> str:
    return f"/services/v2/extracts/{_enc(extract_name)}"


def update_extract(extract_name: str) -> str:
    return f"/services/v2/extracts/{_enc(extract_name)}"


def create_replicat(replicat_name: str) -> str:
    return f"/services/v2/replicats/{_enc(replicat_name)}"


def update_replicat(replicat_name: str) -> str:
    return f"/services/v2/replicats/{_enc(replicat_name)}"


def create_distribution_path(
    distribution_path_name: str,
    _source_uri: str,
    _source_trail_name: str,
    _target_uri: str,
    _target_port: int,
    _target_authentication_method: str | None = None,
    _target_domain: str | None = None,
    _target_alias: str | None = None,
) -> str:
    return f"/services/v2/sources/{_enc(distribution_path_name)}"


def create_data_stream(
    data_stream_name: str,
    _trail_name: str,
    _quality_of_service: str | None = None,
    _cloud_events_format: bool | None = None,
    _buffer_size: int | None = None,
) -> str:
    return f"/services/distsrvr/v2/stream/{_enc(data_stream_name)}"


def start(_process_name: str) -> str:
    return "/services/v2/commands/execute"


def stop(_process_name: str) -> str:
    return "/services/v2/commands/execute"


def start_distribution_path(process_name: str) -> str:
    return f"/services/distsrvr/v2/sources/{_enc(process_name)}"


def stop_distribution_path(process_name: str) -> str:
    return f"/services/distsrvr/v2/sources/{_enc(process_name)}"


def get_extract_lag(extract_name: str) -> str:
    return f"/services/v2/extracts/{_enc(extract_name)}/command"


def get_replicat_lag(replicat_name: str) -> str:
    return f"/services/v2/replicats/{_enc(replicat_name)}/command"


def get_extract_report(extract_name: str) -> str:
    return f"/services/v2/extracts/{_enc(extract_name)}/info/reports/{_enc(extract_name)}.rpt"


def get_replicat_report(replicat_name: str) -> str:
    return f"/services/v2/replicats/{_enc(replicat_name)}/info/reports/{_enc(replicat_name)}.rpt"


def get_data_stream_info(data_stream_name: str) -> str:
    return f"/services/distsrvr/v2/stream/{_enc(data_stream_name)}/info"


def get_data_stream_yaml(data_stream_name: str) -> str:
    return f"/services/distsrvr/v2/stream/{_enc(data_stream_name)}/yaml"


def get_extract_stats(extract_name: str) -> str:
    return f"/services/v2/extracts/{_enc(extract_name)}/command"


def get_replicat_stats(replicat_name: str) -> str:
    return f"/services/v2/replicats/{_enc(replicat_name)}/command"


def get_extract_details(extract_name: str) -> str:
    return f"/services/v2/extracts/{_enc(extract_name)}"


def get_replicat_details(replicat_name: str) -> str:
    return f"/services/v2/replicats/{_enc(replicat_name)}"
