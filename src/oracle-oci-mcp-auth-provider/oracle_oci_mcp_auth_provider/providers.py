"""OCI SDK and CLI authentication providers shared by MCP servers."""

import atexit
import base64
import configparser
import datetime
import hashlib
import hmac
import io
import json
import os
import shutil
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus, urlencode, urlparse, urlsplit
from urllib.request import Request, urlopen

import oci
import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

_UPST_REQUIRED = ("OCI_UPST_DOMAIN_URL", "OCI_UPST_CLIENT_ID", "OCI_UPST_CLIENT_SECRET", "OCI_UPST_REGION")
_UPST_PROFILE = "UPST"
_EXPIRY_SKEW_SECONDS = 60
IMDS_INSTANCE_ENDPOINT = "http://169.254.169.254/opc/v2/instance/"
RPST_HTTP_TIMEOUT = (5, 30)
_temporary_directory: Path | None = None


class UpstAuthenticationError(RuntimeError):
    """Raised when the user-principal session-token exchange fails."""


@dataclass(frozen=True)
class AuthContext:
    """Signer and optional endpoint to use when constructing an OCI SDK client."""

    signer: Any
    service_endpoint: str | None = None
    config: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class _UpstSession:
    token: str
    private_key: rsa.RSAPrivateKey
    private_key_file: Path
    token_file: Path
    config_file: Path
    expires_at: int | None

    def is_usable(self, now: float) -> bool:
        return self.expires_at is None or now < self.expires_at - _EXPIRY_SKEW_SECONDS


class SecurityTokenProfileProvider:
    """Build an SDK signer from an OCI configuration profile security token."""

    def __init__(self, environment: Mapping[str, str] | None = None):
        self._environment = environment or os.environ

    def get_context(self, *, region: str | None = None) -> AuthContext:
        config = oci.config.from_file(
            file_location=self._environment.get("OCI_CONFIG_FILE", oci.config.DEFAULT_LOCATION),
            profile_name=self._environment.get("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE),
        )
        private_key = oci.signer.load_private_key_from_file(config["key_file"])
        with open(os.path.expanduser(config["security_token_file"]), encoding="utf-8") as token_file:
            token = token_file.read()
        return AuthContext(oci.auth.signers.SecurityTokenSigner(token, private_key), config=config)


class InstancePrincipalProvider:
    """Build an SDK signer from OCI instance-principal credentials."""

    def get_context(self, *, region: str | None = None) -> AuthContext:
        return AuthContext(oci.auth.signers.InstancePrincipalsSecurityTokenSigner())


class UserPrincipalSessionTokenProvider:
    """Exchange identity-domain client credentials for a renewable OCI UPST."""

    def __init__(self, environment: Mapping[str, str] | None = None):
        self._environment = environment or os.environ
        self._session: _UpstSession | None = None
        self._lock = threading.Lock()

    @classmethod
    def is_configured(cls, environment: Mapping[str, str] | None = None) -> bool:
        environment = environment or os.environ
        return any(environment.get(name) for name in _UPST_REQUIRED)

    def get_context(self, *, region: str | None = None) -> AuthContext:
        session = self._get_session()
        return AuthContext(oci.auth.signers.SecurityTokenSigner(session.token, session.private_key))

    def get_cli_context(self) -> tuple[str, str]:
        session = self._get_session()
        return str(session.config_file), _UPST_PROFILE

    def _get_session(self) -> _UpstSession:
        _validate_upst_environment(self._environment)
        with self._lock:
            if self._session and self._session.is_usable(time.time()):
                return self._session
            directory = _credential_directory(self._environment)
            key_path = _path_from_environment(self._environment, "OCI_UPST_PRIVATE_KEY_FILE", directory / "private_key.pem")
            token_path = _path_from_environment(self._environment, "OCI_UPST_TOKEN_FILE", directory / "token")
            config_path = _path_from_environment(self._environment, "OCI_UPST_CONFIG_FILE", directory / "config")
            private_key = _load_or_create_private_key(key_path)
            public_key = base64.b64encode(private_key.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)).decode("ascii")
            bearer = _get_service_bearer_token(self._environment)
            token = _exchange_for_upst(self._environment, bearer, public_key)
            expires_at = _jwt_expiration(token)
            if expires_at is not None and expires_at <= time.time():
                raise UpstAuthenticationError("UPST exchange returned an expired token.")
            _write_private_file(token_path, token)
            _write_cli_config(config_path, key_path, token_path, self._environment["OCI_UPST_REGION"])
            self._session = _UpstSession(token, private_key, key_path, token_path, config_path, expires_at)
            return self._session


class ResourcePrincipalSessionTokenProvider:
    """Exchange a resource principal token bootstrap response for an OCI RPST signer."""

    def __init__(
        self,
        *,
        resource_token_endpoint: str,
        auth_endpoint: str,
        tenancy_ocid: str,
        resource_ocid: str,
        private_key_path: str,
        rci: str,
        t0: str,
        region: str | None = None,
        timeout: tuple[int, int] = RPST_HTTP_TIMEOUT,
    ):
        self.resource_token_endpoint = resource_token_endpoint.rstrip("/")
        self.auth_endpoint = auth_endpoint.rstrip("/")
        self.tenancy_ocid = tenancy_ocid
        self.resource_ocid = resource_ocid
        self.private_key_path = private_key_path
        self.rci = rci
        self.t0 = t0
        self.region = region
        self.timeout = timeout
        self._context: AuthContext | None = None

    def get_context(self, *, region: str | None = None) -> AuthContext:
        if self._context is None:
            private_key = serialization.load_pem_private_key(Path(self.private_key_path).read_bytes(), password=None)
            security_context = _security_context(self.rci, self.t0)
            rpt, spst = _fetch_resource_tokens(self.resource_token_endpoint, self.resource_ocid, self.tenancy_ocid, private_key, security_context, self.timeout)
            rpst, session_key = _exchange_rpst(self.auth_endpoint, self.tenancy_ocid, self.resource_ocid, private_key, rpt, spst, self.timeout)
            config = {"region": self.region} if self.region else None
            self._context = AuthContext(oci.auth.signers.SecurityTokenSigner(rpst, session_key), self.resource_token_endpoint, config)
        return self._context

    @classmethod
    def from_database_environment(
        cls,
        environment: Mapping[str, str] | None = None,
        *,
        database_endpoint: str | None = None,
        tenancy_ocid: str | None = None,
        private_key_path: str | None = None,
        resource_ocid: str | None = None,
        rci: str | None = None,
        t0: str | None = None,
    ) -> "ResourcePrincipalSessionTokenProvider":
        """Create the legacy Database RPST flow from its environment contract."""
        environment = environment or os.environ
        values = {
            "TENANCY_OCID": tenancy_ocid or environment.get("TENANCY_OCID"),
            "PRIVATE_KEY_PATH": private_key_path or environment.get("PRIVATE_KEY_PATH"),
            "RESOURCE_OCID": resource_ocid or environment.get("RESOURCE_OCID"),
            "RCI": rci or environment.get("RCI"),
            "T0": t0 or environment.get("T0"),
        }
        missing = [name for name, value in values.items() if not value]
        if missing:
            raise ValueError("Missing required resource principal values: " + ", ".join(missing))

        region = get_region_from_instance_metadata()
        default_database_endpoint, auth_endpoint = build_default_database_rpst_endpoints(region)
        return cls(
            resource_token_endpoint=database_endpoint
            or environment.get("DATABASE_ENDPOINT")
            or default_database_endpoint,
            auth_endpoint=auth_endpoint,
            tenancy_ocid=values["TENANCY_OCID"],
            private_key_path=values["PRIVATE_KEY_PATH"],
            resource_ocid=values["RESOURCE_OCID"],
            rci=values["RCI"],
            t0=values["T0"],
            region=region,
        )


def _validate_upst_environment(environment: Mapping[str, str]) -> None:
    missing = [name for name in _UPST_REQUIRED if not environment.get(name)]
    if missing:
        raise UpstAuthenticationError("UPST authentication requires environment variables: " + ", ".join(missing))
    parsed = urlsplit(environment["OCI_UPST_DOMAIN_URL"])
    if parsed.scheme != "https" or not parsed.netloc or parsed.query or parsed.fragment:
        raise UpstAuthenticationError("OCI_UPST_DOMAIN_URL must be an HTTPS identity domain URL.")


def _credential_directory(environment: Mapping[str, str]) -> Path:
    global _temporary_directory
    if _temporary_directory is None:
        configured = environment.get("OCI_UPST_CREDENTIALS_DIR")
        if configured:
            _temporary_directory = Path(os.path.expanduser(configured))
            _temporary_directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        else:
            _temporary_directory = Path(tempfile.mkdtemp(prefix="oci-upst-"))
            atexit.register(shutil.rmtree, _temporary_directory, ignore_errors=True)
    if not _temporary_directory.is_dir() or _temporary_directory.stat().st_mode & 0o077:
        raise UpstAuthenticationError("UPST credentials directory must be private.")
    return _temporary_directory


def _path_from_environment(environment: Mapping[str, str], name: str, default: Path) -> Path:
    return Path(os.path.expanduser(environment.get(name, str(default))))


def _load_or_create_private_key(path: Path) -> rsa.RSAPrivateKey:
    if path.exists():
        if path.stat().st_mode & 0o077:
            raise UpstAuthenticationError("UPST private key must not be group or world accessible.")
        try:
            key = serialization.load_pem_private_key(path.read_bytes(), password=None)
        except (TypeError, ValueError) as error:
            raise UpstAuthenticationError("Failed to load the UPST RSA private key.") from error
        if not isinstance(key, rsa.RSAPrivateKey) or key.key_size < 2048:
            raise UpstAuthenticationError("UPST private key must be an RSA key of at least 2048 bits.")
        return key
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    _write_private_file(path, key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()).decode("ascii"))
    return key


def _post_token_request(environment: Mapping[str, str], payload: Mapping[str, str]) -> dict:
    endpoint = environment["OCI_UPST_DOMAIN_URL"].rstrip("/") + "/oauth2/v1/token"
    credentials = f"{environment['OCI_UPST_CLIENT_ID']}:{environment['OCI_UPST_CLIENT_SECRET']}"
    request = Request(endpoint, data=urlencode(payload).encode(), headers={"Authorization": "Basic " + base64.b64encode(credentials.encode()).decode(), "Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    try:
        with urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode())
    except HTTPError as error:
        raise UpstAuthenticationError(f"OCI UPST token request failed with HTTP {error.code}.") from error
    except (OSError, URLError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise UpstAuthenticationError("OCI UPST token request failed.") from error
    if not isinstance(data, dict):
        raise UpstAuthenticationError("OCI UPST token response was not a JSON object.")
    return data


def _get_service_bearer_token(environment: Mapping[str, str]) -> str:
    token = _post_token_request(environment, {"grant_type": "client_credentials", "scope": "urn:opc:idm:__myscopes__"}).get("access_token")
    if not isinstance(token, str) or not token or token.count(".") != 2 or any(token.isspace() for token in token):
        raise UpstAuthenticationError("Service-bearer response did not contain a valid JWT access_token.")
    return token


def _exchange_for_upst(environment: Mapping[str, str], bearer: str, public_key: str) -> str:
    token = _post_token_request(environment, {"grant_type": "urn:ietf:params:oauth:grant-type:token-exchange", "requested_token_type": "urn:oci:token-type:oci-upst", "public_key": public_key, "subject_token": bearer, "subject_token_type": "jwt"}).get("token")
    if not isinstance(token, str) or not token:
        raise UpstAuthenticationError("UPST exchange response did not contain token.")
    return token


def _jwt_expiration(token: str) -> int | None:
    try:
        payload = json.loads(base64.urlsafe_b64decode(token.split(".")[1] + "=" * (-len(token.split(".")[1]) % 4)))
    except (IndexError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return None
    expiration = payload.get("exp") if isinstance(payload, dict) else None
    return int(expiration) if isinstance(expiration, (int, float)) else None


def _write_private_file(path: Path, content: str) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.chmod(temporary, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _write_cli_config(path: Path, key_path: Path, token_path: Path, region: str) -> None:
    config = configparser.ConfigParser()
    config[_UPST_PROFILE] = {"region": region, "key_file": str(key_path), "security_token_file": str(token_path)}
    output = io.StringIO()
    config.write(output)
    _write_private_file(path, output.getvalue())


def get_region_from_instance_metadata() -> str:
    """Return the OCI instance region using the legacy IMDS v2 request."""
    response = requests.get(
        IMDS_INSTANCE_ENDPOINT, headers={"Authorization": "Bearer Oracle"}, timeout=5
    )
    if response.status_code != 200:
        raise Exception(f"IMDS lookup failed: {response.status_code} {response.text}")
    payload = response.json()
    region = payload.get("canonicalRegionName") or payload.get("region")
    if not region:
        raise Exception(
            "Unable to determine region from IMDS payload (missing canonicalRegionName/region)"
        )
    return region


def build_default_database_rpst_endpoints(region: str) -> tuple[str, str]:
    """Return the Database and Auth endpoints used by the existing RPST flow."""
    return (
        f"https://database.{region}.oraclecloud.com",
        f"https://auth.{region}.oraclecloud.com",
    )


def _security_context(rci: str, t0: str) -> str:
    started = datetime.datetime.fromisoformat(t0.replace("Z", "+00:00"))
    now = datetime.datetime.now(datetime.timezone.utc)
    started_milliseconds = int(started.timestamp() * 1000)
    now_milliseconds = int(now.timestamp() * 1000)
    digest = hmac.new(
        base64.b64decode(rci),
        (now_milliseconds - started_milliseconds).to_bytes(8, "big"),
        hashlib.sha1,
    ).digest()
    offset = digest[-1] & 0x0F
    code = (((digest[offset] & 0x7F) << 24) | (digest[offset + 1] << 16) | (digest[offset + 2] << 8) | digest[offset + 3]) % 100000000
    return json.dumps(
        {
            "RPTSecurityContext": {
                "contextVersion": "V1",
                "keyType": "REGULAR_RPT",
                "securitySignature": {
                    "currentUTCTime": now.isoformat(timespec="microseconds").replace(
                        "+00:00", "Z"
                    ),
                    "Signature": f"{code:08d}",
                },
            }
        },
        indent=2,
    )


def _signature_header(key_id: str, signature: bytes, headers: str) -> str:
    return f'Signature headers="{headers}",keyId="{key_id}",algorithm="rsa-sha256",signature="{base64.b64encode(signature).decode()}",version="1"'


def _fetch_resource_tokens(endpoint: str, resource: str, tenancy: str, private_key: Any, context: str, timeout: tuple[int, int]) -> tuple[str, str]:
    url = f"{endpoint}/20180711/resourcePrincipalTokenV212/{resource}"
    parsed = urlparse(url)
    date = datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    signature = private_key.sign(f"date: {date}\n(request-target): get {parsed.path}\nhost: {parsed.netloc}".encode(), padding.PKCS1v15(), hashes.SHA256())
    headers = {"date": date, "host": parsed.netloc, "security-context": quote_plus(context), "Authorization": _signature_header(f"resource/v2.1.2/{tenancy}/{resource}", signature, "date (request-target) host")}
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
    except requests.exceptions.Timeout as error:
        raise RuntimeError("Timed out fetching resource principal tokens") from error
    if response.status_code != 200:
        request = requests.Request(
            "GET", url, params={"securityContext": context}, headers={"date": date, "host": parsed.netloc}
        )
        prepared = request.prepare()
        query_signature = private_key.sign(
            f"date: {date}\n(request-target): get {prepared.path_url}\nhost: {parsed.netloc}".encode(),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        prepared.headers["Authorization"] = _signature_header(
            f"resource/v2.1.2/{tenancy}/{resource}",
            query_signature,
            "date (request-target) host",
        )
        try:
            response = requests.Session().send(prepared, timeout=timeout)
        except requests.exceptions.Timeout as error:
            raise RuntimeError("Timed out fetching resource principal tokens") from error
    if response.status_code != 200:
        raise Exception(f"Token fetch failed: {response.status_code} {response.text}")
    payload = response.json()
    return payload["resourcePrincipalToken"], payload["servicePrincipalSessionToken"]


def _exchange_rpst(endpoint: str, tenancy: str, resource: str, private_key: Any, rpt: str, spst: str, timeout: tuple[int, int]) -> tuple[str, rsa.RSAPrivateKey]:
    session_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    session_public = base64.b64encode(session_key.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)).decode()
    body = json.dumps({"resourcePrincipalToken": rpt, "servicePrincipalSessionToken": spst, "sessionPublicKey": session_public}, separators=(",", ":")).encode()
    url = f"{endpoint}/v1/resourcePrincipalSessionToken"
    parsed = urlparse(url)
    date = datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    content_sha = base64.b64encode(hashlib.sha256(body).digest()).decode()
    signing = f"date: {date}\n(request-target): post {parsed.path}\nhost: {parsed.netloc}\ncontent-length: {len(body)}\ncontent-type: application/json\nx-content-sha256: {content_sha}"
    signature = private_key.sign(signing.encode(), padding.PKCS1v15(), hashes.SHA256())
    headers = {"date": date, "host": parsed.netloc, "content-type": "application/json", "content-length": str(len(body)), "x-content-sha256": content_sha, "Authorization": _signature_header(f"resource/v2.1.2/{tenancy}/{resource}", signature, "date (request-target) host content-length content-type x-content-sha256")}
    try:
        response = requests.post(url, data=body, headers=headers, timeout=timeout)
    except requests.exceptions.Timeout as error:
        raise RuntimeError("Timed out exchanging resource principal session token") from error
    if response.status_code != 200:
        raise Exception(f"RPST exchange failed: {response.status_code} {response.text}")
    return response.json()["token"], session_key
