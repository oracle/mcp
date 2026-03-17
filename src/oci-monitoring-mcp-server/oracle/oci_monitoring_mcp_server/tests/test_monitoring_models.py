"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime
from types import SimpleNamespace

from oracle.oci_monitoring_mcp_server.alarm_models import (
    AlarmOverride,
    AlarmSummary,
    Suppression,
    map_alarm_override,
    map_alarm_overrides,
    map_alarm_summary,
    map_suppression,
)
from oracle.oci_monitoring_mcp_server.metric_models import (
    AggregatedDatapoint,
    Datapoint,
)
from oracle.oci_monitoring_mcp_server.metric_models import (
    ListMetricsDetails as PListMetricsDetails,
)
from oracle.oci_monitoring_mcp_server.metric_models import (
    Metric,
    MetricData,
    MetricDataDetails,
)
from oracle.oci_monitoring_mcp_server.metric_models import (
    SummarizeMetricsDataDetails as PSummarizeMetricsDataDetails,
)
from oracle.oci_monitoring_mcp_server.metric_models import (
    map_aggregated_datapoint,
    map_aggregated_datapoints,
    map_datapoint,
    map_datapoints,
    map_list_metrics_details,
    map_metric,
    map_metric_data,
    map_metric_data_details,
)


class TestAlarmModels:
    def test_map_suppression_none(self) -> None:
        assert map_suppression(None) is None

    def test_map_suppression_values_snake_and_camel(self) -> None:
        s1 = SimpleNamespace(
            description="Desc",
            time_suppress_from=datetime(2024, 1, 1),
            time_suppress_until=datetime(2024, 1, 2),
        )
        mapped1 = map_suppression(s1)
        assert isinstance(mapped1, Suppression)
        assert mapped1.description == "Desc"
        assert mapped1.time_suppress_from == datetime(2024, 1, 1)
        assert mapped1.time_suppress_until == datetime(2024, 1, 2)

        s2 = SimpleNamespace(
            description="D",
            timeSuppressFrom=datetime(2023, 5, 1),
            timeSuppressUntil=datetime(2023, 5, 2),
        )
        mapped2 = map_suppression(s2)
        assert mapped2.time_suppress_from == datetime(2023, 5, 1)
        assert mapped2.time_suppress_until == datetime(2023, 5, 2)

    def test_map_alarm_override_none_and_values(self) -> None:
        assert map_alarm_override(None) is None
        ov = SimpleNamespace(
            ruleName="BASE",
            query="Q",
            severity="CRITICAL",
            body="B",
            pendingDuration="PT5M",
        )
        mapped = map_alarm_override(ov)
        assert isinstance(mapped, AlarmOverride)
        assert mapped.rule_name == "BASE"
        assert mapped.query == "Q"
        assert mapped.severity == "CRITICAL"
        assert mapped.body == "B"
        assert mapped.pending_duration == "PT5M"

    def test_map_alarm_overrides_list_and_empty(self) -> None:
        assert map_alarm_overrides(None) is None
        assert map_alarm_overrides([]) is None
        ov = SimpleNamespace(ruleName="BASE")
        out = map_alarm_overrides([ov, None])
        assert isinstance(out, list)
        assert out and out[0].rule_name == "BASE"

    def test_map_alarm_summary(self) -> None:
        alarm_snake = SimpleNamespace(
            id="ocid1.alarm.oc1..abc",
            display_name="High CPU",
            compartment_id="ocid1.compartment.oc1..xyz",
            metric_compartment_id="ocid1.compartment.oc1..m",
            namespace="oci_compute",
            query="CpuUtilization[1m].mean()>80",
            severity="CRITICAL",
            destinations=["ocid1.topic.oc1..t1"],
            suppression=SimpleNamespace(description="maint"),
            is_enabled=True,
            isNotificationsPerMetricDimensionEnabled=False,
            freeform_tags={"env": "dev"},
            defined_tags={"NS": {"K": "V"}},
            lifecycle_state="ACTIVE",
            overrides=[SimpleNamespace(ruleName="BASE")],
            rule_name="BASE",
            notification_version="1.0",
            notification_title="Title",
            evaluation_slack_duration="PT3M",
            alarm_summary="summary",
            resource_group="rg",
        )
        mapped = map_alarm_summary(alarm_snake)
        assert isinstance(mapped, AlarmSummary)
        assert mapped.id == "ocid1.alarm.oc1..abc"
        assert mapped.display_name == "High CPU"
        assert mapped.compartment_id == "ocid1.compartment.oc1..xyz"
        assert mapped.metric_compartment_id == "ocid1.compartment.oc1..m"
        assert mapped.namespace == "oci_compute"
        assert mapped.query.startswith("CpuUtilization")
        assert mapped.severity == "CRITICAL"
        assert mapped.destinations == ["ocid1.topic.oc1..t1"]
        assert mapped.suppression and mapped.suppression.description == "maint"
        assert mapped.is_enabled is True
        assert mapped.is_notifications_per_metric_dimension_enabled is False
        assert mapped.freeform_tags == {"env": "dev"}
        assert mapped.defined_tags == {"NS": {"K": "V"}}
        assert mapped.lifecycle_state == "ACTIVE"
        assert mapped.overrides and mapped.overrides[0].rule_name == "BASE"
        assert mapped.rule_name == "BASE"
        assert mapped.notification_version == "1.0"
        assert mapped.notification_title == "Title"
        assert mapped.evaluation_slack_duration == "PT3M"
        assert mapped.alarm_summary == "summary"
        assert mapped.resource_group == "rg"


class TestMetricModels:
    def test_map_metric(self) -> None:
        m = SimpleNamespace(
            namespace="oci_compute",
            resource_group="rg",
            compartment_id="ocid1.compartment.oc1..xyz",
            name="CpuUtilization",
            dimensions={"resourceId": "ocid1.instance..."},
            metadata={"unit": "%"},
            resolution="1m",
        )
        mapped = map_metric(m)
        assert isinstance(mapped, Metric)
        assert mapped.name == "CpuUtilization"
        assert mapped.dimensions == {"resourceId": "ocid1.instance..."}
        assert mapped.metadata == {"unit": "%"}
        assert mapped.resolution == "1m"

    def test_map_aggregated_datapoint_and_list(self) -> None:
        assert map_aggregated_datapoint(None) is None
        p = SimpleNamespace(timestamp=datetime(2024, 1, 1), value=1.5)
        mp = map_aggregated_datapoint(p)
        assert isinstance(mp, AggregatedDatapoint)
        assert mp.value == 1.5
        assert map_aggregated_datapoints(None) is None
        lst = map_aggregated_datapoints([p, None])
        assert isinstance(lst, list)
        assert lst and isinstance(lst[0], AggregatedDatapoint)

    def test_map_metric_data(self) -> None:
        md = SimpleNamespace(
            namespace="oci_compute",
            resource_group="rg",
            compartment_id="ocid1.compartment.oc1..xyz",
            name="CpuUtilization",
            dimensions={"k": "v"},
            metadata={"unit": "%"},
            resolution="1m",
            aggregated_datapoints=[SimpleNamespace(timestamp=datetime(2024, 1, 1), value=2.0)],
        )
        mapped = map_metric_data(md)
        assert isinstance(mapped, MetricData)
        assert mapped.name == "CpuUtilization"
        assert mapped.aggregated_datapoints and isinstance(
            mapped.aggregated_datapoints[0], AggregatedDatapoint
        )

    def test_map_datapoint_and_list(self) -> None:
        assert map_datapoint(None) is None
        d = SimpleNamespace(timestamp=datetime(2024, 1, 1), value=3.3, count=2)
        md = map_datapoint(d)
        assert isinstance(md, Datapoint)
        assert md.count == 2
        assert map_datapoints(None) is None
        lst = map_datapoints([d, None])
        assert isinstance(lst, list)
        assert lst and isinstance(lst[0], Datapoint)

    def test_map_metric_data_details(self) -> None:
        mdd = SimpleNamespace(
            namespace="oci_compute",
            resource_group="rg",
            compartment_id="c",
            name="MetricName",
            dimensions={"x": "y"},
            metadata={"unit": "bytes"},
            datapoints=[SimpleNamespace(timestamp=datetime(2024, 1, 1), value=1.0)],
        )
        mapped = map_metric_data_details(mdd)
        assert isinstance(mapped, MetricDataDetails)
        assert mapped.datapoints and isinstance(mapped.datapoints[0], Datapoint)

    def test_map_list_metrics_details_with_camel_case_fallback(self) -> None:
        sdk = SimpleNamespace(namespace="ns", resource_group="rg", name="n")
        # Add camelCase attrs to be used when snake_case is missing
        setattr(sdk, "dimensionFilters", {"k": "v"})
        setattr(sdk, "groupBy", ["namespace"])
        mapped = map_list_metrics_details(sdk)  # type: ignore[arg-type]
        assert isinstance(mapped, PListMetricsDetails)
        assert mapped.dimension_filters == {"k": "v"}
        assert mapped.group_by == ["namespace"]

    def test_construct_pydantic_summarize_metrics_details(self) -> None:
        # Not a mapping, but ensures model can be created coherently
        p = PSummarizeMetricsDataDetails(
            namespace="ns",
            resource_group="rg",
            query="MQL",
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2),
            resolution="1m",
        )
        assert p.query == "MQL"
