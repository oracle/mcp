# Monitoring Query Language (MQL) Quick Guide

Use MQL to query metrics in Oracle Cloud Infrastructure (OCI) Monitoring. MQL is supported in:
- Metrics Explorer (Advanced mode)
- Service Metrics (open in Metrics Explorer → Advanced mode)
- Alarm definitions (Advanced mode)

Source: Monitoring Query Language (MQL) Reference  
https://docs.oracle.com/en-us/iaas/Content/Monitoring/Reference/mql.htm

## 1) Anatomy of an MQL Expression

Basic pattern:
```
<MetricName>[<interval>]{<dimension_filters>}.groupBy(<dim1>[, <dim2> ...]).<statistic>(<stat_arg_opt>) <predicate_opt>
```

Component overview:
- Metric name: The metric to query, e.g., `CpuUtilization`, `ServiceConnectorHubErrors`
- Interval: Window for aggregating raw datapoints (e.g., `1m`, `5m`, `1h`, `1d`)
- Dimension filters (optional): Key/value pairs narrowing the series, e.g., `{resourceId = "<ocid>", availabilityDomain = "phx-AD-1"}`
- groupBy (optional): Aggregate (combine) series by one or more dimensions
- Statistic: Aggregation over the interval (e.g., `mean()`, `sum()`, `percentile(0.9)`)
- Predicate (optional): A threshold or absence test (e.g., `> 80`, `in (60,80)`, `absent(20)`)

Example:
```
CpuUtilization[1m]{availabilityDomain = "VeBZ:PHX-AD-1"}.groupBy(poolId).percentile(0.9) > 85
```

## 2) Valid Intervals

Choose an interval appropriate to the metric emission rate and time range:
- Valid intervals: `1m`-`60m`, `1h`-`24h`, `1d`
- For metric queries, the default resolution equals the interval. Resolution governs the maximum time range returned
- For alarm queries, resolution is always `1m` (interval does not change resolution)

Examples:
```
CpuUtilization[1m].mean()
TotalRequestLatency[5m].mean()
```

Tip: Smaller time ranges support more granular intervals. For long time ranges (e.g., 90 days), coarser intervals (≥ 1h) are required.

## 3) Statistics

You MUST Apply one statistic per expression (you can nest or chain via multiple queries/join operators).

Common statistics:
- mean(), avg() — average (avg is identical to mean)
- sum() — sum of values per interval
- count() — number of observations in the interval
- min(), max() — min/max in the interval
- first(), last() — earliest/latest value in the interval
- rate() — per-interval average rate of change (per-second)
- increment() — per-interval change
- percentile(p) — 0.0 < p < 1.0 (e.g., `percentile(0.9)`)

Absence statistic (special):
- absent(x) — returns 1 if a metric is absent for the entire interval; 0 if present
  - Optional absence detection period (minutes/hours/days): `absent(20)`, `absent(2h)`, `absent(1d)`
  - Default absence detection period is 2 hours (alarms can customize)

Examples:
```
CpuUtilization[1m].mean()
ServiceConnectorHubErrors[1m].count()
FileSystemReadRequestsBySize[5m]{size = "0B_to_8KiB"}.percentile(.50)
CpuUtilization[1m]{resourceId = "<ocid>"}.groupBy(resourceId).absent(20)
```

## 4) Predicates (Thresholds and Absence)

Use a predicate to keep only values that meet a condition.

Supported operators:
- >, >=, <, <=, ==, !=
- in (a, b)    — inclusive range
- not in (a, b) — inclusive outside range
- absent()     — absence predicate (see above)

Examples:
```
CpuUtilization[1m].mean() > 80
CpuUtilization[1m].mean() in (60, 80)           # inclusive range
ServiceConnectorHubErrors[1m].count() > 1
```

## 5) Dimension Filters and Fuzzy Matching

Filter series with exact matches:
```
CpuUtilization[1m]{resourceId = "<ocid>", availabilityDomain = "phx-AD-1"}.mean()
```

Use fuzzy matching for multiple values or wildcard patterns with `=~`:
- `|` — OR between values
- `*` — wildcard for zero or more characters

Examples:
```
CpuUtilization[1m]{resourceDisplayName =~ "ol8|ol7"}.min() >= 20
CpuUtilization[1m]{resourceDisplayName =~ "instance-2023-*"}.min() >= 30
CpuUtilization[1m]{faultDomain =~ "FAULT-DOMAIN-1|FAULT-DOMAIN-2"}.mean()
```

## 6) Grouping

Aggregate across multiple streams and then compute a statistic:
```
CpuUtilization[1m]{availabilityDomain = "VeBZ:PHX-AD-1"}.groupBy(poolId).percentile(0.9) > 85
```

Common groupBy fields: `resourceId`, `availabilityDomain`, `faultDomain`, `resourceDisplayName`, service-specific dimensions.

## 7) Arithmetic

You can do math with metrics and constants:
```
100 - CpuUtilization[1m].mean()                  # available CPU %
TotalRequestLatency[1m].mean() / 1000            # ms → seconds
```

## 8) Joining Multiple Queries

Combine queries with logical AND/OR. Joins are only valid between complete queries (not between dimension sets).

Operators:
- `&&` — AND
- `||` — OR

Examples:
```
CpuUtilization[1m]{faultDomain =~ "FAULT-DOMAIN-1|FAULT-DOMAIN-2"}.mean()
|| 
MemoryUtilization[1m]{faultDomain =~ "FAULT-DOMAIN-1|FAULT-DOMAIN-2"}.mean()

ServiceConnectorHubErrors[1m].count() > 1
&&
ServiceConnectorHubErrors[1m].mean() > 0.5
```

Invalid (don’t join inside a dimension set):
```
# INVALID
CpuUtilization[1m]{faultDomain =~ "FD-1" || resourceDisplayName = "test"}.mean()
```

## 9) Practical Examples

- Mean CPU over 1 minute:
```
CpuUtilization[1m].mean()
```

- Errors per minute > 1:
```
ServiceConnectorHubErrors[1m].count() > 1
```

- 90th percentile CPU by pool in an AD, alarm when > 85:
```
CpuUtilization[1m]{availabilityDomain = "VeBZ:PHX-AD-1"}.groupBy(poolId).percentile(0.9) > 85
```

- Minimum CPU ≥ 20 for instances named ol8 or ol7:
```
CpuUtilization[1m]{resourceDisplayName =~ "ol8|ol7"}.min() >= 20
```

- Absence alarm for a specific resource (20 hours absence detection):
```
CpuUtilization[1m]{resourceId = "<resource_ocid>"}.groupBy(resourceId).absent(20h)
```

- Join: CPU or Memory in fault domains 1 or 2:
```
CpuUtilization[1m]{faultDomain =~ "FAULT-DOMAIN-1|FAULT-DOMAIN-2"}.mean()
||
MemoryUtilization[1m]{faultDomain =~ "FAULT-DOMAIN-1|FAULT-DOMAIN-2"}.mean()
```

- Compute available CPU:
```
100 - CpuUtilization[1m].mean()
```

## 10) Notes and Tips

- Pick an interval aligned with the metric emission frequency (most service metrics are emitted every minute)
- For metric queries, interval drives default resolution and thus maximum time range returned
- For alarm queries, resolution is fixed at `1m`
- Use `groupBy()` to combine multiple metric streams before applying statistics
- Use `=~` with `|` and `*` to match multiple values and wildcard patterns
- For absence alarms, customize the absence detection period to match your operational expectations

## References

- MQL Reference: https://docs.oracle.com/en-us/iaas/Content/Monitoring/Reference/mql.htm
- Building Metric Queries: https://docs.oracle.com/en-us/iaas/Content/Monitoring/Tasks/buildingqueries.htm
- Selecting Interval: https://docs.oracle.com/en-us/iaas/Content/Monitoring/Tasks/query-metric-interval.htm
- Selecting Statistic: https://docs.oracle.com/en-us/iaas/Content/Monitoring/Tasks/query-metric-statistic.htm
- Fuzzy Matching: https://docs.oracle.com/en-us/iaas/Content/Monitoring/Reference/mql.htm#fuzzy-mql
- Join Queries: https://docs.oracle.com/en-us/iaas/Content/Monitoring/Reference/mql.htm#join
