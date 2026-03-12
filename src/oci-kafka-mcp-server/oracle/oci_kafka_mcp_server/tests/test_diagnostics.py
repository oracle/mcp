"""Tests for AI diagnostic tools (recommend_scaling, analyze_lag_root_cause)."""

from __future__ import annotations

from unittest.mock import MagicMock

from oracle.oci_kafka_mcp_server.tools.diagnostics import _build_lag_report, _build_scaling_report


class TestBuildScalingReport:
    """Test the scaling recommendation report builder."""

    def test_healthy_cluster(self) -> None:
        """Should return INFO recommendation for a healthy balanced cluster."""
        admin = MagicMock()
        admin.get_cluster_health.return_value = {
            "cluster_id": "test-cluster",
            "broker_count": 3,
            "topic_count": 5,
        }
        admin.get_partition_skew.return_value = {
            "skew_detected": False,
            "skew_ratio": 1.1,
            "broker_partition_counts": {0: 10, 1: 10, 2: 11},
        }
        admin.detect_under_replicated_partitions.return_value = {
            "total_partitions": 31,
            "under_replicated_count": 0,
            "healthy": True,
        }

        report = _build_scaling_report(admin)

        assert report["report_type"] == "scaling_recommendation"
        assert report["cluster_summary"]["broker_count"] == 3
        assert report["cluster_summary"]["total_partitions"] == 31
        assert report["replication_health"]["healthy"] is True
        assert len(report["recommendations"]) == 1
        assert report["recommendations"][0]["severity"] == "INFO"

    def test_skewed_cluster(self) -> None:
        """Should return WARNING for partition skew."""
        admin = MagicMock()
        admin.get_cluster_health.return_value = {
            "cluster_id": "test-cluster",
            "broker_count": 3,
            "topic_count": 5,
        }
        admin.get_partition_skew.return_value = {
            "skew_detected": True,
            "skew_ratio": 2.5,
            "broker_partition_counts": {0: 25, 1: 10, 2: 10},
        }
        admin.detect_under_replicated_partitions.return_value = {
            "total_partitions": 45,
            "under_replicated_count": 0,
            "healthy": True,
        }

        report = _build_scaling_report(admin)

        skew_rec = [r for r in report["recommendations"] if r["category"] == "partition_balance"]
        assert len(skew_rec) == 1
        assert skew_rec[0]["severity"] == "WARNING"
        assert "2.5" in skew_rec[0]["finding"]

    def test_under_replicated_partitions(self) -> None:
        """Should return CRITICAL for under-replicated partitions."""
        admin = MagicMock()
        admin.get_cluster_health.return_value = {
            "cluster_id": "test-cluster",
            "broker_count": 3,
            "topic_count": 2,
        }
        admin.get_partition_skew.return_value = {
            "skew_detected": False,
            "skew_ratio": 1.0,
            "broker_partition_counts": {0: 5, 1: 5, 2: 5},
        }
        admin.detect_under_replicated_partitions.return_value = {
            "total_partitions": 15,
            "under_replicated_count": 3,
            "healthy": False,
        }

        report = _build_scaling_report(admin)

        repl_rec = [r for r in report["recommendations"] if r["category"] == "replication_health"]
        assert len(repl_rec) == 1
        assert repl_rec[0]["severity"] == "CRITICAL"
        assert "3" in repl_rec[0]["finding"]

    def test_broker_analysis(self) -> None:
        """Should calculate per-broker deviation percentages."""
        admin = MagicMock()
        admin.get_cluster_health.return_value = {
            "cluster_id": "test-cluster",
            "broker_count": 3,
            "topic_count": 2,
        }
        admin.get_partition_skew.return_value = {
            "skew_detected": True,
            "skew_ratio": 2.0,
            "broker_partition_counts": {0: 20, 1: 10, 2: 10},
        }
        admin.detect_under_replicated_partitions.return_value = {
            "total_partitions": 40,
            "under_replicated_count": 0,
            "healthy": True,
        }

        report = _build_scaling_report(admin)
        broker_analysis = report["partition_balance"]["broker_analysis"]

        # Broker 0 has 20 partitions, avg is ~13.3, so ~50% over
        overloaded = [b for b in broker_analysis if b["status"] == "overloaded"]
        assert len(overloaded) >= 1

    def test_small_cluster_warning(self) -> None:
        """Should warn about clusters with fewer than 3 brokers."""
        admin = MagicMock()
        admin.get_cluster_health.return_value = {
            "cluster_id": "test-cluster",
            "broker_count": 1,
            "topic_count": 1,
        }
        admin.get_partition_skew.return_value = {
            "skew_detected": False,
            "skew_ratio": 1.0,
            "broker_partition_counts": {0: 3},
        }
        admin.detect_under_replicated_partitions.return_value = {
            "total_partitions": 3,
            "under_replicated_count": 0,
            "healthy": True,
        }

        report = _build_scaling_report(admin)

        ha_rec = [r for r in report["recommendations"] if r["category"] == "high_availability"]
        assert len(ha_rec) == 1
        assert ha_rec[0]["severity"] == "WARNING"


class TestBuildLagReport:
    """Test the lag root cause analysis report builder."""

    def test_empty_consumer_group(self) -> None:
        """Should identify empty consumer group as root cause."""
        admin = MagicMock()
        admin.get_cluster_health.return_value = {"broker_count": 3, "controller_id": 0}
        admin.describe_topic.return_value = {
            "partition_count": 6,
            "config": {},
        }

        consumer = MagicMock()
        consumer.describe_consumer_group.return_value = {
            "group_id": "my-group",
            "state": "Empty",
            "member_count": 0,
            "coordinator": {"id": 0, "host": "broker-0", "port": 9092},
        }
        consumer.get_consumer_lag.return_value = {
            "group_id": "my-group",
            "total_lag": 50000,
            "partitions": [
                {
                    "topic": "orders",
                    "partition": 0,
                    "lag": 25000,
                    "committed_offset": 0,
                    "end_offset": 25000,
                },
                {
                    "topic": "orders",
                    "partition": 1,
                    "lag": 25000,
                    "committed_offset": 0,
                    "end_offset": 25000,
                },
            ],
        }

        report = _build_lag_report(admin, consumer, "my-group")

        assert report["report_type"] == "lag_root_cause_analysis"
        assert report["consumer_group"]["state"] == "Empty"
        assert report["lag_summary"]["total_lag"] == 50000

        causes = report["potential_root_causes"]
        empty_cause = [c for c in causes if "no active members" in c["cause"]]
        assert len(empty_cause) == 1
        assert empty_cause[0]["likelihood"] == "HIGH"

    def test_under_provisioned_consumers(self) -> None:
        """Should detect when consumers < partitions."""
        admin = MagicMock()
        admin.get_cluster_health.return_value = {"broker_count": 3, "controller_id": 0}
        admin.describe_topic.return_value = {
            "partition_count": 12,
            "config": {},
        }

        consumer = MagicMock()
        consumer.describe_consumer_group.return_value = {
            "group_id": "slow-group",
            "state": "Stable",
            "member_count": 2,
            "coordinator": {"id": 0, "host": "broker-0", "port": 9092},
        }
        consumer.get_consumer_lag.return_value = {
            "group_id": "slow-group",
            "total_lag": 100000,
            "partitions": [
                {
                    "topic": "events",
                    "partition": i,
                    "lag": 8333,
                    "committed_offset": 0,
                    "end_offset": 8333,
                }
                for i in range(12)
            ],
        }

        report = _build_lag_report(admin, consumer, "slow-group")

        causes = report["potential_root_causes"]
        under_prov = [c for c in causes if "Under-provisioned" in c["cause"]]
        assert len(under_prov) == 1
        assert "12 partitions" in under_prov[0]["detail"]
        assert "2 consumer" in under_prov[0]["detail"]

    def test_hot_partitions_detected(self) -> None:
        """Should detect hot partitions with disproportionate lag."""
        admin = MagicMock()
        admin.get_cluster_health.return_value = {"broker_count": 3, "controller_id": 0}
        admin.describe_topic.return_value = {
            "partition_count": 3,
            "config": {},
        }

        consumer = MagicMock()
        consumer.describe_consumer_group.return_value = {
            "group_id": "hot-group",
            "state": "Stable",
            "member_count": 3,
            "coordinator": {"id": 0, "host": "broker-0", "port": 9092},
        }
        consumer.get_consumer_lag.return_value = {
            "group_id": "hot-group",
            "total_lag": 200100,
            "partitions": [
                {
                    "topic": "payments",
                    "partition": 0,
                    "lag": 200000,
                    "committed_offset": 0,
                    "end_offset": 200000,
                },
                {
                    "topic": "payments",
                    "partition": 1,
                    "lag": 50,
                    "committed_offset": 950,
                    "end_offset": 1000,
                },
                {
                    "topic": "payments",
                    "partition": 2,
                    "lag": 50,
                    "committed_offset": 950,
                    "end_offset": 1000,
                },
            ],
        }

        report = _build_lag_report(admin, consumer, "hot-group")

        assert len(report["hot_partitions"]) >= 1
        assert report["hot_partitions"][0]["partition"] == 0

        causes = report["potential_root_causes"]
        hot_cause = [c for c in causes if "Hot partitions" in c["cause"]]
        assert len(hot_cause) == 1

    def test_no_lag(self) -> None:
        """Should report no issues when consumer is caught up."""
        admin = MagicMock()
        admin.get_cluster_health.return_value = {"broker_count": 3, "controller_id": 0}
        admin.describe_topic.return_value = {"partition_count": 1, "config": {}}

        consumer = MagicMock()
        consumer.describe_consumer_group.return_value = {
            "group_id": "healthy-group",
            "state": "Stable",
            "member_count": 3,
            "coordinator": {"id": 0, "host": "broker-0", "port": 9092},
        }
        consumer.get_consumer_lag.return_value = {
            "group_id": "healthy-group",
            "total_lag": 0,
            "partitions": [
                {
                    "topic": "orders",
                    "partition": 0,
                    "lag": 0,
                    "committed_offset": 1000,
                    "end_offset": 1000,
                },
            ],
        }

        report = _build_lag_report(admin, consumer, "healthy-group")

        assert report["lag_summary"]["total_lag"] == 0
        causes = report["potential_root_causes"]
        assert causes[0]["likelihood"] == "INFO"
        assert "caught up" in causes[0]["cause"]

    def test_group_describe_error(self) -> None:
        """Should return error when consumer group describe fails."""
        admin = MagicMock()
        consumer = MagicMock()
        consumer.describe_consumer_group.return_value = {"error": "Group 'missing' not found"}

        report = _build_lag_report(admin, consumer, "missing")

        assert "error" in report

    def test_lag_severity_classification(self) -> None:
        """Should correctly classify lag severity levels."""
        admin = MagicMock()
        admin.get_cluster_health.return_value = {"broker_count": 3, "controller_id": 0}
        admin.describe_topic.return_value = {"partition_count": 4, "config": {}}

        consumer = MagicMock()
        consumer.describe_consumer_group.return_value = {
            "group_id": "test-group",
            "state": "Stable",
            "member_count": 4,
            "coordinator": {"id": 0, "host": "broker-0", "port": 9092},
        }
        consumer.get_consumer_lag.return_value = {
            "group_id": "test-group",
            "total_lag": 161500,
            "partitions": [
                {
                    "topic": "t",
                    "partition": 0,
                    "lag": 0,
                    "committed_offset": 100,
                    "end_offset": 100,
                },
                {
                    "topic": "t",
                    "partition": 1,
                    "lag": 500,
                    "committed_offset": 500,
                    "end_offset": 1000,
                },
                {
                    "topic": "t",
                    "partition": 2,
                    "lag": 11000,
                    "committed_offset": 0,
                    "end_offset": 11000,
                },
                {
                    "topic": "t",
                    "partition": 3,
                    "lag": 150000,
                    "committed_offset": 0,
                    "end_offset": 150000,
                },
            ],
        }

        report = _build_lag_report(admin, consumer, "test-group")
        partitions = report["lag_by_partition"]

        severity_map = {p["partition"]: p["severity"] for p in partitions}
        assert severity_map[0] == "NONE"
        assert severity_map[1] == "LOW"
        assert severity_map[2] == "HIGH"
        assert severity_map[3] == "CRITICAL"
