createReplicat tool: structured options and advanced parameters

Overview
- Supports either a raw MAP statement (backward compatible) or structured source/options.
- Advanced settings now allow emitting common Replicat parameters such as DBOPTIONS, BATCHSQL, and custom EXTTRAIL paths.

Input shape (abridged)
- Required:
  - replicatName: string (<= 8 alphanumeric)
  - trailName: string (two-character trail name used for `source.name`)
  - domainName: string
  - connectionName: string
- Either:
  - mapStatement: string (raw), or
  - source/options pair:
    - source: {
        container?: string
        schema: string
        table: string
        partitionObjIds?: number[]
        targetTable: string
      }
    - options?: CreateReplicatOptions (see src/mapStatement.ts for full set)
- Optional:
  - advanced?: {
      dbOptions?: string | string[] | {
        entries?: string[]
        additional?: string[]
      }
      batchSql?: string | string[]
      additionalParameters?: string[]
      modeType?: "nonintegrated" | "integrated" | "parallel" | "coordinated"
      modeParallel?: boolean
    }

Advanced parameter emission order
1. `DBOPTIONS ...` (if provided)
2. One `BATCHSQL ...` line per entry
3. Any `additionalParameters` strings (emitted as-is)
- `extTrail`, when provided, overrides the default `EXTTRAIL {trailName}` entry.

Example requests

1) Raw MAP statement
Request:
{
  "replicatName": "REP01",
  "trailName": "AA",
  "domainName": "OracleGoldenGate",
  "connectionName": "TARGET_CONN",
  "mapStatement": "MAP HR.EMPLOYEES, TARGET HR_REP.EMPLOYEES;"
}

2) Structured MAP with advanced DBOPTIONS and BATCHSQL
Request:
{
  "replicatName": "MYREP",
  "trailName": "LT",
  "domainName": "OracleGoldenGate",
  "connectionName": "TARGET_CONN",
  "source": {
    "schema": "SCHEMA",
    "table": "*",
    "targetTable": "SCHEMA.*"
  },
  "advanced": {
    "dbOptions": [
      "FETCHBATCHSIZE 5000",
      "EMPTYLOBSTRING 'N/A'"
    ],
    "batchSql": [
      "BATCHERRORMODE",
      "BATCHESPERQUEUE 100",
      "OPSPERBATCH 2000"
    ],
    "extTrail": "./dirdat/lt"
  }
}
Builds parameter lines:
REPLICAT MYREP
EXTTRAIL ./dirdat/lt
USERIDALIAS TARGET_CONN DOMAIN OracleGoldenGate
DBOPTIONS FETCHBATCHSIZE 5000, EMPTYLOBSTRING 'N/A'
BATCHSQL BATCHERRORMODE
BATCHSQL BATCHESPERQUEUE 100
BATCHSQL OPSPERBATCH 2000
MAP SCHEMA.* , TARGET SCHEMA.*;

3) Alternative credentials and advanced parallelism
Request:
{
  "replicatName": "REP_PARA",
  "trailName": "PR",
  "domainName": "OracleGoldenGate",
  "connectionName": "ggadmin",
  "source": {
    "schema": "ORDERS",
    "table": "*",
    "targetTable": "ORDERS.*"
  },
  "advanced": {
    "credential": [
      "USERID ggadmin, PASSWORD mypass"
    ],
    "applyParallelism": 4,
    "splitTransRecs": 1000,
    "chunkSize": 10000
  }
}
Builds parameter lines:
REPLICAT REP_PARA
USERID ggadmin, PASSWORD mypass
APPLY_PARALLELISM 4
SPLIT_TRANS_RECS 1000
CHUNK_SIZE 10000
MAP ORDERS.* , TARGET ORDERS.*;

4) DDL handling and source catalog
Request:
{
  "replicatName": "REP_DDL",
  "trailName": "DD",
  "domainName": "OracleGoldenGate",
  "connectionName": "ggadmin",
  "source": {
    "schema": "APP",
    "table": "SCHEMAA.*",
    "targetTable": "APP.SCHEMAA.*"
  },
  "advanced": {
    "ddlError": "default discard",
    "repError": "(default, discard)",
    "ddlOptions": "REPORT",
    "sourceCatalog": "PDB1",
    "assumeTargetDefs": true
  }
}

5) OBEY file and additional parameters
Request:
{
  "replicatName": "REP_MOD",
  "trailName": "MD",
  "domainName": "OracleGoldenGate",
  "connectionName": "ggadmin",
  "mapStatement": "MAP hr.?TAB, TARGET hr.?TAB;",
  "advanced": {
    "obey": "common_settings.prm"
  }
}

Notes
- When `advanced.extTrail` is omitted, the tool uses `trailName` for the EXTTRAIL entry (legacy behavior).
- If `advanced.credential` is provided, its lines replace the default `USERIDALIAS` declaration (allowing USERID/PASSWORD syntax).
- The `source` object must include `targetTable` when using structured MAP; otherwise provide a raw `mapStatement`.
- `advanced.applyParallelism` cannot be combined with `advanced.minApplyParallelism` or `advanced.maxApplyParallelism`. Supplying both will result in an error prior to issuing the request.
- `advanced.modeType` / `advanced.modeParallel` allow controlling the Replicat `mode` object for REST calls. When omitted, the server defaults to classic (`nonintegrated`) mode with `parallel: false`.
- Replicat parameter files do not support `EXTTRAIL`, so the server no longer emits this line when creating or updating replicats. For parallel replicat (`modeType: 'parallel'`) the server also suppresses `MAP_PARALLELISM` since it is unsupported.
- See createExtract documentation for additional structured option handling patterns.
