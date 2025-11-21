"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime
from typing import Literal, Optional, Union

import oci
from pydantic import BaseModel, Field

# Nested OCI models represented as Pydantic classes


def _oci_to_dict(obj):
    """Best-effort conversion of OCI SDK model objects to plain dicts."""
    if obj is None:
        return None
    try:
        from oci.util import to_dict as oci_to_dict

        return oci_to_dict(obj)
    except Exception:
        pass
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    return None


# region InstanceAgentCommandExecutionOutputContent


class InstanceAgentCommandExecutionOutputViaTextDetails(BaseModel):
    """The execution output from a command when returned in plain text."""

    output_type: Literal["TEXT"] = Field(
        "TEXT", description="The output destination type for the command."
    )
    exit_code: int = Field(
        ...,
        description="The exit code for the command. Exit code `0` indicates success.",
    )
    message: Optional[str] = Field(
        None,
        description="An optional status message that Oracle Cloud Agent "
        "can populate for additional troubleshooting.",
    )
    text: Optional[str] = Field(None, description="The command output.")
    text_sha256: Optional[str] = Field(
        None, description="SHA-256 checksum value of the text content."
    )


class InstanceAgentCommandExecutionOutputViaObjectStorageUriDetails(BaseModel):
    """The execution output from a command when saved to an Object Storage URL."""

    output_type: Literal["OBJECT_STORAGE_URI"] = Field(
        "OBJECT_STORAGE_URI", description="The output destination type for the command."
    )
    exit_code: int = Field(
        ...,
        description="The exit code for the command. Exit code `0` indicates success.",
    )
    message: Optional[str] = Field(
        None,
        description="An optional status message that Oracle Cloud Agent "
        "can populate for additional troubleshooting.",
    )
    output_uri: str = Field(
        ...,
        description="The Object Storage URL or pre-authenticated request (PAR) for the command output.",
    )


class InstanceAgentCommandExecutionOutputViaObjectStorageTupleDetails(BaseModel):
    """The execution output from a command when saved to an Object Storage bucket."""

    output_type: Literal["OBJECT_STORAGE_TUPLE"] = Field(
        "OBJECT_STORAGE_TUPLE",
        description="The output destination type for the command.",
    )
    exit_code: int = Field(
        ...,
        description="The exit code for the command. Exit code `0` indicates success.",
    )
    message: Optional[str] = Field(
        None,
        description="An optional status message that Oracle Cloud Agent "
        "can populate for additional troubleshooting.",
    )
    bucket_name: str = Field(
        ..., description="The Object Storage bucket for the command output."
    )
    namespace_name: str = Field(
        ..., description="The Object Storage namespace for the command output."
    )
    object_name: str = Field(
        ..., description="The Object Storage object name for the command output."
    )


OutputContent = Union[
    InstanceAgentCommandExecutionOutputViaTextDetails,
    InstanceAgentCommandExecutionOutputViaObjectStorageUriDetails,
    InstanceAgentCommandExecutionOutputViaObjectStorageTupleDetails,
]


# Based on oci.compute_instance_agent.models.InstanceAgentCommandExecution
class InstanceAgentCommandExecution(BaseModel):
    """
    Pydantic model mirroring the fields of oci.compute_instance_agent.models.InstanceAgentCommandExecution.
    Nested OCI model types are represented as Pydantic classes (above).
    """

    instance_agent_command_id: str = Field(..., description="The OCID of the command.")
    instance_id: str = Field(..., description="The OCID of the instance.")
    delivery_state: Literal[
        "VISIBLE", "PENDING", "ACKED", "ACKED_CANCELED", "EXPIRED"
    ] = Field(
        ...,
        description=(
            "Specifies the command delivery state. "
            "* `VISIBLE` - The command is visible to instance. "
            "* `PENDING` - The command is pending ack from the instance. "
            "* `ACKED` - The command has been received and acked by the instance. "
            "* `ACKED_CANCELED` - The canceled command has been received and "
            "acked by the instance. "
            "* `EXPIRED` - The instance has not requested for commands and "
            "its delivery has expired."
        ),
    )
    lifecycle_state: Literal[
        "ACCEPTED", "IN_PROGRESS", "SUCCEEDED", "FAILED", "TIMED_OUT", "CANCELED"
    ] = Field(
        ...,
        description=(
            "Command execution life cycle state. "
            "* `ACCEPTED` - The command execution has been accepted to run. "
            "* `IN_PROGRESS` - The command execution is in progress. "
            "* `SUCCEEDED` - The command execution is successful. "
            "* `FAILED` - The command execution has failed. "
            "* `TIMED_OUT` - The command execution has timedout. "
            "* `CANCELED` - The command execution has canceled."
        ),
    )
    time_created: datetime = Field(..., description="The command creation date.")
    time_updated: datetime = Field(..., description="The command last updated at date.")
    sequence_number: int = Field(
        ...,
        description="The large non-consecutive number that Run Command Service "
        "assigns to each created command.",
    )
    display_name: Optional[str] = Field(
        None, description="The user friendly display name of the command."
    )
    content: OutputContent = Field(..., description="The command output details.")


def map_text_output(
    content,
) -> InstanceAgentCommandExecutionOutputViaTextDetails | None:
    if not content:
        return None
    data = _oci_to_dict(content) or {}
    return InstanceAgentCommandExecutionOutputViaTextDetails(
        exit_code=data.get("exit_code", getattr(content, "exit_code", None)),
        message=data.get("message", getattr(content, "message", None)),
        text=data.get("text", getattr(content, "text", None)),
        text_sha256=data.get("text_sha256", getattr(content, "text_sha256", None)),
    )


def map_uri_output(
    content,
) -> InstanceAgentCommandExecutionOutputViaObjectStorageUriDetails | None:
    if not content:
        return None
    data = _oci_to_dict(content) or {}
    return InstanceAgentCommandExecutionOutputViaObjectStorageUriDetails(
        exit_code=data.get("exit_code", getattr(content, "exit_code", None)),
        message=data.get("message", getattr(content, "message", None)),
        output_uri=data.get("output_uri", getattr(content, "output_uri", None)),
    )


def map_tuple_output(
    content,
) -> InstanceAgentCommandExecutionOutputViaObjectStorageTupleDetails | None:
    if not content:
        return None
    data = _oci_to_dict(content) or {}
    return InstanceAgentCommandExecutionOutputViaObjectStorageTupleDetails(
        exit_code=data.get("exit_code", getattr(content, "exit_code", None)),
        message=data.get("message", getattr(content, "message", None)),
        bucket_name=data.get("bucket_name", getattr(content, "bucket_name", None)),
        namespace_name=data.get(
            "namespace_name", getattr(content, "namespace_name", None)
        ),
        object_name=data.get("object_name", getattr(content, "object_name", None)),
    )


def map_output_content(
    content: oci.compute_instance_agent.models.InstanceAgentCommandExecutionOutputContent,
) -> OutputContent | None:
    if not content:
        return None
    output_type = getattr(content, "output_type", None)
    if output_type == "TEXT":
        return map_text_output(content)
    elif output_type == "OBJECT_STORAGE_URI":
        return map_uri_output(content)
    elif output_type == "OBJECT_STORAGE_TUPLE":
        return map_tuple_output(content)
    return None


def map_instance_agent_command_execution(
    command_execution: oci.compute_instance_agent.models.InstanceAgentCommandExecution,
) -> InstanceAgentCommandExecution:
    """
    Convert an oci.compute_instance_agent.models.InstanceAgentCommandExecution to
    oracle.oci_compute_instance_agent_mcp_server.models.InstanceAgentCommandExecution,
    including all nested types.
    """
    return InstanceAgentCommandExecution(
        instance_agent_command_id=getattr(
            command_execution, "instance_agent_command_id", None
        ),
        instance_id=getattr(command_execution, "instance_id", None),
        delivery_state=getattr(command_execution, "delivery_state", None),
        lifecycle_state=getattr(command_execution, "lifecycle_state", None),
        time_created=getattr(command_execution, "time_created", None),
        time_updated=getattr(command_execution, "time_updated", None),
        sequence_number=getattr(command_execution, "sequence_number", None),
        display_name=getattr(command_execution, "display_name", None),
        content=map_output_content(getattr(command_execution, "content", None)),
    )


# endregion

# region InstanceAgentCommandSummary


class InstanceAgentCommandSummary(BaseModel):
    """
    Pydantic model mirroring the fields of oci.compute_instance_agent.models.InstanceAgentCommandSummary.
    """

    instance_agent_command_id: str = Field(..., description="The OCID of the command.")
    display_name: Optional[str] = Field(
        None, description="A user-friendly name. Does not have to be unique."
    )
    compartment_id: str = Field(
        ..., description="The OCID of the compartment containing the command."
    )
    time_created: datetime = Field(
        ..., description="The date and time the command was created (RFC3339)."
    )
    time_updated: datetime = Field(
        ..., description="The date and time the command was last updated (RFC3339)."
    )
    is_canceled: Optional[bool] = Field(
        None,
        description="Whether a request was made to cancel the command. "
        "Canceling a command is a best-effort attempt.",
    )


def map_instance_agent_command_summary(
    command_summary: oci.compute_instance_agent.models.InstanceAgentCommandSummary,
) -> InstanceAgentCommandSummary:
    """
    Convert an oci.compute_instance_agent.models.InstanceAgentCommandSummary to
    oracle.oci_compute_instance_agent_mcp_server.models.InstanceAgentCommandSummary.
    """
    return InstanceAgentCommandSummary(
        instance_agent_command_id=getattr(
            command_summary, "instance_agent_command_id", None
        ),
        display_name=getattr(command_summary, "display_name", None),
        compartment_id=getattr(command_summary, "compartment_id", None),
        time_created=getattr(command_summary, "time_created", None),
        time_updated=getattr(command_summary, "time_updated", None),
        is_canceled=getattr(command_summary, "is_canceled", None),
    )


# endregion

# region InstanceAgentCommandExecutionSummary


class InstanceAgentCommandExecutionSummary(BaseModel):
    """
    Pydantic model mirroring the fields of
    oci.compute_instance_agent.models.InstanceAgentCommandExecutionSummary.
    Nested OCI model types are represented as Pydantic classes (above).
    """

    instance_agent_command_id: str = Field(..., description="The OCID of the command.")
    instance_id: str = Field(..., description="The OCID of the instance.")
    delivery_state: Literal[
        "VISIBLE", "PENDING", "ACKED", "ACKED_CANCELED", "EXPIRED"
    ] = Field(
        ...,
        description="The command delivery state. "
        "* `VISIBLE` - The command is visible to the instance. "
        "* `PENDING` - The command is pending acknowledgment from the instance. "
        "* `ACKED` - The command has been received and acknowledged by the instance. "
        "* `ACKED_CANCELED` - The canceled command has been received and acknowledged by the instance. "
        "* `EXPIRED` - The instance has not requested for commands and the command's delivery has expired.",
    )
    lifecycle_state: Literal[
        "ACCEPTED", "IN_PROGRESS", "SUCCEEDED", "FAILED", "TIMED_OUT", "CANCELED"
    ] = Field(
        ...,
        description="The command execution lifecycle state. "
        "* `ACCEPTED` - The command has been accepted to run. "
        "* `IN_PROGRESS` - The command is in progress. "
        "* `SUCCEEDED` - The command was successfully executed. "
        "* `FAILED` - The command failed to execute. "
        "* `TIMED_OUT` - The command execution timed out. "
        "* `CANCELED` - The command execution was canceled.",
    )
    time_created: datetime = Field(
        ..., description="The date and time the command was created (RFC3339)."
    )
    time_updated: datetime = Field(
        ..., description="The date and time the command was last updated (RFC3339)."
    )
    sequence_number: int = Field(
        ...,
        description="A large, non-consecutive number that Oracle Cloud Agent "
        "assigns to each created command.",
    )
    display_name: Optional[str] = Field(
        None, description="A user-friendly name. Does not have to be unique."
    )
    content: Optional[OutputContent] = Field(
        None, description="The execution output from a command."
    )


def map_instance_agent_command_execution_summary(
    command_execution_summary: oci.compute_instance_agent.models.InstanceAgentCommandExecutionSummary,
) -> InstanceAgentCommandExecutionSummary:
    """
    Convert an oci.compute_instance_agent.models.InstanceAgentCommandExecutionSummary to
    oracle.oci_compute_instance_agent_mcp_server.models.InstanceAgentCommandExecutionSummary,
    including all nested types.
    """
    return InstanceAgentCommandExecutionSummary(
        instance_agent_command_id=getattr(
            command_execution_summary, "instance_agent_command_id", None
        ),
        instance_id=getattr(command_execution_summary, "instance_id", None),
        delivery_state=getattr(command_execution_summary, "delivery_state", None),
        lifecycle_state=getattr(command_execution_summary, "lifecycle_state", None),
        time_created=getattr(command_execution_summary, "time_created", None),
        time_updated=getattr(command_execution_summary, "time_updated", None),
        sequence_number=getattr(command_execution_summary, "sequence_number", None),
        display_name=getattr(command_execution_summary, "display_name", None),
        content=map_output_content(getattr(command_execution_summary, "content", None)),
    )


# endregion
