# Copyright (c) 2025, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

'''
Oracle Data Studio MCP Server.

Creates a FastMCP server that exposes Essbase and ADP APIs as tools.
Connects to configured services on startup via the lifespan pattern.
'''

from __future__ import annotations

import sys
import logging
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from .config import load_config, ServerConfig
from .profiles import apply_profile
from .tools._helpers import wrap_mutating_tools_with_audit
from .http_runtime import (
    decide_bind,
    wrap_app_with_bearer_auth,
    InsecureBindRefused,
)

# Logging to stderr (required for stdio transport)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(name)s %(levelname)s %(message)s',
    stream=sys.stderr)
logger = logging.getLogger('oracle-data-studio-mcp')

# Module-level config — set by main() before server starts
_config: ServerConfig | None = None


@asynccontextmanager
async def app_lifespan(server: FastMCP):
    '''Connect to Essbase and/or ADP at startup, yield context dict.'''
    context: dict = {}

    # Stash the active profile so tools that need profile-aware behaviour
    # (e.g. connection metadata redaction) can read it without threading
    # the value through every signature. Default 'viewer' = least
    # privilege if config didn't run.
    context['_profile'] = (_config.profile
                           if _config is not None else 'viewer')
    # Select AI table allow / deny lists. Consumed by adp_ai_chat.
    context['_ai_chat_allowed_tables'] = (
        _config.ai_chat_allowed_tables if _config is not None else None)
    context['_ai_chat_denied_tables'] = (
        _config.ai_chat_denied_tables if _config is not None else None)

    # -- Essbase --
    if _config and _config.essbase:
        try:
            import essbase
            cfg = _config.essbase
            if cfg.token:
                ess = essbase.login_token(cfg.url, cfg.token)
                logger.info('Essbase connected (token) to %s', cfg.url)
            else:
                ess = essbase.login(cfg.url, cfg.user, cfg.password)
                logger.info('Essbase connected to %s as %s',
                            cfg.url, cfg.user)
            context['essbase'] = ess
        except Exception as e:
            logger.error('Essbase connection failed: %s', e)
    else:
        logger.warning(
            'Essbase not configured — set ESSBASE_URL + '
            'ESSBASE_USER/ESSBASE_PASSWORD or ESSBASE_TOKEN')

    # -- ADP --
    if _config and _config.adp:
        cfg = _config.adp
        context['_adp_config'] = cfg          # stored for auto-reconnect
        try:
            import adp
            adp_client = adp.login(cfg.url, cfg.user, cfg.password)
            logger.info('ADP connected to %s as %s', cfg.url, cfg.user)
            context['adp'] = adp_client
        except Exception as e:
            logger.error('ADP initial connection failed (will retry on '
                         'first tool call): %s', e)
    else:
        logger.info(
            'ADP not configured — set ADP_URL, ADP_USER, ADP_PASSWORD')

    # -- Data Transforms --
    # DT on ADBS is connected via adp.login()'s background thread which
    # discovers OCI params (tenancy, ADW OCID) from dba_pdbs and uses the
    # ADBS token flow.  We just store the config here for lazy retry;
    # the first DT tool call will pick up the workbench from ADP or
    # re-attempt the connection.
    if _config and _config.datatransforms:
        cfg = _config.datatransforms
        context['_dt_config'] = cfg
        logger.info('Data Transforms configured for %s — '
                     'connection deferred to first tool call', cfg.url)
    else:
        logger.info(
            'Data Transforms not configured — set DT_URL, DT_USER, DT_PASSWORD')

    yield context


# Server-level instructions. MCP clients forward these to the LLM as
# part of its system context, shaping behavior across every tool call.
# The goal: when querying a user-owned object, the LLM should first
# fetch Oracle 23ai annotations so it uses the right units, aggregates,
# join keys, and time grains — skipping this is the leading cause of
# wrong answers (e.g. unit-conversion errors returning 100× values).
SERVER_INSTRUCTIONS = """\
Oracle Data Studio MCP — usage guidelines:

ANNOTATION-FIRST SQL (ADP / Autonomous Database):
Before writing or running SQL against ANY user table or view, call
`adp_get_annotations(object_name=...)` to fetch its Oracle 23ai column
and table annotations. Annotations carry semantic metadata the LLM
cannot infer from column names alone:
  - DESCRIPTION / DISPLAY_NAME — confirm table/column meaning
  - UNIT — avoid unit mistakes (cents vs dollars, ms vs seconds, ...)
  - AGGREGATE — use the intended aggregation function (SUM, AVG, ...)
  - JOIN_HINT — prefer these keys when joining tables
  - ROLE / GRAIN — honor time granularity (DAY / MONTH / YEAR)
  - DATA_CLASS / PII — avoid PII columns unless explicitly requested

If `adp_get_annotations` returns `annotation_count: 0` (pre-23ai or
unannotated schema), fall back to `adp_search` with `include_ddl=True`.

For natural-language questions, use the `adp_sql_with_annotations`
prompt, then run the resulting SQL via the Oracle SQLcl MCP server.
This MCP server does not auto-execute LLM-generated SQL — that's by
design (annotations + your own LLM produces better results than
in-database NL→SQL, and execution belongs to SQLcl).

REPORT/AGGREGATE QUERY ROUTING (annotation-driven):
For aggregate / report-style questions ("total/sum/average X by Y",
"top N by …", "trend over time"), do NOT immediately run SQL against
the fact table. The DBA can DECLARE the right query source via
table-level annotations on the fact table. Routing convention:

  Table annotations:
    cube              — '<app>.<database>' Essbase cube ref
    analytic_view     — '<av_name>' ADP Analytic View ref
    preferred_source  — 'cube' | 'analytic_view' | 'table'

  Column annotations (optional, refine the query):
    cube_dimension    — '<dim_name>' (column → cube dim mapping)
    cube_member       — '[Measures].[Sales]' (column → MDX member)

Routing decision (call `adp_get_annotations(object_name=...)` first):
  1. If `preferred_source='cube'` AND `cube` is set → query via
     `essbase_query` against that app.database.
  2. Else if `preferred_source='analytic_view'` AND `analytic_view`
     is set → query via `adp_query_analytic_view`.
  3. Else if `cube` is set (no preference) → cube wins (faster).
  4. Else if `analytic_view` is set → AV.
  5. Else fall back to SQL via the Oracle SQLcl MCP server's
     `execute_sql`. The composite MCP intentionally does NOT expose
     raw `run_query` or auto-executed Select-AI SQL — arbitrary SQL
     belongs to SQLcl.

This is DETERMINISTIC — no name-matching or guessing. The data
engineer who built the cube/AV declares the mapping once on the
source table, and every MCP client (Claude, Cursor, Codex)
automatically routes correctly.

If no routing annotations exist, only THEN fall back to discovery:
  - `adp_manage_analytic_views(action='list')` — look for an AV
    whose fact_table matches.
  - `essbase_explore` — look for a cube with matching name/dims.
Going to the raw fact table directly for a report-style question
is both slower and silently loses business semantics.

BOUNDARY:
Pure SQL execution (arbitrary DDL/DML) is OUT OF SCOPE — use the
Oracle SQLcl MCP server for that. Tools here focus on data-platform
features: Analytic Views, Select AI, Insights, cloud loading,
catalogs, data sharing, and annotation-aware query support.

ESSBASE: use `essbase_query` (MDX), not ad-hoc SQL.
DATA TRANSFORMS: always test connection before running a pipeline.
"""

# Create server instance
mcp = FastMCP('oracle-data-studio',
              instructions=SERVER_INSTRUCTIONS,
              lifespan=app_lifespan)


# ------------------------------------------------------------------ #
#  Register all tool modules                                          #
# ------------------------------------------------------------------ #

from .tools import (  # noqa: E402
    essbase_tools,
    adp_tools,
    dt_tools,
)

_tool_modules = [
    essbase_tools,
    adp_tools,
    dt_tools,
]

for _mod in _tool_modules:
    _mod.register_tools(mcp)


# ------------------------------------------------------------------ #
#  Entry point                                                        #
# ------------------------------------------------------------------ #

def main():
    '''Parse config and start the MCP server.'''
    global _config
    _config = load_config()

    # Apply tool access profile (must be after tool registration)
    apply_profile(mcp, _config.profile)

    # Wire audit logging for every mutating / executing tool. The
    # wrapper emits a single INFO line on the 'oracle-data-studio-mcp.audit'
    # logger for every call so operators retain a who/what/when trail.
    n_audited = wrap_mutating_tools_with_audit(mcp, profile=_config.profile)
    logger.info('Audit logging wired for %d mutating tools', n_audited)

    logger.info('Starting Oracle Data Studio MCP server '
                '(transport=%s, profile=%s)',
                _config.transport, _config.profile)

    if _config.transport == 'streamable-http':
        # Fail-closed gate: non-loopback bind requires either an
        # MCP_AUTH_TOKEN (server enforces bearer auth) or an explicit
        # --allow-insecure-bind acknowledgement (operator confirms an
        # authenticated reverse proxy is in front). Default bind is
        # 127.0.0.1, which never trips the gate.
        try:
            decide_bind(
                _config.host,
                auth_token=_config.auth_token,
                allow_insecure_bind=_config.allow_insecure_bind)
        except InsecureBindRefused as e:
            logger.error('%s', e)
            sys.exit(2)

        mcp.settings.host = _config.host
        mcp.settings.port = _config.port

        if _config.auth_token:
            # Build the HTTP app ourselves, wrap with bearer-auth
            # middleware, and serve via uvicorn. Equivalent to what
            # FastMCP.run('streamable-http') does internally, but with
            # the middleware injected before tool dispatch.
            import uvicorn  # local import: not needed for stdio path
            app = wrap_app_with_bearer_auth(
                mcp.streamable_http_app(),
                _config.auth_token)
            logger.info(
                'streamable-http: bearer auth enforced on %s:%s',
                _config.host, _config.port)
            uvicorn.run(app, host=_config.host, port=_config.port,
                        log_level=mcp.settings.log_level.lower())
        else:
            mcp.run(transport='streamable-http')
    else:
        mcp.run(transport='stdio')
