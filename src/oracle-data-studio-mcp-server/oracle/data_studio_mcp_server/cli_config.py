# Copyright (c) 2025, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

'''
CLI tool for managing Oracle Data Studio MCP Server credentials.

Usage:
    oracle-data-studio-config set essbase --url https://... --user admin
    oracle-data-studio-config set adp --url https://... --user admin --password secret
    oracle-data-studio-config set server --transport stdio --port 8000
    oracle-data-studio-config list
    oracle-data-studio-config remove essbase
'''

from __future__ import annotations

import sys
import argparse
import getpass
import json

from .credential_store import (
    store_credentials,
    remove_credentials,
    list_credentials,
    VALID_SERVICES,
)


def _cmd_set(args):
    '''Handle the "set" sub-command.'''
    service = args.service

    kwargs = {}
    if hasattr(args, 'url') and args.url:
        kwargs['url'] = args.url
    if hasattr(args, 'user') and args.user:
        kwargs['user'] = args.user

    # Server-specific options
    if hasattr(args, 'transport') and args.transport:
        kwargs['transport'] = args.transport
    if hasattr(args, 'port') and args.port:
        kwargs['port'] = args.port

    # Essbase-specific
    if hasattr(args, 'token') and args.token:
        kwargs['token'] = args.token

    # Password handling
    password = getattr(args, 'password', None)
    if service != 'server' and not password and args.user:
        # Prompt interactively if user is set but password is not
        password = getpass.getpass(f'Password for {args.user}: ')

    result = store_credentials(service, password=password, **kwargs)
    print(json.dumps(result, indent=2))

    if password and not result.get('keyring_stored'):
        print('\nWarning: Password could not be stored in OS keyring.',
              file=sys.stderr)
        print('Install the "keyring" package: pip install keyring',
              file=sys.stderr)


def _cmd_list(args):
    '''Handle the "list" sub-command.'''
    creds = list_credentials()
    if not creds:
        print('No credentials configured.')
        print(f'Use: oracle-data-studio-config set <service> --url ... --user ...')
        return
    for service, values in creds.items():
        print(f'\n[{service}]')
        for key, val in values.items():
            print(f'  {key} = {val}')


def _cmd_remove(args):
    '''Handle the "remove" sub-command.'''
    result = remove_credentials(args.service)
    print(json.dumps(result, indent=2))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='oracle-data-studio-config',
        description='Manage Oracle Data Studio MCP Server credentials')

    sub = parser.add_subparsers(dest='command', required=True)

    # -- set --
    set_parser = sub.add_parser('set', help='Store credentials for a service')
    set_parser.add_argument('service', choices=VALID_SERVICES,
                            help='Service to configure')
    set_parser.add_argument('--url', help='Server URL')
    set_parser.add_argument('--user', help='Username')
    set_parser.add_argument('--password', default=None,
                            help='Password (prompted if omitted)')
    set_parser.add_argument('--token', default=None,
                            help='Bearer token (Essbase only)')
    set_parser.add_argument('--transport', default=None,
                            help='MCP transport (server only)')
    set_parser.add_argument('--port', default=None,
                            help='HTTP port (server only)')
    set_parser.set_defaults(func=_cmd_set)

    # -- list --
    list_parser = sub.add_parser('list', help='List stored credentials')
    list_parser.set_defaults(func=_cmd_list)

    # -- remove --
    rm_parser = sub.add_parser('remove', help='Remove credentials for a service')
    rm_parser.add_argument('service', choices=VALID_SERVICES,
                           help='Service to remove')
    rm_parser.set_defaults(func=_cmd_remove)

    return parser


def main():
    parser = _build_parser()
    args = parser.parse_args()
    args.func(args)
