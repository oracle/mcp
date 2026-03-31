createExtract tool: structured options for TABLE clause

Overview
- Goal: allow clients to pass a typed payload describing the TABLE clause instead of a single free-form string.
- Backward compatible: existing tableStatement string is still supported. If provided, it is normalized and used as-is. If not provided, the server builds the TABLE clause from source and options.

What changed
- New builder module: src/tableStatement.ts
  - buildTableStatement(params) constructs a GoldenGate TABLE statement with all supported options.
  - normalizeTableStatement(stmt) ensures a raw statement starts with TABLE and ends with ;.
- Server update (src/server.ts): createExtract tool now accepts either:
  - tableStatement: string (raw passthrough), or
  - source: object and options: object (structured form)
- Validation and assembly
  - Mutual exclusivity enforced for option pairs: cols vs colsExcept, def vs targetDef, fetchCols vs fetchColsExcept, fetchModCols vs fetchModColsExcept.
  - getBeforeCols accepts "ALL" or a non-empty array.
  - partitionObjIds must be positive integers.
  - Booleans trimSpaces and trimVarSpaces are tri-state: undefined emits nothing, true emits TRIM…, false emits NOTRIM….
  - EXITPARAM and SQLPREDICATE parameters are safely single-quoted (with internal quotes doubled). TOKENS values are also single-quoted and escaped.

Input shape (abridged)
- Required:
  - extractName: string (<= 8 alphanumeric by OG rules)
  - trailName: string (2 alphanumeric by OG rules)
  - domainName: string
  - connectionName: string
- Either:
  - tableStatement: string (raw, e.g., "TABLE HR.EMPLOYEES, COLS (EMPLOYEE_ID);")
  - or:
    - source: object
      - container?: string
      - schema: string
      - table: string
      - partitionObjIds?: number[]
      - targetTable?: string
    - options?: object
      - attrCharset?: string
      - charset?: string
      - colCharset?: string
      - colMap?: string
      - cols?: string[]
      - colsExcept?: string[]
      - def?: string
      - targetDef?: string
      - eventActions?: string
      - exitParam?: string
      - fetchCols?: string[]
      - fetchColsExcept?: string[]
      - fetchModCols?: string[]
      - fetchModColsExcept?: string[]
      - fetchBeforeFilter?: boolean
      - filter?: string
      - getBeforeCols?: "ALL" | string[]
      - keyCols?: string[]
      - sqlExec?: string
      - sqlPredicate?: string  // emits SQLPREDICATE 'WHERE {clause}'
      - tokens?: Record<string, string>
      - trimSpaces?: boolean   // true -> TRIMSPACES; false -> NOTRIMSPACES
      - trimVarSpaces?: boolean // true -> TRIMVARSPACES; false -> NOTRIMVARSPACES
      - where?: string
    - advanced?: object (new)
      - disableHeartbeatTable?: boolean
      - tranlogOptions?: string | string[] | {
          clauses?: string[]
          integratedParams?: string | string[] | {
            entries?: string[]
            keyValues?: Record<string, string | number | boolean>
          }
          additional?: string[]
        }
      - reportCount?: {
          every?: string | { value: number; unit: "SECONDS" | "MINUTES" | "HOURS" }
          records?: number
          rate?: boolean
          additional?: string[]
        }
      - boundedRecovery?: {
          interval?: string
          dir?: string
          additional?: string[]
        }
      - dbOptions?: string | string[] | {
          entries?: string[]
          additional?: string[]
        }
      - extTrail?: string  // overrides trailName when provided
      - sourceCatalog?: string
      - ddl?: string | string[]  // emits one DDL line per entry
      - additionalParameters?: string[]

Mapping to GoldenGate syntax (stable emission order)
- TABLE [container.]schema.table [PARTITIONOBJID id, ...]
- , TARGET target_table
- , ATTRCHARSET (value)
- , CHARSET value
- , COLCHARSET value
- , COLMAP (value)
- , COLS (c1, c2, ...)
- , COLSEXCEPT (c1, c2, ...)
- , DEF template
- , TARGETDEF template
- , EVENTACTIONS value
- , EXITPARAM 'parameter'
- , FETCHCOLS (c1, c2, ...)
- , FETCHCOLSEXCEPT (c1, c2, ...)
- , FETCHMODCOLS (c1, c2, ...)
- , FETCHMODCOLSEXCEPT (c1, c2, ...)
- , FETCHBEFOREFILTER
- , FILTER (clause)
- , GETBEFORECOLS (ALL | c1, c2, ...)
- , KEYCOLS (c1, c2, ...)
- , SQLEXEC (spec)
- , SQLPREDICATE 'WHERE where_clause'
- , TOKENS (NAME1='v1', NAME2='v2', ...)
- , TRIMSPACES | NOTRIMSPACES
- , TRIMVARSPACES | NOTRIMVARSPACES
- , WHERE (clause)
- ;

Examples

1) Backward-compatible raw statement
Request:
{
  "extractName": "EXT1",
  "trailName": "AZ",
  "domainName": "OracleGoldenGate",
  "connectionName": "SRC_CONN",
  "tableStatement": "TABLE HR.EMPLOYEES, COLS (EMPLOYEE_ID, LAST_NAME)"
}
Normalized/used as:
TABLE HR.EMPLOYEES, COLS (EMPLOYEE_ID, LAST_NAME);

2) Minimal structured
Request:
{
  "extractName": "EXT2",
  "trailName": "TR",
  "domainName": "OracleGoldenGate",
  "connectionName": "SRC_CONN",
  "source": { "schema": "HR", "table": "EMPLOYEES" }
}
Builds:
TABLE HR.EMPLOYEES;

3) Advanced parameters example
Request:
{
  "extractName": "EXTADV",
  "trailName": "H1",
  "domainName": "OracleGoldenGate",
  "connectionName": "SRC_CONN",
  "source": { "schema": "HR", "table": "EMPLOYEES" },
  "advanced": {
    "disableHeartbeatTable": true,
    "extTrail": "./dirdat/h1",
    "tranlogOptions": {
      "clauses": ["DBLOGREADER"],
      "integratedParams": {
        "entries": ["parallelism 4"],
        "keyValues": { "max_sga": 1024 }
      }
    },
    "reportCount": {
      "every": { "value": 10, "unit": "MINUTES" },
      "rate": true
    },
    "boundedRecovery": { "interval": "30MIN" },
    "dbOptions": ["FETCHBATCHSIZE 5000", "FETCHCHECKFREQ 10"],
    "sourceCatalog": "PDB1",
    "ddl": ["INCLUDE MAPPED"],
    "additionalParameters": ["DYNAMICRESOLUTION"]
  }
}
Builds:
EXTRACT EXTADV
EXTTRAIL ./dirdat/h1
USERIDALIAS SRC_CONN DOMAIN OracleGoldenGate
DISABLE_HEARTBEAT_TABLE
TRANLOGOPTIONS DBLOGREADER INTEGRATEDPARAMS (parallelism 4, max_sga 1024)
REPORTCOUNT EVERY 10 MINUTES, RATE
BR BRINTERVAL 30MIN
DBOPTIONS FETCHBATCHSIZE 5000, FETCHCHECKFREQ 10
SOURCECATALOG PDB1
DDL INCLUDE MAPPED
DYNAMICRESOLUTION
TABLE HR.EMPLOYEES;

4) With container and PARTITIONOBJID and TARGET
Request:
{
  "extractName": "EXT3",
  "trailName": "TR",
  "domainName": "OracleGoldenGate",
  "connectionName": "SRC_CONN",
  "source": {
    "container": "PDB1",
    "schema": "SALES",
    "table": "ORDERS",
    "partitionObjIds": [101, 202],
    "targetTable": "ARCH.ORDERS"
  }
}
Builds:
TABLE PDB1.SALES.ORDERS PARTITIONOBJID 101, 202, TARGET ARCH.ORDERS;

5) Column include/exclude and filters
Request:
{
  "extractName": "EXT4",
  "trailName": "TR",
  "domainName": "OracleGoldenGate",
  "connectionName": "SRC_CONN",
  "source": { "schema": "HR", "table": "EMPLOYEES" },
  "options": {
    "colsExcept": ["SENSITIVE_DATA"],
    "filter": "SALARY > 0",
    "where": "DEPARTMENT_ID IN (10, 20)"
  }
}
Builds:
TABLE HR.EMPLOYEES, COLSEXCEPT (SENSITIVE_DATA), FILTER (SALARY > 0), WHERE (DEPARTMENT_ID IN (10, 20));

6) Fetch options and GETBEFORECOLS
Request:
{
  "extractName": "EXT5",
  "trailName": "TR",
  "domainName": "OracleGoldenGate",
  "connectionName": "SRC_CONN",
  "source": { "schema": "HR", "table": "EMPLOYEES" },
  "options": {
    "fetchCols": ["EMPLOYEE_ID", "STATUS"],
    "fetchModColsExcept": ["LAST_UPDATE_TS"],
    "fetchBeforeFilter": true,
    "getBeforeCols": "ALL"
  }
}
Builds:
TABLE HR.EMPLOYEES, FETCHCOLS (EMPLOYEE_ID, STATUS), FETCHMODCOLSEXCEPT (LAST_UPDATE_TS), FETCHBEFOREFILTER, GETBEFORECOLS (ALL);

7) Templates and TOKENS with safe quoting
Request:
{
  "extractName": "EXT6",
  "trailName": "TR",
  "domainName": "OracleGoldenGate",
  "connectionName": "SRC_CONN",
  "source": { "schema": "HR", "table": "EMPLOYEES" },
  "options": {
    "def": "EMPDEF",
    "tokens": { "ENV": "PROD", "APP": "ERP'suite" },
    "exitParam": "terminate on error"
  }
}
Builds:
TABLE HR.EMPLOYEES, DEF EMPDEF, TOKENS (APP='ERP''suite', ENV='PROD'), EXITPARAM 'terminate on error';

8) SQLPREDICATE
Request:
{
  "extractName": "EXT7",
  "trailName": "TR",
  "domainName": "OracleGoldenGate",
  "connectionName": "SRC_CONN",
  "source": { "schema": "SALES", "table": "ORDERS" },
  "options": {
    "sqlPredicate": "AMOUNT > 0 AND STATUS = 'OPEN'"
  }
}
Builds:
TABLE SALES.ORDERS, SQLPREDICATE 'WHERE AMOUNT > 0 AND STATUS = ''OPEN''';

Validation behavior
- Mutual exclusivity errors:
  - cols and colsExcept cannot both be provided.
  - def and targetDef cannot both be provided.
  - fetchCols and fetchColsExcept cannot both be provided.
  - fetchModCols and fetchModColsExcept cannot both be provided.
- getBeforeCols must be "ALL" or a non-empty array.
- partitionObjIds must be positive integers.
- trimSpaces and trimVarSpaces:
  - true -> TRIMSPACES/TRIMVARSPACES
  - false -> NOTRIMSPACES/NOTRIMVARSPACES
  - omit -> no emission.
- EXITPARAM and SQLPREDICATE and TOKENS values are single-quoted with internal quotes doubled.

Notes
- PARTITIONOBJID is appended immediately after the table identifier: "schema.table PARTITIONOBJID ...", not as a comma-separated option later.
- Raw expressions (colMap, filter, sqlExec, where, eventActions) are passed through as-is into their expected parentheses/positions. The server does not parse or rewrite those expressions.
- The server normalizes a raw tableStatement by ensuring a TABLE prefix and trailing semicolon.

Change summary for maintainers
- src/tableStatement.ts: new module with types and builder.
- src/server.ts: createExtract input schema extended; handler now builds statement when tableStatement is omitted; imports builder utilities.
- No REST path changes (src/api.ts untouched for this feature).
