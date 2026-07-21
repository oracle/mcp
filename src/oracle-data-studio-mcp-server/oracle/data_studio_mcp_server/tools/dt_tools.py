# Copyright (c) 2025, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

'''Upleveled Data Transforms MCP tools.

Each tool combines multiple SDK calls into a single task-oriented
operation that returns an LLM-friendly result.  See TOOLS_DESIGN.md.
'''

import json
import logging

from mcp.server.fastmcp import FastMCP, Context

from ._dt_connect import get_dt
from ._helpers import safe_call, build_response, err, fmt

logger = logging.getLogger('oracle-data-studio-mcp')

_NO = 'Data Transforms not connected. Set DT_URL, DT_USER, DT_PASSWORD.'


def register_tools(mcp: FastMCP):

    # ── 27. dt_explore ────────────────────────────────────────────────
    @mcp.tool()
    def dt_explore(ctx: Context) -> str:
        """Get a full Data Transforms environment overview: version, connections, projects, and active schedules.

        This is the starting point for any Data Transforms task.
        """
        dt = get_dt(ctx)
        if not dt:
            return err(_NO)
        try:
            client = dt['client']
            wb = dt.get('workbench')
            errors = []
            data = {}

            # About / version
            about, e = safe_call('about', client.get_about)
            if about:
                data['about'] = about
            if e:
                errors.append(e)

            # Connections — redact host/userinfo/wallet by profile so we
            # don't leak JDBC URLs and wallet paths to a viewer-level LLM.
            from ._helpers import redact_connection_metadata, get_profile
            conns, e = safe_call('connections',
                                 client.list_connections)
            if conns:
                data['connections'] = redact_connection_metadata(
                    conns, profile=get_profile(ctx))
            if e:
                errors.append(e)

            # Projects
            projects, e = safe_call('projects',
                                    client.list_projects)
            if projects:
                data['projects'] = projects
            if e:
                errors.append(e)

            # Schedules
            schedules, e = safe_call('schedules',
                                     client.list_schedules)
            if schedules:
                data['schedules'] = schedules
            if e:
                errors.append(e)

            return build_response(data, errors or None)
        except Exception as exc:
            return err(str(exc))

    # ── 28. dt_describe_project ───────────────────────────────────────
    @mcp.tool()
    def dt_describe_project(project_name: str,
                             ctx: Context = None) -> str:
        """Get a complete inventory of a Data Transforms project (read-only).

        Args:
            project_name: Name of the project.
        """
        dt = get_dt(ctx)
        if not dt:
            return err(_NO)
        try:
            client = dt['client']
            errors = []
            data = {'project_name': project_name}

            # Check project exists
            project_id = client.check_if_project_exists(project_name)
            if not project_id:
                return err(f'Project "{project_name}" not found.')
            data['project_id'] = project_id

            # Dataflows
            dfs, e = safe_call('dataflows',
                               client.list_dataflows_in_project,
                               project_id)
            if dfs:
                data['dataflows'] = dfs
            if e:
                errors.append(e)

            # Workflows
            wfs, e = safe_call('workflows',
                               client.list_workflows_in_project,
                               project_id)
            if wfs:
                data['workflows'] = wfs
            if e:
                errors.append(e)

            # Dataloads
            dls, e = safe_call('dataloads',
                               client.list_dataloads_in_project,
                               project_id)
            if dls:
                data['dataloads'] = dls
            if e:
                errors.append(e)

            return build_response(data, errors or None)
        except Exception as exc:
            return err(str(exc))

    # ── 28b. dt_manage_project ────────────────────────────────────────
    @mcp.tool()
    def dt_manage_project(action: str, project_name: str,
                           confirm: str = None,
                           ctx: Context = None) -> str:
        """Manage Data Transforms projects (admin-only).

        Destructive actions (`delete`) require `confirm` to match
        `project_name` exactly — guards against prompt-injected
        deletions.

        Args:
            action: One of 'delete'.
            project_name: Name of the project.
            confirm: For delete: must equal `project_name`.
        """
        from ._helpers import require_confirm
        dt = get_dt(ctx)
        if not dt:
            return err(_NO)
        try:
            client = dt['client']

            if action == 'delete':
                msg = require_confirm(project_name, confirm,
                                       action_label='delete project')
                if msg:
                    return err(msg)
                project_id = client.check_if_project_exists(project_name)
                if not project_id:
                    return err(f'Project "{project_name}" not found.')
                client.delete_project(project_name)
                return json.dumps({'status': 'deleted', 'project': project_name})
            else:
                return err(f'Unknown action: {action}. Use delete.')
        except Exception as exc:
            return err(str(exc))

    # ── 29. dt_describe_connection ────────────────────────────────────
    @mcp.tool()
    def dt_describe_connection(connection_name: str,
                                ctx: Context) -> str:
        """Get connection details, test it, and list its available schemas.

        Args:
            connection_name: Name of the connection.
        """
        dt = get_dt(ctx)
        if not dt:
            return err(_NO)
        try:
            client = dt['client']
            errors = []
            data = {'connection_name': connection_name}

            # Details — redact JDBC URL, wallet path, host/userinfo for
            # non-admin profiles. Even `viewer` keeps the connection
            # name + type so it remains useful for discovery.
            from ._helpers import redact_connection_metadata, get_profile
            details, e = safe_call('details',
                                   client.get_connection_details,
                                   connection_name)
            if details:
                data['details'] = redact_connection_metadata(
                    details, profile=get_profile(ctx))
            if e:
                errors.append(e)

            # Test
            test, e = safe_call('test',
                                client.test_connection_by_name,
                                connection_name)
            if test is not None:
                data['test_result'] = test
            if e:
                errors.append(e)

            # Schemas
            schemas, e = safe_call('schemas',
                                   client.get_live_schemas,
                                   connection_name)
            if schemas:
                data['schemas'] = schemas
            if e:
                errors.append(e)

            return build_response(data, errors or None)
        except Exception as exc:
            return err(str(exc))

    # ── 30. dt_create_pipeline ────────────────────────────────────────
    @mcp.tool()
    def dt_create_pipeline(project_name: str,
                            source_connection: str,
                            source_schema: str,
                            source_table: str,
                            target_connection: str,
                            target_schema: str,
                            target_table: str,
                            dataflow_name: str = None,
                            integration_type: str = 'CONTROL_APPEND',
                            ctx: Context = None) -> str:
        """Create a simple source-to-target dataflow in a Data Transforms project.

        Creates the project if it doesn't exist, then builds a dataflow
        that maps data from a source table to a target table.

        Args:
            project_name: Target project name (created if it doesn't exist).
            source_connection: Name of the source connection (use dt_explore to list available connections).
            source_schema: Schema in the source connection (use dt_describe_connection to list schemas).
            source_table: Table name in the source schema.
            target_connection: Name of the target connection.
            target_schema: Schema in the target connection.
            target_table: Table name in the target schema.
            dataflow_name: Name for the dataflow (defaults to 'DF_{source_table}_to_{target_table}').
            integration_type: How to load data. One of: 'CONTROL_APPEND' (append rows, default), 'INCREMENTAL_UPDATE' (upsert changed rows), 'INSERT' (simple insert).
        """
        dt = get_dt(ctx)
        if not dt:
            return err(_NO)
        try:
            client = dt['client']
            wb = dt.get('workbench')
            data = {'project_name': project_name}

            if not dataflow_name:
                dataflow_name = f'DF_{source_table}_to_{target_table}'
            data['dataflow_name'] = dataflow_name

            # Ensure project exists
            project_id = client.check_if_project_exists(project_name)
            if not project_id:
                client.create_project(project_name)
                project_id = client.check_if_project_exists(project_name)
            data['project_id'] = project_id

            # Use the SDK's builder classes if workbench is available
            if wb:
                try:
                    from datatransforms.dataflow import (
                        Project, SourceDataStore, TargetDataStore)
                    from datatransforms.dataflow import DataFlow

                    project = Project(project_name, project_name)
                    src = SourceDataStore('SRC', source_table)
                    tgt = TargetDataStore('TGT', target_table,
                                          {'integrationType': integration_type})
                    df = DataFlow(project, dataflow_name)
                    df.add_source(source_connection, source_schema, src)
                    df.add_target(target_connection, target_schema, tgt)
                    df.connect(src, tgt)
                    df.create()
                    data['action'] = 'created'
                    data['success'] = True
                    return json.dumps(data, indent=2, default=str)
                except ImportError:
                    pass  # fall through to raw API
                except Exception as e:
                    logger.debug('DataFlow builder failed: %s', e)
                    # fall through to raw API

            # Fallback: build the JSON payload manually
            payload = _build_simple_dataflow_payload(
                project_name, dataflow_name,
                source_connection, source_schema, source_table,
                target_connection, target_schema, target_table,
                integration_type)
            success, global_id = \
                client.create_dataflow_from_json_payload(
                    json.dumps(payload))
            data['action'] = 'created'
            data['success'] = success
            data['global_id'] = global_id

            return json.dumps(data, indent=2, default=str)
        except Exception as exc:
            return err(str(exc))

    # ── 31. dt_check_health ───────────────────────────────────────────
    @mcp.tool()
    def dt_check_health(ctx: Context) -> str:
        """Check Data Transforms environment health: test all connections and list schedules.
        """
        dt = get_dt(ctx)
        if not dt:
            return err(_NO)
        try:
            client = dt['client']
            errors = []
            data = {}

            # List and test all connections
            conns, e = safe_call('connections',
                                 client.list_connections)
            if e:
                errors.append(e)

            if conns:
                conn_results = []
                conn_list = conns if isinstance(conns, list) else \
                    conns.get('items', [conns])
                for conn in conn_list:
                    name = conn.get('name', '') if isinstance(
                        conn, dict) else str(conn)
                    if name:
                        test, e2 = safe_call(
                            f'test/{name}',
                            client.test_connection_by_name, name)
                        conn_results.append({
                            'name': name,
                            'status': test if test is not None
                            else 'unknown'
                        })
                        if e2:
                            errors.append(e2)
                data['connections'] = conn_results

            # Schedules
            schedules, e = safe_call('schedules',
                                     client.list_schedules)
            if schedules:
                data['schedules'] = schedules
            if e:
                errors.append(e)

            # Deployment time
            deploy, e = safe_call('deployment',
                                  client.get_deployment_time)
            if deploy:
                data['deployment'] = deploy
            if e:
                errors.append(e)

            return build_response(data, errors or None)
        except Exception as exc:
            return err(str(exc))

    # ── 32. dt_browse_data ────────────────────────────────────────────
    @mcp.tool()
    def dt_browse_data(connection_name: str, schema: str = None,
                        ctx: Context = None) -> str:
        """Browse schemas and tables available through a Data Transforms connection.

        Args:
            connection_name: Connection to browse.
            schema: Optional schema filter (shows all if omitted).
        """
        dt = get_dt(ctx)
        if not dt:
            return err(_NO)
        try:
            client = dt['client']
            errors = []
            data = {'connection_name': connection_name}

            if schema:
                tables, e = safe_call('tables',
                                      client.get_live_tables,
                                      connection_name, schema)
                if tables:
                    data['tables'] = tables
                if e:
                    errors.append(e)
            else:
                schemas, e = safe_call('schemas',
                                       client.get_live_schemas,
                                       connection_name)
                if schemas:
                    data['schemas'] = schemas
                if e:
                    errors.append(e)

            return build_response(data, errors or None)
        except Exception as exc:
            return err(str(exc))

    # ── 33. dt_manage_dataflow ────────────────────────────────────────
    @mcp.tool()
    def dt_manage_dataflow(project_name: str, dataflow_name: str,
                            ctx: Context = None) -> str:
        """Check if a dataflow exists in a project and return its details.

        Use dt_create_pipeline to create new dataflows with explicit
        source/target parameters.

        Args:
            project_name: Project name.
            dataflow_name: Dataflow name to look up.
        """
        dt = get_dt(ctx)
        if not dt:
            return err(_NO)
        try:
            client = dt['client']
            data = {'project_name': project_name,
                    'dataflow_name': dataflow_name}

            project_id = client.check_if_project_exists(project_name)
            if not project_id:
                return err(f'Project "{project_name}" not found.')

            exists, global_id = client.check_if_df_exists(
                project_id, dataflow_name)
            data['exists'] = exists
            if exists:
                data['global_id'] = global_id
                # Try to get dataflow details
                details, e = safe_call(
                    'details',
                    client.get_dataflow_by_id, global_id)
                if details:
                    data['details'] = details

            return json.dumps(data, indent=2, default=str)
        except Exception as exc:
            return err(str(exc))

    # ── 34. dt_manage_schedule ────────────────────────────────────────
    @mcp.tool()
    def dt_manage_schedule(action: str,
                            schedule_name: str = None,
                            project_name: str = None,
                            resource_name: str = None,
                            resource_type: str = 'dataflow',
                            frequency: str = None,
                            time: str = None,
                            days: str = None,
                            status: str = 'INACTIVE',
                            confirm: str = None,
                            ctx: Context = None) -> str:
        """Manage Data Transforms schedules: list, create, or delete.

        For 'create', builds a schedule from explicit parameters — no raw JSON needed.

        Args:
            action: One of 'list', 'create', 'delete'.
            schedule_name: Schedule name (required for create/delete).
            project_name: Project containing the resource to schedule (required for create).
            resource_name: Dataflow or workflow name to schedule (required for create).
            resource_type: 'dataflow' or 'workflow' (default: dataflow).
            frequency: Schedule frequency. One of: 'immediate' (run once now), 'hourly', 'daily', 'weekly', 'monthly'. Required for create.
            time: Time for the schedule. Format depends on frequency: for 'hourly' use 'MM:SS' (e.g. '30:00' = at 30 minutes past), for 'daily' use 'HH:MM' (e.g. '14:30'), for 'weekly'/'monthly' use 'HH:MM:SS' (e.g. '06:00:00'). Required for all except 'immediate'.
            days: Days for weekly schedules, comma-separated (e.g. 'MONDAY,WEDNESDAY,FRIDAY'). Valid values: MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY. Required for weekly.
            status: 'ACTIVE' or 'INACTIVE' (default: INACTIVE). Set to ACTIVE to enable immediately.
        """
        from ._helpers import require_confirm
        dt = get_dt(ctx)
        if not dt:
            return err(_NO)
        try:
            client = dt['client']
            if action == 'list':
                result = client.list_schedules()
                return fmt(result)

            elif action == 'delete':
                msg = require_confirm(schedule_name, confirm,
                                       action_label='delete schedule')
                if msg:
                    return err(msg)
                if not schedule_name:
                    return err('schedule_name required for delete.')
                result = client.delete_schedule(schedule_name)
                return fmt(result)

            elif action == 'create':
                if not all([schedule_name, project_name,
                            resource_name, frequency]):
                    return err(
                        'create requires: schedule_name, project_name, '
                        'resource_name, frequency.')

                # Build schedule using the SDK's Schedule builder
                try:
                    from datatransforms.schedule import Schedule
                    sched = Schedule(schedule_name)

                    # Attach resource
                    if resource_type == 'workflow':
                        sched.workflow(project_name, resource_name)
                    else:
                        sched.dataflow(project_name, resource_name)

                    # Set frequency
                    if frequency == 'immediate':
                        sched.immediate()
                    elif frequency == 'hourly':
                        parts = (time or '00:00').split(':')
                        mins = int(parts[0])
                        secs = int(parts[1]) if len(parts) > 1 else 0
                        sched.hourly(mins, secs)
                    elif frequency == 'daily':
                        parts = (time or '00:00').split(':')
                        hh = int(parts[0])
                        mm = int(parts[1]) if len(parts) > 1 else 0
                        ss = int(parts[2]) if len(parts) > 2 else 0
                        sched.daily(hh, mm, ss)
                    elif frequency == 'weekly':
                        if not days:
                            return err('days required for weekly schedule '
                                       '(e.g. "MONDAY,FRIDAY").')
                        day_list = [d.strip() for d in days.split(',')]
                        sched.weekly(day_list, time or '00:00')
                    elif frequency == 'monthly':
                        parts = (time or '01 00:00:00').split(' ')
                        if len(parts) == 2:
                            date_part = parts[0]
                            time_part = parts[1]
                        else:
                            date_part = '1'
                            time_part = time or '00:00:00'
                        sched.monthly(date_part, time_part)
                    else:
                        return err(
                            f'Unknown frequency: {frequency}. '
                            f'Use immediate/hourly/daily/weekly/monthly.')

                    # Set status
                    sched.schedule_status(status)

                    # Create it
                    sched.create()

                    return json.dumps({
                        'action': 'created',
                        'schedule_name': schedule_name,
                        'frequency': frequency,
                        'status': status,
                        'resource': resource_name,
                        'project': project_name,
                    }, indent=2)

                except ImportError:
                    return err(
                        'Schedule builder not available. '
                        'Install oracle-data-studio>=1.0.25.')
            else:
                return err(f'Unknown action: {action}. '
                           f'Use list/create/delete.')
        except Exception as exc:
            return err(str(exc))

    # ── 35. dt_manage_variables ───────────────────────────────────────
    @mcp.tool()
    def dt_manage_variables(action: str, variable_name: str = None,
                             value: str = None,
                             ctx: Context = None) -> str:
        """Manage Data Transforms variables: list, create, or update.

        Args:
            action: One of 'list', 'set'.
            variable_name: Variable name (required for set).
            value: Variable value (required for set).
        """
        dt = get_dt(ctx)
        if not dt:
            return err(_NO)
        try:
            client = dt['client']
            if action == 'list':
                result = client.list_variables()
                return fmt(result)
            elif action == 'set':
                if not variable_name or value is None:
                    return err('variable_name and value required for set.')
                # Try update first, create on failure
                try:
                    result = client.update_variable(variable_name, value)
                    return json.dumps({'action': 'updated',
                                       'variable': variable_name,
                                       'value': value})
                except Exception:
                    result = client.create_variable(variable_name, value)
                    return json.dumps({'action': 'created',
                                       'variable': variable_name,
                                       'value': value})
            else:
                return err(f'Unknown action: {action}. Use list/set.')
        except Exception as exc:
            return err(str(exc))

    # ── 36. dt_run_pipeline ──────────────────────────────────────────
    @mcp.tool()
    def dt_run_pipeline(project_name: str,
                         resource_name: str,
                         resource_type: str = 'dataflow',
                         ctx: Context = None) -> str:
        """Execute a dataflow, workflow, or dataload in a Data Transforms project. Returns the job session and status.

        Args:
            project_name: Project containing the resource.
            resource_name: Name of the dataflow, workflow, or dataload to run.
            resource_type: One of 'dataflow', 'workflow', 'dataload' (default: dataflow).
        """
        dt = get_dt(ctx)
        if not dt:
            return err(_NO)
        try:
            wb = dt.get('workbench')
            if not wb:
                return err('Data Transforms workbench not available. Execution requires a full workbench connection.')
            runtime = wb.get_runtime_client()
            data = {'project': project_name, 'resource': resource_name, 'type': resource_type}

            if resource_type == 'dataflow':
                result = runtime.run_dataflow(project_name, resource_name)
            elif resource_type == 'workflow':
                result = runtime.run_workflow(project_name, resource_name)
            elif resource_type == 'dataload':
                result = runtime.run_dataload(project_name, resource_name)
            else:
                return err(f'Unknown resource_type: {resource_type}. Use dataflow/workflow/dataload.')

            data['job_result'] = result
            return json.dumps(data, indent=2, default=str)
        except Exception as exc:
            return err(str(exc))

    # ── 37. dt_manage_connection ─────────────────────────────────────
    @mcp.tool()
    def dt_manage_connection(action: str,
                               connection_name: str = None,
                               connection_type: str = None,
                               host: str = None,
                               port: int = None,
                               service_name: str = None,
                               user: str = None,
                               password: str = None,
                               wallet_path: str = None,
                               jdbc_url: str = None,
                               confirm: str = None,
                               ctx: Context = None) -> str:
        """Manage Data Transforms connections: list, create, delete, or test.

        Args:
            action: One of 'list', 'get_types', 'create', 'delete', 'test'.
            connection_name: Connection name (required for create/delete/test).
            connection_type: Connection type for create (e.g. 'Oracle').
            host: Host for create.
            port: Port for create.
            service_name: Service name for create.
            user: Username for create.
            password: Password for create.
            wallet_path: Wallet path for create (alternative to host/port).
            jdbc_url: JDBC URL for create (alternative to host/port).
        """
        from ._helpers import require_confirm
        dt = get_dt(ctx)
        if not dt:
            return err(_NO)
        try:
            client = dt['client']

            if action == 'list':
                result = client.list_connections()
                return fmt(result)

            elif action == 'get_types':
                result = client.get_connection_types()
                return fmt(result)

            elif action == 'create':
                if not connection_name:
                    return err('connection_name required for create.')
                try:
                    from datatransforms.connection import Connection
                    conn = Connection(connection_name)
                    if connection_type:
                        conn.of_type(connection_type)
                    if user and password:
                        conn.with_credentials(user, password)
                    if wallet_path:
                        conn.usingWallet(wallet_path)
                    if jdbc_url:
                        conn.property('jdbcUrl', jdbc_url)
                    elif host:
                        conn.property('host', host)
                        if port:
                            conn.property('port', str(port))
                        if service_name:
                            conn.property('serviceName', service_name)
                    wb = dt.get('workbench')
                    if not wb:
                        return err('Workbench required for create.')
                    result = wb.save_connection(conn)
                    return json.dumps({'action': 'created', 'connection': connection_name, 'result': str(result)}, indent=2)
                except ImportError:
                    return err('Connection builder not available. Install oracle-data-studio>=1.0.25.')

            elif action == 'delete':
                msg = require_confirm(connection_name, confirm,
                                       action_label='delete connection')
                if msg:
                    return err(msg)
                if not connection_name:
                    return err('connection_name required for delete.')
                result = client.delete_connection(connection_name)
                return json.dumps({'action': 'deleted', 'connection': connection_name, 'result': str(result)}, indent=2)

            elif action == 'test':
                if not connection_name:
                    return err('connection_name required for test.')
                result = client.test_connection_by_name(connection_name)
                return json.dumps({'action': 'tested', 'connection': connection_name, 'result': result}, indent=2, default=str)

            else:
                return err(f'Unknown action: {action}. Use list/get_types/create/delete/test.')
        except Exception as exc:
            return err(str(exc))

    # ── 38. dt_manage_dataload ───────────────────────────────────────
    @mcp.tool()
    def dt_manage_dataload(action: str,
                            project_name: str,
                            dataload_name: str = None,
                            source_connection: str = None,
                            source_schema: str = None,
                            target_connection: str = None,
                            target_schema: str = None,
                            tables: str = None,
                            load_type: str = 'TRUNCATE',
                            ctx: Context = None) -> str:
        """Manage dataloads in a Data Transforms project.

        Args:
            action: One of 'list', 'get', 'check_exists', 'create'.
            project_name: Project name.
            dataload_name: Dataload name (required for get/check_exists/create).
            source_connection: Source connection name (required for create).
            source_schema: Source schema name (required for create).
            target_connection: Target connection name (required for create).
            target_schema: Target schema name (required for create).
            tables: Comma-separated list of table names (required for create).
            load_type: Load type for create: TRUNCATE (default), APPEND, or RECREATE.
        """
        dt = get_dt(ctx)
        if not dt:
            return err(_NO)
        try:
            client = dt['client']
            data = {'project_name': project_name, 'action': action}

            project_id = client.check_if_project_exists(project_name)
            if not project_id:
                return err(f'Project "{project_name}" not found.')
            data['project_id'] = project_id

            if action == 'list':
                result = client.list_dataloads_in_project(project_id)
                data['dataloads'] = result
                return json.dumps(data, indent=2, default=str)

            elif action == 'get':
                if not dataload_name:
                    return err('dataload_name required for get.')
                exists, global_id = client.check_if_dataload_exists(project_id, dataload_name)
                data['exists'] = exists
                if exists:
                    data['global_id'] = global_id
                    details = client.get_dataload_by_id(global_id)
                    data['details'] = details
                return json.dumps(data, indent=2, default=str)

            elif action == 'check_exists':
                if not dataload_name:
                    return err('dataload_name required for check_exists.')
                exists, global_id = client.check_if_dataload_exists(project_id, dataload_name)
                data['exists'] = exists
                if exists:
                    data['global_id'] = global_id
                return json.dumps(data, indent=2, default=str)

            elif action == 'create':
                if not all([dataload_name, source_connection, source_schema,
                            target_connection, target_schema, tables]):
                    return err('create requires: dataload_name, source_connection, '
                               'source_schema, target_connection, target_schema, tables.')
                try:
                    from datatransforms.dataload import DataLoad
                    dl = DataLoad(dataload_name, project_name)
                    dl.source(f'{source_connection}.{source_schema}')
                    dl.target(f'{target_connection}.{target_schema}')
                    table_list = [t.strip() for t in tables.split(',')]
                    for table_name in table_list:
                        if load_type == 'TRUNCATE':
                            dl.truncate(table_name)
                        elif load_type == 'APPEND':
                            dl.append(table_name)
                        elif load_type == 'RECREATE':
                            dl.recreate(table_name)
                        else:
                            dl.truncate(table_name)
                    dl.create_dataload()
                    return json.dumps({'action': 'created', 'dataload': dataload_name,
                                       'tables': table_list, 'load_type': load_type})
                except ImportError:
                    return err('DataLoad builder not available. Install oracle-data-studio>=1.0.25.')

            else:
                return err(f'Unknown action: {action}. Use list/get/check_exists/create.')
        except Exception as exc:
            return err(str(exc))

    # ── 39. dt_manage_data_entities ──────────────────────────────────
    @mcp.tool()
    def dt_manage_data_entities(action: str,
                                  connection_name: str = None,
                                  schema_name: str = None,
                                  entity_name: str = None,
                                  entity_id: str = None,
                                  ctx: Context = None) -> str:
        """Manage data entities in Data Transforms: list, get details, or import from a connection.

        Args:
            action: One of 'list', 'get', 'import_entities'.
            connection_name: Connection name (required for import_entities).
            schema_name: Schema name (required for import_entities).
            entity_name: Entity name (for get by name).
            entity_id: Entity global ID (for get by ID).
        """
        dt = get_dt(ctx)
        if not dt:
            return err(_NO)
        try:
            client = dt['client']
            data = {'action': action}

            if action == 'list':
                try:
                    result = client.list_data_entities()
                except Exception:
                    result = client.get_all_datastores()
                data['entities'] = result
                return json.dumps(data, indent=2, default=str)

            elif action == 'get':
                if entity_id:
                    result = client.get_data_entity_by_id(entity_id)
                    data['entity'] = result
                elif entity_name:
                    result = client.get_data_entity_by_name(entity_name)
                    data['entity'] = result
                else:
                    return err('entity_id or entity_name required for get.')
                return json.dumps(data, indent=2, default=str)

            elif action == 'import_entities':
                if not connection_name or not schema_name:
                    return err('connection_name and schema_name required for import_entities.')
                wb = dt.get('workbench')
                if not wb:
                    return err('Workbench required for import_entities.')
                result = wb.import_data_entities(connection_name, schema_name)
                data['connection_name'] = connection_name
                data['schema_name'] = schema_name
                data['result'] = result
                return json.dumps(data, indent=2, default=str)

            else:
                return err(f'Unknown action: {action}. Use list/get/import_entities.')
        except Exception as exc:
            return err(str(exc))

    # ── 40. dt_manage_workflow ──────────────────────────────────────────
    @mcp.tool()
    def dt_manage_workflow(action: str,
                            project_name: str,
                            workflow_name: str = None,
                            ctx: Context = None) -> str:
        """Manage workflows in a Data Transforms project: list, get details, or check existence.

        Args:
            action: One of 'list', 'get', 'check_exists'.
            project_name: Project name.
            workflow_name: Workflow name (required for get/check_exists).
        """
        dt = get_dt(ctx)
        if not dt:
            return err(_NO)
        try:
            client = dt['client']
            data = {'project_name': project_name, 'action': action}

            project_id = client.check_if_project_exists(project_name)
            if not project_id:
                return err(f'Project "{project_name}" not found.')
            data['project_id'] = project_id

            if action == 'list':
                result = client.list_workflows_in_project(project_id)
                return fmt(result)

            elif action == 'get':
                if not workflow_name:
                    return err('workflow_name required for get.')
                exists, global_id = client.check_if_workflow_exists(project_id, workflow_name)
                data['exists'] = exists
                if exists:
                    data['global_id'] = global_id
                    details, e = safe_call(
                        'details',
                        client.get_workflow_by_id, global_id)
                    if details:
                        data['details'] = details
                return json.dumps(data, indent=2, default=str)

            elif action == 'check_exists':
                if not workflow_name:
                    return err('workflow_name required for check_exists.')
                exists, global_id = client.check_if_workflow_exists(project_id, workflow_name)
                data['exists'] = exists
                if exists:
                    data['global_id'] = global_id
                return json.dumps(data, indent=2, default=str)

            else:
                return err(f'Unknown action: {action}. Use list/get/check_exists.')
        except Exception as exc:
            return err(str(exc))


# ── Private helpers ───────────────────────────────────────────────────

def _build_simple_dataflow_payload(project_name, dataflow_name,
                                    src_conn, src_schema, src_table,
                                    tgt_conn, tgt_schema, tgt_table,
                                    integration_type):
    '''Build a minimal dataflow JSON payload for the REST API.

    This is the fallback when the SDK builder classes are not available.
    '''
    return {
        'name': dataflow_name,
        'projectName': project_name,
        'sources': [{
            'connectionName': src_conn,
            'schemaName': src_schema,
            'dataEntityName': src_table,
            'operatorName': 'SRC',
        }],
        'targets': [{
            'connectionName': tgt_conn,
            'schemaName': tgt_schema,
            'dataEntityName': tgt_table,
            'operatorName': 'TGT',
            'integrationType': integration_type,
        }],
        'connections': [
            {'from': 'SRC', 'to': 'TGT'}
        ]
    }
