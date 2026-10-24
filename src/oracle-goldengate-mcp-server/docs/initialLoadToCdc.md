# Oracle Initial Load to CDC Workflow

Use this ordered workflow when an Oracle Initial Load is followed by ongoing change data capture (CDC). The wait
points are prerequisites, not optional recommendations.

## Required sequence

1. Configure, register, and start the primary CDC Extract. Starting it first preserves source changes that occur
   while the initial load is running.
2. Determine an appropriate instantiation SCN after the CDC Extract registration. The instantiation SCN must be
   later than the registration SCN and should account for open transactions.
3. Create the Initial Load Extract with `asOfScn` set to the instantiation SCN. This emits
   `SQLPREDICATE 'AS OF SCN <scn>'` in the `TABLE` statement.
4. Start the Initial Load Extract.
5. Wait until the Initial Load Extract stops. Call `get_extract_status` and then `get_extract_report`. Do not proceed
   if it is still running, has abended, or its completion state is ambiguous.
6. After the Initial Load Extract has completed and its `EXTFILE` is available to the target deployment, start the
   Initial Load Replicat with `start_initial_load_replicat`. Do not use the generic `start` tool for this step.
7. Wait until the Initial Load Replicat has finished processing the initial-load data. Review its status, report,
   statistics, and lag as appropriate for the deployment.
8. Start the CDC Replicat at the matching instantiation SCN, using the `AT CSN` or `AFTER CSN` behavior selected for
   the synchronization design.

The `asOfScn` value controls the Oracle flashback query performed by the Initial Load Extract. It is not the Extract
process start position.

## Agent entry points

- Call `get_initial_load_cdc_workflow` before planning or executing the workflow.
- Use `create_initial_load_extract(..., asOfScn=<instantiation_scn>)` for the snapshot.
- Use `start_initial_load_replicat(replicatName, initialLoadExtractName)` to enforce the Extract prerequisite checks.
- Use the generic `start` tool for CDC processes only after their workflow prerequisites are satisfied.

## Guard behavior

`start_initial_load_replicat` reads the backend configuration and verifies that the Extract uses `source: tables`
and that its EXTFILE path matches the Replicat source path. It then requires `STOPPED` status, a process ID and
`lastStarted` timestamp, and matching execution history with a successful exit, a finish time, and no manual kill.
The report must identify that process ID and contain no strong failure indicator or operator STOP/KILL command.
The Extract status and run identity are checked again immediately before the start command.

Missing, stale, inconsistent, or unrecognized evidence fails closed. This is a conservative check of the available
backend evidence, not proof that every intended row was loaded. It cannot prove that an externally transferred
file is present on a different deployment or prevent changes made by another operator after the final check.
Verify transferred file availability and the completeness of the load separately.

The generic `start` tool inspects the process configuration. It allows Extract starts, and allows a Replicat only
when its source matches a local CDC Extract's EXTTRAIL and no local Extract produces that source as an EXTFILE.
The check requires a complete collection of at most 128 Extracts; it refuses incomplete discovery and ambiguous
or remote-only producer associations. Initial-load Replicats must use `start_initial_load_replicat`.

Tool calls execute on worker threads so blocking HTTP does not block the MCP event loop. Operations remain
serialized to preserve shared-session ownership and the check-and-start sequence. Cancellation is not rollback;
check the process status before deciding whether to retry a mutation.

For the documented Oracle precise-instantiation procedure, see:

https://docs.oracle.com/en/database/goldengate/core/26/coredoc/instantiate-add-initial-load-extract-using-admin-client.html

The backend evidence fields follow Oracle's [Extract execution history](https://docs.oracle.com/en/database/goldengate/core/26/oggra/op-services-version-extracts-extract-info-history-get.html),
[status](https://docs.oracle.com/en/database/goldengate/core/26/oggra/op-services-version-extracts-extract-info-status-get.html),
and [report](https://docs.oracle.com/en/database/goldengate/core/26/oggra/op-services-version-extracts-extract-info-reports-report-get.html) REST contracts.
