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
from contextlib import ExitStack, asynccontextmanager
from functools import partial

from fastmcp import FastMCP
from starlette.middleware import Middleware

from .config import load_config, ServerConfig
from .tools import adp_tools, dt_tools, essbase_tools
from .http_runtime import (
    decide_bind,
    make_bearer_middleware,
    InsecureBindRefused,
)

# Logging to stderr (required for stdio transport)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(name)s %(levelname)s %(message)s',
    stream=sys.stderr)
logger = logging.getLogger('oracle-data-studio-mcp')


@asynccontextmanager
async def app_lifespan(_server: FastMCP, *, config: ServerConfig):
    '''Connect to the configured services and release their HTTP sessions.'''
    with ExitStack() as cleanup:
        owned_sessions: set[int] = set()

        def register_session(session):
            session_id = id(session)
            if session_id not in owned_sessions:
                cleanup.callback(session.close)
                owned_sessions.add(session_id)

        context = {
            '_register_session': register_session,
            '_profile': config.profile,
            '_ai_chat_allowed_tables': config.ai_chat_allowed_tables,
            '_ai_chat_denied_tables': config.ai_chat_denied_tables,
        }

        # -- Essbase --
        if config.essbase:
            try:
                import essbase
                cfg = config.essbase
                if cfg.token:
                    ess = essbase.login_token(cfg.url, cfg.token)
                    logger.info('Essbase connected (token) to %s', cfg.url)
                else:
                    ess = essbase.login(cfg.url, cfg.user, cfg.password)
                    logger.info('Essbase connected to %s as %s',
                                cfg.url, cfg.user)
                register_session(ess.get_client().session)
                context['essbase'] = ess
            except Exception as e:
                logger.error('Essbase connection failed: %s', e)
        else:
            logger.warning(
                'Essbase not configured — set ESSBASE_URL + '
                'ESSBASE_USER/ESSBASE_PASSWORD or ESSBASE_TOKEN')

        # -- ADP --
        if config.adp:
            cfg = config.adp
            context['_adp_config'] = cfg          # stored for auto-reconnect
            try:
                import adp
                adp_client = adp.login(cfg.url, cfg.user, cfg.password)
                register_session(adp_client.rest.session)
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
        if config.datatransforms:
            cfg = config.datatransforms
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

def create_server(config: ServerConfig) -> FastMCP:
    mcp = FastMCP(
        'oracle-data-studio',
        instructions=SERVER_INSTRUCTIONS,
        lifespan=partial(app_lifespan, config=config),
    )
    for module in (essbase_tools, adp_tools, dt_tools):
        module.register_tools(mcp, profile=config.profile)
    return mcp


def main():
    '''Parse config and start the MCP server.'''
    config = load_config()
    mcp = create_server(config)
    logger.info('Starting Oracle Data Studio MCP server '
                '(transport=%s, profile=%s)',
                config.transport, config.profile)

    if config.transport == 'streamable-http':
        try:
            decide_bind(
                config.host,
                auth_token=config.auth_token,
                allow_insecure_bind=config.allow_insecure_bind)
        except InsecureBindRefused as e:
            logger.error('%s', e)
            sys.exit(2)

        middleware = None
        if config.auth_token:
            middleware = [Middleware(make_bearer_middleware(config.auth_token))]
            logger.info(
                'streamable-http: bearer auth enforced on %s:%s',
                config.host, config.port)
        mcp.run(transport='streamable-http', host=config.host, port=config.port,
                path='/mcp', middleware=middleware, show_banner=False)
    else:
        mcp.run(transport='stdio', show_banner=False)
