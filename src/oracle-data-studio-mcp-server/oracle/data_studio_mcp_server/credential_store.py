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

    - url and user are written to the config file.
    - password is stored in the OS keyring (never written to the file).
    - extra kwargs (e.g. transport, port, token) are written to the file.
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
    for k, v in extra.items():
        if v is not None:
            cp.set(service, k, str(v))

    _write_config(cp)

    keyring_ok = False
    if password and user:
        keyring_ok = _set_keyring_password(service, user, password)

    return {
        'status': 'success',
        'config_file': str(CONFIG_FILE),
        'keyring_stored': keyring_ok,
    }


def remove_credentials(service: str) -> dict:
    '''Remove a service section from config file and its password from keyring.'''
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

    return {
        'status': 'success',
        'removed_config': removed_file,
        'removed_keyring': removed_keyring,
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
