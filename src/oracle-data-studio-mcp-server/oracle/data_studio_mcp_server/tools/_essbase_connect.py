# Copyright (c) 2025, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

'''Shared Essbase connection helper for upleveled tools.

Usage in tool modules::

    from ._essbase_connect import get_essbase

    @mcp.tool()
    def essbase_explore(ctx: Context) -> str:
        ess = get_essbase(ctx)
        if not ess:
            return err('Essbase not connected. Set ESSBASE_URL + credentials.')
        ...
'''

import logging
from mcp.server.fastmcp import Context

logger = logging.getLogger('oracle-data-studio-mcp')

_NO_CONN_MSG = ('Essbase not connected. '
                'Set ESSBASE_URL, ESSBASE_USER, ESSBASE_PASSWORD '
                'or ESSBASE_TOKEN.')


def get_essbase(ctx: Context):
    '''Return the Essbase client from the lifespan context, or None.'''
    lc = ctx.request_context.lifespan_context
    return lc.get('essbase')
