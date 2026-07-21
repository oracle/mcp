# Copyright (c) 2025, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

'''
Configuration for the Oracle Data Studio MCP Server.

Priority: CLI args > environment variables > OS keyring (passwords) >
          config file (~/.oracle-data-studio/config) > defaults.
'''

from __future__ import annotations

import os
import argparse
from dataclasses import dataclass
from typing import Optional

from .credential_store import load_config_file, get_keyring_password


@dataclass
class EssbaseConfig:
    '''Essbase connection configuration.'''
    url: str
    user: str
    password: str
    token: Optional[str] = None


@dataclass
class AdpConfig:
    '''ADP connection configuration.'''
    url: str
    user: str
    password: str


@dataclass
class DataTransformsConfig:
    '''Data Transforms connection configuration.'''
    url: str
    user: str
    password: str


@dataclass
class ServerConfig:
    '''Top-level server configuration.'''
    essbase: Optional[EssbaseConfig] = None
    adp: Optional[AdpConfig] = None
    datatransforms: Optional[DataTransformsConfig] = None
    transport: str = 'stdio'
    host: str = '127.0.0.1'   # streamable-http bind address; loopback by default
    port: int = 8000
    # Default profile is `viewer` — safe metadata-only access. The
    # full admin surface requires explicit `--profile admin` (or
    # MCP_PROFILE=admin). This follows oracle/mcp BEST_PRACTICES on
    # scope minimisation and safe defaults.
    profile: str = 'viewer'
    # Optional first-party bearer auth for streamable-http. When set,
    # every HTTP request must carry `Authorization: Bearer <token>`.
    # Required for any non-loopback bind unless allow_insecure_bind is
    # explicitly set.
    auth_token: Optional[str] = None
    # Operator opt-in: acknowledge a non-loopback bind without
    # MCP_AUTH_TOKEN. Use this only when an authenticated reverse proxy
    # / API gateway sits in front of the MCP port. Without one of
    # auth_token or allow_insecure_bind, non-loopback bind fails closed
    # at startup.
    allow_insecure_bind: bool = False
    # Select AI / adp_ai_chat table policy. Tables are matched
    # case-insensitively against both bare names and `OWNER.NAME` forms.
    # If allowlist is set and a request references tables not in it,
    # the call is rejected. If denylist is set and a request references
    # any denied table, the call is rejected. Both can coexist; deny
    # always wins.
    ai_chat_allowed_tables: Optional[frozenset] = None
    ai_chat_denied_tables: Optional[frozenset] = None


def _build_parser() -> argparse.ArgumentParser:
    '''Build the CLI argument parser.'''
    parser = argparse.ArgumentParser(
        description='Oracle Data Studio MCP Server')

    # Transport
    parser.add_argument(
        '--transport', choices=['stdio', 'streamable-http'],
        default=None,
        help='MCP transport (default: stdio)')
    parser.add_argument(
        '--host', default=None,
        help='Bind address for streamable-http transport '
             '(default: 127.0.0.1 — loopback only). '
             'Use 0.0.0.0 to expose externally; the server has no '
             'built-in auth so put a reverse proxy in front.')
    parser.add_argument(
        '--port', type=int, default=None,
        help='HTTP port for streamable-http transport (default: 8000)')
    parser.add_argument(
        '--auth-token', default=None,
        help='Bearer token for streamable-http auth (env MCP_AUTH_TOKEN). '
             'When set, every HTTP request must carry '
             '`Authorization: Bearer <token>`. Required for any '
             'non-loopback bind unless --allow-insecure-bind is set.')
    parser.add_argument(
        '--allow-insecure-bind', action='store_true', default=None,
        help='Acknowledge a non-loopback streamable-http bind without '
             'MCP_AUTH_TOKEN. Use only when an authenticated reverse '
             'proxy or API gateway is in front of this server. Without '
             'this flag (or --auth-token), non-loopback bind fails '
             'closed at startup. (env MCP_ALLOW_INSECURE_BIND=1)')

    # Essbase
    ess = parser.add_argument_group('Essbase')
    ess.add_argument('--essbase-url', default=None,
                     help='Essbase server URL')
    ess.add_argument('--essbase-user', default=None,
                     help='Essbase username')
    ess.add_argument('--essbase-password', default=None,
                     help='Essbase password')
    ess.add_argument('--essbase-token', default=None,
                     help='Essbase Bearer token (alternative to user/password)')

    # ADP
    adp = parser.add_argument_group('ADP')
    adp.add_argument('--adp-url', default=None,
                     help='ADP server URL')
    adp.add_argument('--adp-user', default=None,
                     help='ADP username')
    adp.add_argument('--adp-password', default=None,
                     help='ADP password')

    # Profile
    parser.add_argument(
        '--profile', choices=['viewer', 'analyst', 'admin'],
        default=None,
        help='Tool access profile: viewer, analyst, admin (default: admin)')

    # Data Transforms
    dt = parser.add_argument_group('Data Transforms')
    dt.add_argument('--dt-url', default=None,
                    help='Data Transforms server URL')
    dt.add_argument('--dt-user', default=None,
                    help='Data Transforms username')
    dt.add_argument('--dt-password', default=None,
                    help='Data Transforms password')

    return parser


def load_config() -> ServerConfig:
    '''Load configuration from CLI args, env vars, keyring, and config file.

    Priority: CLI args > environment variables > OS keyring (passwords) >
              config file (~/.oracle-data-studio/config) > defaults.
    '''
    parser = _build_parser()
    args, _ = parser.parse_known_args()
    file_cfg = load_config_file()

    # Helper: resolve a value through the priority chain
    def _val(cli, env_key, section, key):
        return (cli
                or os.environ.get(env_key)
                or file_cfg.get(section, {}).get(key))

    # -- Transport & Profile --
    transport = (_val(args.transport, 'MCP_TRANSPORT', 'server', 'transport')
                 or 'stdio')
    host = (_val(args.host, 'MCP_HOST', 'server', 'host')
            or '127.0.0.1')
    port_str = _val(args.port, 'MCP_PORT', 'server', 'port')
    port = int(port_str) if port_str else 8000
    profile = (_val(args.profile, 'MCP_PROFILE', 'server', 'profile')
               or 'viewer')

    # -- Streamable-HTTP auth gate --
    # Tokens are never read from the INI file (would be plaintext on disk).
    auth_token = (args.auth_token
                  or os.environ.get('MCP_AUTH_TOKEN'))
    # `allow_insecure_bind` is intentionally CLI-flag-or-env-only — never
    # from the config file. Putting it in a file would make "I accept
    # the risk" a one-time, easy-to-forget decision.
    allow_insecure_bind = bool(
        args.allow_insecure_bind
        or os.environ.get('MCP_ALLOW_INSECURE_BIND', '').lower()
           in ('1', 'true', 'yes'))

    # -- adp_ai_chat table policy (env-only; no CLI / no INI file) --
    def _csv_set(env_key):
        raw = os.environ.get(env_key, '').strip()
        if not raw:
            return None
        return frozenset(t.strip().upper()
                          for t in raw.split(',') if t.strip())
    ai_chat_allowed_tables = _csv_set('MCP_AI_CHAT_ALLOWED_TABLES')
    ai_chat_denied_tables = _csv_set('MCP_AI_CHAT_DENIED_TABLES')

    # -- Essbase --
    # Tokens are NEVER read from the INI file (would be plaintext on
    # disk). Resolve from CLI > env > keyring only.
    from .credential_store import get_keyring_token
    ess_url = _val(args.essbase_url, 'ESSBASE_URL', 'essbase', 'url')
    ess_user = _val(args.essbase_user, 'ESSBASE_USER', 'essbase', 'user')
    ess_token = (args.essbase_token
                 or os.environ.get('ESSBASE_TOKEN')
                 or get_keyring_token('essbase'))
    ess_password = (args.essbase_password
                    or os.environ.get('ESSBASE_PASSWORD')
                    or get_keyring_password('essbase', ess_user))

    essbase_config = None
    if ess_url and (ess_token or (ess_user and ess_password)):
        essbase_config = EssbaseConfig(
            url=ess_url,
            user=ess_user or '',
            password=ess_password or '',
            token=ess_token)

    # -- ADP --
    adp_url = _val(args.adp_url, 'ADP_URL', 'adp', 'url')
    adp_user = _val(args.adp_user, 'ADP_USER', 'adp', 'user')
    adp_password = (args.adp_password
                    or os.environ.get('ADP_PASSWORD')
                    or get_keyring_password('adp', adp_user))

    adp_config = None
    if adp_url and adp_user and adp_password:
        adp_config = AdpConfig(
            url=adp_url,
            user=adp_user,
            password=adp_password)

    # -- Data Transforms --
    dt_url = _val(args.dt_url, 'DT_URL', 'datatransforms', 'url')
    dt_user = _val(args.dt_user, 'DT_USER', 'datatransforms', 'user')
    dt_password = (args.dt_password
                   or os.environ.get('DT_PASSWORD')
                   or get_keyring_password('datatransforms', dt_user))

    dt_config = None
    if dt_url and dt_user and dt_password:
        dt_config = DataTransformsConfig(
            url=dt_url,
            user=dt_user,
            password=dt_password)

    return ServerConfig(
        essbase=essbase_config,
        adp=adp_config,
        datatransforms=dt_config,
        transport=transport,
        host=host,
        port=port,
        profile=profile,
        auth_token=auth_token,
        allow_insecure_bind=allow_insecure_bind,
        ai_chat_allowed_tables=ai_chat_allowed_tables,
        ai_chat_denied_tables=ai_chat_denied_tables)
