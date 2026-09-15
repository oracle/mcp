# Copyright (c) 2025, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

'''Upleveled Essbase MCP tools.

Each tool combines multiple SDK calls into a single task-oriented
operation that returns an LLM-friendly result.  See TOOLS_DESIGN.md.
'''

import json
import logging

from mcp.server.fastmcp import FastMCP, Context

from ._essbase_connect import get_essbase
from ._helpers import safe_call, build_response, err, fmt

logger = logging.getLogger('oracle-data-studio-mcp')

_NO = 'Essbase not connected. Set ESSBASE_URL + credentials.'


def register_tools(mcp: FastMCP):

    # ── 1. essbase_explore ────────────────────────────────────────────
    @mcp.tool()
    def essbase_explore(ctx: Context) -> str:
        """Get a full overview of the Essbase server: applications, their databases, status, sizes, and settings.

        Combines list_applications + list_databases + get_statistics + get_settings per app.
        This is the starting point for any Essbase task.
        """
        ess = get_essbase(ctx)
        if not ess:
            return err(_NO)
        try:
            apps_data = ess.applications.list_applications()
            apps = apps_data.get('items', [])
            errors = []
            result = []
            for app in apps:
                name = app.get('name', '')
                entry = {'application': app}

                dbs, e = safe_call(f'{name}/databases',
                                   ess.applications.list_databases, name)
                if dbs:
                    entry['databases'] = dbs.get('items', dbs)
                if e:
                    errors.append(e)

                stats, e = safe_call(f'{name}/statistics',
                                     ess.applications.get_statistics, name)
                if stats:
                    entry['statistics'] = stats
                if e:
                    errors.append(e)

                settings, e = safe_call(f'{name}/settings',
                                        ess.applications.get_settings, name)
                if settings:
                    entry['settings'] = settings
                if e:
                    errors.append(e)

                result.append(entry)

            return build_response(
                {'applications': result, 'count': len(result)},
                errors or None)
        except Exception as exc:
            return err(str(exc))

    # ── 2. essbase_describe_database ──────────────────────────────────
    @mcp.tool()
    def essbase_describe_database(app_name: str, db_name: str,
                                  ctx: Context) -> str:
        """Get a complete database profile: dimensions with member counts, storage type (BSO/ASO), settings, statistics, and substitution variables.

        Args:
            app_name: Application name.
            db_name: Database (cube) name.
        """
        ess = get_essbase(ctx)
        if not ess:
            return err(_NO)
        try:
            errors = []
            data = {}

            db, e = safe_call('database',
                              ess.applications.get_database,
                              app_name, db_name)
            if db:
                data['database'] = db
            if e:
                errors.append(e)

            dims, e = safe_call('dimensions',
                                ess.dimensions.list_dimensions,
                                app_name, db_name)
            if dims:
                data['dimensions'] = dims.get('items', dims)
            if e:
                errors.append(e)

            settings, e = safe_call('settings',
                                    ess.database_settings.get_settings,
                                    app_name, db_name)
            if settings:
                data['settings'] = settings
            if e:
                errors.append(e)

            stats, e = safe_call('statistics',
                                 ess.database_settings.get_statistics,
                                 app_name, db_name)
            if stats:
                data['statistics'] = stats
            if e:
                errors.append(e)

            storage, e = safe_call('storage',
                                   ess.database_settings.get_storage_statistics,
                                   app_name, db_name)
            if storage:
                data['storage'] = storage
            if e:
                errors.append(e)

            vars_data, e = safe_call('variables',
                                     ess.variables.list_db_variables,
                                     app_name, db_name)
            if vars_data:
                data['variables'] = vars_data.get('items', vars_data)
            if e:
                errors.append(e)

            return build_response(data, errors or None)
        except Exception as exc:
            return err(str(exc))

    # ── 3. essbase_query ──────────────────────────────────────────────
    @mcp.tool()
    def essbase_query(app_name: str, db_name: str, mdx: str,
                      max_rows: int = 1000,
                      ctx: Context = None) -> str:
        """Execute an MDX query and return formatted tabular results.

        Results are capped at `max_rows` (default 1000). When the cap
        fires, `truncated: true`, `original_row_count`, and `max_rows`
        are added to the response so the caller can decide whether to
        re-query with a tighter WHERE clause.

        Args:
            app_name: Application name.
            db_name: Database (cube) name.
            mdx: MDX query string.
            max_rows: Maximum row-axis tuples to return. Default 1000.
                Hard floor 1; values ≤0 fall back to the default.
        """
        from ._helpers import bound_mdx_result
        ess = get_essbase(ctx)
        if not ess:
            return err(_NO)
        try:
            result = ess.grid.execute_mdx(app_name, db_name, mdx)
            result = bound_mdx_result(result, max_rows=max_rows)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            return err(str(exc))

    # ── 4. essbase_browse_outline ─────────────────────────────────────
    @mcp.tool()
    def essbase_browse_outline(app_name: str, db_name: str,
                                parent: str = None, depth: int = 2,
                                ctx: Context = None) -> str:
        """Browse the cube outline hierarchy.

        Without a parent, returns top-level dimensions.
        With a parent, returns children recursively up to *depth* levels.

        Args:
            app_name: Application name.
            db_name: Database (cube) name.
            parent: Parent member name (omit for top-level dimensions).
            depth: How many levels deep to recurse (default 2, max 5).
        """
        ess = get_essbase(ctx)
        if not ess:
            return err(_NO)
        try:
            depth = min(depth, 5)
            if parent is None:
                outline = ess.dimensions.get_outline(app_name, db_name)
                return json.dumps(outline, indent=2, default=str)

            def _get_tree(par, lvl):
                if lvl <= 0:
                    return None
                children_data = ess.dimensions.get_children(
                    app_name, db_name, par, limit=200)
                items = children_data.get('items',
                            children_data.get('data', []))
                for item in items:
                    name = item.get('name', item.get('memberName', ''))
                    if name and lvl > 1:
                        sub = _get_tree(name, lvl - 1)
                        if sub:
                            item['children'] = sub
                return items

            tree = _get_tree(parent, depth)
            return json.dumps({'parent': parent, 'members': tree},
                              indent=2, default=str)
        except Exception as exc:
            return err(str(exc))

    # ── 5. essbase_search_members ─────────────────────────────────────
    @mcp.tool()
    def essbase_search_members(app_name: str, db_name: str,
                                pattern: str, ctx: Context) -> str:
        """Search for members in the cube outline and return matches with their properties and ancestors.

        Args:
            app_name: Application name.
            db_name: Database (cube) name.
            pattern: Search keyword or pattern.
        """
        ess = get_essbase(ctx)
        if not ess:
            return err(_NO)
        try:
            hits = ess.dimensions.search_members(
                app_name, db_name, pattern, limit=50)
            items = hits.get('items', hits.get('data', []))
            errors = []
            enriched = []
            for item in items:
                name = item.get('name', item.get('memberName', ''))
                if name:
                    ancestors, e = safe_call(
                        f'ancestors/{name}',
                        ess.dimensions.get_member_ancestors,
                        app_name, db_name, name)
                    if ancestors:
                        item['ancestors'] = ancestors
                    if e:
                        errors.append(e)
                enriched.append(item)
            return build_response(
                {'matches': enriched, 'count': len(enriched)},
                errors or None)
        except Exception as exc:
            return err(str(exc))

    # ── 6. essbase_run_calculation ────────────────────────────────────
    @mcp.tool()
    def essbase_run_calculation(app_name: str, db_name: str,
                                 script_name: str = None,
                                 calc_script: str = None,
                                 ctx: Context = None) -> str:
        """Run a calculation on an Essbase database — fire-and-forget with automatic wait.

        Provide either a saved script name OR inline calc script text.
        Automatically waits for completion and returns the final status.
        On failure, includes the relevant log excerpt.

        Args:
            app_name: Application name.
            db_name: Database (cube) name.
            script_name: Name of a saved calc script (e.g. 'CalcAll').
            calc_script: Inline calc script text (e.g. 'CALC ALL;').
        """
        ess = get_essbase(ctx)
        if not ess:
            return err(_NO)
        if not script_name and not calc_script:
            return err('Provide either script_name or calc_script.')
        try:
            payload = {
                'jobtype': 'calc',
                'application': app_name,
                'db': db_name,
                'parameters': {}
            }
            if script_name:
                payload['parameters']['file'] = script_name
            else:
                payload['parameters']['script'] = calc_script

            job = ess.jobs.execute(payload)
            job_id = job.get('id', job.get('jobID'))
            result = ess.jobs.wait_for_completion(job_id)

            # On failure, try to get the log
            if result.get('statusCode') == 400:
                log, _ = safe_call('log',
                                   ess.applications.get_latest_log,
                                   app_name)
                if log:
                    if isinstance(log, bytes):
                        log = log.decode('utf-8', errors='replace')
                    # Return last 2000 chars of log
                    result['log_excerpt'] = log[-2000:]

            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            return err(str(exc))

    # ── 7. essbase_load_data ──────────────────────────────────────────
    @mcp.tool()
    def essbase_load_data(app_name: str, db_name: str,
                           rule_file: str = None,
                           data_file: str = None,
                           ctx: Context = None) -> str:
        """Load data into an Essbase database.

        Executes a dataload job and waits for completion.

        Args:
            app_name: Application name.
            db_name: Database (cube) name.
            rule_file: Rules file name (optional).
            data_file: Data file name (optional).
        """
        ess = get_essbase(ctx)
        if not ess:
            return err(_NO)
        try:
            payload = {
                'jobtype': 'dataload',
                'application': app_name,
                'db': db_name,
                'parameters': {}
            }
            if rule_file:
                payload['parameters']['rule'] = rule_file
            if data_file:
                payload['parameters']['file'] = data_file

            job = ess.jobs.execute(payload)
            job_id = job.get('id', job.get('jobID'))
            result = ess.jobs.wait_for_completion(job_id)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            return err(str(exc))

    # ── 8. essbase_deploy_workbook ────────────────────────────────────
    @mcp.tool()
    def essbase_deploy_workbook(app_name: str, file_path: str,
                                 ctx: Context) -> str:
        """Import an Excel workbook to create or update an Essbase cube.

        Uploads the file if needed, then runs an importExcel job and
        waits for completion.  Returns the created application/database info.

        Args:
            app_name: Application name to create or update.
            file_path: Server-side file path to the Excel workbook.
        """
        ess = get_essbase(ctx)
        if not ess:
            return err(_NO)
        try:
            payload = {
                'jobtype': 'importExcel',
                'application': app_name,
                'parameters': {
                    'file': file_path
                }
            }
            job = ess.jobs.execute(payload)
            job_id = job.get('id', job.get('jobID'))
            result = ess.jobs.wait_for_completion(job_id)

            # If success, get the created app info
            if result.get('statusCode') in (200, 300):
                app_info, _ = safe_call('app_info',
                                        ess.applications.get_application,
                                        app_name)
                if app_info:
                    result['application'] = app_info

            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            return err(str(exc))

    # ── 9. essbase_manage_variables ───────────────────────────────────
    @mcp.tool()
    def essbase_manage_variables(action: str, scope: str,
                                  app_name: str = None,
                                  db_name: str = None,
                                  variable_name: str = None,
                                  value: str = None,
                                  confirm: str = None,
                                  ctx: Context = None) -> str:
        """Manage Essbase substitution variables at any scope.

        Destructive actions (`delete`) require `confirm` to match
        `variable_name` exactly — guards against prompt-injected
        deletions.

        Args:
            action: One of 'list', 'get', 'set', 'delete'.
            scope: One of 'server', 'application', 'database'.
            app_name: Application name (required for app/db scope).
            db_name: Database name (required for db scope).
            variable_name: Variable name (required for get/set/delete).
            value: Variable value (required for set).
            confirm: For delete: must equal `variable_name`.
        """
        from ._helpers import require_confirm
        ess = get_essbase(ctx)
        if not ess:
            return err(_NO)
        try:
            v = ess.variables
            if action == 'list':
                if scope == 'server':
                    return fmt(v.list_server_variables())
                elif scope == 'application':
                    return fmt(v.list_app_variables(app_name))
                else:
                    return fmt(v.list_db_variables(app_name, db_name))
            elif action == 'get':
                if scope == 'server':
                    return fmt(v.get_server_variable(variable_name))
                elif scope == 'application':
                    return fmt(v.get_app_variable(app_name, variable_name))
                else:
                    return fmt(v.get_db_variable(
                        app_name, db_name, variable_name))
            elif action == 'set':
                payload = {'name': variable_name, 'value': value}
                # Try update first, create on failure
                try:
                    if scope == 'server':
                        return fmt(v.update_server_variable(
                            variable_name, payload))
                    elif scope == 'application':
                        return fmt(v.update_app_variable(
                            app_name, variable_name, payload))
                    else:
                        return fmt(v.update_db_variable(
                            app_name, db_name, variable_name, payload))
                except Exception:
                    if scope == 'server':
                        return fmt(v.create_server_variable(payload))
                    elif scope == 'application':
                        return fmt(v.create_app_variable(app_name, payload))
                    else:
                        return fmt(v.create_db_variable(
                            app_name, db_name, payload))
            elif action == 'delete':
                if not variable_name:
                    return err('variable_name required for delete.')
                msg = require_confirm(variable_name, confirm,
                                       action_label='delete variable')
                if msg:
                    return err(msg)
                if scope == 'server':
                    v.delete_server_variable(variable_name)
                elif scope == 'application':
                    v.delete_app_variable(app_name, variable_name)
                else:
                    v.delete_db_variable(app_name, db_name, variable_name)
                return json.dumps({'status': 'deleted',
                                   'variable': variable_name})
            else:
                return err(f'Unknown action: {action}. '
                           f'Use list/get/set/delete.')
        except Exception as exc:
            return err(str(exc))

    # ── 10. essbase_get_script ────────────────────────────────────────
    @mcp.tool()
    def essbase_get_script(app_name: str, db_name: str,
                            script_name: str, ctx: Context) -> str:
        """Get a script's content along with its validation status.

        Args:
            app_name: Application name.
            db_name: Database (cube) name.
            script_name: Script name.
        """
        ess = get_essbase(ctx)
        if not ess:
            return err(_NO)
        try:
            errors = []
            data = {}
            content, e = safe_call('content',
                                   ess.scripts.get_script_content,
                                   app_name, db_name, script_name)
            if content is not None:
                data['content'] = content
            if e:
                errors.append(e)

            validation, e = safe_call(
                'validate',
                ess.scripts.validate_script,
                app_name, db_name,
                {'name': script_name})
            if validation:
                data['validation'] = validation
            if e:
                errors.append(e)

            return build_response(data, errors or None)
        except Exception as exc:
            return err(str(exc))

    # ── 11. essbase_manage_security ───────────────────────────────────
    @mcp.tool()
    def essbase_manage_security(username: str = None,
                                 group_name: str = None,
                                 ctx: Context = None) -> str:
        """Get the complete security profile for a user or group.

        Returns service roles, application roles, filters, and group memberships.
        Provide either username OR group_name.

        Args:
            username: User to look up (provide this or group_name).
            group_name: Group to look up (provide this or username).
        """
        ess = get_essbase(ctx)
        if not ess:
            return err(_NO)
        if not username and not group_name:
            return err('Provide either username or group_name.')
        try:
            errors = []
            data = {}
            if username:
                user, e = safe_call('user', ess.users.get_user, username)
                if user:
                    data['user'] = user
                if e:
                    errors.append(e)

                prov, e = safe_call(
                    'provisioning',
                    ess.users.get_user_provisioning_report, username)
                if prov:
                    data['provisioning'] = prov
                if e:
                    errors.append(e)
            else:
                group, e = safe_call('group', ess.groups.get_group,
                                     group_name)
                if group:
                    data['group'] = group
                if e:
                    errors.append(e)

                prov, e = safe_call(
                    'provisioning',
                    ess.groups.get_group_provisioning_report,
                    group_name)
                if prov:
                    data['provisioning'] = prov
                if e:
                    errors.append(e)

                members, e = safe_call(
                    'members',
                    ess.groups.get_group_members, group_name)
                if members:
                    data['members'] = members
                if e:
                    errors.append(e)

            return build_response(data, errors or None)
        except Exception as exc:
            return err(str(exc))

    # ── 12. essbase_server_health ─────────────────────────────────────
    @mcp.tool()
    def essbase_server_health(ctx: Context) -> str:
        """Quick Essbase server health check: version, instance config, active sessions, locked objects.
        """
        ess = get_essbase(ctx)
        if not ess:
            return err(_NO)
        try:
            errors = []
            data = {}

            about, e = safe_call('about', ess.about.get)
            if about:
                data['about'] = about
            if e:
                errors.append(e)

            instance, e = safe_call('instance', ess.about.get_instance)
            if instance:
                data['instance'] = instance
            if e:
                errors.append(e)

            sessions, e = safe_call('sessions',
                                    ess.sessions.list_sessions)
            if sessions:
                if isinstance(sessions, list):
                    data['active_sessions'] = len(sessions)
                    data['sessions'] = sessions
                else:
                    data['sessions'] = sessions
            if e:
                errors.append(e)

            return build_response(data, errors or None)
        except Exception as exc:
            return err(str(exc))

    # ── 13. essbase_export_data ───────────────────────────────────────
    @mcp.tool()
    def essbase_export_data(app_name: str, db_name: str,
                             mdx: str = None,
                             report_name: str = None,
                             max_rows: int = 1000,
                             ctx: Context = None) -> str:
        """Export data from an Essbase database.

        Provide either an MDX query or a saved report name. Results
        are row-capped at `max_rows` (default 1000); when the cap
        fires, `truncated: true` and `original_row_count` are added
        to the response.

        Args:
            app_name: Application name.
            db_name: Database (cube) name.
            mdx: MDX query string.
            report_name: Name of a saved MDX report.
            max_rows: Maximum row-axis tuples to return (default 1000).
        """
        from ._helpers import bound_mdx_result
        ess = get_essbase(ctx)
        if not ess:
            return err(_NO)
        try:
            if mdx:
                result = ess.grid.execute_mdx(app_name, db_name, mdx)
            elif report_name:
                result = ess.grid.execute_mdx_report(
                    app_name, db_name, report_name)
            else:
                # Default: get the default grid
                result = ess.grid.get_default_grid(app_name, db_name)
            result = bound_mdx_result(result, max_rows=max_rows)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            return err(str(exc))

    # ── 14. essbase_manage_application ─────────────────────────────────
    @mcp.tool()
    def essbase_manage_application(action: str, app_name: str,
                                    db_name: str = None,
                                    db_type: str = 'BSO',
                                    new_name: str = None,
                                    confirm: str = None,
                                    ctx: Context = None) -> str:
        """Create, delete, copy, rename, start, or stop an Essbase application.

        Destructive actions (`delete`, `rename`) require `confirm` to
        match `app_name` exactly — guards against prompt-injected
        deletions.

        Args:
            action: One of 'create', 'delete', 'copy', 'rename', 'start', 'stop'.
            app_name: Application name (for all actions).
            db_name: Database name (required for create — creates the app with this initial database).
            db_type: Database type for create: 'BSO' (block storage, default) or 'ASO' (aggregate storage).
            new_name: New name for copy or rename actions.
            confirm: For destructive actions only: must equal `app_name`.
        """
        from ._helpers import require_confirm
        ess = get_essbase(ctx)
        if not ess:
            return err(_NO)
        try:
            a = ess.applications
            if action == 'create':
                if not db_name:
                    return err('db_name required for create.')
                result = a.create_application({
                    'applicationName': app_name,
                    'databaseName': db_name,
                    'databaseType': db_type,
                })
                return fmt(result)
            elif action == 'delete':
                msg = require_confirm(app_name, confirm,
                                       action_label='delete application')
                if msg:
                    return err(msg)
                a.delete_application(app_name)
                return json.dumps({'status': 'deleted',
                                   'application': app_name})
            elif action == 'copy':
                if not new_name:
                    return err('new_name required for copy.')
                result = a.copy_application({
                    'from': app_name, 'to': new_name})
                return fmt(result)
            elif action == 'rename':
                if not new_name:
                    return err('new_name required for rename.')
                msg = require_confirm(app_name, confirm,
                                       action_label='rename application')
                if msg:
                    return err(msg)
                result = a.rename_application({
                    'oldAppName': app_name, 'newAppName': new_name})
                return fmt(result)
            elif action == 'start':
                a.update_application(app_name, {'status': 1})
                return json.dumps({'status': 'started',
                                   'application': app_name})
            elif action == 'stop':
                a.update_application(app_name, {'status': 0})
                return json.dumps({'status': 'stopped',
                                   'application': app_name})
            else:
                return err(f'Unknown action: {action}. '
                           f'Use create/delete/copy/rename/start/stop.')
        except Exception as exc:
            return err(str(exc))

    # ── 15. essbase_manage_script ──────────────────────────────────────
    @mcp.tool()
    def essbase_manage_script(action: str, app_name: str,
                               db_name: str,
                               script_name: str,
                               content: str = None,
                               new_name: str = None,
                               confirm: str = None,
                               ctx: Context = None) -> str:
        """Manage calc scripts: list, create, update, delete, or validate.

        Use 'create' to have the LLM write new calc scripts. Automatically
        validates after create/update.

        Args:
            action: One of 'list', 'create', 'update', 'delete', 'validate'.
            app_name: Application name.
            db_name: Database (cube) name.
            script_name: Script name (ignored for 'list').
            content: Calc script text (required for create/update, e.g. 'CALC ALL;').
            new_name: New name for rename (optional with 'update').
        """
        from ._helpers import require_confirm
        ess = get_essbase(ctx)
        if not ess:
            return err(_NO)
        try:
            s = ess.scripts
            if action == 'list':
                result = s.list_scripts(app_name, db_name)
                return fmt(result)

            elif action == 'create':
                if not content:
                    return err('content required for create.')
                result = s.create_script(app_name, db_name, {
                    'name': script_name, 'content': content})
                errors = []
                data = {'action': 'created', 'script': result}
                # Auto-validate
                val, e = safe_call('validate', s.validate_script,
                                   app_name, db_name,
                                   {'name': script_name})
                if val:
                    data['validation'] = val
                if e:
                    errors.append(e)
                return build_response(data, errors or None)

            elif action == 'update':
                payload = {'name': script_name, 'content': content}
                if new_name:
                    # Rename first, then update content
                    s.rename_script(app_name, db_name, {
                        'oldName': script_name, 'newName': new_name})
                    script_name = new_name
                    payload['name'] = new_name
                if content:
                    result = s.update_script(app_name, db_name,
                                             script_name, payload)
                    errors = []
                    data = {'action': 'updated', 'script': result}
                    val, e = safe_call('validate', s.validate_script,
                                       app_name, db_name,
                                       {'name': script_name})
                    if val:
                        data['validation'] = val
                    if e:
                        errors.append(e)
                    return build_response(data, errors or None)
                return json.dumps({'action': 'renamed',
                                   'old_name': script_name,
                                   'new_name': new_name})

            elif action == 'delete':
                msg = require_confirm(script_name, confirm,
                                       action_label='delete script')
                if msg:
                    return err(msg)
                s.delete_script(app_name, db_name, script_name)
                return json.dumps({'status': 'deleted',
                                   'script': script_name})

            elif action == 'validate':
                result = s.validate_script(app_name, db_name,
                                           {'name': script_name})
                return fmt(result)

            else:
                return err(f'Unknown action: {action}. '
                           f'Use list/create/update/delete/validate.')
        except Exception as exc:
            return err(str(exc))

    # ── 16. essbase_manage_files ───────────────────────────────────────
    @mcp.tool()
    def essbase_manage_files(action: str, path: str = None,
                              target_path: str = None,
                              content: str = None,
                              confirm: str = None,
                              ctx: Context = None) -> str:
        """Manage files in the Essbase file catalog: list, upload, download, copy, move, delete, create_folder.

        Paths use the catalog format: 'applications/Sample/Basic/data.csv',
        'shared/uploads/', etc.

        Args:
            action: One of 'list', 'download', 'upload', 'copy', 'move', 'delete', 'create_folder'.
            path: File or folder path in the catalog (e.g. 'applications/Sample').
            target_path: Destination path (required for copy/move).
            content: Text content to upload (required for upload, e.g. data file contents or rule file).
        """
        from ._helpers import require_confirm
        ess = get_essbase(ctx)
        if not ess:
            return err(_NO)
        try:
            f = ess.files
            if action == 'list':
                if path:
                    result = f.list_files(path)
                else:
                    result = f.list_root()
                return fmt(result)

            elif action == 'download':
                if not path:
                    return err('path required for download.')
                data = f.download(path)
                if isinstance(data, bytes):
                    # Return metadata about the download
                    return json.dumps({
                        'path': path,
                        'size_bytes': len(data),
                        'preview': data[:500].decode(
                            'utf-8', errors='replace')
                    })
                return fmt(data)

            elif action == 'copy':
                if not path or not target_path:
                    return err('path and target_path required for copy.')
                result = f.copy(path, target_path)
                return fmt(result)

            elif action == 'move':
                if not path or not target_path:
                    return err('path and target_path required for move.')
                result = f.move(path, target_path)
                return fmt(result)

            elif action == 'delete':
                msg = require_confirm(path, confirm,
                                       action_label='delete file')
                if msg:
                    return err(msg)
                if not path:
                    return err('path required for delete.')
                f.delete_file(path)
                return json.dumps({'status': 'deleted', 'path': path})

            elif action == 'upload':
                if not path:
                    return err('path required for upload.')
                if not content:
                    return err('content required for upload.')
                result = f.upload(path, content.encode('utf-8'))
                return fmt(result) if result else json.dumps(
                    {'status': 'uploaded', 'path': path})

            elif action == 'create_folder':
                if not path:
                    return err('path required for create_folder.')
                result = f.create_folder(path)
                return fmt(result) if result else json.dumps(
                    {'status': 'created', 'path': path})

            else:
                return err(f'Unknown action: {action}. '
                           f'Use list/download/upload/copy/move/delete/'
                           f'create_folder.')
        except Exception as exc:
            return err(str(exc))

    # ── 17. essbase_manage_connections ──────────────────────────────────
    @mcp.tool()
    def essbase_manage_connections(action: str,
                                    connection_name: str = None,
                                    host: str = None,
                                    port: int = None,
                                    service_name: str = None,
                                    user: str = None,
                                    password: str = None,
                                    db_type: str = 'oracle',
                                    confirm: str = None,
                                    ctx: Context = None) -> str:
        """Manage Essbase global connections: list, get, create, update, test, or delete.

        Connections define data sources for data loads, drill-through,
        and datasource operations.

        Args:
            action: One of 'list', 'get', 'create', 'update', 'test', 'delete'.
            connection_name: Connection name (required for get/create/update/test/delete).
            host: Database hostname (required for create).
            port: Database port (required for create, e.g. 1521).
            service_name: Database service name (required for create).
            user: Database username (required for create).
            password: Database password (required for create).
            db_type: Connection type: 'oracle' (default), 'sql_server', 'db2'.
        """
        from ._helpers import require_confirm
        ess = get_essbase(ctx)
        if not ess:
            return err(_NO)
        try:
            c = ess.connections
            if action == 'list':
                result = c.list_connections()
                return fmt(result)

            elif action == 'get':
                if not connection_name:
                    return err('connection_name required.')
                result = c.get_connection(connection_name)
                return fmt(result)

            elif action == 'create':
                if not all([connection_name, host, port, service_name,
                            user, password]):
                    return err('create requires: connection_name, host, '
                               'port, service_name, user, password.')
                payload = {
                    'name': connection_name,
                    'type': db_type,
                    'host': host,
                    'port': port,
                    'serviceName': service_name,
                    'user': user,
                    'password': password,
                }
                result = c.create_connection(payload)
                # Auto-test after create
                errors = []
                data = {'action': 'created', 'connection': result}
                test, e = safe_call('test', c.test_saved_connection,
                                    connection_name)
                if test:
                    data['test_result'] = test
                if e:
                    errors.append(e)
                return build_response(data, errors or None)

            elif action == 'test':
                if not connection_name:
                    return err('connection_name required.')
                result = c.test_saved_connection(connection_name)
                return fmt(result)

            elif action == 'update':
                if not connection_name:
                    return err('connection_name required for update.')
                if not any([host, port, service_name, user, password]):
                    return err('update requires at least one of: host, '
                               'port, service_name, user, password.')
                payload = {}
                if host:
                    payload['host'] = host
                if port:
                    payload['port'] = port
                if service_name:
                    payload['serviceName'] = service_name
                if user:
                    payload['user'] = user
                if password:
                    payload['password'] = password
                result = c.update_connection(connection_name, payload)
                return fmt(result)

            elif action == 'delete':
                msg = require_confirm(connection_name, confirm,
                                       action_label='delete connection')
                if msg:
                    return err(msg)
                if not connection_name:
                    return err('connection_name required.')
                c.delete_connection(connection_name)
                return json.dumps({'status': 'deleted',
                                   'connection': connection_name})

            else:
                return err(f'Unknown action: {action}. '
                           f'Use list/get/create/update/test/delete.')
        except Exception as exc:
            return err(str(exc))

    # ── 18. essbase_manage_locks ───────────────────────────────────────
    @mcp.tool()
    def essbase_manage_locks(app_name: str, db_name: str,
                              action: str = 'list',
                              object_name: str = None,
                              ctx: Context = None) -> str:
        """View and manage locks on an Essbase database.

        Lists all locks, locked objects, and locked data blocks.
        Can unlock a specific object to resolve blocked operations.

        Args:
            action: One of 'list' (default), 'unlock'.
            app_name: Application name.
            db_name: Database (cube) name.
            object_name: Object name to unlock (required for unlock).
        """
        ess = get_essbase(ctx)
        if not ess:
            return err(_NO)
        try:
            lk = ess.locks
            if action == 'list':
                errors = []
                data = {}

                locks, e = safe_call('locks', lk.list_locks,
                                     app_name, db_name)
                if locks:
                    data['locks'] = locks
                if e:
                    errors.append(e)

                objects, e = safe_call('locked_objects',
                                       lk.list_locked_objects,
                                       app_name, db_name)
                if objects:
                    data['locked_objects'] = objects
                if e:
                    errors.append(e)

                blocks, e = safe_call('locked_blocks',
                                      lk.list_locked_blocks,
                                      app_name, db_name)
                if blocks:
                    data['locked_blocks'] = blocks
                if e:
                    errors.append(e)

                return build_response(data, errors or None)

            elif action == 'unlock':
                if not object_name:
                    return err('object_name required for unlock.')
                result = lk.unlock_object(app_name, db_name,
                                          {'name': object_name})
                return fmt(result)

            else:
                return err(f'Unknown action: {action}. Use list/unlock.')
        except Exception as exc:
            return err(str(exc))

    # ── 19. essbase_manage_filters ─────────────────────────────────────
    @mcp.tool()
    def essbase_manage_filters(action: str, app_name: str,
                                db_name: str,
                                filter_name: str = None,
                                filter_rows: str = None,
                                user_or_group: str = None,
                                access: str = 'read',
                                new_name: str = None,
                                confirm: str = None,
                                ctx: Context = None) -> str:
        """Manage security filters for row-level access control on an Essbase database.

        Filters define which data intersections specific users or groups
        can read or write.

        Args:
            action: One of 'list', 'get', 'create', 'update', 'copy', 'rename', 'delete', 'assign'.
            app_name: Application name.
            db_name: Database (cube) name.
            filter_name: Filter name (required for get/create/update/copy/rename/delete/assign).
            filter_rows: Comma-separated filter row definitions for create/update. Each row is 'access_type, member_spec' (e.g. 'READ, @IDESCENDANTS(East); WRITE, @IDESCENDANTS(West)').
            user_or_group: User or group name to assign the filter to (required for assign).
            access: Access type for simple filter creation: 'read' (default), 'write', 'none', 'metaread'.
            new_name: New filter name (required for copy/rename).
        """
        from ._helpers import require_confirm
        ess = get_essbase(ctx)
        if not ess:
            return err(_NO)
        try:
            fl = ess.filters
            if action == 'list':
                result = fl.list_filters(app_name, db_name)
                return fmt(result)

            elif action == 'get':
                if not filter_name:
                    return err('filter_name required.')
                errors = []
                data = {}
                filt, e = safe_call('filter', fl.get_filter,
                                    app_name, db_name, filter_name)
                if filt:
                    data['filter'] = filt
                if e:
                    errors.append(e)
                rows, e = safe_call('rows', fl.get_filter_rows,
                                    app_name, db_name, filter_name)
                if rows:
                    data['rows'] = rows
                if e:
                    errors.append(e)
                perms, e = safe_call('permissions',
                                     fl.get_permissions,
                                     app_name, db_name, filter_name)
                if perms:
                    data['permissions'] = perms
                if e:
                    errors.append(e)
                return build_response(data, errors or None)

            elif action == 'create':
                if not filter_name:
                    return err('filter_name required for create.')
                # Build filter rows from the string
                rows = []
                if filter_rows:
                    for row_def in filter_rows.split(';'):
                        row_def = row_def.strip()
                        if ',' in row_def:
                            acc, member = row_def.split(',', 1)
                            rows.append({
                                'access': acc.strip().upper(),
                                'member': member.strip()
                            })
                if not rows:
                    rows = [{'access': access.upper(),
                             'member': '@ALL'}]
                payload = {'name': filter_name, 'rows': rows}
                result = fl.create_filter(app_name, db_name, payload)
                # Auto-validate
                errors = []
                data = {'action': 'created', 'filter': result}
                val, e = safe_call('validate', fl.validate_filter,
                                   app_name, db_name, payload)
                if val:
                    data['validation'] = val
                if e:
                    errors.append(e)
                return build_response(data, errors or None)

            elif action == 'update':
                if not filter_name:
                    return err('filter_name required for update.')
                if not filter_rows:
                    return err('filter_rows required for update.')
                rows_list = []
                for row_def in filter_rows.split(';'):
                    row_def = row_def.strip()
                    if ',' in row_def:
                        acc, member = row_def.split(',', 1)
                        rows_list.append({
                            'access': acc.strip().upper(),
                            'member': member.strip()
                        })
                result = fl.update_filter(
                    app_name, db_name, filter_name,
                    {'rows': rows_list})
                # Auto-validate after update
                errors = []
                data = {'action': 'updated', 'filter': result}
                val, e = safe_call('validate', fl.validate_filter,
                                   app_name, db_name,
                                   {'name': filter_name,
                                    'rows': rows_list})
                if val:
                    data['validation'] = val
                if e:
                    errors.append(e)
                return build_response(data, errors or None)

            elif action == 'copy':
                if not filter_name:
                    return err('filter_name required for copy.')
                if not new_name:
                    return err('new_name required for copy.')
                result = fl.copy_filter(
                    app_name, db_name,
                    {'from': filter_name, 'to': new_name})
                return fmt(result)

            elif action == 'rename':
                if not filter_name:
                    return err('filter_name required for rename.')
                if not new_name:
                    return err('new_name required for rename.')
                result = fl.rename_filter(
                    app_name, db_name,
                    {'oldName': filter_name, 'newName': new_name})
                return fmt(result)

            elif action == 'delete':
                msg = require_confirm(filter_name, confirm,
                                       action_label='delete filter')
                if msg:
                    return err(msg)
                if not filter_name:
                    return err('filter_name required for delete.')
                fl.delete_filter(app_name, db_name, filter_name)
                return json.dumps({'status': 'deleted',
                                   'filter': filter_name})

            elif action == 'assign':
                if not filter_name or not user_or_group:
                    return err('filter_name and user_or_group required '
                               'for assign.')
                result = fl.add_permissions(
                    app_name, db_name, filter_name,
                    {'userOrGroup': user_or_group})
                return fmt(result)

            else:
                return err(f'Unknown action: {action}. '
                           f'Use list/get/create/update/copy/rename/'
                           f'delete/assign.')
        except Exception as exc:
            return err(str(exc))

    # ── 20. essbase_manage_jobs ────────────────────────────────────────
    @mcp.tool()
    def essbase_manage_jobs(action: str = 'list',
                             job_id: int = None,
                             limit: int = 50,
                             confirm: str = None,
                             ctx: Context = None) -> str:
        """Monitor and manage Essbase jobs: list recent jobs, check status, or rerun a failed job.

        Status codes: 100=in progress, 200=completed, 300=completed with warnings, 400=failed.

        Args:
            action: One of 'list' (default), 'status', 'rerun', 'purge'.
            job_id: Job ID (required for status/rerun).
            limit: Maximum jobs to return for list (default 50).
        """
        from ._helpers import require_confirm
        ess = get_essbase(ctx)
        if not ess:
            return err(_NO)
        try:
            j = ess.jobs
            if action == 'list':
                result = j.list_jobs(limit=limit)
                return fmt(result)

            elif action == 'status':
                if not job_id:
                    return err('job_id required for status.')
                result = j.get_status(job_id)
                return fmt(result)

            elif action == 'rerun':
                if not job_id:
                    return err('job_id required for rerun.')
                result = j.rerun(job_id)
                new_id = result.get('id', result.get('jobID'))
                data = {'action': 'rerun', 'original_job': job_id,
                        'new_job': result}
                # Wait for the new job
                if new_id:
                    final = j.wait_for_completion(new_id)
                    data['final_status'] = final
                return json.dumps(data, indent=2, default=str)

            elif action == 'purge':
                msg = require_confirm('all', confirm,
                                       action_label='purge jobs')
                if msg:
                    return err(msg)
                j.purge()
                return json.dumps({'status': 'purged'})

            else:
                return err(f'Unknown action: {action}. '
                           f'Use list/status/rerun/purge.')
        except Exception as exc:
            return err(str(exc))

    # ── essbase_edit_outline ──────────────────────────────────────────
    @mcp.tool()
    def essbase_edit_outline(app_name: str, db_name: str,
                              action: str,
                              member_name: str,
                              parent_name: str = None,
                              new_name: str = None,
                              formula: str = None,
                              consolidation: str = None,
                              data_storage: str = None,
                              alias_table: str = 'Default',
                              alias_value: str = None,
                              uda_value: str = None,
                              confirm: str = None,
                              ctx: Context = None) -> str:
        """Edit the cube outline: add, remove, move, or rename members and set properties.

        Wraps Essbase Batch Outline Edit (BOE) into explicit parameters.
        Multiple edits can be chained by calling this tool repeatedly.

        Args:
            app_name: Application name.
            db_name: Database (cube) name.
            action: One of 'add', 'remove', 'move', 'rename', 'set_formula', 'set_alias', 'set_uda'.
            member_name: Member to act on (or new member name for 'add').
            parent_name: Parent member (required for 'add' and 'move').
            new_name: New name (required for 'rename').
            formula: Member formula (for 'set_formula', or optionally with 'add').
            consolidation: Consolidation operator: '+', '-', '*', '/', '~' (optional for 'add').
            data_storage: Storage type: 'storeData', 'dynamicCalc', 'dynamicCalcAndStore', 'neverShare', 'labelOnly', 'sharedMember' (optional for 'add').
            alias_table: Alias table name (default 'Default', used with 'set_alias' or 'add').
            alias_value: Alias value (for 'set_alias', or optionally with 'add').
            uda_value: User-Defined Attribute value (for 'set_uda').
        """
        from ._helpers import require_confirm
        ess = get_essbase(ctx)
        if not ess:
            return err(_NO)
        try:
            edit_actions = []

            if action == 'add':
                if not parent_name:
                    return err('parent_name required for add.')
                entry = {'actionType': 'addMember',
                         'parentName': parent_name,
                         'memberName': member_name}
                if consolidation:
                    entry['consolidation'] = consolidation
                if data_storage:
                    entry['dataStorage'] = data_storage
                edit_actions.append(entry)
                # Optionally set formula
                if formula:
                    edit_actions.append({
                        'actionType': 'setFormula',
                        'memberName': member_name,
                        'formula': formula})
                # Optionally set alias
                if alias_value:
                    edit_actions.append({
                        'actionType': 'setAlias',
                        'memberName': member_name,
                        'aliasTable': alias_table,
                        'alias': alias_value})

            elif action == 'remove':
                msg = require_confirm(member_name, confirm,
                                       action_label='remove outline member')
                if msg:
                    return err(msg)
                edit_actions.append({
                    'actionType': 'removeMember',
                    'memberName': member_name})

            elif action == 'move':
                if not parent_name:
                    return err('parent_name required for move.')
                edit_actions.append({
                    'actionType': 'moveMember',
                    'memberName': member_name,
                    'parentName': parent_name})

            elif action == 'rename':
                if not new_name:
                    return err('new_name required for rename.')
                edit_actions.append({
                    'actionType': 'renameMember',
                    'memberName': member_name,
                    'newName': new_name})

            elif action == 'set_formula':
                if formula is None:
                    return err('formula required for set_formula.')
                edit_actions.append({
                    'actionType': 'setFormula',
                    'memberName': member_name,
                    'formula': formula})

            elif action == 'set_alias':
                if not alias_value:
                    return err('alias_value required for set_alias.')
                edit_actions.append({
                    'actionType': 'setAlias',
                    'memberName': member_name,
                    'aliasTable': alias_table,
                    'alias': alias_value})

            elif action == 'set_uda':
                if not uda_value:
                    return err('uda_value required for set_uda.')
                edit_actions.append({
                    'actionType': 'setUDA',
                    'memberName': member_name,
                    'uda': uda_value})

            else:
                return err(f'Unknown action: {action}. '
                           f'Use add/remove/move/rename/'
                           f'set_formula/set_alias/set_uda.')

            payload = {'editActions': edit_actions}
            result = ess.dimensions.batch_outline_edit(
                app_name, db_name, payload)
            data = {'action': action, 'member': member_name,
                    'result': result}
            return json.dumps(data, indent=2, default=str)
        except Exception as exc:
            return err(str(exc))

    # ── essbase_manage_datasources ────────────────────────────────────
    @mcp.tool()
    def essbase_manage_datasources(action: str,
                                    datasource_name: str = None,
                                    connection: str = None,
                                    query: str = None,
                                    columns: str = None,
                                    confirm: str = None,
                                    ctx: Context = None) -> str:
        """Manage global datasources for data loads and drill-through.

        Args:
            action: One of 'list', 'get', 'create', 'update', 'delete'.
            datasource_name: Datasource name (required for get/create/update/delete).
            connection: Connection name to use (for create).
            query: SQL query for the datasource (for create).
            columns: Comma-separated column names (for create).
        """
        from ._helpers import require_confirm
        ess = get_essbase(ctx)
        if not ess:
            return err(_NO)
        try:
            ds = ess.datasources

            if action == 'list':
                return fmt(ds.list_datasources())

            elif action == 'get':
                if not datasource_name:
                    return err('datasource_name required for get.')
                return fmt(ds.get_datasource(datasource_name))

            elif action == 'create':
                if not datasource_name:
                    return err('datasource_name required for create.')
                if not connection:
                    return err('connection required for create.')
                payload = {
                    'name': datasource_name,
                    'connection': connection,
                }
                if query:
                    payload['query'] = query
                if columns:
                    payload['columns'] = [c.strip()
                                          for c in columns.split(',')]
                result = ds.create_datasource(payload)
                return fmt(result)

            elif action == 'update':
                if not datasource_name:
                    return err('datasource_name required for update.')
                payload = {}
                if connection:
                    payload['connection'] = connection
                if query:
                    payload['query'] = query
                if columns:
                    payload['columns'] = [c.strip()
                                          for c in columns.split(',')]
                result = ds.update_datasource(datasource_name, payload)
                return fmt(result)

            elif action == 'delete':
                msg = require_confirm(datasource_name, confirm,
                                       action_label='delete datasource')
                if msg:
                    return err(msg)
                if not datasource_name:
                    return err('datasource_name required for delete.')
                ds.delete_datasource(datasource_name)
                return json.dumps({'status': 'deleted',
                                   'datasource': datasource_name})

            else:
                return err(f'Unknown action: {action}. '
                           f'Use list/get/create/update/delete.')
        except Exception as exc:
            return err(str(exc))

    # ── essbase_manage_drill_through ──────────────────────────────────
    @mcp.tool()
    def essbase_manage_drill_through(action: str,
                                      app_name: str,
                                      db_name: str,
                                      report_name: str = None,
                                      connection: str = None,
                                      sql_query: str = None,
                                      columns: str = None,
                                      drillable_regions: str = None,
                                      confirm: str = None,
                                      ctx: Context = None) -> str:
        """Manage drill-through reports that link cube cells to detail data.

        Args:
            action: One of 'list', 'get', 'create', 'update', 'delete', 'execute'.
            app_name: Application name.
            db_name: Database name.
            report_name: Report name (required for get/create/delete/execute).
            connection: Connection name for external data (for create).
            sql_query: SQL query to run on drill-through (for create).
            columns: Comma-separated column names to display (for create).
            drillable_regions: Comma-separated member specifications defining where drill-through is available (for create, e.g. '@IDESCENDANTS(East),@IDESCENDANTS(Sales)').
        """
        from ._helpers import require_confirm
        ess = get_essbase(ctx)
        if not ess:
            return err(_NO)
        try:
            dt = ess.drill_through

            if action == 'list':
                return fmt(dt.list_reports(app_name, db_name))

            elif action == 'get':
                if not report_name:
                    return err('report_name required for get.')
                return fmt(dt.get_report(
                    app_name, db_name, report_name))

            elif action == 'create':
                if not report_name:
                    return err('report_name required for create.')
                if not connection:
                    return err('connection required for create.')
                payload = {
                    'name': report_name,
                    'connection': connection,
                }
                if sql_query:
                    payload['query'] = sql_query
                if columns:
                    payload['columns'] = [c.strip()
                                          for c in columns.split(',')]
                if drillable_regions:
                    payload['drillableRegions'] = [
                        r.strip()
                        for r in drillable_regions.split(',')]
                result = dt.create_report(
                    app_name, db_name, payload)
                return fmt(result)

            elif action == 'update':
                if not report_name:
                    return err('report_name required for update.')
                payload = {}
                if connection:
                    payload['connection'] = connection
                if sql_query:
                    payload['query'] = sql_query
                if columns:
                    payload['columns'] = [c.strip()
                                          for c in columns.split(',')]
                if drillable_regions:
                    payload['drillableRegions'] = [
                        r.strip()
                        for r in drillable_regions.split(',')]
                result = dt.update_report(
                    app_name, db_name, report_name, payload)
                return fmt(result)

            elif action == 'delete':
                msg = require_confirm(report_name, confirm,
                                       action_label='delete drill-through report')
                if msg:
                    return err(msg)
                if not report_name:
                    return err('report_name required for delete.')
                dt.delete_report(app_name, db_name, report_name)
                return json.dumps({'status': 'deleted',
                                   'report': report_name})

            elif action == 'execute':
                if not report_name:
                    return err('report_name required for execute.')
                result = dt.execute_report(
                    app_name, db_name, report_name)
                return fmt(result)

            else:
                return err(f'Unknown action: {action}. '
                           f'Use list/get/create/update/delete/execute.')
        except Exception as exc:
            return err(str(exc))

    # ── 24. essbase_manage_database ────────────────────────────────────
    @mcp.tool()
    def essbase_manage_database(action: str, app_name: str,
                                 db_name: str,
                                 new_name: str = None,
                                 target_app: str = None,
                                 target_db: str = None,
                                 confirm: str = None,
                                 ctx: Context = None) -> str:
        """Manage databases within an Essbase application: delete, copy, or rename.

        Destructive actions (`delete`) require `confirm` to match
        `db_name` exactly — guards against prompt-injected deletions.

        Args:
            action: One of 'delete', 'copy', 'rename', 'update'.
            app_name: Application name.
            db_name: Database (cube) name.
            new_name: New database name (required for rename).
            target_app: Target application name (required for copy).
            target_db: Target database name (required for copy).
            confirm: For delete only: must equal `db_name`.
        """
        from ._helpers import require_confirm
        ess = get_essbase(ctx)
        if not ess:
            return err(_NO)
        try:
            a = ess.applications
            if action == 'delete':
                msg = require_confirm(db_name, confirm,
                                       action_label='delete database')
                if msg:
                    return err(msg)
                a.delete_database(app_name, db_name)
                return json.dumps({'status': 'deleted',
                                   'application': app_name,
                                   'database': db_name})

            elif action == 'copy':
                if not target_app or not target_db:
                    return err('target_app and target_db required for copy.')
                result = a.copy_database(app_name,
                                         {'from': db_name,
                                          'to': target_db})
                return fmt(result) if result else json.dumps(
                    {'status': 'copied', 'from': db_name,
                     'to': target_db})

            elif action == 'rename':
                if not new_name:
                    return err('new_name required for rename.')
                result = a.rename_database(app_name,
                                           {'oldDbName': db_name,
                                            'newDbName': new_name})
                return fmt(result) if result else json.dumps(
                    {'status': 'renamed', 'old_name': db_name,
                     'new_name': new_name})

            elif action == 'update':
                result = a.update_database(app_name, db_name, {})
                return fmt(result) if result else json.dumps(
                    {'status': 'updated', 'application': app_name,
                     'database': db_name})

            else:
                return err(f'Unknown action: {action}. '
                           f'Use delete/copy/rename/update.')
        except Exception as exc:
            return err(str(exc))

    # ── 25. essbase_manage_users ───────────────────────────────────────
    @mcp.tool()
    def essbase_manage_users(action: str,
                              user_id: str = None,
                              password: str = None,
                              role: str = None,
                              app_name: str = None,
                              confirm: str = None,
                              ctx: Context = None) -> str:
        """Manage Essbase users: list, get details, create, update, delete, provision, deprovision roles, or list roles.

        Destructive actions (`delete`) require `confirm` to match
        `user_id` exactly — guards against prompt-injected deletions.

        Args:
            action: One of 'list', 'get', 'create', 'update', 'delete', 'provision', 'deprovision', 'list_roles', 'list_service_roles', 'list_app_roles'.
            user_id: User ID (required for get/create/update/delete/provision/deprovision).
            password: Password (required for create).
            role: Role name (required for provision, e.g. 'service_administrator', 'power_user').
            app_name: Application name (for app-level provisioning; omit for service-level).
            confirm: For delete only: must equal `user_id`.
        """
        from ._helpers import require_confirm
        ess = get_essbase(ctx)
        if not ess:
            return err(_NO)
        try:
            u = ess.users
            if action == 'list':
                return fmt(u.list_users())

            elif action == 'get':
                if not user_id:
                    return err('user_id required for get.')
                errors = []
                data = {}
                user, e = safe_call('user', u.get_user, user_id)
                if user:
                    data['user'] = user
                if e:
                    errors.append(e)
                prov, e = safe_call('provisioning',
                                    u.get_user_provisioning_report,
                                    user_id)
                if prov:
                    data['provisioning'] = prov
                if e:
                    errors.append(e)
                return build_response(data, errors or None)

            elif action == 'create':
                if not user_id or not password:
                    return err('user_id and password required for create.')
                result = u.create_user(
                    {'id': user_id, 'password': password})
                return fmt(result) if result else json.dumps(
                    {'status': 'created', 'user': user_id})

            elif action == 'delete':
                if not user_id:
                    return err('user_id required for delete.')
                msg = require_confirm(user_id, confirm,
                                       action_label='delete user')
                if msg:
                    return err(msg)
                u.delete_user(user_id)
                return json.dumps({'status': 'deleted',
                                   'user': user_id})

            elif action == 'provision':
                if not user_id or not role:
                    return err('user_id and role required for provision.')
                if app_name:
                    result = u.provision_app_role(
                        app_name, user_id, {'role': role})
                else:
                    result = u.provision_service_role(
                        user_id, {'role': role})
                return fmt(result) if result else json.dumps(
                    {'status': 'provisioned', 'user': user_id,
                     'role': role})

            elif action == 'update':
                if not user_id:
                    return err('user_id required for update.')
                payload = {}
                if password:
                    payload['password'] = password
                result = u.update_user(user_id, payload)
                return fmt(result)

            elif action == 'deprovision':
                if not user_id:
                    return err('user_id required for deprovision.')
                if app_name:
                    result = u.deprovision_app_role(app_name, user_id)
                else:
                    result = u.deprovision_service_role(user_id)
                return fmt(result) if result else json.dumps(
                    {'status': 'deprovisioned', 'user': user_id})

            elif action == 'list_roles':
                return fmt(u.list_roles())

            elif action == 'list_service_roles':
                return fmt(u.list_service_roles())

            elif action == 'list_app_roles':
                if not app_name:
                    return err('app_name required for list_app_roles.')
                return fmt(u.list_app_roles(app_name))

            else:
                return err(f'Unknown action: {action}. '
                           f'Use list/get/create/update/delete/provision/'
                           f'deprovision/list_roles/list_service_roles/'
                           f'list_app_roles.')
        except Exception as exc:
            return err(str(exc))

    # ── 26. essbase_manage_groups ──────────────────────────────────────
    @mcp.tool()
    def essbase_manage_groups(action: str,
                               group_id: str = None,
                               user_ids: str = None,
                               confirm: str = None,
                               ctx: Context = None) -> str:
        """Manage Essbase groups: list, get details, create, delete, add/remove users, get users, add/remove subgroups.

        Args:
            action: One of 'list', 'get', 'create', 'delete', 'add_users', 'remove_users', 'get_users', 'add_subgroups', 'remove_subgroups'.
            group_id: Group ID (required for get/create/delete/add_users/remove_users/get_users/add_subgroups/remove_subgroups).
            user_ids: Comma-separated user IDs (required for add_users). For add_subgroups, comma-separated subgroup IDs.
        """
        from ._helpers import require_confirm
        ess = get_essbase(ctx)
        if not ess:
            return err(_NO)
        try:
            g = ess.groups
            if action == 'list':
                return fmt(g.list_groups())

            elif action == 'get':
                if not group_id:
                    return err('group_id required for get.')
                errors = []
                data = {}
                group, e = safe_call('group', g.get_group, group_id)
                if group:
                    data['group'] = group
                if e:
                    errors.append(e)
                members, e = safe_call('members',
                                       g.get_members, group_id)
                if members:
                    data['members'] = members
                if e:
                    errors.append(e)
                prov, e = safe_call('provisioning',
                                    g.get_provisioning_report,
                                    group_id)
                if prov:
                    data['provisioning'] = prov
                if e:
                    errors.append(e)
                return build_response(data, errors or None)

            elif action == 'create':
                if not group_id:
                    return err('group_id required for create.')
                result = g.create_group({'id': group_id})
                return fmt(result) if result else json.dumps(
                    {'status': 'created', 'group': group_id})

            elif action == 'delete':
                msg = require_confirm(group_id, confirm,
                                       action_label='delete group')
                if msg:
                    return err(msg)
                if not group_id:
                    return err('group_id required for delete.')
                g.delete_group(group_id)
                return json.dumps({'status': 'deleted',
                                   'group': group_id})

            elif action == 'add_users':
                if not group_id or not user_ids:
                    return err('group_id and user_ids required '
                               'for add_users.')
                users = [{'id': u.strip()}
                         for u in user_ids.split(',')]
                result = g.add_users(group_id, users)
                return fmt(result) if result else json.dumps(
                    {'status': 'users_added', 'group': group_id,
                     'users': [u['id'] for u in users]})

            elif action == 'remove_users':
                msg = require_confirm(group_id, confirm,
                                       action_label='remove users from group')
                if msg:
                    return err(msg)
                if not group_id:
                    return err('group_id required for remove_users.')
                result = g.remove_users(group_id)
                return fmt(result) if result else json.dumps(
                    {'status': 'users_removed',
                     'group': group_id})

            elif action == 'get_users':
                if not group_id:
                    return err('group_id required for get_users.')
                result = g.get_users(group_id)
                return fmt(result)

            elif action == 'add_subgroups':
                if not group_id or not user_ids:
                    return err('group_id and user_ids (subgroup IDs) '
                               'required for add_subgroups.')
                subgroups = [{'id': s.strip()}
                             for s in user_ids.split(',')]
                result = g.add_subgroups(group_id, subgroups)
                return fmt(result) if result else json.dumps(
                    {'status': 'subgroups_added',
                     'group': group_id,
                     'subgroups': [s['id'] for s in subgroups]})

            elif action == 'remove_subgroups':
                msg = require_confirm(group_id, confirm,
                                       action_label='remove subgroups from group')
                if msg:
                    return err(msg)
                if not group_id:
                    return err('group_id required for remove_subgroups.')
                result = g.remove_subgroups(group_id)
                return fmt(result) if result else json.dumps(
                    {'status': 'subgroups_removed',
                     'group': group_id})

            else:
                return err(f'Unknown action: {action}. '
                           f'Use list/get/create/delete/add_users/'
                           f'remove_users/get_users/add_subgroups/'
                           f'remove_subgroups.')
        except Exception as exc:
            return err(str(exc))

    # ── 27. essbase_manage_sessions ────────────────────────────────────
    @mcp.tool()
    def essbase_manage_sessions(action: str = 'list',
                                  session_id: str = None,
                                  confirm: str = None,
                                  ctx: Context = None) -> str:
        """Manage Essbase sessions: list active sessions, get current session, kill a session, or kill all sessions.

        Destructive actions (`kill`, `kill_all`) require `confirm`:
          - `kill`: must equal `session_id`.
          - `kill_all`: must equal the literal string 'all'.

        Args:
            action: One of 'list' (default), 'current', 'kill', 'kill_all'.
            session_id: Session ID (required for kill).
            confirm: Confirmation token (required for kill and kill_all).
        """
        from ._helpers import require_confirm
        ess = get_essbase(ctx)
        if not ess:
            return err(_NO)
        try:
            s = ess.sessions
            if action == 'list':
                return fmt(s.list_sessions())

            elif action == 'current':
                return fmt(s.get_current_session())

            elif action == 'kill':
                if not session_id:
                    return err('session_id required for kill.')
                msg = require_confirm(session_id, confirm,
                                       action_label='kill session')
                if msg:
                    return err(msg)
                s.delete_session(session_id)
                return json.dumps({'status': 'killed',
                                   'session': session_id})

            elif action == 'kill_all':
                msg = require_confirm('all', confirm,
                                       action_label='kill all sessions')
                if msg:
                    return err(msg)
                s.delete_all_sessions()
                return json.dumps({'status': 'all_sessions_killed'})

            else:
                return err(f'Unknown action: {action}. '
                           f'Use list/current/kill/kill_all.')
        except Exception as exc:
            return err(str(exc))

    # ── 28. essbase_manage_db_settings ─────────────────────────────────
    @mcp.tool()
    def essbase_manage_db_settings(app_name: str, db_name: str,
                                     category: str = 'all',
                                     settings_json: str = None,
                                     ctx: Context = None) -> str:
        """Get or update detailed database settings and tuning information for performance analysis.

        Retrieves configuration across multiple categories: startup, calculation,
        cache, compression, transactions, runtime statistics, and storage statistics.
        Use category='all' for a full snapshot or specify a single category.
        Provide settings_json to update database settings.

        Args:
            app_name: Application name.
            db_name: Database (cube) name.
            category: One of 'all' (default), 'startup', 'calculation', 'cache', 'compression', 'transactions', 'runtime', 'storage'.
            settings_json: JSON string of settings to update (when provided, performs an update instead of a read).
        """
        ess = get_essbase(ctx)
        if not ess:
            return err(_NO)
        try:
            if settings_json:
                import json as json_mod
                settings = json_mod.loads(settings_json)
                result = ess.database_settings.update_settings(
                    app_name, db_name, settings)
                return json.dumps({'action': 'updated',
                                   'result': str(result)})

            ds = ess.database_settings
            if category == 'all':
                errors = []
                data = {}

                settings, e = safe_call(
                    'settings', ds.get_settings,
                    app_name, db_name)
                if settings:
                    data['settings'] = settings
                if e:
                    errors.append(e)

                startup, e = safe_call(
                    'startup', ds.get_startup_settings,
                    app_name, db_name)
                if startup:
                    data['startup'] = startup
                if e:
                    errors.append(e)

                calc, e = safe_call(
                    'calculation', ds.get_calculation_settings,
                    app_name, db_name)
                if calc:
                    data['calculation'] = calc
                if e:
                    errors.append(e)

                cache, e = safe_call(
                    'cache', ds.get_cache_settings,
                    app_name, db_name)
                if cache:
                    data['cache'] = cache
                if e:
                    errors.append(e)

                buf, e = safe_call(
                    'buffer', ds.get_buffer_settings,
                    app_name, db_name)
                if buf:
                    data['buffer'] = buf
                if e:
                    errors.append(e)

                comp, e = safe_call(
                    'compression', ds.get_compression_settings,
                    app_name, db_name)
                if comp:
                    data['compression'] = comp
                if e:
                    errors.append(e)

                txn, e = safe_call(
                    'transactions', ds.get_transaction_settings,
                    app_name, db_name)
                if txn:
                    data['transactions'] = txn
                if e:
                    errors.append(e)

                return build_response(data, errors or None)

            elif category == 'startup':
                return fmt(ds.get_startup_settings(app_name, db_name))
            elif category == 'calculation':
                return fmt(ds.get_calculation_settings(
                    app_name, db_name))
            elif category == 'cache':
                return fmt(ds.get_cache_settings(app_name, db_name))
            elif category == 'compression':
                return fmt(ds.get_compression_settings(
                    app_name, db_name))
            elif category == 'transactions':
                return fmt(ds.get_transaction_settings(
                    app_name, db_name))
            elif category == 'runtime':
                return fmt(ds.get_runtime_statistics(
                    app_name, db_name))
            elif category == 'storage':
                return fmt(ds.get_storage_statistics(
                    app_name, db_name))
            else:
                return err(f'Unknown category: {category}. '
                           f'Use all/startup/calculation/cache/'
                           f'compression/transactions/runtime/storage.')
        except Exception as exc:
            return err(str(exc))

    # ── 29. essbase_get_logs ───────────────────────────────────────────
    @mcp.tool()
    def essbase_get_logs(app_name: str,
                          latest_only: bool = True,
                          ctx: Context = None) -> str:
        """Retrieve application logs from Essbase.

        Returns the latest log entry by default, or all available logs.

        Args:
            app_name: Application name.
            latest_only: If True (default), return only the latest log. If False, return all logs.
        """
        ess = get_essbase(ctx)
        if not ess:
            return err(_NO)
        try:
            if latest_only:
                result = ess.applications.get_latest_log(app_name)
            else:
                result = ess.applications.get_logs(app_name)
            if isinstance(result, bytes):
                result = result.decode('utf-8', errors='replace')
            if isinstance(result, str):
                return json.dumps({'application': app_name,
                                   'log': result}, default=str)
            return fmt(result)
        except Exception as exc:
            return err(str(exc))

    # ── 30. essbase_outline_metadata ──────────────────────────────────
    @mcp.tool()
    def essbase_outline_metadata(app_name: str, db_name: str,
                                   category: str = 'all',
                                   dimension_name: str = None,
                                   ctx: Context = None) -> str:
        """Get detailed outline metadata: dimensions, generations, levels, smart lists, and outline settings.

        Args:
            app_name: Application name.
            db_name: Database name.
            category: One of 'all', 'generations', 'levels', 'smart_lists', 'outline_settings', 'export_xml', 'member'.
            dimension_name: Dimension name (required for generations/levels). For 'member' category, this is the member unique name.
        """
        ess = get_essbase(ctx)
        if not ess:
            return err(_NO)
        try:
            if category == 'all':
                errors = []
                data = {}

                dims, e = safe_call(
                    'dimensions',
                    ess.dimensions.list_dimensions,
                    app_name, db_name)
                if dims:
                    data['dimensions'] = dims
                if e:
                    errors.append(e)

                smart, e = safe_call(
                    'smart_lists',
                    ess.dimensions.get_smart_lists,
                    app_name, db_name)
                if smart:
                    data['smart_lists'] = smart
                if e:
                    errors.append(e)

                outline_settings, e = safe_call(
                    'outline_settings',
                    ess.dimensions.get_outline_settings,
                    app_name, db_name)
                if outline_settings:
                    data['outline_settings'] = outline_settings
                if e:
                    errors.append(e)

                attr_settings, e = safe_call(
                    'attribute_settings',
                    ess.dimensions.get_attribute_settings,
                    app_name, db_name)
                if attr_settings:
                    data['attribute_settings'] = attr_settings
                if e:
                    errors.append(e)

                return build_response(data, errors or None)

            elif category == 'generations':
                if not dimension_name:
                    return err('dimension_name required for generations.')
                return fmt(ess.dimensions.list_generations(
                    app_name, db_name, dimension_name))

            elif category == 'levels':
                if not dimension_name:
                    return err('dimension_name required for levels.')
                return fmt(ess.dimensions.list_levels(
                    app_name, db_name, dimension_name))

            elif category == 'smart_lists':
                return fmt(ess.dimensions.get_smart_lists(
                    app_name, db_name))

            elif category == 'outline_settings':
                return fmt(ess.dimensions.get_outline_settings(
                    app_name, db_name))

            elif category == 'export_xml':
                return fmt(ess.dimensions.export_outline_xml(
                    app_name, db_name))

            elif category == 'member':
                if not dimension_name:
                    return err('dimension_name (member unique name) '
                               'required for member.')
                errors = []
                data = {}

                member, e = safe_call(
                    'member',
                    ess.dimensions.get_member,
                    app_name, db_name, dimension_name)
                if member:
                    data['member'] = member
                if e:
                    errors.append(e)

                count, e = safe_call(
                    'descendants_count',
                    ess.dimensions.get_descendants_count,
                    app_name, db_name, dimension_name)
                if count is not None:
                    data['descendants_count'] = count
                if e:
                    errors.append(e)

                return build_response(data, errors or None)

            else:
                return err(f'Unknown category: {category}. '
                           f'Use all/generations/levels/smart_lists/'
                           f'outline_settings/export_xml/member.')
        except Exception as exc:
            return err(str(exc))
