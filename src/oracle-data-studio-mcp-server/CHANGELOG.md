# Changelog

## 1.0.0

Initial contribution.

### Features

- **60 high-level composite tools** spanning three Oracle Data Studio
  services:
  - **Essbase**: 30 tools — apps, databases, outline, MDX, calc scripts,
    files, security, jobs.
  - **ADP** (Autonomous Database Data Platform): 15 tools — Analytic
    Views, Select AI, Insights, cloud loading, catalogs, data sharing,
    annotations.
  - **Data Transforms**: 15 tools — pipelines, schedules, connections,
    workflows, dataloads.
- **Oracle 23ai annotation-aware query routing**.
  - New `adp_get_annotations` tool — composite reader of
    `ALL_ANNOTATIONS_USAGE` that groups results into table vs column
    annotations and returns a tidy structure for the LLM to consume.
  - New `adp_sql_with_annotations` prompt template — instructs the
    assistant to fetch annotations first, then construct SQL using
    them as semantic hints (units, aggregations, join keys, time
    grain, PII).
  - Server-level `instructions` advertise the annotation-first SQL
    flow and the cube/AV/table routing convention on MCP handshake;
    compliant clients (Claude Desktop, Cursor, Codex) forward them to
    the LLM as system context.
- **Three access profiles**: `viewer` (read-only), `analyst` (read +
  execute), `admin` (full access). Verb-based filtering applied at
  tool-registration time.

### Annotation-driven cube / AV / table routing

For aggregate questions, the LLM picks the correct query source by
reading routing annotations on the fact table:

| Annotation | Where | Meaning |
|---|---|---|
| `cube` | table | `'<app>.<database>'` Essbase cube reference |
| `analytic_view` | table | `'<av_name>'` ADP Analytic View reference |
| `preferred_source` | table | `'cube'` / `'analytic_view'` / `'table'` |
| `cube_dimension` | column | column → cube dim mapping |
| `cube_member` | column | column → MDX member |

### Validated against

Oracle Autonomous Database 23.26 with the MovieLens dataset and an
Essbase cube of the same name. A/B tested over 5 realistic SQL
generation scenarios (UNIT mismatch, GRAIN mismatch, AGGREGATE choice,
JOIN_HINT, PII avoidance) — annotation-aware SQL won 5/5, naive
generation won 0/5.
