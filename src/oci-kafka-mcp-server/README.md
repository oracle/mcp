# OCI Kafka MCP Server

## Overview

This server provides tools for AI agents to manage **OCI Streaming with Apache Kafka** clusters. It covers both the **Kafka data plane** (topics, consumers, observability, diagnostics) and the **OCI control plane** (cluster lifecycle, configuration management, work requests).

The server supports secure Kafka connectivity via SASL/SCRAM-512, SASL/PLAIN, and mTLS, and uses the OCI Python SDK for control plane operations authenticated via `~/.oci/config`.

## Running the server

### STDIO transport mode

```sh
uvx oracle.oci-kafka-mcp-server
```

### With write tools enabled (required for create/update/delete operations)

```sh
uvx oracle.oci-kafka-mcp-server --allow-writes
```

### HTTP streaming transport mode

```sh
ORACLE_MCP_HOST=<hostname/IP> ORACLE_MCP_PORT=<port> uvx oracle.oci-kafka-mcp-server
```

## Configuration

Configure the server via environment variables:

| Variable | Description | Default |
| --- | --- | --- |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka broker addresses | `localhost:9092` |
| `KAFKA_SECURITY_PROTOCOL` | `PLAINTEXT`, `SASL_SSL`, `SSL` | `PLAINTEXT` |
| `KAFKA_SASL_MECHANISM` | `SCRAM-SHA-512`, `SCRAM-SHA-256`, `PLAIN` | — |
| `KAFKA_SASL_USERNAME` | SASL username | — |
| `KAFKA_SASL_PASSWORD` | SASL password | — |
| `KAFKA_SSL_CA_LOCATION` | CA certificate path | — |
| `OCI_CONFIG_FILE` | OCI config file path | `~/.oci/config` |
| `OCI_PROFILE` | OCI config profile | `DEFAULT` |
| `OCI_COMPARTMENT_ID` | Default OCI compartment OCID | — |
| `OCI_CLUSTER_ID` | Default OCI Kafka cluster (stream pool) OCID | — |
| `ALLOW_WRITES` | Enable write tools at startup | `false` |

## Tools

### Connection

| Tool Name | Description |
| --- | --- |
| `oci_kafka_configure_connection` | Configure Kafka broker connection (bootstrap servers, SASL/TLS credentials) |
| `oci_kafka_get_connection_info` | Get current connection configuration and circuit breaker status |

### Topics

| Tool Name | Description |
| --- | --- |
| `oci_kafka_list_topics` | List all Kafka topics with partition and replication details |
| `oci_kafka_get_topic_details` | Get detailed configuration for a specific topic |
| `oci_kafka_get_cluster_config` | Get cluster-level Kafka broker configuration |
| `oci_kafka_create_topic` | Create a new Kafka topic with configurable partitions and replication |
| `oci_kafka_delete_topic` | Delete a Kafka topic permanently |
| `oci_kafka_update_topic_config` | Update topic-level configuration settings |

### Consumers

| Tool Name | Description |
| --- | --- |
| `oci_kafka_list_consumer_groups` | List all consumer groups and their status |
| `oci_kafka_get_consumer_group_details` | Get detailed offset and lag information for a consumer group |
| `oci_kafka_reset_consumer_offset` | Reset consumer group offsets to earliest, latest, or a specific offset |
| `oci_kafka_delete_consumer_group` | Delete an inactive consumer group |

### Observability

| Tool Name | Description |
| --- | --- |
| `oci_kafka_get_cluster_health` | Get overall Kafka cluster health metrics |
| `oci_kafka_get_broker_metrics` | Get per-broker performance metrics |
| `oci_kafka_get_topic_metrics` | Get topic-level throughput and lag metrics |
| `oci_kafka_get_consumer_lag` | Get consumer lag summary across all groups and topics |

### Diagnostics (AI-powered)

| Tool Name | Description |
| --- | --- |
| `oci_kafka_run_diagnostics` | Run comprehensive cluster diagnostics |
| `oci_kafka_check_connectivity` | Verify broker connectivity and authentication |
| `oci_kafka_recommend_scaling` | Get AI-generated scaling recommendations based on current metrics |
| `oci_kafka_analyze_lag_root_cause` | Analyze consumer lag and identify root causes with remediation steps |

### OCI Cluster Metadata

| Tool Name | Description |
| --- | --- |
| `oci_kafka_list_oci_clusters` | List OCI Streaming with Apache Kafka clusters in a compartment |
| `oci_kafka_get_oci_cluster_info` | Get OCI control plane metadata for a Kafka cluster |

### OCI Cluster Lifecycle (requires `--allow-writes`)

| Tool Name | Description |
| --- | --- |
| `oci_kafka_create_cluster` | Create a new OCI Kafka cluster (HIGH RISK — incurs costs) |
| `oci_kafka_update_cluster` | Update cluster display name, tags, or applied configuration |
| `oci_kafka_scale_cluster` | Scale cluster to a different broker count (HIGH RISK) |
| `oci_kafka_delete_cluster` | Delete a cluster permanently — all data lost (HIGH RISK) |
| `oci_kafka_change_cluster_compartment` | Move cluster to a different OCI compartment (HIGH RISK) |
| `oci_kafka_enable_superuser` | Enable the Kafka superuser for administrative tasks |
| `oci_kafka_disable_superuser` | Disable the Kafka superuser to restore least-privilege access |

### OCI Cluster Configuration (requires `--allow-writes` for writes)

| Tool Name | Description |
| --- | --- |
| `oci_kafka_create_cluster_config` | Create a new named, versioned cluster configuration |
| `oci_kafka_get_oci_cluster_config` | Get details of a cluster configuration |
| `oci_kafka_list_cluster_configs` | List cluster configurations in a compartment |
| `oci_kafka_update_cluster_config` | Update a cluster configuration's name or tags |
| `oci_kafka_delete_cluster_config` | Delete a cluster configuration (HIGH RISK) |
| `oci_kafka_change_cluster_config_compartment` | Move a cluster configuration to a different compartment |
| `oci_kafka_get_cluster_config_version` | Get a specific version of a cluster configuration |
| `oci_kafka_list_cluster_config_versions` | List all versions of a cluster configuration |
| `oci_kafka_delete_cluster_config_version` | Delete a specific configuration version |

### OCI Work Requests

| Tool Name | Description |
| --- | --- |
| `oci_kafka_get_work_request` | Poll the status of an asynchronous OCI operation |
| `oci_kafka_list_work_requests` | List work requests for a compartment or resource |
| `oci_kafka_cancel_work_request` | Cancel an in-progress work request |
| `oci_kafka_get_work_request_errors` | Get error details from a failed work request |
| `oci_kafka_get_work_request_logs` | Get log entries from a work request |
| `oci_kafka_list_node_shapes` | List available broker node shapes for cluster provisioning |

## Security

The server enforces a three-tier risk model:

- **LOW** — Read-only tools; always permitted
- **MEDIUM** — Write tools; require `--allow-writes` flag
- **HIGH** — Destructive operations; require `--allow-writes` plus explicit confirmation from the user

All tool executions are recorded as structured JSON audit log entries.

⚠️ **NOTE**: All actions are performed with the permissions of the configured OCI CLI profile and Kafka credentials. We advise least-privilege IAM setup, secure credential management, and never exposing SASL passwords or OCI private keys in plaintext.

## Third-Party APIs

Developers choosing to distribute a binary implementation of this project are responsible for obtaining and providing all required licenses and copyright notices for the third-party code used in order to ensure compliance with their respective open source licenses.

## Disclaimer

Users are responsible for their local environment and credential safety. Different language model selections may yield different results and performance.

## License

Copyright (c) 2025 Oracle and/or its affiliates.

Released under the Universal Permissive License v1.0 as shown at
<https://oss.oracle.com/licenses/upl/>.
