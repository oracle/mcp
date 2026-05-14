# Copyright (c) 2025, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

'''MCP tool access profiles.

Profiles control which tools are exposed to AI assistants.
Three tiers (least → most privilege):

  - viewer  (default) — metadata browsing only, no execution.
  - analyst — read + query/execute (MDX, run_calculation, AV reads,
              insights). No create/delete/manage.
  - admin   — full surface. EXPLICIT OPT-IN ONLY.

Default is `viewer` for safety. Per the oracle/mcp BEST_PRACTICES
guidance on scope minimisation, admin access is never granted
implicitly.

Usage:
    oracle.data-studio-mcp-server                       # viewer (default)
    oracle.data-studio-mcp-server --profile analyst
    oracle.data-studio-mcp-server --profile admin       # explicit opt-in
    MCP_PROFILE=admin oracle.data-studio-mcp-server
    # or in ~/.oracle-data-studio/config:
    # [server]
    # profile = admin

Upleveled tool naming conventions:
    essbase_explore           — read-only server overview
    essbase_describe_database — read-only database profile
    essbase_query             — execute MDX query
    essbase_browse_outline    — read-only outline navigation
    essbase_search_members    — read-only member search
    essbase_run_calculation   — execute calc script
    essbase_load_data         — modify: load data
    essbase_deploy_workbook   — modify: import Excel
    essbase_manage_variables  — modify: CRUD variables
    essbase_get_script        — read-only script content
    essbase_manage_security   — read-only security report
    essbase_server_health     — read-only health check
    essbase_export_data       — execute: runs free-form MDX via the
                                grid endpoint (analyst+, NOT viewer)
    essbase_manage_application — modify: create/delete/copy/rename/start/stop
    essbase_manage_script     — modify: CRUD calc scripts
    essbase_manage_files      — modify: file catalog operations
    essbase_manage_connections — modify: CRUD connections
    essbase_manage_locks      — read/modify: list/unlock locks
    essbase_manage_filters    — modify: CRUD security filters
    essbase_manage_jobs       — read/modify: list/rerun/purge jobs
    essbase_edit_outline      — modify: add/remove/move/rename members
    essbase_manage_datasources — modify: CRUD datasources
    essbase_manage_drill_through — modify: CRUD drill-through reports
    essbase_manage_database   — modify: delete/copy/rename databases
    essbase_manage_users      — modify: CRUD users + role provisioning
    essbase_manage_groups     — modify: CRUD groups + membership
    essbase_manage_sessions   — read/modify: list/kill sessions
    essbase_manage_db_settings — read-only: detailed database settings
    essbase_get_logs          — read-only: application logs
    essbase_outline_metadata  — read-only: generations, levels, smart lists, settings
    adp_build_analytic_view   — modify: create AV
    adp_query_analytic_view   — read-only AV query
    adp_analyze_analytic_view — read-only AV analysis
    adp_generate_insights     — execute: generate insights
    adp_ai_chat               — execute: conversational AI
    adp_search                — read-only search
    adp_load_from_cloud       — modify: load data
    adp_browse_catalog        — read-only catalog browsing
    adp_manage_catalog        — modify: enable/disable/unmount catalogs
    adp_manage_sharing        — modify: sharing
    adp_manage_analytic_views — read/modify: list/drop AVs
    adp_manage_credentials    — modify: CRUD credentials + storage links
    adp_manage_insights       — read/modify: insight lifecycle
    adp_manage_db_links       — modify: database link operations
    adp_get_annotations       — read-only: Oracle 23ai annotations for NL→SQL
    dt_explore                — read-only overview
    dt_describe_project       — read-only project profile
    dt_manage_project         — modify: delete projects
    dt_describe_connection    — read-only connection profile
    dt_create_pipeline        — modify: create pipeline
    dt_check_health           — read-only health check
    dt_browse_data            — read-only data browsing
    dt_manage_dataflow        — modify: create/update dataflow
    dt_run_pipeline           — execute: run dataflow/workflow/dataload
    dt_manage_connection      — modify: CRUD connections
    dt_manage_dataload        — read: list/get dataloads
    dt_manage_data_entities   — read/modify: list/import data entities
    dt_manage_workflow        — read: list/get workflows
    dt_manage_schedule        — modify: schedule CRUD
    dt_manage_variables       — modify: variable CRUD
'''

import logging

logger = logging.getLogger('oracle-data-studio-mcp')

# ------------------------------------------------------------------ #
#  Profile definitions                                                #
# ------------------------------------------------------------------ #

PROFILES = {
    'viewer': {
        'description': 'Browse and view metadata, settings, data — '
                       'no modifications or execution',
        'allowed_verbs': frozenset({
            'explore', 'describe_', 'browse_', 'search_',
            'get_', 'explain_', 'analyze_', 'server_health',
            'check_health',
            # NOTE: 'export_' was removed deliberately. Although exports
            # look read-only by name, `essbase_export_data` accepts a
            # free-form MDX string and runs `ess.grid.execute_mdx(...)`,
            # which is execution. Viewer must not be able to run MDX.
            # If a future tool with verb 'export_*' is genuinely
            # read-only and safe for viewer, add it via `explicit_allow`.
        }),
        'explicit_allow': frozenset({
            'adp_query_analytic_view',
            'adp_search',
        }),
        'explicit_deny': frozenset({
            # Calc-script source code can contain business logic,
            # hardcoded values, datasource references — viewer must
            # not see content. (Analyst keeps it because they may
            # need to read a script they intend to run.)
            'essbase_get_script',
            # Server logs frequently contain SQL with PII, error
            # paths, sometimes credentials in error messages — admin
            # only.
            'essbase_get_logs',
        }),
    },
    'analyst': {
        'description': 'Read + query/execute — '
                       'no create/delete/modify/manage',
        'allowed_verbs': frozenset({
            # viewer verbs
            'explore', 'describe_', 'browse_', 'search_',
            'get_', 'explain_', 'analyze_', 'server_health',
            'check_health', 'export_',
            # analyst verbs (query + execute)
            'query', 'execute_', 'run_',
            'generate_', 'ai_',
        }),
        'explicit_allow': frozenset({
            'adp_query_analytic_view',
            'adp_search',
        }),
        'explicit_deny': frozenset({
            'adp_load_from_cloud',     # data loading is admin
            # Logs contain operational PII / SQL — admin only.
            'essbase_get_logs',
            # Pipelines mutate target tables (INSERT / TRUNCATE /
            # RECREATE) — analyst is "read + query/execute, no
            # modify" and pipelines write, so admin only.
            'dt_run_pipeline',
        }),
    },
    'admin': None,  # No filtering — all tools
}

VALID_PROFILES = tuple(PROFILES.keys())


# ------------------------------------------------------------------ #
#  Verb extraction                                                    #
# ------------------------------------------------------------------ #

# Service prefixes used in tool names: essbase_, adp_, dt_
_SERVICE_PREFIXES = ('essbase_', 'adp_', 'dt_')


def _get_verb_suffix(tool_name: str) -> str:
    '''Strip service prefix to get the verb portion of a tool name.

    Examples:
        essbase_explore           -> explore
        essbase_describe_database -> describe_database
        adp_execute_sql           -> execute_sql
        dt_manage_schedule        -> manage_schedule
    '''
    for prefix in _SERVICE_PREFIXES:
        if tool_name.startswith(prefix):
            return tool_name[len(prefix):]
    return tool_name


# ------------------------------------------------------------------ #
#  Public API                                                         #
# ------------------------------------------------------------------ #

def apply_profile(mcp_server, profile_name: str) -> None:
    '''Remove tools that don't match the selected profile.

    Must be called AFTER all register_tools() calls and BEFORE mcp.run().

    Args:
        mcp_server: The FastMCP server instance.
        profile_name: One of 'viewer', 'analyst', 'admin'.
    '''
    if profile_name == 'admin':
        total = len(mcp_server._tool_manager._tools)
        logger.info('Profile %r: all %d tools available', profile_name, total)
        return

    profile = PROFILES.get(profile_name)
    if profile is None:
        raise ValueError(
            f'Unknown profile: {profile_name!r}. '
            f'Valid profiles: {", ".join(VALID_PROFILES)}')

    allowed_verbs = profile['allowed_verbs']
    explicit_allow = profile.get('explicit_allow', frozenset())
    explicit_deny = profile.get('explicit_deny', frozenset())

    tools = mcp_server._tool_manager._tools
    to_remove = []

    for tool_name in list(tools.keys()):
        suffix = _get_verb_suffix(tool_name)

        # Explicit deny always wins
        if tool_name in explicit_deny:
            to_remove.append(tool_name)
        # Explicit allow always keeps
        elif tool_name in explicit_allow:
            continue
        # Verb prefix match — check if suffix starts with any allowed verb
        elif any(suffix.startswith(verb) for verb in allowed_verbs):
            continue
        # Exact match for single-word verbs (e.g. 'explore', 'query')
        elif suffix in allowed_verbs:
            continue
        # No match → remove
        else:
            to_remove.append(tool_name)

    for name in to_remove:
        del tools[name]

    logger.info('Profile %r: %d tools available (%d removed)',
                profile_name, len(tools), len(to_remove))
