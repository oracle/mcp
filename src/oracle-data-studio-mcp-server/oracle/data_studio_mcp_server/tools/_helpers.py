# Copyright (c) 2025, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

'''Shared helpers for upleveled MCP tools.'''

import json
import logging
import re
from typing import Optional

logger = logging.getLogger('oracle-data-studio-mcp')


# ────────────────────────────────────────────────────────────────────
#  Error sanitisation
# ────────────────────────────────────────────────────────────────────
# Oracle / cx_Oracle / ORDS exceptions routinely contain credentials,
# connect strings, OCIDs, file paths, and bearer tokens.  Returning
# them verbatim to the LLM (which then echoes them back to the user
# or downstream tools) is a quiet info-disclosure path.  Every tool
# that catches Exception should funnel the message through `safe_err`.

# Patterns we redact.  Each tuple is (regex, replacement). Order matters
# — earliest wins.  Patterns are case-insensitive where useful.
_REDACTORS = [
    # JDBC / SQL*Net DSN with embedded password:
    #   tcps://user/PASSWORD@host:port
    #   user/PASSWORD@//host:port/svc
    (re.compile(r'(?P<u>[\w.\-+]+)/[^/@\s\'"]+@'),
     r'\g<u>/***@'),
    # URL with userinfo: https://user:password@host
    (re.compile(r'(?P<scheme>\bhttps?://)[^/@\s:]+:[^/@\s]+@'),
     r'\g<scheme>***:***@'),
    # Authorization headers / Bearer tokens
    (re.compile(r'(?i)(authorization\s*[:=]\s*)(?:bearer|basic)\s+\S+'),
     r'\1***'),
    (re.compile(r'(?i)\bbearer\s+[A-Za-z0-9._\-]{8,}\b'),
     r'Bearer ***'),
    # OCI OCIDs — keep prefix for context, redact the random tail
    (re.compile(r'\bocid1\.([a-z]+)\.[a-z0-9.\-]*[a-z0-9]+'),
     r'ocid1.\1.***'),
    # password=... / pwd=...  (query strings, env-style, JSON)
    (re.compile(r'(?i)(["\']?(?:password|passwd|pwd)["\']?\s*[:=]\s*["\']?)'
                r'[^"\'\s,&}]+'),
     r'\1***'),
    # OS / wallet absolute paths — drop the prefix to keep the basename
    (re.compile(r'(?:/(?:Users|home|opt|var|tmp|u\d+)/[\w./\-]+/)'
                r'(?P<base>[\w.\-]+)'),
     r'<path>/\g<base>'),
    # Windows-style paths (C:\Users\...\file)
    (re.compile(r'(?i)\b[A-Z]:\\(?:Users|Documents and Settings)\\[\w\\.\-]+\\'
                r'(?P<base>[\w.\-]+)'),
     r'<path>\\\g<base>'),
]


def safe_err(exc, *, label: str = None) -> str:
    '''Sanitize an exception (or string) into an LLM-safe error message.

    Strips: embedded passwords (DSN/URL/JSON), Authorization headers,
    Bearer tokens, OCID tails, absolute filesystem paths.

    The full original message is logged at DEBUG so operators retain
    diagnostics without leaking them to the LLM client.

    Args:
        exc: Exception or any object str()-able.
        label: Optional prefix included in the returned message.
    '''
    raw = str(exc) if exc is not None else ''
    if label:
        logger.debug('%s failed: %s', label, raw)
    else:
        logger.debug('error: %s', raw)

    cleaned = raw
    for pattern, replacement in _REDACTORS:
        cleaned = pattern.sub(replacement, cleaned)

    # Cap length — Oracle stack traces can be huge; keep first 800 chars
    if len(cleaned) > 800:
        cleaned = cleaned[:800] + '… [truncated]'

    return f'{label}: {cleaned}' if label else cleaned


def safe_call(label, fn, *args, **kwargs):
    '''Call *fn* and return (result, None) or (None, error_string).

    Used by composite tools to gather partial results gracefully.
    Errors are funnelled through `safe_err` to strip credentials.
    '''
    try:
        return fn(*args, **kwargs), None
    except Exception as e:
        return None, safe_err(e, label=label)


def build_response(data, errors=None):
    '''Build a JSON response string with optional collected errors.'''
    if errors:
        data['_errors'] = errors
    return json.dumps(data, indent=2, default=str)


def err(msg):
    '''Return a JSON error string.

    The message is funnelled through `safe_err` to strip credentials,
    OCIDs, paths, and bearer tokens. Pass either a plain string or an
    Exception — both are sanitised.
    '''
    return json.dumps({'error': safe_err(msg)})


def fmt(result):
    '''Standard JSON formatting for SDK results.'''
    if result is None:
        return json.dumps({'status': 'success'})
    if isinstance(result, (dict, list)):
        return json.dumps(result, indent=2, default=str)
    return str(result)


# ────────────────────────────────────────────────────────────────────
#  Audit logging for mutating / destructive tools
# ────────────────────────────────────────────────────────────────────
# Every tool that creates, modifies, or deletes server state should
# call `audit(...)` once it has decided what to do. We emit a single
# structured INFO line so operators can answer "who/what/when" without
# enabling DEBUG on every component. The line is also useful for
# correlation when investigating an incident.
#
# Format (single line, key=value, value-quoted-if-spaces):
#   audit tool=<tool_name> action=<sub_action> target=<resource>
#         profile=<server profile> outcome=<ok|error>
#
# The values are funnelled through `safe_err` to strip any credential
# fragments before they hit the log stream.

_audit_logger = logging.getLogger('oracle-data-studio-mcp.audit')


def _audit_value(v) -> str:
    '''Stringify, redact, and shell-quote a single audit value.'''
    s = safe_err(v) if v is not None else ''
    # Cap each field at 200 chars so a long ORA-error doesn't blow up
    # the line.
    if len(s) > 200:
        s = s[:200] + '…'
    if ' ' in s or '"' in s or '=' in s:
        s = '"{0}"'.format(s.replace('"', '\\"'))
    return s


def audit(tool: str, *, action: str = None, target: str = None,
          profile: str = None, outcome: str = 'ok',
          **extra) -> None:
    '''Emit a single-line INFO audit record for a mutating tool call.

    Call this from inside any tool that creates / modifies / deletes
    state, right after the SDK call resolves (success or failure). The
    `outcome` defaults to 'ok'; pass 'error' from an except branch.

    Examples:
        audit('essbase_manage_application',
              action='delete', target=app_name, outcome='ok')

        audit('dt_run_pipeline',
              action='dataflow', target=name, outcome='error')

    Args are intentionally string-typed and small; do not pass entire
    response payloads here — emit a separate DEBUG log for those if
    you need the details.
    '''
    parts = ['audit', 'tool=' + tool]
    if action is not None:
        parts.append('action=' + _audit_value(action))
    if target is not None:
        parts.append('target=' + _audit_value(target))
    if profile is not None:
        parts.append('profile=' + _audit_value(profile))
    parts.append('outcome=' + _audit_value(outcome))
    for k, v in extra.items():
        parts.append('{0}={1}'.format(k, _audit_value(v)))
    _audit_logger.info(' '.join(parts))


# Tool-name prefixes that indicate a mutating / executing tool. Used by
# `wrap_mutating_tools_with_audit` to wire `audit()` calls in a single
# pass rather than touching ~40 individual tool function bodies. Add
# new mutating tool prefixes here; the wrapper picks them up.
_MUTATING_PREFIXES = (
    'essbase_manage_',
    'essbase_run_calculation',
    'essbase_load_data',
    'essbase_deploy_workbook',
    'essbase_edit_outline',
    'essbase_query',           # executes MDX
    'essbase_export_data',     # executes MDX via grid
    'adp_manage_',
    'adp_load_from_cloud',
    'adp_build_analytic_view',
    'adp_generate_insights',
    'adp_ai_chat',
    'dt_manage_',
    'dt_create_pipeline',
    'dt_run_pipeline',
)

# Argument-name candidates for the "target" field on the audit line.
# We pick the FIRST string kwarg in this order; the goal is a useful
# resource label, not a perfect identification.
_TARGET_KEYS = (
    'app_name', 'application', 'db_name', 'database',
    'name', 'username', 'user_id', 'group_name', 'group_id',
    'script_name', 'filter_name', 'connection_name', 'datasource_name',
    'project_name', 'dataflow_name', 'workflow_name', 'dataload_name',
    'schedule_name', 'variable_name', 'fact_table', 'object_name',
    'storage_link', 'credential_name', 'av_name', 'catalog_name',
    'report_name', 'session_id', 'recipient_name', 'share_name',
    'provider_name', 'table_name', 'view_name',
)


def is_mutating_tool(tool_name: str) -> bool:
    '''True if `tool_name` is in the mutating/executing set we audit.'''
    return any(tool_name.startswith(p) for p in _MUTATING_PREFIXES)


def wrap_mutating_tools_with_audit(mcp_server, profile: str = None) -> int:
    '''Wrap mutating/executing tools so they emit an `audit` log line.

    Idempotent: re-running on an already-wrapped server is a no-op
    (we set `__audited__ = True` on the wrapper).

    Order rule: call this AFTER `register_tools()` and EITHER before
    or after `apply_profile()` (profile filtering only deletes
    entries; wrapping survives).

    @param mcp_server: FastMCP server instance.
    @param profile: The active profile name; included in every emitted
        audit line. Pass `None` if unknown.
    @return: number of tools wrapped.
    '''
    tools = mcp_server._tool_manager._tools
    wrapped = 0
    for name, tool in list(tools.items()):
        if not is_mutating_tool(name):
            continue
        orig = tool.fn
        if getattr(orig, '__audited__', False):
            continue

        def _make_wrapper(orig_fn, tool_name):
            def _wrapped(*args, **kwargs):
                action = kwargs.get('action')
                target = None
                for key in _TARGET_KEYS:
                    val = kwargs.get(key)
                    if isinstance(val, str) and val:
                        target = val
                        break
                try:
                    result = orig_fn(*args, **kwargs)
                except Exception:
                    audit(tool_name, action=action, target=target,
                          profile=profile, outcome='error')
                    raise
                # Tools return JSON strings; treat {'error': ...} as failure
                outcome = 'ok'
                if isinstance(result, str):
                    try:
                        parsed = json.loads(result)
                        if isinstance(parsed, dict) and 'error' in parsed:
                            outcome = 'error'
                    except ValueError:
                        pass
                audit(tool_name, action=action, target=target,
                      profile=profile, outcome=outcome)
                return result
            _wrapped.__audited__ = True
            _wrapped.__wrapped__ = orig_fn
            _wrapped.__name__ = getattr(orig_fn, '__name__', tool_name)
            return _wrapped

        tool.fn = _make_wrapper(orig, name)
        wrapped += 1
    return wrapped


# ────────────────────────────────────────────────────────────────────
#  Output bounding for query-style tools
# ────────────────────────────────────────────────────────────────────
# MDX queries and AV reads can return arbitrarily large payloads.
# Returning all of them to the LLM is expensive (token cost, latency,
# context window), creates an info-disclosure surface (the LLM may
# repeat sensitive cell values in chat), and lets a single bad query
# DoS the conversation. Bound the result and surface a `truncated`
# flag the model can act on.

DEFAULT_MAX_ROWS = 1000


def _coerce_int_max_rows(max_rows, default: int = DEFAULT_MAX_ROWS) -> int:
    '''Normalise a user-supplied max_rows to a sane positive int.'''
    if max_rows is None:
        return default
    try:
        n = int(max_rows)
    except (TypeError, ValueError):
        return default
    if n <= 0:
        return default
    return n


def bound_mdx_result(result, max_rows=None) -> dict:
    '''Apply a row cap to an Essbase MDX response.

    The Essbase REST surface returns either an "axes + cells" shape
    or a "slice + ranges" shape; for both, we trim the row-axis tuples
    and corresponding cells/values so the returned payload is no
    larger than `max_rows`. A `truncated: true` flag is set on the
    response when the cap fires, along with the original row count
    so the LLM (and the operator) can see what was dropped.

    Returns a (possibly mutated) dict. Non-dict inputs (or shapes we
    don't recognise) pass through unchanged.
    '''
    cap = _coerce_int_max_rows(max_rows)
    if not isinstance(result, dict):
        return result

    # axes + cells shape
    axes = result.get('axes')
    if isinstance(axes, list) and len(axes) >= 2:
        row_axis = axes[1] if isinstance(axes[1], dict) else None
        if row_axis is None:
            return result
        tuples = row_axis.get('tuples')
        if not isinstance(tuples, list) or len(tuples) <= cap:
            return result
        total = len(tuples)
        n_cols = 0
        col_axis = axes[0] if isinstance(axes[0], dict) else None
        if col_axis and isinstance(col_axis.get('tuples'), list):
            n_cols = len(col_axis['tuples'])
        row_axis['tuples'] = tuples[:cap]
        # Trim the flat cell array. Cells are row-major: r*n_cols + c.
        cells = result.get('cells') or result.get('data')
        if isinstance(cells, list) and n_cols > 0:
            keep = cap * n_cols
            if 'cells' in result:
                result['cells'] = cells[:keep]
            else:
                result['data'] = cells[:keep]
        result['truncated'] = True
        result['original_row_count'] = total
        result['max_rows'] = cap
        return result

    # slice + ranges shape
    sl = result.get('slice')
    if isinstance(sl, dict):
        rows = sl.get('rows')
        if isinstance(rows, list) and len(rows) > cap:
            total = len(rows)
            n_cols = len(sl.get('columns', []) or [])
            sl['rows'] = rows[:cap]
            ranges = (sl.get('data') or {}).get('ranges')
            if isinstance(ranges, list) and ranges and n_cols > 0:
                values = ranges[0].get('values')
                if isinstance(values, list):
                    ranges[0]['values'] = values[:cap * n_cols]
            result['truncated'] = True
            result['original_row_count'] = total
            result['max_rows'] = cap
        return result

    return result


def bound_rows(rows, max_rows=None) -> dict:
    '''Apply a row cap to a list-of-dicts (or list-of-anything) result.

    Returns an envelope::

        {'rows': [...], 'truncated': bool,
         'original_row_count': N, 'max_rows': cap}

    Useful for SDK calls that return a bare list (ADP analytic-view
    reads, search results, ...).
    '''
    cap = _coerce_int_max_rows(max_rows)
    if not isinstance(rows, list):
        # Unknown shape — return unchanged in an envelope without truncation.
        return {'rows': rows, 'truncated': False, 'max_rows': cap}
    total = len(rows)
    if total <= cap:
        return {'rows': rows, 'truncated': False,
                'original_row_count': total, 'max_rows': cap}
    return {'rows': rows[:cap], 'truncated': True,
            'original_row_count': total, 'max_rows': cap}


# ────────────────────────────────────────────────────────────────────
#  Connection / metadata redaction by profile (LLM02)
# ────────────────────────────────────────────────────────────────────
# Connection-shaped SDK responses routinely embed sensitive platform
# details — JDBC URLs (sometimes with credentials), wallet paths,
# hostnames, usernames, OCI tenancy/compartment OCIDs. Returning those
# verbatim to the LLM is an info-disclosure path (LLM02 in the OWASP
# GenAI Top 10).
#
# `redact_connection_metadata` keeps only fields explicitly listed in
# the per-profile allow-set; everything else is dropped. This is
# deny-by-default — new SDK fields don't accidentally leak. Admin
# sees the raw response so operators can still debug.
#
# Profile rules (least-privilege ↑):
#   viewer   — name, type, status, description only
#   analyst  — + host, port, schema, serviceName, database (no auth)
#   admin    — raw

# Common identifier and type fields safe to surface even to viewer.
_REDACT_VIEWER_ALLOW = frozenset({
    'name', 'connectionName', 'connection_name',
    'type', 'connectionType', 'connection_type',
    'status', 'state', 'enabled',
    'description', 'globalId', 'global_id', 'id',
    'createdAt', 'created_at', 'updatedAt', 'updated_at',
})

# Analyst additionally sees the "where" of a connection (host, db,
# schema) but never the "how" (auth material). Hosts may still
# disclose internal network topology — that's the trade-off analysts
# accept when they pick this profile over viewer.
_REDACT_ANALYST_EXTRA = frozenset({
    'host', 'port', 'serviceName', 'service_name',
    'schema', 'schemaName', 'schema_name',
    'database', 'databaseName', 'database_name',
    'dataServerName', 'data_server_name',
})


def redact_connection_metadata(payload, profile: str = 'viewer'):
    '''Recursively keep only profile-safe fields from a connection-shaped payload.

    Accepts a dict (single connection), a list (collection), or any
    other shape (returned unchanged). Nested dicts/lists are walked.

    @param payload: SDK response object.
    @param profile: 'viewer', 'analyst', 'admin', or any other string
        (treated as 'viewer' — fail closed on unknown profiles).
    @return: A pruned copy of the payload safe for the given profile.
    '''
    if profile == 'admin':
        return payload
    if profile == 'analyst':
        allow = _REDACT_VIEWER_ALLOW | _REDACT_ANALYST_EXTRA
    else:
        # Treat unknown profile as viewer — least privilege.
        allow = _REDACT_VIEWER_ALLOW
    return _redact_walk(payload, allow)


def _redact_walk(node, allow):
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            if k in allow:
                out[k] = _redact_walk(v, allow)
        # Add a marker so the caller / LLM can see the response was
        # filtered. Skip if the dict is empty after filtering (avoid
        # noise on already-empty objects).
        if out:
            out['_redacted'] = True
        return out
    if isinstance(node, list):
        return [_redact_walk(item, allow) for item in node]
    # Scalars (or any other shape) pass through unchanged.
    return node


def get_profile(ctx) -> str:
    '''Return the active server profile from the lifespan context.

    Tools that need profile-aware behaviour call this rather than
    threading the profile through every signature. Defaults to
    'viewer' (least privilege) when missing — fail closed.
    '''
    try:
        return ctx.request_context.lifespan_context.get(
            '_profile', 'viewer')
    except AttributeError:
        return 'viewer'


# ────────────────────────────────────────────────────────────────────
#  adp_ai_chat table allow / deny policy (LLM01 / LLM06)
# ────────────────────────────────────────────────────────────────────
# `adp_ai_chat` is an NL→SQL surface backed by the database. Without
# operator-configured constraints, a prompt-injected LLM could pivot
# to sensitive tables (DBA_USERS, audit logs, application secrets).
# The policy is enforced before the SDK call so a denied table never
# reaches Select AI.

def _normalize_table_key(t: str) -> str:
    '''Strip whitespace + quotes; uppercase. Returns "" for empties.'''
    if not t:
        return ''
    return t.strip().strip('"').strip("'").upper()


def check_ai_chat_tables(tables_csv: Optional[str],
                          allowed: Optional[frozenset] = None,
                          denied: Optional[frozenset] = None) -> Optional[str]:
    '''Validate a comma-separated table list against allow / deny policy.

    Returns None if the call should proceed, otherwise a human-readable
    error message describing the policy violation. Both bare table
    names ("ORDERS") and qualified names ("SALES.ORDERS") are matched
    case-insensitively against both forms.

    @param tables_csv: The `tables` kwarg as supplied to the tool.
        May be None or empty for chat-mode requests with no table list.
    @param allowed: Optional allow-list. When set, every requested
        table must be in it. None = no allow-list constraint.
    @param denied: Optional deny-list. When set, no requested table
        may be in it. None = no deny-list constraint.
    '''
    # No constraints configured → nothing to check.
    if allowed is None and denied is None:
        return None

    # Parse requested tables.
    requested = []
    if tables_csv:
        for raw in tables_csv.split(','):
            key = _normalize_table_key(raw)
            if key:
                requested.append(key)

    # Allow-list set but no tables requested: caller must declare
    # tables explicitly so policy can be evaluated. This blocks the
    # "no tables = chat mode = unconstrained Select AI" hole.
    if allowed is not None and not requested:
        return ('adp_ai_chat: MCP_AI_CHAT_ALLOWED_TABLES is set but '
                'no `tables` were specified. List the tables your '
                'question targets so the table policy can be applied.')

    def _matches(name, policy):
        '''Return True if `name` is in `policy` either as-is or as
        its bare-name part / fully-qualified counterpart.'''
        if name in policy:
            return True
        # Compare bare name component
        bare = name.rsplit('.', 1)[-1]
        return bare in policy

    # Deny wins, always.
    if denied is not None:
        for t in requested:
            if _matches(t, denied):
                return ('adp_ai_chat: table {!r} is on the deny list '
                        '(MCP_AI_CHAT_DENIED_TABLES). Refusing the '
                        'request.'.format(t))

    # Allow-list mode: every requested table must match.
    if allowed is not None:
        for t in requested:
            if not _matches(t, allowed):
                return ('adp_ai_chat: table {!r} is not in the '
                        'allow list (MCP_AI_CHAT_ALLOWED_TABLES). '
                        'Refusing the request.'.format(t))
    return None


# ────────────────────────────────────────────────────────────────────
#  Destructive-action confirmation tokens (LLM06)
# ────────────────────────────────────────────────────────────────────
# Profile filtering and audit logging are necessary but not
# sufficient — an admin (or a prompt-injected LLM running as admin)
# can still issue "delete that application" against a real cube.
# `require_confirm` makes destructive actions require an explicit
# confirm token matching the target resource name. The token never
# travels server→LLM, so the LLM has to be told the resource name
# by the operator. This is OWASP LLM06 (excessive agency) mitigation.

def require_confirm(resource_name: str,
                    confirm: Optional[str],
                    *, action_label: str = 'this destructive action') -> Optional[str]:
    '''Validate a `confirm` token against a resource name.

    Returns None when the call may proceed, otherwise a human-readable
    error message describing what the caller must pass. Comparison is
    case-sensitive and exact — typos block the call. The error message
    is deliberately specific so the operator can tell the LLM the
    right token; the audit log will record both the attempt and the
    `outcome=error`.

    @param resource_name: The thing being mutated (app name, user id,
        session id, project name, …).
    @param confirm: The token the caller supplied. None / '' / wrong
        value → block.
    @param action_label: Human-readable phrase used in the error
        message — e.g. "delete application", "kill session".
    '''
    if confirm and confirm == resource_name:
        return None
    return (
        'Refusing {0}: pass confirm={1!r} to acknowledge. '
        'Confirmation tokens are required for irreversible actions.'
        .format(action_label, resource_name))


def ai_chat_envelope(result, *, mode: str, max_rows=None) -> dict:
    '''Wrap Select AI output in an "untrusted-output" envelope.

    Select AI responses interleave LLM-generated text with database
    query results. Neither piece is trustworthy from the perspective
    of downstream tool execution — the LLM can prompt-inject the
    next call, and the DB content can carry stale or attacker-
    controlled values. Tag the envelope so the calling client knows
    not to feed it back into another tool unchecked (OWASP LLM05).

    Rows are bounded if the result includes a list payload.
    '''
    envelope = {
        'source': 'select_ai',
        'mode': mode,
        'untrusted': True,
    }
    # If result is a list, bound it. If a dict carrying a list, bound
    # the inner list. Otherwise pass through.
    if isinstance(result, list):
        envelope.update(bound_rows(result, max_rows=max_rows))
        return envelope
    if isinstance(result, dict):
        # Common shapes: {'rows': [...], ...} or {'data': [...], ...}
        for key in ('rows', 'data', 'items'):
            if isinstance(result.get(key), list):
                bounded = bound_rows(result[key], max_rows=max_rows)
                new = dict(result)
                new[key] = bounded.get('rows', new[key])
                for k in ('truncated', 'original_row_count', 'max_rows'):
                    if k in bounded:
                        new[k] = bounded[k]
                envelope['result'] = new
                return envelope
        envelope['result'] = result
        return envelope
    envelope['result'] = result
    return envelope
