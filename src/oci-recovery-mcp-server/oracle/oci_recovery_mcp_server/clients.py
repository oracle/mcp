"""
Copyright (c) 2025, 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

OCI SDK client factories.

One place that knows how a client is built: resolve the caller's credentials
for the target region, construct the SDK client, and wrap it so every call it
makes is logged and carries this server's request id.
"""

import uuid
from typing import Any, Callable, Optional

import oci

from . import auth, telemetry
from .logging_setup import logger


def _make_client(
    ctor: Callable[..., Any],
    region: str | None = None,
    *,
    client_name: str,
    request_id: Optional[str] = None,
):
    """Construct and wrap an OCI SDK client for the current call's credentials."""
    config, signer = auth._config_and_signer(region)
    client = ctor(config, signer=signer)
    rid = request_id or uuid.uuid4().hex
    return telemetry._wrap_oci_client(client, request_id=rid, client_name=client_name)


def get_recovery_client(
    region: str | None = None,
    *,
    request_id: Optional[str] = None,
) -> oci.recovery.DatabaseRecoveryClient:
    """Create a Recovery Service client using auth selected via env vars."""
    return _make_client(
        oci.recovery.DatabaseRecoveryClient,
        region,
        client_name="recovery",
        request_id=request_id,
    )


def get_identity_client(*, request_id: Optional[str] = None):
    """
    Create an OCI Identity client using auth selected via env vars.

    Always built for the home region: IAM compartments and region subscriptions
    are tenancy-wide, so there is no region to pass.
    """
    return _make_client(
        oci.identity.IdentityClient,
        None,
        client_name="identity",
        request_id=request_id,
    )


def get_database_client(region: str | None = None, *, request_id: Optional[str] = None):
    """Create an OCI Database client using auth selected via env vars."""
    return _make_client(
        oci.database.DatabaseClient,
        region,
        client_name="database",
        request_id=request_id,
    )


def get_work_request_client(region: str | None = None, *, request_id: Optional[str] = None):
    """Create an OCI Work Requests client using auth selected via env vars."""
    return _make_client(
        oci.work_requests.WorkRequestClient,
        region,
        client_name="work_requests",
        request_id=request_id,
    )


def get_monitoring_client(region: str | None = None, *, request_id: Optional[str] = None):
    """Create an OCI Monitoring client using auth selected via env vars."""
    logger.info("entering get_monitoring_client")
    return _make_client(
        oci.monitoring.MonitoringClient,
        region,
        client_name="monitoring",
        request_id=request_id,
    )


def get_limits_client(region: str | None = None, *, request_id: Optional[str] = None):
    """Create an OCI Limits client using auth selected via env vars."""
    return _make_client(
        oci.limits.LimitsClient,
        region,
        client_name="limits",
        request_id=request_id,
    )


def get_onesubscription_client(region: str | None = None, *, request_id: Optional[str] = None):
    """
    Create a OneSubscription SubscribedService client.

    We use this to discover which regions a tenancy is subscribed to for a given service,
    so we can execute compartment-scoped queries across all relevant regions.
    """
    return _make_client(
        oci.onesubscription.SubscribedServiceClient,
        region,
        client_name="onesubscription",
        request_id=request_id,
    )
