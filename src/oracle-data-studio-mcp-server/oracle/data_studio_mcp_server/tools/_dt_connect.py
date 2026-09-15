# Copyright (c) 2025, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

'''
Lazy connection helper for Data Transforms.

On ADBS deployments the DT container can be idle at server startup.
This helper defers connection to the first DT tool call.  It tries
three strategies in order:

1. Check if adp.login()'s background thread already connected the
   DataTransformsWorkbench (stored on the Adp object).
2. Use the ADP connection to query dba_pdbs for OCI params (tenancy,
   ADW OCID) and call connect_workbench with the full ADBS-style dict.
3. Fall back to simple URL auth (for non-ADBS / marketplace deployments).
'''

import sys
import logging
from mcp.server.fastmcp import Context

logger = logging.getLogger('oracle-data-studio-mcp')

# SQL used by adp.login() to discover OCI identity
_DBA_PDBS_SQL = """
SELECT
  JSON_VALUE(cloud_identity, '$.DATABASE_NAME') AS database_name,
  JSON_VALUE(cloud_identity, '$.DATABASE_OCID') AS cloud_database_name,
  JSON_VALUE(cloud_identity, '$.TENANT_OCID')   AS tenant_name
FROM dba_pdbs
"""


def _reset_singletons():
    '''Reset DataTransformsWorkbench and DataTransformsClient singletons.'''
    try:
        from datatransforms.workbench import DataTransformsWorkbench
        DataTransformsWorkbench._instance = None
        if hasattr(DataTransformsWorkbench, 'initialized'):
            del DataTransformsWorkbench.initialized
    except ImportError:
        pass
    try:
        from datatransforms.client import DataTransformsClient
        DataTransformsClient._instance = None
        if hasattr(DataTransformsClient, '_instances'):
            DataTransformsClient._instances.pop(DataTransformsClient, None)
        if hasattr(DataTransformsClient, 'initialized'):
            del DataTransformsClient.initialized
        DataTransformsClient.connected = False
    except ImportError:
        pass


def _try_from_adp_thread(adp_client):
    '''Strategy 1: get workbench from adp.login() background thread.'''
    if adp_client is None:
        return None
    try:
        adp_client.wait_for_datatransforms(timeout=300)
        wb = getattr(adp_client, 'dt', None)
        if wb:
            return {'workbench': wb, 'client': wb.get_client()}
    except Exception as e:
        logger.debug('DT from ADP thread failed: %s', e)
    return None


def _try_adbs_connect(adp_client, cfg):
    '''Strategy 2: query OCI params via ADP and do ADBS token connect.'''
    if adp_client is None or cfg is None:
        return None
    try:
        rows = adp_client.Misc.run_query(_DBA_PDBS_SQL)
        if not (isinstance(rows, list) and len(rows) > 0):
            logger.debug('DT lazy: dba_pdbs query returned no rows')
            return None
        row = rows[0]

        connect_params = {
            'xforms_url': cfg.url,
            'data_transforms_url': cfg.url,
            'data_transforms_user': cfg.user,
            'xforms_user': cfg.user,
            'pswd': cfg.password,
            'tenancy_ocid': row['tenant_name'],
            'adw_name': row['database_name'],
            'adw_ocid': row['cloud_database_name'],
        }

        _reset_singletons()

        from datatransforms.workbench import DataTransformsWorkbench
        wb = DataTransformsWorkbench()
        wb.connect_workbench(connect_params)
        logger.info('Data Transforms lazy-connected (ADBS) to %s', cfg.url)
        return {'workbench': wb, 'client': wb.get_client()}
    except Exception as e:
        logger.warning('DT ADBS lazy connect failed: %s', e)
        print(f'DT ADBS lazy connect failed: {e}', file=sys.stderr, flush=True)
    return None


def _try_simple_connect(cfg):
    '''Strategy 3: simple URL + Basic auth (non-ADBS deployments).'''
    if cfg is None:
        return None
    try:
        _reset_singletons()

        from datatransforms.workbench import DataTransformsWorkbench
        wb = DataTransformsWorkbench()
        wb.connect_workbench({
            'data_transforms_url': cfg.url,
            'data_transforms_user': cfg.user,
            'pswd': cfg.password,
        })
        logger.info('Data Transforms lazy-connected (simple) to %s', cfg.url)
        return {'workbench': wb, 'client': wb.get_client()}
    except Exception as e:
        logger.debug('DT simple lazy connect failed: %s', e)
    return None


def get_dt(ctx: Context):
    '''Return the DT connection dict, attempting lazy connect if needed.'''
    lc = ctx.request_context.lifespan_context

    # Already connected
    dt = lc.get('datatransforms')
    if dt:
        return dt

    cfg = lc.get('_dt_config')
    if not cfg:
        return None  # not configured at all

    adp_client = lc.get('adp')

    logger.info('DT lazy connect: attempting connection to %s', cfg.url)
    print(f'DT lazy connect: attempting connection to {cfg.url}',
          file=sys.stderr, flush=True)

    # Strategy 1 — ADP background thread
    dt = _try_from_adp_thread(adp_client)
    if dt:
        lc['datatransforms'] = dt
        logger.info('DT connected via ADP background thread')
        return dt

    # Strategy 2 — ADBS token via OCI params
    dt = _try_adbs_connect(adp_client, cfg)
    if dt:
        lc['datatransforms'] = dt
        return dt

    # Strategy 3 — simple URL auth (marketplace / non-ADBS)
    dt = _try_simple_connect(cfg)
    if dt:
        lc['datatransforms'] = dt
        return dt

    logger.warning('Data Transforms lazy connect: all strategies failed')
    return None
