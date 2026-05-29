# Copyright (c) 2025, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

'''Upleveled ADP (Autonomous Database) MCP tools.

Each tool combines multiple SDK calls into a single task-oriented
operation that returns an LLM-friendly result.  See TOOLS_DESIGN.md.
'''

import json
import logging

from mcp.server.fastmcp import FastMCP, Context

from ._adp_connect import get_adp, run_adp, _err, _NO_CONN_MSG
from ._helpers import safe_call, build_response, err, fmt

logger = logging.getLogger('oracle-data-studio-mcp')


def register_tools(mcp: FastMCP):

    # NOTE: Pure SQL tools (execute_sql, discover_schema, explain_table,
    # modify_data) are intentionally omitted — use Oracle SQLcl MCP
    # server for direct SQL operations.  The tools below focus on ADP
    # data-platform features: Analytic Views, Select AI, Insights,
    # cloud loading, catalogs, and data sharing.

    # ── adp_build_analytic_view ─────────────────────────────────────
    @mcp.tool()
    def adp_build_analytic_view(fact_table: str,
                                 av_name: str = None,
                                 ctx: Context = None) -> str:
        """Create an Analytic View from a fact table, compile it, and return metadata with a data preview.

        Args:
            fact_table: Name of the fact table.
            av_name: Optional — currently informational only.
                The SDK's auto-creation derives the AV name from the
                fact table; if a different name is required, use
                `client.Analytics.create()` directly with explicit
                dimensions and measures.
        """
        client = get_adp(ctx)
        if not client:
            return err(_NO_CONN_MSG)
        try:
            errors = []
            data = {'fact_table': fact_table}
            if av_name:
                data['av_name_requested'] = av_name
                errors.append(
                    'av_name parameter is informational only — the auto '
                    'creator derives the AV name from the fact table. '
                    'Use Analytics.create() with explicit dims/measures '
                    'to specify a custom name.')

            # Create — Analytics.create_auto signature is
            # (fact_table, skip_dimensions: bool = False, owner: str = None).
            # Do NOT pass av_name here — it would be coerced to a truthy
            # `skip_dimensions` and silently dropped.
            create_result = client.Analytics.create_auto(fact_table)
            data['create'] = json.loads(create_result) if isinstance(
                create_result, str) else create_result

            # Determine actual AV name from the create result
            actual_name = fact_table
            if isinstance(data['create'], dict):
                actual_name = data['create'].get('name', actual_name)

            # Compile
            compile_result, e = safe_call('compile',
                                          client.Analytics.compile,
                                          actual_name)
            if compile_result:
                data['compile'] = json.loads(compile_result) if isinstance(
                    compile_result, str) else compile_result
            if e:
                errors.append(e)

            # Metadata
            meta, e = safe_call('metadata',
                                client.Analytics.get_metadata,
                                actual_name)
            if meta:
                data['metadata'] = json.loads(meta) if isinstance(
                    meta, str) else meta
            if e:
                errors.append(e)

            # Preview
            preview, e = safe_call('preview',
                                   client.Analytics.get_data_preview,
                                   actual_name)
            if preview:
                data['data_preview'] = json.loads(preview) if isinstance(
                    preview, str) else preview
            if e:
                errors.append(e)

            return build_response(data, errors or None)
        except Exception as exc:
            return err(str(exc))

    # ── 18. adp_query_analytic_view ───────────────────────────────────
    @mcp.tool()
    def adp_query_analytic_view(av_name: str,
                                 show_sql: bool = False,
                                 owner: str = None,
                                 max_rows: int = 1000,
                                 ctx: Context = None) -> str:
        """Query data from an Analytic View with auto-discovered dimensions and measures.

        Results are row-capped at `max_rows` (default 1000). When the
        cap fires, the response is wrapped in
        ``{"rows": [...], "truncated": true, "original_row_count": N,
        "max_rows": M}`` so the caller can decide whether to re-query
        with a tighter filter.

        Args:
            av_name: Analytic View name.
            show_sql: If true, return the generated SQL instead of data.
            owner: Schema owner (defaults to current user).
            max_rows: Maximum rows to return (default 1000).
        """
        from ._helpers import bound_rows
        client = get_adp(ctx)
        if not client:
            return err(_NO_CONN_MSG)
        try:
            if not client.Analytics.is_exist(av_name, owner):
                return err(f'Analytic view "{av_name}" does not exist.')

            if show_sql:
                result = client.Analytics.get_sql_simple(av_name, owner)
                if isinstance(result, str):
                    return result
                return json.dumps(result, indent=2, default=str)

            # Data path: apply the row cap and surface truncation flag.
            rows = client.Analytics.get_data_simple(av_name, owner)
            # SDK may return a list, a JSON-string list, or an envelope dict.
            if isinstance(rows, str):
                try:
                    rows = json.loads(rows)
                except ValueError:
                    return rows
            if isinstance(rows, dict):
                inner = rows.get('items') or rows.get('rows')
                if isinstance(inner, list):
                    rows = inner
            bounded = bound_rows(rows, max_rows=max_rows)
            return json.dumps(bounded, indent=2, default=str)
        except Exception as exc:
            return err(str(exc))

    # ── 19. adp_analyze_analytic_view ─────────────────────────────────
    @mcp.tool()
    def adp_analyze_analytic_view(av_name: str, owner: str = None,
                                   ctx: Context = None) -> str:
        """Get a full health report for an Analytic View: metadata, measures, dimensions, quality issues, errors.

        Args:
            av_name: Analytic View name.
            owner: Schema owner (defaults to current user).
        """
        client = get_adp(ctx)
        if not client:
            return err(_NO_CONN_MSG)
        try:
            if not client.Analytics.is_exist(av_name, owner):
                return err(f'Analytic view "{av_name}" does not exist.')

            errors = []
            data = {'av_name': av_name}

            meta, e = safe_call('metadata',
                                client.Analytics.get_metadata,
                                av_name, owner)
            if meta:
                data['metadata'] = json.loads(meta) if isinstance(
                    meta, str) else meta
            if e:
                errors.append(e)

            measures, e = safe_call('measures',
                                    client.Analytics.get_measures_list,
                                    av_name, owner)
            if measures:
                data['measures'] = json.loads(measures) if isinstance(
                    measures, str) else measures
            if e:
                errors.append(e)

            dims, e = safe_call('dimensions',
                                client.Analytics.get_dimension_names,
                                av_name)
            if dims:
                data['dimensions'] = json.loads(dims) if isinstance(
                    dims, str) else dims
            if e:
                errors.append(e)

            quality, e = safe_call('quality',
                                   client.Analytics.quality_report,
                                   av_name)
            if quality:
                data['quality_report'] = json.loads(quality) if isinstance(
                    quality, str) else quality
            if e:
                errors.append(e)

            return build_response(data, errors or None)
        except Exception as exc:
            return err(str(exc))

    # ── 20. adp_generate_insights ─────────────────────────────────────
    @mcp.tool()
    def adp_generate_insights(object_name: str, measure: str,
                               ctx: Context = None) -> str:
        """Generate AI-powered insights for an Analytic View or table.

        Starts insight generation and returns the request details.

        Args:
            object_name: Analytic View or table name.
            measure: Measure column to analyze.
        """
        client = get_adp(ctx)
        if not client:
            return err(_NO_CONN_MSG)
        try:
            result = client.Insight.generate(object_name, measure)
            if isinstance(result, str):
                return result
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            return err(str(exc))

    # ── 21. (removed: adp_ai_query) ──────────────────────────────────
    # adp_ai_query was intentionally removed from the composite MCP.
    # Reasoning:
    #   1. Select AI is a separate LLM that does NOT reliably honor
    #      Oracle 23ai annotations (verified empirically). The MCP
    #      client's own LLM, given annotations via adp_get_annotations
    #      and the adp_sql_with_annotations prompt, produces strictly
    #      better SQL.
    #   2. Auto-executing LLM-generated SQL is a security surface
    #      even with safeguards. Pure SQL execution is delegated to
    #      the Oracle SQLcl MCP server by design.
    # If Select-AI-generated SQL is needed, call SQLcl + the AI
    # generator from the client side.

    # ── 22. adp_search ────────────────────────────────────────────────
    @mcp.tool()
    def adp_search(search_term: str, include_ddl: bool = False,
                    ctx: Context = None) -> str:
        """Search for database objects by name and optionally return their DDL.

        Args:
            search_term: Search term.
            include_ddl: Whether to fetch DDL for top matches (default false).
        """
        client = get_adp(ctx)
        if not client:
            return err(_NO_CONN_MSG)
        try:
            errors = []
            result_str = client.Misc.global_search(
                search_term, 1, 50)
            data = {'search_term': search_term}
            results = json.loads(result_str) if isinstance(
                result_str, str) else result_str
            data['results'] = results

            if include_ddl:
                names = _extract_entity_names(results)
                ddl_list = []
                for entry in names[:10]:
                    ddl, e = safe_call(
                        f'ddl/{entry}',
                        client.Misc.get_entity_ddl,
                        entry, 'TABLE')
                    if ddl:
                        ddl_list.append({
                            'name': entry,
                            'ddl': json.loads(ddl) if isinstance(
                                ddl, str) else ddl
                        })
                    if e:
                        errors.append(e)
                if ddl_list:
                    data['ddl'] = ddl_list

            return build_response(data, errors or None)
        except Exception as exc:
            return err(str(exc))

    # ── 23. adp_load_from_cloud ───────────────────────────────────────
    @mcp.tool()
    def adp_load_from_cloud(storage_link: str = None,
                             object_name: str = None,
                             target_table: str = None,
                             consumer_group: str = 'LOW',
                             request_id: str = None,
                             ctx: Context = None) -> str:
        """Load a cloud storage object into the database as a table.

        Pass request_id (without other params) to check load progress.
        Pass storage_link + object_name to start a new load.

        Requires an existing Cloud Storage link and credential (create
        them via SQLcl or the ADP console if you haven't already).

        Args:
            storage_link: Name of an existing Cloud Storage link (created via DBMS_CLOUD.CREATE_CLOUD_STORAGE_LINK or the ADP UI).
            object_name: Object name (file) in the cloud storage link (e.g. 'sales_2024.csv', 'data/orders.parquet').
            target_table: Table name to create in the database. Defaults to a name derived from the object.
            consumer_group: Resource consumer group for the load job: 'LOW' (default), 'MEDIUM', or 'HIGH'.
            request_id: Request ID from a previous load to check progress.
        """
        client = get_adp(ctx)
        if not client:
            return err(_NO_CONN_MSG)
        try:
            # Progress check mode
            if request_id:
                progress, e = safe_call('progress',
                                         client.Ingest.cloud_progress_status,
                                         request_id)
                data = {'request_id': request_id}
                if progress:
                    data['progress'] = json.loads(progress) if isinstance(
                        progress, str) else progress
                errors = [e] if e else []
                return build_response(data, errors or None)

            if not storage_link or not object_name:
                return err('storage_link and object_name required to start a load, '
                           'or provide request_id to check progress.')

            errors = []
            data = {'storage_link': storage_link,
                    'object_name': object_name}

            # Verify credentials exist
            creds, e = safe_call('credentials',
                                 client.Ingest.get_credential_list)
            if creds:
                data['available_credentials'] = json.loads(
                    creds) if isinstance(creds, str) else creds
            if e:
                errors.append(e)

            # List consumer groups
            groups, e = safe_call('consumer_groups',
                                   client.Ingest.get_consumer_groups)
            if groups:
                data['consumer_groups'] = json.loads(
                    groups) if isinstance(groups, str) else groups
            if e:
                errors.append(e)

            # Build the objects list expected by the SDK
            obj_spec = {
                'storageLink': storage_link,
                'objectName': object_name,
            }
            if target_table:
                obj_spec['targetTableName'] = target_table
                data['target_table'] = target_table

            # Copy from cloud
            result = client.Ingest.copy_cloud_objects(
                [obj_spec], consumer_group)
            if isinstance(result, str):
                data['result'] = json.loads(result)
            else:
                data['result'] = result

            return build_response(data, errors or None)
        except Exception as exc:
            return err(str(exc))

    # ── 24. adp_browse_catalog ──────────────────────────────────────────
    @mcp.tool()
    def adp_browse_catalog(action: str, catalog_name: str = None,
                            ctx: Context = None) -> str:
        """Browse data catalogs (read-only): list catalogs, get entities, preview data, list database links, list databases, or check a database link.

        Args:
            action: One of 'list', 'entities', 'preview', 'db_links', 'list_databases', 'check_db_link'.
            catalog_name: Catalog or entity name (required for all actions except list/list_databases). Used as db_link_name for check_db_link.
        """
        client = get_adp(ctx)
        if not client:
            return err(_NO_CONN_MSG)
        try:
            if action == 'list':
                result = client.Catalog.get_catalogs()
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'entities':
                if not catalog_name:
                    return err('catalog_name required for entities action.')
                result = client.Catalog.get_catalog_entities(catalog_name)
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'preview':
                if not catalog_name:
                    return err('catalog_name required for preview action.')
                result = client.Catalog.preview_catalog_table(
                    catalog_name)
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'db_links':
                if not catalog_name:
                    return err('catalog_name required for db_links action.')
                result = client.Catalog.get_database_links(catalog_name)
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'list_databases':
                result = client.Catalog.get_autonomous_databases()
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'check_db_link':
                if not catalog_name:
                    return err('catalog_name required for check_db_link action (used as db_link_name).')
                result = client.Catalog.check_database_link(catalog_name)
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            else:
                return err(f'Unknown action: {action}. '
                           f'Use list/entities/preview/'
                           f'db_links/list_databases/check_db_link.')
        except Exception as exc:
            return err(str(exc))

    # ── 24b. adp_manage_catalog ──────────────────────────────────────
    @mcp.tool()
    def adp_manage_catalog(action: str, catalog_name: str = None,
                            ctx: Context = None) -> str:
        """Manage data catalogs (admin-only): enable, disable, or unmount catalogs.

        Args:
            action: One of 'enable', 'disable', 'unmount'.
            catalog_name: Catalog name (required).
        """
        client = get_adp(ctx)
        if not client:
            return err(_NO_CONN_MSG)
        try:
            if not catalog_name:
                return err('catalog_name required.')
            if action == 'enable':
                result = client.Catalog.enable_catalog(catalog_name)
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'disable':
                result = client.Catalog.disable_catalog(catalog_name)
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'unmount':
                result = client.Catalog.unmount_catalog(catalog_name)
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            else:
                return err(f'Unknown action: {action}. '
                           f'Use enable/disable/unmount.')
        except Exception as exc:
            return err(str(exc))

    # ── 25. adp_manage_sharing ────────────────────────────────────────
    @mcp.tool()
    def adp_manage_sharing(action: str, share_name: str = None,
                            tables: str = None,
                            recipient_name: str = None,
                            email: str = None,
                            new_name: str = None,
                            ctx: Context = None) -> str:
        """Manage data sharing: list shares, create share, publish, delete, manage recipients, providers, and more.

        Args:
            action: One of 'list', 'get', 'create', 'publish',
                'grant_recipient', 'delete', 'unpublish',
                'create_recipient', 'list_recipients', 'delete_recipient',
                'get_objects', 'rename', 'list_providers',
                'create_provider', 'delete_provider'.
            share_name: Share name (for create/publish/get/delete/
                unpublish/get_objects/rename/grant_recipient).
            tables: Comma-separated table names (for create or
                grant_recipient — the shares granted to the recipient).
            recipient_name: Recipient name (for create_recipient/
                delete_recipient/create_provider/delete_provider/
                grant_recipient).
            email: Email address (optional, for create_recipient/create_provider).
            new_name: New name for renaming a share (for rename action).

        NOTE: `publish` activates the share globally; it does NOT take a
        recipient. To grant a published share to a specific recipient,
        call action='grant_recipient' with recipient_name + tables.
        """
        client = get_adp(ctx)
        if not client:
            return err(_NO_CONN_MSG)
        try:
            if action == 'list':
                result = client.Share.get_shares()
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'get':
                if not share_name:
                    return err('share_name required.')
                result = client.Share.get_share(share_name)
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'create':
                if not share_name:
                    return err('share_name required for create.')
                result = client.Share.create_share(share_name)
                data = {'create': json.loads(result) if isinstance(
                    result, str) else result}
                if tables:
                    table_list = [t.strip() for t in tables.split(',')]
                    upd, e = safe_call(
                        'update_objects',
                        client.Share.update_share_objects,
                        share_name, table_list)
                    if upd:
                        data['objects'] = json.loads(upd) if isinstance(
                            upd, str) else upd
                return json.dumps(data, indent=2, default=str)
            elif action == 'publish':
                if not share_name:
                    return err('share_name required for publish.')
                # publish_share(name, owner=None) — does NOT take a
                # recipient. Recipients are granted separately via
                # action='grant_recipient'.
                result = client.Share.publish_share(share_name)
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'grant_recipient':
                if not recipient_name or not tables:
                    return err('recipient_name and tables (comma-separated '
                               'share names) required for grant_recipient.')
                result = client.Share.update_recipient_shares(
                    recipient_name, tables)
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'delete':
                if not share_name:
                    return err('share_name required for delete.')
                result = client.Share.delete_share(share_name)
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'unpublish':
                if not share_name:
                    return err('share_name required for unpublish.')
                result = client.Share.unpublish_share(share_name)
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'create_recipient':
                if not recipient_name:
                    return err('recipient_name required for create_recipient.')
                result = client.Share.create_recipient(
                    recipient_name, email=email)
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'list_recipients':
                result = client.Share.get_recipients()
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'delete_recipient':
                if not recipient_name:
                    return err('recipient_name required for delete_recipient.')
                result = client.Share.delete_recipient(recipient_name)
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'get_objects':
                if not share_name:
                    return err('share_name required for get_objects.')
                result = client.Share.get_share_objects(share_name)
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'rename':
                if not share_name or not new_name:
                    return err('share_name and new_name required for rename.')
                result = client.Share.rename_share(share_name, new_name)
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'list_providers':
                result = client.Share.get_providers()
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'create_provider':
                if not recipient_name:
                    return err('recipient_name required for create_provider.')
                result = client.Share.create_provider(
                    recipient_name, email=email or '')
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'delete_provider':
                if not recipient_name:
                    return err('recipient_name required for delete_provider.')
                result = client.Share.delete_provider(recipient_name)
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            else:
                return err(f'Unknown action: {action}. '
                           f'Use list/get/create/publish/grant_recipient/'
                           f'delete/unpublish/create_recipient/'
                           f'list_recipients/delete_recipient/'
                           f'get_objects/rename/list_providers/'
                           f'create_provider/delete_provider.')
        except Exception as exc:
            return err(str(exc))


    # ── 26. adp_manage_analytic_views ────────────────────────────────
    @mcp.tool()
    def adp_manage_analytic_views(action: str,
                                    av_name: str = None,
                                    owner: str = None,
                                    confirm: str = None,
                                    ctx: Context = None) -> str:
        """Manage Analytic Views: list all AVs or drop one.

        Destructive actions (`drop`) require `confirm` to match
        `av_name` exactly — guards against prompt-injected deletions.

        Args:
            action: One of 'list', 'drop'.
            av_name: Analytic View name (required for drop).
            owner: Schema owner (optional, for list).
            confirm: For drop: must equal `av_name`.
        """
        from ._helpers import require_confirm
        client = get_adp(ctx)
        if not client:
            return err(_NO_CONN_MSG)
        try:
            if action == 'list':
                result = client.Analytics.get_list(owner)
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'drop':
                if not av_name:
                    return err('av_name required for drop action.')
                msg = require_confirm(av_name, confirm,
                                       action_label='drop analytic view')
                if msg:
                    return err(msg)
                result = client.Analytics.drop(av_name)
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            else:
                return err(f'Unknown action: {action}. '
                           f'Use list/drop.')
        except Exception as exc:
            return err(str(exc))

    # ── 27. adp_manage_credentials ───────────────────────────────────
    @mcp.tool()
    def adp_manage_credentials(action: str,
                                 credential_name: str = None,
                                 username: str = None,
                                 password: str = None,
                                 user_ocid: str = None,
                                 tenancy_ocid: str = None,
                                 private_key: str = None,
                                 fingerprint: str = None,
                                 storage_link_name: str = None,
                                 uri: str = None,
                                 description: str = None,
                                 ctx: Context = None) -> str:
        """Manage cloud credentials and storage links for data loading.

        Args:
            action: One of 'list', 'create', 'create_ocid', 'drop', 'list_storage_links', 'create_storage_link', 'drop_storage_link', 'list_cloud_objects'.
            credential_name: Credential name (for create/create_ocid/drop/create_storage_link).
            username: Username (for create).
            password: Password (for create).
            user_ocid: User OCID (for create_ocid).
            tenancy_ocid: Tenancy OCID (for create_ocid).
            private_key: Private key (for create_ocid).
            fingerprint: Key fingerprint (for create_ocid).
            storage_link_name: Storage link name (for create_storage_link/drop_storage_link/list_cloud_objects).
            uri: URI for cloud storage (for create_storage_link).
            description: Description (optional, for create_storage_link).
        """
        client = get_adp(ctx)
        if not client:
            return err(_NO_CONN_MSG)
        try:
            if action == 'list':
                result = client.Ingest.get_credential_list()
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'create':
                if not credential_name or not username or not password:
                    return err('credential_name, username, and password '
                               'required for create.')
                result = client.Ingest.create_credential(
                    credential_name, username, password)
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'create_ocid':
                if not all([credential_name, user_ocid, tenancy_ocid,
                            private_key, fingerprint]):
                    return err('credential_name, user_ocid, tenancy_ocid, '
                               'private_key, and fingerprint required '
                               'for create_ocid.')
                result = client.Ingest.create_ocid_credential(
                    credential_name, user_ocid, tenancy_ocid,
                    private_key, fingerprint)
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'drop':
                if not credential_name:
                    return err('credential_name required for drop.')
                result = client.Ingest.drop_credential(credential_name)
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'list_storage_links':
                result = client.Ingest.get_cloud_storage_link_list()
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'create_storage_link':
                if not storage_link_name or not uri or not credential_name:
                    return err('storage_link_name, uri, and credential_name '
                               'required for create_storage_link.')
                result = client.Ingest.create_cloud_storage_link(
                    storage_link_name, uri, credential_name,
                    description or '')
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'drop_storage_link':
                if not storage_link_name:
                    return err('storage_link_name required for '
                               'drop_storage_link.')
                result = client.Ingest.drop_cloud_storage_link(
                    storage_link_name)
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'list_cloud_objects':
                if not storage_link_name:
                    return err('storage_link_name required for '
                               'list_cloud_objects.')
                result = client.Ingest.get_cloud_objects(
                    storage_link_name)
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            else:
                return err(f'Unknown action: {action}. '
                           f'Use list/create/create_ocid/drop/'
                           f'list_storage_links/create_storage_link/'
                           f'drop_storage_link/list_cloud_objects.')
        except Exception as exc:
            return err(str(exc))

    # ── 28. adp_ai_chat ──────────────────────────────────────────────
    @mcp.tool()
    def adp_ai_chat(question: str,
                      mode: str = 'chat',
                      tables: str = None,
                      profile_name: str = None,
                      max_rows: int = 1000,
                      ctx: Context = None) -> str:
        """Chat with the database using Oracle Select AI in different modes.

        The returned payload is wrapped in an "untrusted-output"
        envelope (`{"source": "select_ai", "untrusted": true, ...}`)
        because the response interleaves LLM-generated text with DB
        query results — callers must not feed it back into another
        tool unchecked. Row results are capped at `max_rows`.

        When `MCP_AI_CHAT_ALLOWED_TABLES` is set, every requested table
        must match the allowlist. When `MCP_AI_CHAT_DENIED_TABLES` is
        set, no requested table may match it. Both can coexist;
        deny wins.

        Args:
            question: Natural language question or prompt.
            mode: One of 'chat', 'chat_with_db', 'generate_insight'.
            tables: Comma-separated table names (for chat_with_db /
                generate_insight). Required if
                MCP_AI_CHAT_ALLOWED_TABLES is set.
            profile_name: Select AI profile name (optional).
            max_rows: Max rows from any DB-backed response. Default 1000.
        """
        from ._helpers import check_ai_chat_tables, ai_chat_envelope
        client = get_adp(ctx)
        if not client:
            return err(_NO_CONN_MSG)

        # Table-policy gate. Pulled from the lifespan context which is
        # populated from env at startup.
        lc = (ctx.request_context.lifespan_context
              if ctx is not None else {})
        policy_err = check_ai_chat_tables(
            tables,
            allowed=lc.get('_ai_chat_allowed_tables'),
            denied=lc.get('_ai_chat_denied_tables'))
        if policy_err:
            return err(policy_err)

        try:
            table_list = None
            if tables:
                owner = client.rest.username if hasattr(
                    client, 'rest') else None
                table_list = [(owner, t.strip())
                              for t in tables.split(',')]

            if mode == 'chat':
                result = client.AI.chat(question, profile_name)
            elif mode == 'chat_with_db':
                result = client.AI.chat_with_db(
                    question, table_list, profile_name)
            elif mode == 'generate_insight':
                result = client.AI.generate_insight(
                    question, table_list, profile_name)
            else:
                return err(f'Unknown mode: {mode}. '
                           f'Use chat/chat_with_db/generate_insight.')

            # Normalise: some SDK paths return a JSON string instead of
            # a dict / list. Parse so the envelope sees structured data.
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except (json.JSONDecodeError, TypeError):
                    pass

            envelope = ai_chat_envelope(result, mode=mode,
                                         max_rows=max_rows)
            return json.dumps(envelope, indent=2, default=str)
        except Exception as exc:
            return err(str(exc))

    # ── 29. adp_manage_insights ──────────────────────────────────────
    @mcp.tool()
    def adp_manage_insights(action: str,
                              request_name: str = None,
                              insight_name: str = None,
                              viz_id: int = None,
                              ctx: Context = None) -> str:
        """Manage AI-generated insights: list requests, view results, check status.

        Args:
            action: One of 'list_requests', 'list_insights', 'get_graph', 'status', 'drop'.
            request_name: Insight request name (for list_insights/get_graph/status/drop).
            insight_name: Insight name (for get_graph).
            viz_id: Visualization ID (for get_graph).
        """
        client = get_adp(ctx)
        if not client:
            return err(_NO_CONN_MSG)
        try:
            if action == 'list_requests':
                result = client.Insight.get_request_list()
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'list_insights':
                if not request_name:
                    return err('request_name required for list_insights.')
                result = client.Insight.get_insights_list(request_name)
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'get_graph':
                name = insight_name or request_name
                if not name or viz_id is None:
                    return err('insight_name (or request_name) and viz_id '
                               'required for get_graph.')
                result = client.Insight.get_graph_details(name, viz_id)
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'status':
                if not request_name:
                    return err('request_name required for status.')
                result = client.Insight.get_job_status(request_name)
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'drop':
                if not request_name:
                    return err('request_name required for drop.')
                result = client.Insight.drop(request_name)
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            else:
                return err(f'Unknown action: {action}. '
                           f'Use list_requests/list_insights/get_graph/'
                           f'status/drop.')
        except Exception as exc:
            return err(str(exc))

    # ── 30. adp_manage_db_links ────────────────────────────────────────
    @mcp.tool()
    def adp_manage_db_links(action: str,
                              db_link_name: str = None,
                              tables: str = None,
                              consumer_group: str = 'LOW',
                              ctx: Context = None) -> str:
        """Manage database links and copy/link tables from remote databases.

        Args:
            action: One of 'list', 'list_tables', 'copy_tables', 'link_tables', 'check', 'drop'.
            db_link_name: Database link name (required for list_tables/copy_tables/link_tables/check/drop).
            tables: Comma-separated table names for copy_tables/link_tables.
            consumer_group: Resource consumer group: 'LOW' (default), 'MEDIUM', 'HIGH'.
        """
        client = get_adp(ctx)
        if not client:
            return err(_NO_CONN_MSG)
        try:
            if action == 'list':
                result = client.Ingest.get_database_links()
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'list_tables':
                if not db_link_name:
                    return err('db_link_name required for list_tables.')
                result = client.Ingest.get_db_link_owner_tables(
                    db_link_name)
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'copy_tables':
                if not db_link_name or not tables:
                    return err('db_link_name and tables required for '
                               'copy_tables.')
                table_descs = [{'tableName': t.strip(),
                                'dbLink': db_link_name}
                               for t in tables.split(',')]
                result = client.Ingest.copy_tables_from_db_link(
                    table_descs, consumer_group)
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'link_tables':
                if not db_link_name or not tables:
                    return err('db_link_name and tables required for '
                               'link_tables.')
                table_descs = [{'tableName': t.strip(),
                                'dbLink': db_link_name}
                               for t in tables.split(',')]
                result = client.Ingest.link_tables_from_db_link(
                    table_descs, consumer_group)
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'check':
                if not db_link_name:
                    return err('db_link_name required for check.')
                result = client.Catalog.check_database_link(
                    db_link_name)
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            elif action == 'drop':
                if not db_link_name:
                    return err('db_link_name required for drop.')
                result = client.Catalog.drop_database_link(
                    db_link_name)
                return fmt(json.loads(result) if isinstance(
                    result, str) else result)
            else:
                return err(f'Unknown action: {action}. '
                           f'Use list/list_tables/copy_tables/'
                           f'link_tables/check/drop.')
        except Exception as exc:
            return err(str(exc))

    # ── adp_get_annotations ─────────────────────────────────────────
    @mcp.tool()
    def adp_get_annotations(object_name: str,
                              object_type: str = 'TABLE',
                              annotation_owner: str = None,
                              column_name: str = None,
                              ctx: Context = None) -> str:
        """Fetch Oracle 23ai annotations on a table/view and its columns — useful for NL→SQL.

        Annotations carry semantic metadata (description, display_name,
        data_class, join_hint, unit, aggregate, etc.) that helps an LLM
        generate correct SQL without guessing from column names.

        Reads from ALL_ANNOTATIONS_USAGE. Annotation names come back
        UPPERCASE (Oracle stores them that way). Returns a tidy structure:
            {
              "object": "SALES",
              "annotations": {
                "table":   {"DESCRIPTION": "...", "DATA_DOMAIN": "..."},
                "columns": {
                  "CUST_ID":   {"DISPLAY_NAME": "Customer", ...},
                  "AMOUNT":    {"UNIT": "USD", "AGGREGATE": "SUM"},
                  ...
                }
              }
            }

        Args:
            object_name: Table/view name (case-insensitive).
            object_type: TABLE | VIEW | MATERIALIZED VIEW (default TABLE).
            annotation_owner: Optional — filter by the user who defined the
                annotation (ALL_ANNOTATIONS_USAGE.ANNOTATION_OWNER). The
                annotations view itself is implicitly scoped to objects
                visible to the current user, so there is no object-owner
                filter to apply.
            column_name: Optional — fetch annotations for a single column only.
        """
        client = get_adp(ctx)
        if not client:
            return err(_NO_CONN_MSG)
        try:
            # Build the query — quote the identifier literals properly
            where = ["UPPER(object_name) = UPPER('{0}')".format(
                object_name.replace("'", "''"))]
            if object_type:
                where.append("UPPER(object_type) = UPPER('{0}')".format(
                    object_type.replace("'", "''")))
            if annotation_owner:
                where.append(
                    "UPPER(annotation_owner) = UPPER('{0}')".format(
                        annotation_owner.replace("'", "''")))
            if column_name:
                where.append("UPPER(column_name) = UPPER('{0}')".format(
                    column_name.replace("'", "''")))

            sql = (
                "SELECT object_name, object_type, column_name, "
                "annotation_owner, annotation_name, annotation_value "
                "FROM all_annotations_usage "
                "WHERE " + " AND ".join(where) + " "
                "ORDER BY column_name NULLS FIRST, annotation_name"
            )

            raw = client.Misc.run_query(sql)
            rows = json.loads(raw) if isinstance(raw, str) else raw

            # Normalize — run_query can return either a bare list of row
            # dicts OR an ORDS envelope {'items': [...]}. Handle both.
            if isinstance(rows, dict):
                rows = rows.get('items', rows.get('rows', []))

            data = {
                'object': object_name.upper(),
                'object_type': object_type.upper() if object_type else None,
                'annotation_owner_filter':
                    annotation_owner.upper() if annotation_owner else None,
                'annotations': {'table': {}, 'columns': {}},
                'annotation_count': 0,
            }
            for row in rows or []:
                # Rows may come back with lowercase or uppercase keys.
                if isinstance(row, dict):
                    col = row.get('column_name') or row.get('COLUMN_NAME')
                    nm = (row.get('annotation_name')
                          or row.get('ANNOTATION_NAME'))
                    val = (row.get('annotation_value')
                           or row.get('ANNOTATION_VALUE'))
                elif isinstance(row, list) and len(row) >= 6:
                    # obj, obj_type, col, ann_owner, ann_name, ann_value
                    col, nm, val = row[2], row[4], row[5]
                else:
                    continue
                if not nm:
                    continue
                data['annotation_count'] += 1
                if col:
                    data['annotations']['columns'].setdefault(col, {})[nm] = val
                else:
                    data['annotations']['table'][nm] = val

            if data['annotation_count'] == 0:
                data['note'] = (
                    'No annotations found. Requires Oracle 23ai and '
                    'annotations defined via CREATE/ALTER ... ANNOTATIONS(...). '
                    'Check that ALL_ANNOTATIONS_USAGE is accessible.')

            return fmt(data)
        except Exception as exc:
            return err(str(exc))

    # ── Prompt: adp_sql_with_annotations ────────────────────────────
    @mcp.prompt(
        description='Generate SQL for Oracle ADB using column/table '
                    'annotations as semantic hints. Instructs the '
                    'assistant to call adp_get_annotations first.')
    def adp_sql_with_annotations(question: str, tables: str) -> str:
        """Prompt template — annotation-aware SQL generation.

        Args:
            question: The natural-language question to answer with SQL.
            tables: Comma-separated list of candidate tables/views.
        """
        return (
            "You are writing SQL for an Oracle Autonomous Database (23ai).\n\n"
            "Task: answer the question below with a single SQL statement.\n\n"
            f"QUESTION:\n{question}\n\n"
            f"CANDIDATE TABLES: {tables}\n\n"
            "Process:\n"
            "1. For each candidate table, call `adp_get_annotations` to "
            "fetch its table- and column-level annotations.\n"
            "2. Use the annotations as semantic hints:\n"
            "   - `description` / `display_name` — confirm table/column meaning\n"
            "   - `data_class` / `pii` — avoid PII unless explicitly requested\n"
            "   - `join_hint` — prefer these keys when joining\n"
            "   - `unit` — keep unit-consistency in arithmetic/filters\n"
            "   - `aggregate` — use the suggested aggregation function\n"
            "   - `role` / `grain` — honor time granularity (DAY/MONTH/YEAR)\n"
            "3. If annotations conflict with the question, ask before guessing.\n"
            "4. If no annotations exist, fall back to column names + "
            "`adp_search` (include_ddl=true) to inspect DDL.\n"
            "5. Return the final SQL in a fenced ```sql block, followed by a "
            "one-sentence rationale citing which annotations drove the choice."
        )


# ── Helpers ───────────────────────────────────────────────────────────

def _extract_entity_names(search_result):
    '''Extract entity names from an ADP global_search result.'''
    names = []
    if isinstance(search_result, dict):
        nodes = search_result.get('nodes', [])
        for node in nodes:
            d = node.get('data', {})
            name = d.get('name', d.get('entity_name', ''))
            if name:
                names.append(name)
    elif isinstance(search_result, list):
        for item in search_result:
            if isinstance(item, dict):
                name = item.get('name', item.get('entity_name', ''))
                if name:
                    names.append(name)
    return names
