# Copyright (c) 2025, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

'''
Credential management for Oracle Data Studio MCP Server.

Stores non-sensitive settings (URLs, usernames) in an INI config file
at ~/.oracle-data-studio/config and passwords in the OS keyring
(macOS Keychain, Windows Credential Manager, Linux Secret Service).
'''

from __future__ import annotations

import os
import configparser
from pathlib import Path
from typing import Optional

# Keyring service prefix — entries are stored as
# "oracle-data-studio/essbase", "oracle-data-studio/adp", etc.
SERVICE_PREFIX = 'oracle-data-studio'

VALID_SERVICES = ('essbase', 'adp', 'datatransforms', 'server')

CONFIG_DIR = Path.home() / '.oracle-data-studio'
CONFIG_FILE = CONFIG_DIR / 'config'

# Keys that MUST NEVER appear in the plaintext INI config file.
# Even if a caller passes them via store_credentials(**extra), they
# are routed to the OS keyring instead of being written to disk.
# Reviewers requested this hardening — defence-in-depth against
# accidental token-in-config-file mistakes.
SECRET_KEYS = frozenset({
    'password', 'passwd', 'pswd',
    'token', 'bearer',
    'secret', 'api_key', 'apikey',
})

# Pseudo-username for keyring entries that aren't tied to a real
# username (e.g. bearer tokens).
_TOKEN_KEYRING_USER = '__token__'


def _ensure_config_dir():
    '''Create ~/.oracle-data-studio/ with restricted permissions.'''
    CONFIG_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)


def _read_config() -> configparser.ConfigParser:
    '''Read the INI config file. Returns empty parser if file is missing.'''
    cp = configparser.ConfigParser()
    if CONFIG_FILE.exists():
        cp.read(str(CONFIG_FILE))
    return cp


def _write_config(cp: configparser.ConfigParser):
    '''Write the config parser back to the INI file with restricted perms.'''
    _ensure_config_dir()
    with open(CONFIG_FILE, 'w') as f:
        cp.write(f)
    os.chmod(CONFIG_FILE, 0o600)


def _keyring_service(service: str) -> str:
    '''Build the keyring service name for a given service.'''
    return f'{SERVICE_PREFIX}/{service}'


def _set_keyring_password(service: str, user: str, password: str) -> bool:
    '''Store a password in the OS keyring. Returns True on success.'''
    try:
        import keyring
        keyring.set_password(_keyring_service(service), user, password)
        return True
    except ImportError:
        return False
    except Exception:
        return False


def _get_keyring_password(service: str, user: str) -> Optional[str]:
    '''Retrieve a password from the OS keyring. Returns None if unavailable.'''
    if not user:
        return None
    try:
        import keyring
        return keyring.get_password(_keyring_service(service), user)
    except ImportError:
        return None
    except Exception:
        return None


def _delete_keyring_password(service: str, user: str) -> bool:
    '''Remove a password from the OS keyring. Returns True on success.'''
    if not user:
        return False
    try:
        import keyring
        keyring.delete_password(_keyring_service(service), user)
        return True
    except ImportError:
        return False
    except Exception:
        return False


# ------------------------------------------------------------------ #
#  Public API                                                         #
# ------------------------------------------------------------------ #

def store_credentials(service: str, url: Optional[str] = None,
                      user: Optional[str] = None,
                      password: Optional[str] = None,
                      **extra) -> dict:
    '''Store credentials for a service.

    Splits inputs into two destinations:

    - **OS keyring** — `password` (keyed by user), and any kwargs whose
      name is in `SECRET_KEYS` (`token`, `bearer`, `api_key`, …).
      Bearer tokens are stored under the pseudo-user `__token__`.
      Nothing in this category is ever written to disk by this server.
    - **INI config file** — `url`, `user`, and any non-secret kwargs
      (`transport`, `port`, `host`, etc.).

    A caller cannot trick this function into persisting a secret by
    renaming the field: passing `token=…` or `password=…` always goes
    to keyring, never to the file.

    Returns a dict that reports which secret destinations were used.
    '''
    if service not in VALID_SERVICES:
        raise ValueError(f'Unknown service: {service}. '
                         f'Valid: {", ".join(VALID_SERVICES)}')

    cp = _read_config()
    if not cp.has_section(service):
        cp.add_section(service)

    if url is not None:
        cp.set(service, 'url', url)
    if user is not None:
        cp.set(service, 'user', user)

    # Track secret extras so we can store them in keyring after the
    # file write.  NEVER set them as INI keys.
    secret_extras: dict[str, str] = {}
    for k, v in extra.items():
        if v is None:
            continue
        if k.lower() in SECRET_KEYS:
            secret_extras[k.lower()] = str(v)
            continue
        cp.set(service, k, str(v))

    _write_config(cp)

    keyring_ok = False
    if password and user:
        keyring_ok = _set_keyring_password(service, user, password)

    # Route secret kwargs to keyring under stable keys.
    secret_extras_stored: list[str] = []
    for k, v in secret_extras.items():
        # Tokens / bearer / api_key: pseudo-user
        ok = _set_keyring_password(service, _TOKEN_KEYRING_USER, v)
        if ok:
            secret_extras_stored.append(k)

    return {
        'status': 'success',
        'config_file': str(CONFIG_FILE),
        'keyring_stored': keyring_ok,
        'secret_extras_stored': secret_extras_stored,
    }


def remove_credentials(service: str) -> dict:
    '''Remove a service section from config file and its secrets from keyring.

    Scrubs:
    - the INI section
    - the user-keyed password (if a user was set)
    - any token / bearer entries stored under the `__token__` pseudo-user
    '''
    cp = _read_config()
    user = cp.get(service, 'user', fallback=None) if cp.has_section(service) else None

    removed_file = False
    if cp.has_section(service):
        cp.remove_section(service)
        _write_config(cp)
        removed_file = True

    removed_keyring = False
    if user:
        removed_keyring = _delete_keyring_password(service, user)

    # Best-effort token removal — silently ignores "no such entry"
    removed_token = _delete_keyring_password(service, _TOKEN_KEYRING_USER)

    return {
        'status': 'success',
        'removed_config': removed_file,
        'removed_keyring': removed_keyring,
        'removed_token': removed_token,
    }


def list_credentials() -> dict:
    '''List all stored credentials (URLs and usernames, never passwords).'''
    cp = _read_config()
    result = {}
    for section in cp.sections():
        result[section] = dict(cp.items(section))
    return result


def load_config_file() -> dict:
    '''Load the config file as a dict of {section: {key: value}}.

    Used by mcp_server/config.py to layer in config file values.
    '''
    cp = _read_config()
    return {section: dict(cp.items(section)) for section in cp.sections()}


def get_keyring_password(service: str, user: str) -> Optional[str]:
    '''Public wrapper for keyring password retrieval.'''
    return _get_keyring_password(service, user)


def get_keyring_token(service: str) -> Optional[str]:
    '''Public wrapper for bearer-token retrieval from keyring.

    Tokens are stored under a pseudo-user (`__token__`) so they don't
    need a real username to round-trip. Returns None if no token is
    set or the keyring is unavailable.
    '''
    return _get_keyring_password(service, _TOKEN_KEYRING_USER)
