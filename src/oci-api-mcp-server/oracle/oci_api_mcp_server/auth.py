"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

"""JWT-to-UPST authentication support for OCI CLI invocations."""

import atexit
import base64
import configparser
import io
import json
import os
import shutil
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

_REQUIRED_ENVIRONMENT_VARIABLES = (
    "OCI_UPST_DOMAIN_URL",
    "OCI_UPST_CLIENT_ID",
    "OCI_UPST_CLIENT_SECRET",
    "OCI_UPST_REGION",
)
_PROFILE_NAME = "UPST"
_EXPIRY_SKEW_SECONDS = 60
_temporary_directory: Path | None = None
_upst_session: "UpstSession | None" = None
_upst_session_lock = threading.Lock()


class UpstAuthenticationError(RuntimeError):
    """Raised when OCI JWT-to-UPST authentication cannot be completed."""


@dataclass(frozen=True)
class UpstSession:
    """The generated CLI configuration and optional UPST expiration time."""

    config_file: str
    profile_name: str
    expires_at: int | None

    def is_usable(self, now: float) -> bool:
        """Return whether the token is not within the configured renewal window."""
        return self.expires_at is None or now < self.expires_at - _EXPIRY_SKEW_SECONDS


def is_upst_auth_configured(environment: Mapping[str, str] | None = None) -> bool:
    """Return whether any UPST-specific environment variable was supplied."""
    environment = environment or os.environ
    return any(environment.get(name) for name in _REQUIRED_ENVIRONMENT_VARIABLES)


def get_upst_cli_configuration(
    environment: Mapping[str, str] | None = None,
) -> tuple[str, str]:
    """Return a UPST-backed OCI CLI configuration, renewing near token expiration."""
    global _upst_session
    environment = environment or os.environ
    _validate_environment(environment)

    with _upst_session_lock:
        if _upst_session is not None and _upst_session.is_usable(time.time()):
            return _upst_session.config_file, _upst_session.profile_name

        directory = _get_credential_directory(environment)
        private_key_file = _path_from_environment(
            environment, "OCI_UPST_PRIVATE_KEY_FILE", directory / "private_key.pem"
        )
        token_file = _path_from_environment(
            environment, "OCI_UPST_TOKEN_FILE", directory / "token"
        )
        config_file = _path_from_environment(
            environment, "OCI_UPST_CONFIG_FILE", directory / "config"
        )

        private_key = _load_or_create_private_key(private_key_file)
        public_key = base64.b64encode(
            private_key.public_key().public_bytes(
                serialization.Encoding.DER,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        ).decode("ascii")
        service_bearer_token = _get_service_bearer_token(environment)
        upst_token = _exchange_for_upst(environment, service_bearer_token, public_key)
        expires_at = _get_jwt_expiration(upst_token)
        if expires_at is not None and expires_at <= time.time():
            raise UpstAuthenticationError("UPST exchange returned an expired token.")

        _write_private_file(token_file, upst_token)
        _write_cli_config(
            config_file, private_key_file, token_file, environment["OCI_UPST_REGION"]
        )
        _upst_session = UpstSession(str(config_file), _PROFILE_NAME, expires_at)
        return _upst_session.config_file, _upst_session.profile_name


def _validate_environment(environment: Mapping[str, str]) -> None:
    missing = [
        name for name in _REQUIRED_ENVIRONMENT_VARIABLES if not environment.get(name)
    ]
    if missing:
        raise UpstAuthenticationError(
            "UPST authentication requires environment variables: " + ", ".join(missing)
        )
    parsed_url = urlsplit(environment["OCI_UPST_DOMAIN_URL"])
    if (
        parsed_url.scheme != "https"
        or not parsed_url.netloc
        or parsed_url.query
        or parsed_url.fragment
    ):
        raise UpstAuthenticationError(
            "OCI_UPST_DOMAIN_URL must be an HTTPS identity domain URL."
        )


def _get_credential_directory(environment: Mapping[str, str]) -> Path:
    global _temporary_directory
    if _temporary_directory is None:
        configured_directory = environment.get("OCI_UPST_CREDENTIALS_DIR")
        if configured_directory:
            _temporary_directory = Path(os.path.expanduser(configured_directory))
            _temporary_directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        else:
            _temporary_directory = Path(tempfile.mkdtemp(prefix="oci-upst-"))
            atexit.register(shutil.rmtree, _temporary_directory, ignore_errors=True)
    _require_private_directory(_temporary_directory)
    return _temporary_directory


def _path_from_environment(
    environment: Mapping[str, str], name: str, default: Path
) -> Path:
    return Path(os.path.expanduser(environment.get(name, str(default))))


def _require_private_directory(directory: Path) -> None:
    if not directory.is_dir():
        raise UpstAuthenticationError(
            f"UPST credentials directory is not a directory: {directory}"
        )
    if directory.stat().st_mode & 0o077:
        raise UpstAuthenticationError(
            f"UPST credentials directory must not be group or world accessible: {directory}"
        )


def _load_or_create_private_key(private_key_file: Path) -> rsa.RSAPrivateKey:
    if private_key_file.exists():
        if private_key_file.stat().st_mode & 0o077:
            raise UpstAuthenticationError(
                "UPST private key must not be group or world accessible."
            )
        try:
            private_key = serialization.load_pem_private_key(
                private_key_file.read_bytes(), password=None
            )
        except (TypeError, ValueError) as error:
            raise UpstAuthenticationError(
                "Failed to load the UPST RSA private key."
            ) from error
        if (
            not isinstance(private_key, rsa.RSAPrivateKey)
            or private_key.key_size < 2048
        ):
            raise UpstAuthenticationError(
                "UPST private key must be an RSA key of at least 2048 bits."
            )
        return private_key

    private_key_file.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    _write_private_file(
        private_key_file,
        private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        ).decode("ascii"),
    )
    return private_key


def _get_service_bearer_token(environment: Mapping[str, str]) -> str:
    response = _post_token_request(
        environment,
        {"grant_type": "client_credentials", "scope": "urn:opc:idm:__myscopes__"},
    )
    token = response.get("access_token")
    if (
        not isinstance(token, str)
        or not token
        or token.count(".") != 2
        or any(token.isspace() for token in token)
    ):
        raise UpstAuthenticationError(
            "Service-bearer response did not contain a valid JWT access_token."
        )
    return token


def _exchange_for_upst(
    environment: Mapping[str, str], service_bearer_token: str, public_key: str
) -> str:
    response = _post_token_request(
        environment,
        {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "requested_token_type": "urn:oci:token-type:oci-upst",
            "public_key": public_key,
            "subject_token": service_bearer_token,
            "subject_token_type": "jwt",
        },
    )
    token = response.get("token")
    if not isinstance(token, str) or not token:
        raise UpstAuthenticationError("UPST exchange response did not contain token.")
    return token


def _post_token_request(
    environment: Mapping[str, str], payload: Mapping[str, str]
) -> dict:
    endpoint = environment["OCI_UPST_DOMAIN_URL"].rstrip("/") + "/oauth2/v1/token"
    credentials = (
        f"{environment['OCI_UPST_CLIENT_ID']}:{environment['OCI_UPST_CLIENT_SECRET']}"
    )
    authorization = base64.b64encode(credentials.encode("utf-8")).decode("ascii")
    request = Request(
        endpoint,
        data=urlencode(payload).encode("utf-8"),
        headers={
            "Authorization": f"Basic {authorization}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            parsed_response = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise UpstAuthenticationError(
            f"OCI UPST token request failed with HTTP {error.code}."
        ) from error
    except (OSError, URLError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise UpstAuthenticationError("OCI UPST token request failed.") from error
    if not isinstance(parsed_response, dict):
        raise UpstAuthenticationError("OCI UPST token response was not a JSON object.")
    return parsed_response


def _get_jwt_expiration(token: str) -> int | None:
    parts = token.split(".")
    if len(parts) != 3:
        return None
    try:
        payload = json.loads(
            base64.urlsafe_b64decode(parts[1] + "=" * (-len(parts[1]) % 4))
        )
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return None
    expiration = payload.get("exp") if isinstance(payload, dict) else None
    return int(expiration) if isinstance(expiration, int | float) else None


def _write_private_file(path: Path, content: str) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    file_descriptor, temporary_path = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
    try:
        os.chmod(temporary_path, 0o600)
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_path, path)
    except OSError as error:
        raise UpstAuthenticationError(
            f"Failed to write UPST credential file: {path}"
        ) from error
    finally:
        if os.path.exists(temporary_path):
            os.unlink(temporary_path)


def _write_cli_config(
    config_file: Path, private_key_file: Path, token_file: Path, region: str
) -> None:
    config = configparser.ConfigParser()
    config[_PROFILE_NAME] = {
        "region": region,
        "key_file": str(private_key_file),
        "security_token_file": str(token_file),
    }
    output = io.StringIO()
    config.write(output)
    _write_private_file(config_file, output.getvalue())
