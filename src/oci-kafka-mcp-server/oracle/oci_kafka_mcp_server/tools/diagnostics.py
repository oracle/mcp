"""AI diagnostic tools for OCI Kafka MCP Server.

These tools orchestrate multiple Kafka admin operations to produce
structured diagnostic reports and actionable recommendations.
Unlike simple wrapper tools, these synthesize data from multiple
sources for the LLM agent to reason over.
"""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from oracle.oci_kafka_mcp_server.audit.logger import audit
from oracle.oci_kafka_mcp_server.kafka.admin_client import KafkaAdminClient
from oracle.oci_kafka_mcp_server.kafka.connection import CircuitBreaker
from oracle.oci_kafka_mcp_server.kafka.consumer_client import KafkaConsumerClient

CIRCUIT_OPEN_MSG = "Circuit breaker is open. Kafka may be unavailable."


def register_diagnostic_tools(
    mcp: FastMCP,
    admin_client: KafkaAdminClient,
    consumer_client: KafkaConsumerClient,
    circuit_breaker: CircuitBreaker,
) -> None:
    """Register AI diagnostic tools with the MCP server."""

    @mcp.tool()
    def oci_kafka_recommend_scaling() -> str:
        """Analyze the cluster and recommend scaling actions.

        Collects broker count, topic/partition distribution, replication health,
        and partition skew to produce a structured scaling recommendation.

        This tool gathers data only — the LLM agent should interpret the
        findings and present human-readable recommendations to the user.

        Returns a diagnostic report with:
        - Current cluster capacity (brokers, partitions, topics)
        - Partition distribution analysis (skew ratio per broker)
        - Replication health (under-replicated partitions)
        - Broker utilization metrics (leader partitions and replica load)
        - Specific scaling recommendations with severity levels
        """
        if not circuit_breaker.allow_request():
            return json.dumps({"error": CIRCUIT_OPEN_MSG})

        with audit.audit_tool("oci_kafka_recommend_scaling", {}) as entry:
            try:
                report = _build_scaling_report(admin_client)
                entry.result_status = "success"
                circuit_breaker.record_success()
                return json.dumps(report, indent=2)
            except Exception as e:
                circuit_breaker.record_failure()
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to build scaling report: {e}"})

    @mcp.tool()
    def oci_kafka_analyze_lag_root_cause(group_id: str) -> str:
        """Analyze consumer lag and identify potential root causes.

        Collects consumer group state, per-partition lag, topic partition details,
        and cluster health to diagnose why a consumer group may be falling behind.

        This tool gathers data only — the LLM agent should interpret the
        findings and present a root cause analysis to the user.

        Args:
            group_id: The consumer group ID to analyze.

        Returns a diagnostic report with:
        - Consumer group state and member count
        - Per-partition lag breakdown with severity classification
        - Topic health (partition count, replication status)
        - Cluster health context (broker count, controller status)
        - Potential root causes ranked by likelihood
        """
        if not circuit_breaker.allow_request():
            return json.dumps({"error": CIRCUIT_OPEN_MSG})

        params = {"group_id": group_id}
        with audit.audit_tool("oci_kafka_analyze_lag_root_cause", params) as entry:
            try:
                report = _build_lag_report(admin_client, consumer_client, group_id)
                entry.result_status = "success"
                circuit_breaker.record_success()
                return json.dumps(report, indent=2)
            except Exception as e:
                circuit_breaker.record_failure()
                entry.result_status = "error"
                entry.error_message = str(e)
                return json.dumps({"error": f"Failed to analyze lag for group '{group_id}': {e}"})


def _build_scaling_report(admin_client: KafkaAdminClient) -> dict[str, Any]:
    """Collect cluster data and build a scaling recommendation report."""

    # 1. Cluster health
    health = admin_client.get_cluster_health()
    broker_count = health.get("broker_count", 0)
    topic_count = health.get("topic_count", 0)

    # 2. Partition skew across all topics
    skew = admin_client.get_partition_skew()
    broker_partition_counts = skew.get("broker_partition_counts", {})
    total_partitions = sum(broker_partition_counts.values()) if broker_partition_counts else 0

    # 3. Under-replicated partitions
    replication = admin_client.detect_under_replicated_partitions()
    under_replicated_count = replication.get("under_replicated_count", 0)

    # 4. Per-broker analysis
    broker_analysis = []
    for broker_id, leader_count in broker_partition_counts.items():
        avg_per_broker = total_partitions / broker_count if broker_count > 0 else 0
        deviation_pct = (
            round(((leader_count - avg_per_broker) / avg_per_broker) * 100, 1)
            if avg_per_broker > 0
            else 0
        )
        broker_analysis.append(
            {
                "broker_id": broker_id,
                "leader_partitions": leader_count,
                "expected_partitions": round(avg_per_broker, 1),
                "deviation_percent": deviation_pct,
                "status": "overloaded"
                if deviation_pct > 25
                else ("underutilized" if deviation_pct < -25 else "balanced"),
            }
        )

    # 5. Build recommendations
    recommendations = []

    if skew.get("skew_detected", False):
        recommendations.append(
            {
                "severity": "WARNING",
                "category": "partition_balance",
                "finding": f"Partition skew ratio is {skew.get('skew_ratio', 0)}x "
                f"(threshold: 1.5x). Some brokers are handling significantly more "
                f"leader partitions than others.",
                "action": "Run a partition reassignment to rebalance leader partitions "
                "across brokers. Consider using kafka-reassign-partitions tool.",
            }
        )

    if under_replicated_count > 0:
        recommendations.append(
            {
                "severity": "CRITICAL",
                "category": "replication_health",
                "finding": f"{under_replicated_count} under-replicated partition(s) detected. "
                "Data durability is at risk.",
                "action": "Investigate broker health. Check for disk space issues, network "
                "problems, or broker failures. Under-replicated partitions may indicate "
                "a broker needs to be replaced or scaled.",
            }
        )

    partitions_per_broker = total_partitions / broker_count if broker_count > 0 else 0
    if partitions_per_broker > 1000:
        recommendations.append(
            {
                "severity": "WARNING",
                "category": "broker_capacity",
                "finding": f"Average {partitions_per_broker:.0f} partitions per broker. "
                "Recommended limit is ~1000 partitions per broker for optimal performance.",
                "action": f"Consider scaling the cluster from {broker_count} to "
                f"{max(broker_count + 1, int(total_partitions / 800))} brokers.",
            }
        )

    if broker_count < 3:
        recommendations.append(
            {
                "severity": "WARNING",
                "category": "high_availability",
                "finding": f"Cluster has only {broker_count} broker(s). "
                "Minimum 3 brokers recommended for high availability.",
                "action": "Scale the cluster to at least 3 brokers for production workloads.",
            }
        )

    if not recommendations:
        recommendations.append(
            {
                "severity": "INFO",
                "category": "overall",
                "finding": "Cluster is healthy. No scaling actions needed at this time.",
                "action": "Continue monitoring. Re-run this analysis after adding new topics "
                "or when traffic patterns change.",
            }
        )

    return {
        "report_type": "scaling_recommendation",
        "cluster_summary": {
            "cluster_id": health.get("cluster_id", "unknown"),
            "broker_count": broker_count,
            "topic_count": topic_count,
            "total_partitions": total_partitions,
            "partitions_per_broker": round(partitions_per_broker, 1),
        },
        "partition_balance": {
            "skew_detected": skew.get("skew_detected", False),
            "skew_ratio": skew.get("skew_ratio", 1.0),
            "broker_analysis": broker_analysis,
        },
        "replication_health": {
            "total_partitions": replication.get("total_partitions", 0),
            "under_replicated_count": under_replicated_count,
            "healthy": replication.get("healthy", True),
        },
        "recommendations": recommendations,
    }


def _build_lag_report(
    admin_client: KafkaAdminClient,
    consumer_client: KafkaConsumerClient,
    group_id: str,
) -> dict[str, Any]:
    """Collect consumer group data and build a lag root cause report."""

    # 1. Consumer group details
    group_info = consumer_client.describe_consumer_group(group_id)
    if "error" in group_info:
        return {"error": group_info["error"], "group_id": group_id}

    # 2. Consumer lag
    lag_info = consumer_client.get_consumer_lag(group_id)
    if "error" in lag_info:
        return {"error": lag_info["error"], "group_id": group_id}

    total_lag = lag_info.get("total_lag", 0)
    partitions = lag_info.get("partitions", [])

    # 3. Classify lag severity per partition
    lag_analysis = []
    topics_involved = set()
    hot_partitions = []

    for p in partitions:
        lag = p.get("lag", 0)
        topics_involved.add(p["topic"])

        severity = "NONE"
        if lag > 100000:
            severity = "CRITICAL"
        elif lag > 10000:
            severity = "HIGH"
        elif lag > 1000:
            severity = "MEDIUM"
        elif lag > 0:
            severity = "LOW"

        entry = {
            "topic": p["topic"],
            "partition": p["partition"],
            "lag": lag,
            "committed_offset": p.get("committed_offset", -1),
            "end_offset": p.get("end_offset", 0),
            "severity": severity,
        }
        lag_analysis.append(entry)

        if severity in ("CRITICAL", "HIGH"):
            hot_partitions.append(entry)

    # 4. Cluster context
    health = admin_client.get_cluster_health()

    # 5. Topic details for involved topics
    topic_details = {}
    for topic_name in topics_involved:
        topic_info = admin_client.describe_topic(topic_name)
        if "error" not in topic_info:
            topic_details[topic_name] = {
                "partition_count": topic_info.get("partition_count", 0),
                "config": topic_info.get("config", {}),
            }

    # 6. Build potential root causes
    potential_causes = []
    member_count = group_info.get("member_count", 0)
    group_state = group_info.get("state", "unknown")

    if group_state == "Empty" or member_count == 0:
        potential_causes.append(
            {
                "likelihood": "HIGH",
                "cause": "Consumer group has no active members",
                "detail": f"Group state is '{group_state}' with {member_count} members. "
                "No consumers are processing messages.",
                "remediation": (
                    "Start consumer application instances or check for crashes/restarts."
                ),
            }
        )

    if member_count > 0:
        for topic_name in topics_involved:
            td = topic_details.get(topic_name, {})
            partition_count = td.get("partition_count", 0)
            if partition_count > 0 and member_count < partition_count:
                potential_causes.append(
                    {
                        "likelihood": "MEDIUM",
                        "cause": f"Under-provisioned consumers for topic '{topic_name}'",
                        "detail": f"Topic has {partition_count} partitions but group has only "
                        f"{member_count} consumer(s). Maximum parallelism is limited to "
                        f"{member_count} partitions being consumed simultaneously.",
                        "remediation": f"Scale consumer instances to at least {partition_count} "
                        "to match partition count for maximum parallelism.",
                    }
                )

    if hot_partitions:
        hot_partition_ids = [f"{p['topic']}:{p['partition']}" for p in hot_partitions[:5]]
        potential_causes.append(
            {
                "likelihood": "MEDIUM",
                "cause": "Hot partitions with disproportionate lag",
                "detail": f"Partitions {', '.join(hot_partition_ids)} have significantly higher "
                "lag than others. This may indicate uneven message distribution (key skew) "
                "or slow processing for specific partition keys.",
                "remediation": "Review producer partitioning strategy. Check if specific "
                "message keys are causing hot partitions. Consider repartitioning the topic.",
            }
        )

    if total_lag > 0 and not potential_causes:
        potential_causes.append(
            {
                "likelihood": "MEDIUM",
                "cause": "Consumer processing is slower than producer throughput",
                "detail": f"Total lag is {total_lag} across {len(partitions)} partitions. "
                "Consumers may be processing messages slower than producers are writing.",
                "remediation": "Profile consumer processing time. Consider optimizing "
                "consumer logic, increasing consumer instances, or batching.",
            }
        )

    if not potential_causes:
        potential_causes.append(
            {
                "likelihood": "INFO",
                "cause": "No lag detected — consumer group is caught up",
                "detail": "All partitions have zero lag. The consumer group is processing "
                "messages at or above the producer rate.",
                "remediation": "No action needed. Continue monitoring.",
            }
        )

    return {
        "report_type": "lag_root_cause_analysis",
        "group_id": group_id,
        "consumer_group": {
            "state": group_state,
            "member_count": member_count,
            "coordinator": group_info.get("coordinator", {}),
        },
        "lag_summary": {
            "total_lag": total_lag,
            "partition_count": len(partitions),
            "critical_partitions": len([p for p in lag_analysis if p["severity"] == "CRITICAL"]),
            "high_lag_partitions": len([p for p in lag_analysis if p["severity"] == "HIGH"]),
        },
        "lag_by_partition": lag_analysis,
        "hot_partitions": hot_partitions,
        "topic_details": topic_details,
        "cluster_context": {
            "broker_count": health.get("broker_count", 0),
            "controller_id": health.get("controller_id", -1),
        },
        "potential_root_causes": potential_causes,
    }
