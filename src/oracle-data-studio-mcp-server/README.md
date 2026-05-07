# Oracle Data Studio MCP Server

## Overview

This server provides task-oriented MCP tools for three Oracle Data
Studio services:

- **Oracle Essbase** — applications, databases, outline, MDX, calc
  scripts, files, security, jobs.
- **ADP** (Autonomous Database Data Platform) — Analytic Views,
  Select AI, Insights, cloud loading, catalogs, data sharing, **Oracle
  23ai annotations**.
- **Data Transforms** — pipelines, schedules, connections, workflows,
  dataloads.

Built on [FastMCP](https://github.com/jlowin/fastmcp) and the
[oracle-data-studio](https://pypi.org/project/oracle-data-studio/)
Python SDK. Each tool combines multiple SDK calls into a single
coherent operation that returns LLM-ready output, rather than exposing
raw REST endpoints.

**60 high-level tools + 1 reusable prompt template.**

## Running the server

### STDIO transport mode

```sh
uvx oracle.data-studio-mcp-server
```

### MCP client configuration (Claude Desktop, Cursor, Codex, …)

```json
{
  "mcpServers": {
    "oracle-data-studio": {
      "command": "uvx",
      "args": ["oracle.data-studio-mcp-server", "--profile", "admin"]
    }
  }
}
```

## Authentication

Connection details and credentials are read from (in order of priority):

1. CLI args / environment variables
2. OS keyring (recommended for desktop use)
3. INI file at `~/.oracle-data-studio/config`

Configure once with the bundled CLI:

```sh
uvx oracle.data-studio-config set adp \
    --url 'https://<adb-host>.adb.<region>.oraclecloudapps.com' \
    --user ADMIN
# prompts for password, stores in OS keyring

uvx oracle.data-studio-config set essbase --url 'https://<essbase>' --user admin
uvx oracle.data-studio-config set datatransforms --url 'https://<adb-host>...' --user ADMIN
```

Or pass credentials inline via env:

```sh
ADP_URL='...'      ADP_USER='ADMIN'  ADP_PASSWORD='...'  \
ESSBASE_URL='...'  ESSBASE_USER='admin'  ESSBASE_PASSWORD='...'  \
uvx oracle.data-studio-mcp-server
```

Only the services you configure are activated; the others are simply
not registered.

## Annotation-driven query routing

For aggregate questions ("total sales by region last quarter"), the
LLM picks the correct query source by reading routing annotations
defined on the fact table — **declaratively**, with no name-matching
or guessing.

### The routing convention

| Annotation | Where | Meaning |
|---|---|---|
| `cube` | table | `'<app>.<database>'` Essbase cube reference |
| `analytic_view` | table | `'<av_name>'` ADP Analytic View reference |
| `preferred_source` | table | `'cube'` / `'analytic_view'` / `'table'` |
| `cube_dimension` | column | column → cube dim mapping |
| `cube_member` | column | column → MDX member, e.g. `'[Measures].[Sales]'` |

### Example DDL

```sql
CREATE TABLE MOVIELENS.RATINGS (
    USER_ID  NUMBER  ANNOTATIONS (join_hint 'MOVIELENS.USERS.USER_ID'),
    MOVIE_ID NUMBER  ANNOTATIONS (join_hint 'MOVIELENS.MOVIES.MOVIE_ID'),
    RATING   NUMBER  ANNOTATIONS (unit 'STARS_1_TO_5',
                                  aggregate 'AVG',
                                  cube_member '[Measures].[Rating]'),
    RATED_AT DATE    ANNOTATIONS (role 'TIME', grain 'DAY')
)
ANNOTATIONS (
    cube              'MOVIELENS.MOVIELENS',
    preferred_source  'cube',
    description       'MovieLens 1M ratings (also exposed as Essbase cube)'
);
```

After this DDL, any compliant MCP client connecting to the server
automatically routes a natural-language question against `RATINGS` to
the Essbase cube — without per-client tuning. The mechanism is the
server's `instructions`, which every MCP client passes to its LLM at
handshake time.

### Why it matters

A/B tested on Oracle 23.26 with MovieLens, the annotation-aware flow
beat naive SQL generation **5/5** across realistic failure modes:
unit mismatch (cents vs dollars), grain mismatch (hourly vs daily
aggregation), aggregate-function choice (`SUM` vs `AVG` for snapshot
metrics), join key (which FK to use), and PII avoidance.

## Tools

### Essbase (30)

| Tool | What it does |
| --- | --- |
| `essbase_explore` | Full server overview — apps, databases, status, sizes, settings |
| `essbase_describe_database` | Complete database profile — dimensions, storage, settings, variables |
| `essbase_query` | Execute MDX with formatted tabular output |
| `essbase_browse_outline` | Hierarchical outline tree with member properties |
| `essbase_search_members` | Member search with full paths and ancestors |
| `essbase_run_calculation` | Execute calc + wait + return final status / log on failure |
| `essbase_load_data` | End-to-end data load (upload + run + monitor) |
| `essbase_deploy_workbook` | Excel workbook → cube (one-shot import) |
| `essbase_manage_variables` | Variables CRUD across server / app / db scopes |
| `essbase_get_script` | Script content + validation status |
| `essbase_manage_security` | Full security profile: roles, app roles, filters, groups |
| `essbase_server_health` | Version, sessions, locked objects |
| `essbase_export_data` | MDX or level-0 export with job + download |
| `essbase_manage_application` | Application lifecycle: create / copy / rename / delete / start / stop |
| `essbase_manage_script` | Script CRUD + validation |
| `essbase_manage_files` | File catalog: list, upload, download, move, copy, extract, create_folder |
| `essbase_manage_connections` | Saved connections lifecycle and tests |
| `essbase_manage_locks` | Locked objects / blocks |
| `essbase_manage_filters` | Security filters CRUD with permissions |
| `essbase_manage_jobs` | Jobs: list, status, statistics, rerun, purge |
| `essbase_edit_outline` | Batch outline edits — add / remove / move / rename / formulas / aliases / UDAs |
| `essbase_manage_datasources` | Datasources lifecycle |
| `essbase_manage_drill_through` | Drill-through reports lifecycle and execution |
| `essbase_manage_database` | Database lifecycle: create / copy / rename / delete / start / stop |
| `essbase_manage_users` | Users CRUD + role provisioning |
| `essbase_manage_groups` | Groups CRUD + membership |
| `essbase_manage_sessions` | Session inspection and termination |
| `essbase_manage_db_settings` | Database settings reader/writer |
| `essbase_get_logs` | Log retrieval |
| `essbase_outline_metadata` | Outline metadata: generations, levels, smart lists, settings, member |

### ADP (Autonomous Database Data Platform) — 15

| Tool | What it does |
| --- | --- |
| `adp_build_analytic_view` | Auto-create AV from fact table → compile → return metadata + preview |
| `adp_query_analytic_view` | Query AV with auto-discovered dimensions and measures |
| `adp_analyze_analytic_view` | AV health report: metadata, measures, dimensions, quality, errors |
| `adp_manage_analytic_views` | List or drop AVs |
| `adp_ai_chat` | Conversational Select AI: chat / chat_with_db / generate_insight |
| `adp_generate_insights` | Async insight generation with full graph data |
| `adp_manage_insights` | Insight lifecycle: requests, results, status, drop |
| `adp_search` | Global object search; optionally include DDL for top hits |
| **`adp_get_annotations`** | **Fetch Oracle 23ai column/table annotations — drives the annotation-first SQL flow** |
| `adp_load_from_cloud` | End-to-end cloud → table load with progress polling |
| `adp_manage_db_links` | DB links + copy/link tables from remote databases |
| `adp_manage_credentials` | Cloud credentials + storage links |
| `adp_browse_catalog` | Read-only catalog browse (list, entities, preview, db_links) |
| `adp_manage_catalog` | Admin catalog ops: enable / disable / unmount / mount variants |
| `adp_manage_sharing` | Data sharing: shares, recipients, providers, publish/unpublish |

> **Boundary**: arbitrary SQL execution (DDL / DML / `SELECT *`) is
> intentionally OUT of scope. For raw SQL, pair this server with the
> Oracle SQLcl MCP server.

### Data Transforms (15)

| Tool | What it does |
| --- | --- |
| `dt_explore` | Environment overview — version, connections, projects, schedules |
| `dt_describe_project` | Complete project inventory: dataflows, workflows, dataloads |
| `dt_manage_project` | Admin project ops: delete |
| `dt_describe_connection` | Connection details + test + available schemas |
| `dt_create_pipeline` | Create dataflow / workflow (auto-creates project if needed) |
| `dt_check_health` | Connection health + schedule overview |
| `dt_browse_data` | Available schemas and tables with column metadata |
| `dt_manage_dataflow` | Dataflow CRUD + validate (idempotent) |
| `dt_manage_workflow` | Workflow CRUD |
| `dt_manage_schedule` | Schedule CRUD |
| `dt_manage_variables` | Variables CRUD |
| `dt_run_pipeline` | Execute dataflow / workflow / dataload via runtime client |
| `dt_manage_connection` | Connection CRUD + test |
| `dt_manage_dataload` | Dataload CRUD |
| `dt_manage_data_entities` | Data entity discovery and import |

### Prompts

| Prompt | What it does |
| --- | --- |
| `adp_sql_with_annotations` | Annotation-aware SQL generation template — instructs the assistant to fetch `adp_get_annotations` first, then build SQL using `unit`, `aggregate`, `join_hint`, `grain`, `data_class` as semantic hints |

## Access profiles

Every tool is filtered by access profile at registration time.
Pick one with `--profile`:

| Profile | Capability | Tool count |
| --- | --- | --- |
| `viewer` | Read-only — explore, describe, browse, search | ~17 |
| `analyst` | Read + query / execute — no create / delete / manage | ~23 |
| `admin` (default) | All tools | 60 |

## Local development

```sh
git clone https://github.com/oracle/mcp.git
cd mcp/src/oracle-data-studio-mcp-server
uv sync --all-extras
uv run pytest oracle/data_studio_mcp_server/tests/test_unit.py
```

86 tests, runs in ~1 second.

## Third-Party APIs

Developers choosing to distribute a binary implementation of this
project are responsible for obtaining and providing all required
licenses and copyright notices for the third-party code used in order
to ensure compliance with their respective open source licenses.

## Disclaimer

Users are responsible for their local environment and credential
safety. Different language model selections may yield different
results and performance.

## License

Copyright (c) 2025 Oracle and/or its affiliates.

Released under the Universal Permissive License v1.0 as shown at
<https://oss.oracle.com/licenses/upl/>.
