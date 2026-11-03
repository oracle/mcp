"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
"""

import copy

from typing import Optional
from enum import Enum
import json
import os
import re

import keyring
import oci

_PASSWORD_SOURCES = {"password", "password_env", "password_keyring"}
_SECURE_KEYRING_BACKENDS = {
    "keyring.backends.macOS.Keyring",
    "keyring.backends.Windows.WinVaultKeyring",
    "keyring.backends.SecretService.Keyring",
    "keyring.backends.kwallet.DBusKeyring",
    "keyring.backends.kwallet.DBusKeyringKWallet4",
    "keyring.backends.libsecret.Keyring",
}


def _resolve_password(connection: dict) -> str:
    sources = _PASSWORD_SOURCES.intersection(connection)
    if len(sources) != 1:
        raise ValueError("Specify exactly one of password, password_env, or password_keyring")

    source = sources.pop()
    reference = connection[source]
    if source == "password":
        if not isinstance(reference, str):
            raise ValueError("password must be a string")
        return reference

    if source == "password_env":
        if not isinstance(reference, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", reference):
            raise ValueError("password_env must name a valid environment variable")
        password = os.environ.get(reference)
        if not password:
            raise ValueError("password_env points to an unset or empty environment variable")
        return password

    if (
        not isinstance(reference, dict)
        or set(reference) != {"service", "username"}
        or any(not isinstance(value, str) or not value.strip() for value in reference.values())
    ):
        raise ValueError("password_keyring must contain non-empty service and username strings")

    try:
        backend = keyring.get_keyring()
    except Exception:
        raise ValueError("password_keyring could not initialize the OS keyring") from None

    # Reject automatic chains that could fall through to plaintext or null stores.
    backend_name = f"{type(backend).__module__}.{type(backend).__name__}"
    if backend_name not in _SECURE_KEYRING_BACKENDS:
        raise ValueError(
            "password_keyring requires a supported OS keyring backend: "
            "macOS Keychain, Windows Credential Locker, Secret Service, or KWallet"
        )
    try:
        password = backend.get_password(reference["service"], reference["username"])
    except Exception:
        raise ValueError("password_keyring lookup failed; unlock and configure the OS keyring") from None
    if not isinstance(password, str) or not password:
        raise ValueError("password_keyring entry is missing or empty")
    return password


class OciInfo:

    def __init__(self):
        profile_name = os.getenv("PROFILE_NAME", "DEFAULT")

        self.oci_config = oci.config.from_file(profile_name=profile_name)
        self.identity_client = oci.identity.IdentityClient(self.oci_config)

        self.object_storage_client = oci.object_storage.ObjectStorageClient(
            self.oci_config
        )
        self.tenancy_id = os.getenv("TENANCY_ID_OVERRIDE", self.oci_config["tenancy"])

def fill_config_defaults(config : dict) -> dict:
    """
    Validate and normalize the MySQL MCP server configuration.

    Summary:
      - Requires a top-level "server_infos" mapping of connection IDs to MySQL
        connection dictionaries.
      - Requires host, user, database, port and exactly one password source:
        password, password_env, or password_keyring.
      - Resolves passwords at startup and removes reference fields before connection.
      - If a "bastion" block is present, applies defaults and validates allowed/required keys.

    Args:
      config (dict): Raw configuration object loaded from JSON.

    Returns:
      dict: Deep-copied configuration with defaults applied and structure validated.

    Raises:
      Exception:
        - If "server_infos" is missing or empty
        - If any server entry is missing required keys or contains extras
        - If the "bastion" block has invalid/missing keys

    Expected schema:
      {
        "server_infos": {
          "<connection_id>": {
            "host": "<hostname or IP>",
            "user": "<username>",
            "password": "<password>",
            "database": "<default_schema>",
            "port": "<db_port>"
          },
          ...
        },
        "bastion": {                         # optional; for SSH tunneling
          "bastion_host": "<host>",
          "bastion_username": "<user>",
          "private_key_path": "<path to private key>",
          "db_host": "<remote DB host>",
          "db_port": 3306,                   # optional; default 3306
          "bastion_port": 22,                # optional; default 22
          "local_bind_host": "127.0.0.1",    # optional; default 127.0.0.1
          "local_bind_port": 3306            # optional; default 3306
        }
      }

    Notes:
      - This function does not mutate the input; it operates on a deep copy.
      - Use together with load_mysql_config() to read and validate on startup.
    """
    if not isinstance(config, dict):
        raise ValueError("Config must be a JSON object")
    config = copy.deepcopy(config)

    server_configs = config.get("server_infos")

    if server_configs is None:
        raise Exception("Config must specify 'server_infos'")

    if not isinstance(server_configs, dict):
        raise ValueError("server_infos must be an object")

    if len(server_configs) == 0:
        raise Exception("Config must provide at least one server")

    required_server_keys = set([
        "host", "user", "database", "port"
    ])
    for server_config in server_configs.values():
        if not isinstance(server_config, dict):
            raise ValueError("Config server_info entries must be objects")
        if required_server_keys != set(server_config) - _PASSWORD_SOURCES:
            raise Exception(f"Config server_info entries must specify all of the following keys {required_server_keys}")
        password = _resolve_password(server_config)
        for source in _PASSWORD_SOURCES:
            server_config.pop(source, None)
        server_config["password"] = password

    bastion_info = config.get("bastion")
    if bastion_info is not None:
        bastion_defaults = {
            'bastion_port': 22,
            'db_port': 3306,
            'local_bind_host': '127.0.0.1',
            'local_bind_port': 3306,
        }
        for key, value in bastion_defaults.items():
            bastion_info.setdefault(key, value)

        bastion_required_keys = set([
            'bastion_host', 'bastion_username', 'private_key_path', 'db_host'
        ])

        bastion_keys = set([
            'bastion_host', 'bastion_username', 'private_key_path', 'db_host', 'db_port', 'bastion_port',
            'local_bind_host', 'local_bind_port'
        ])

        if bastion_keys != set(bastion_info.keys()):
            raise Exception(f"Config bastion must specify all keys in {bastion_required_keys} and only keys in {bastion_keys}")

    return config

def load_mysql_config():
    """
    Load and validate the MySQL MCP server configuration file.

    Resolution:
      1) If MYSQL_MCP_CONFIG is set, load that absolute path.
      2) Otherwise, load <root__dir>/local_config.json.

    Notes:
      - No other fallbacks (e.g., config.json or CWD) are used.
      - The loaded JSON is validated via fill_config_defaults.
      - The config_path parameter is deprecated and ignored; retained for compatibility.

    Returns:
      dict: Validated configuration object.

    Raises:
      Exception: If the resolved file is not found or validation fails.
    """
    env_path = os.environ.get('MYSQL_MCP_CONFIG')
    module_dir = os.path.dirname(os.path.abspath(__file__))

    local_config_path = os.path.abspath(
        os.path.join(module_dir, "..", "..", "local_config.json")
    )
    config_file = env_path if env_path else local_config_path

    if not os.path.isfile(config_file):
        raise Exception(
            f"Config file not found at {config_file}. "
            "Set MYSQL_MCP_CONFIG to an absolute path or create local_config.json in project root directory."
        )

    with open(config_file, "r") as f:
        config = json.load(f)

    return fill_config_defaults(config)

def get_ssh_command(config : dict) -> Optional[str]:
    """
    Compose an SSH command for tunneling to a database via a bastion host.

    Args:
        config (dict): Configuration containing an optional 'bastion' block with:
            - bastion_host: Bastion host IP or DNS name
            - bastion_port: SSH port of bastion host
            - bastion_username: SSH username for bastion host
            - private_key_path: Path to private SSH key
            - db_host: Target database host
            - db_port: Target database port
            - local_bind_host: Local interface to bind the tunnel
            - local_bind_port: Local port to bind the tunnel

    Returns:
        str | None:
            - The SSH command as a single shell string the user can run to start the jump host if 'bastion' is present in config.
            - None if no 'bastion' block is present.

    Behavior:
        - Generates the SSH tunnel command for database access through a bastion.
        - Does not start the subprocess; only builds the command.

    Notes:
        - Assumes fill_config_defaults has applied defaults/validation.
        - Caller is responsible for launching and managing the subprocess when using this command.
        - Ensure this operation aligns with Oracle security and networking guidelines.
    """
    tunnel_config = config.get("bastion")

    if tunnel_config is None:
        return None

    bastion_host = tunnel_config['bastion_host']
    bastion_port = tunnel_config['bastion_port']
    bastion_username = tunnel_config['bastion_username']
    private_key_path = tunnel_config['private_key_path']
    db_host = tunnel_config['db_host']
    db_port = tunnel_config['db_port']
    local_bind_host = tunnel_config['local_bind_host']
    local_bind_port = tunnel_config['local_bind_port']

    ssh_command = (
        f"`ssh -i {private_key_path} "
        f"-p {bastion_port} "
        f"-L {local_bind_host}:{local_bind_port}:{db_host}:{db_port} "
        "-o ServerAliveInterval=60 "
        "-o ServerAliveCountMax=3 "
        "-N "
        f"{bastion_username}@{bastion_host}`"
    )

    return ssh_command

class Mode(Enum):
    """
    Provider mode for database connection.

    Values:
      - MYSQL_AI: Local MySQL AI (provider 'LCL' maps to MYSQL_AI)
      - OCI: Oracle Cloud Infrastructure (provider 'OCI')
    """

    MYSQL_AI = "MYSQL_AI"
    OCI = "OCI"

    @staticmethod
    def from_string(provider: str) -> "Mode":
        provider_upper = provider.upper()

        provider_to_mode = {"LCL": Mode.MYSQL_AI, "OCI": Mode.OCI}
        mode = provider_to_mode.get(provider_upper)
        if mode is None:
            raise ValueError(
                f"Invalid provider '{provider}'. Valid providers are: {', '.join(provider_to_mode.keys())}."
            )
        return mode

class DatabaseConnectionError(Exception):
    """Raised when a MySQL connection cannot be established."""
