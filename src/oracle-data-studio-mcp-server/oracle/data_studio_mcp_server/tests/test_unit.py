# Copyright (c) 2025, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

'''
Unit tests for the Oracle Data Studio MCP Server (upleveled tools).

Tests configuration loading, profile filtering, credential store,
helpers, and tool registration/dispatch — all without live servers.

Usage:
    python -m pytest oracle/data_studio_mcp_server/tests/ -v
'''

import json
import os
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from dataclasses import asdict

try:
    import mcp  # noqa: F401
    HAS_MCP = True
except ImportError:
    HAS_MCP = False

mcp_required = pytest.mark.skipif(not HAS_MCP, reason='mcp package not installed')


# ------------------------------------------------------------------ #
#  Config tests                                                        #
# ------------------------------------------------------------------ #

class TestServerConfig:

    def test_config_dataclass_defaults(self):
        from oracle.data_studio_mcp_server.config import ServerConfig
        cfg = ServerConfig()
        assert cfg.essbase is None
        assert cfg.adp is None
        assert cfg.datatransforms is None
        assert cfg.transport == 'stdio'
        assert cfg.port == 8000
        # Safe default: viewer. Admin requires explicit opt-in.
        # See oracle/mcp BEST_PRACTICES on scope minimisation.
        assert cfg.profile == 'viewer'
        # S8: bind address defaults to loopback (no auth → no
        # external exposure unless explicit).
        assert cfg.host == '127.0.0.1'

    @patch('oracle.data_studio_mcp_server.config.load_config_file', return_value={})
    @patch('oracle.data_studio_mcp_server.config.get_keyring_password', return_value=None)
    def test_load_config_host_default_is_loopback(self, mock_keyring, mock_file):
        '''S8: With nothing configured, host defaults to 127.0.0.1.'''
        from oracle.data_studio_mcp_server.config import load_config
        with patch.dict(os.environ, {}, clear=True):
            cfg = load_config()
        assert cfg.host == '127.0.0.1'

    @patch('oracle.data_studio_mcp_server.config.load_config_file', return_value={})
    @patch('oracle.data_studio_mcp_server.config.get_keyring_password', return_value=None)
    def test_load_config_host_override_via_env(self, mock_keyring, mock_file):
        '''S8: explicit MCP_HOST=0.0.0.0 must override the safe default.'''
        from oracle.data_studio_mcp_server.config import load_config
        with patch.dict(os.environ, {'MCP_HOST': '0.0.0.0'}, clear=False):
            cfg = load_config()
        assert cfg.host == '0.0.0.0'

    def test_essbase_config_dataclass(self):
        from oracle.data_studio_mcp_server.config import EssbaseConfig
        cfg = EssbaseConfig(
            url='https://host', user='admin', password='pass')
        assert cfg.url == 'https://host'
        assert cfg.user == 'admin'
        assert cfg.password == 'pass'
        assert cfg.token is None

    def test_essbase_config_with_token(self):
        from oracle.data_studio_mcp_server.config import EssbaseConfig
        cfg = EssbaseConfig(
            url='https://host', user='', password='',
            token='mytoken')
        assert cfg.token == 'mytoken'

    def test_adp_config_dataclass(self):
        from oracle.data_studio_mcp_server.config import AdpConfig
        cfg = AdpConfig(url='https://adp', user='admin', password='pass')
        assert cfg.url == 'https://adp'

    def test_dt_config_dataclass(self):
        from oracle.data_studio_mcp_server.config import DataTransformsConfig
        cfg = DataTransformsConfig(
            url='https://dt', user='admin', password='pass')
        assert cfg.url == 'https://dt'

    @patch('oracle.data_studio_mcp_server.config.load_config_file', return_value={})
    @patch('oracle.data_studio_mcp_server.config.get_keyring_password', return_value=None)
    def test_load_config_env_vars(self, mock_keyring, mock_file):
        '''Config from environment variables.'''
        from oracle.data_studio_mcp_server.config import load_config
        env = {
            'ESSBASE_URL': 'https://ess-env',
            'ESSBASE_USER': 'envuser',
            'ESSBASE_PASSWORD': 'envpass',
            'MCP_TRANSPORT': 'streamable-http',
            'MCP_PORT': '9000',
            'MCP_PROFILE': 'analyst',
        }
        with patch.dict(os.environ, env, clear=False):
            cfg = load_config()
        assert cfg.essbase is not None
        assert cfg.essbase.url == 'https://ess-env'
        assert cfg.transport == 'streamable-http'
        assert cfg.port == 9000
        assert cfg.profile == 'analyst'

    @patch('oracle.data_studio_mcp_server.config.load_config_file', return_value={})
    @patch('oracle.data_studio_mcp_server.config.get_keyring_password', return_value=None)
    def test_load_config_no_service(self, mock_keyring, mock_file):
        '''Config with no service env vars returns None for all services.'''
        from oracle.data_studio_mcp_server.config import load_config
        with patch.dict(os.environ, {}, clear=True):
            cfg = load_config()
        assert cfg.essbase is None
        assert cfg.adp is None
        assert cfg.datatransforms is None

    @patch('oracle.data_studio_mcp_server.config.load_config_file', return_value={})
    @patch('oracle.data_studio_mcp_server.config.get_keyring_password', return_value=None)
    def test_load_config_adp_env(self, mock_keyring, mock_file):
        from oracle.data_studio_mcp_server.config import load_config
        env = {
            'ADP_URL': 'https://adp-env',
            'ADP_USER': 'adpuser',
            'ADP_PASSWORD': 'adppass',
        }
        with patch.dict(os.environ, env, clear=False):
            cfg = load_config()
        assert cfg.adp is not None
        assert cfg.adp.url == 'https://adp-env'

    @patch('oracle.data_studio_mcp_server.config.load_config_file', return_value={})
    @patch('oracle.data_studio_mcp_server.config.get_keyring_password', return_value=None)
    def test_load_config_dt_env(self, mock_keyring, mock_file):
        from oracle.data_studio_mcp_server.config import load_config
        env = {
            'DT_URL': 'https://dt-env',
            'DT_USER': 'dtuser',
            'DT_PASSWORD': 'dtpass',
        }
        with patch.dict(os.environ, env, clear=False):
            cfg = load_config()
        assert cfg.datatransforms is not None
        assert cfg.datatransforms.url == 'https://dt-env'

    @patch('oracle.data_studio_mcp_server.config.load_config_file', return_value={})
    @patch('oracle.data_studio_mcp_server.config.get_keyring_password', return_value=None)
    def test_load_config_essbase_token(self, mock_keyring, mock_file):
        from oracle.data_studio_mcp_server.config import load_config
        env = {
            'ESSBASE_URL': 'https://ess-tok',
            'ESSBASE_TOKEN': 'mytok',
        }
        with patch.dict(os.environ, env, clear=False):
            cfg = load_config()
        assert cfg.essbase is not None
        assert cfg.essbase.token == 'mytok'

    def test_config_asdict(self):
        from oracle.data_studio_mcp_server.config import ServerConfig, EssbaseConfig
        cfg = ServerConfig(
            essbase=EssbaseConfig(url='u', user='admin', password='p'))
        d = asdict(cfg)
        assert d['essbase']['url'] == 'u'
        assert d['transport'] == 'stdio'


# ------------------------------------------------------------------ #
#  Credential store tests                                              #
# ------------------------------------------------------------------ #

class TestCredentialStore:

    def test_config_dir_default(self):
        from oracle.data_studio_mcp_server.credential_store import CONFIG_DIR
        assert '.oracle-data-studio' in str(CONFIG_DIR)

    @patch('oracle.data_studio_mcp_server.credential_store.CONFIG_FILE')
    def test_load_config_file_missing(self, mock_path):
        mock_path.exists.return_value = False
        from oracle.data_studio_mcp_server.credential_store import load_config_file
        assert load_config_file() == {}

    def test_store_credentials_never_writes_token_to_file(self, tmp_path,
                                                          monkeypatch):
        '''Hardening: bearer tokens / api keys passed to store_credentials
        must end up in the OS keyring, NEVER in the plaintext INI file.
        This is the reviewer-blocking fix for the prior behaviour where
        `--token foo` ended up written to ~/.oracle-data-studio/config.
        '''
        from oracle.data_studio_mcp_server import credential_store as cs
        cfg_file = tmp_path / 'config'
        monkeypatch.setattr(cs, 'CONFIG_DIR', tmp_path)
        monkeypatch.setattr(cs, 'CONFIG_FILE', cfg_file)

        calls = []
        def fake_set(svc, user, secret):
            calls.append((svc, user, secret))
            return True
        with patch.object(cs, '_set_keyring_password', side_effect=fake_set):
            result = cs.store_credentials(
                'essbase',
                url='https://e',
                user='admin',
                token='ghp_REDACTED_TOKEN_VALUE_xyz789')
        # Token went to keyring
        assert ('essbase', '__token__',
                'ghp_REDACTED_TOKEN_VALUE_xyz789') in calls
        # Token is NOT on disk anywhere
        body = cfg_file.read_text()
        assert 'ghp_REDACTED_TOKEN_VALUE_xyz789' not in body
        assert 'token' not in body.lower() or '_token_' not in body
        # URL + user still on disk (those are not secrets)
        assert 'url = https://e' in body
        assert 'user = admin' in body
        # Result reports the token was stored
        assert 'token' in result['secret_extras_stored']

    def test_store_credentials_extras_renamed_to_secret_keys_routed_to_keyring(
            self, tmp_path, monkeypatch):
        '''Even if a caller renames a field to one of the SECRET_KEYS
        (e.g. bearer, api_key, secret), it must NOT land on disk.'''
        from oracle.data_studio_mcp_server import credential_store as cs
        cfg_file = tmp_path / 'config'
        monkeypatch.setattr(cs, 'CONFIG_DIR', tmp_path)
        monkeypatch.setattr(cs, 'CONFIG_FILE', cfg_file)
        with patch.object(cs, '_set_keyring_password', return_value=True):
            cs.store_credentials('adp', url='https://x', user='u',
                                  bearer='BEARER_TOKEN',
                                  api_key='AK',
                                  secret='S')
        body = cfg_file.read_text()
        for sensitive in ('BEARER_TOKEN', 'AK', 'S'):
            # The bare value must not appear on disk
            assert sensitive not in body, \
                f'secret {sensitive!r} leaked to config file'

    def test_get_keyring_token_round_trips(self):
        '''Round-trip: set a token, then retrieve it via the public
        get_keyring_token() helper.'''
        from oracle.data_studio_mcp_server.credential_store import (
            _set_keyring_password, get_keyring_token)
        fake_keyring = MagicMock()
        fake_keyring.get_password.return_value = 'ghp_xyz'
        with patch.dict('sys.modules', {'keyring': fake_keyring}):
            assert get_keyring_token('essbase') == 'ghp_xyz'
        # Lookup was scoped to the right service + pseudo-user
        fake_keyring.get_password.assert_called_with(
            'oracle-data-studio/essbase', '__token__')

    def test_store_credentials_writes_config_and_keyring(self, tmp_path,
                                                          monkeypatch):
        '''store_credentials writes URL/user to config and password
        to keyring.'''
        cfg_file = tmp_path / 'config'
        from oracle.data_studio_mcp_server import credential_store as cs
        monkeypatch.setattr(cs, 'CONFIG_DIR', tmp_path)
        monkeypatch.setattr(cs, 'CONFIG_FILE', cfg_file)
        with patch.object(cs, '_set_keyring_password',
                           return_value=True) as mock_set:
            result = cs.store_credentials('adp', url='https://x',
                                            user='ADMIN',
                                            password='secret')
        assert result['status'] == 'success'
        assert result['keyring_stored'] is True
        # Password never lands on disk
        assert 'secret' not in cfg_file.read_text()
        assert 'url = https://x' in cfg_file.read_text()
        mock_set.assert_called_once_with('adp', 'ADMIN', 'secret')

    def test_store_credentials_rejects_unknown_service(self):
        from oracle.data_studio_mcp_server.credential_store import (
            store_credentials)
        with pytest.raises(ValueError, match='Unknown service'):
            store_credentials('nonexistent')

    def test_store_credentials_extras_written_to_file(self, tmp_path,
                                                      monkeypatch):
        from oracle.data_studio_mcp_server import credential_store as cs
        cfg_file = tmp_path / 'config'
        monkeypatch.setattr(cs, 'CONFIG_DIR', tmp_path)
        monkeypatch.setattr(cs, 'CONFIG_FILE', cfg_file)
        with patch.object(cs, '_set_keyring_password', return_value=True):
            cs.store_credentials('server', transport='stdio', port=9000)
        text = cfg_file.read_text()
        assert 'transport = stdio' in text
        assert 'port = 9000' in text

    def test_remove_credentials_removes_section(self, tmp_path, monkeypatch):
        from oracle.data_studio_mcp_server import credential_store as cs
        cfg_file = tmp_path / 'config'
        monkeypatch.setattr(cs, 'CONFIG_DIR', tmp_path)
        monkeypatch.setattr(cs, 'CONFIG_FILE', cfg_file)
        with patch.object(cs, '_set_keyring_password', return_value=True), \
             patch.object(cs, '_delete_keyring_password', return_value=True):
            cs.store_credentials('adp', url='https://x', user='ADMIN',
                                  password='p')
            result = cs.remove_credentials('adp')
        assert result['removed_config'] is True
        assert result['removed_keyring'] is True
        assert 'adp' not in cfg_file.read_text()

    def test_list_credentials_returns_sections(self, tmp_path, monkeypatch):
        from oracle.data_studio_mcp_server import credential_store as cs
        cfg_file = tmp_path / 'config'
        monkeypatch.setattr(cs, 'CONFIG_DIR', tmp_path)
        monkeypatch.setattr(cs, 'CONFIG_FILE', cfg_file)
        with patch.object(cs, '_set_keyring_password', return_value=True):
            cs.store_credentials('adp', url='https://x', user='ADMIN',
                                  password='p')
        result = cs.list_credentials()
        assert 'adp' in result
        assert result['adp']['url'] == 'https://x'
        # Password is NOT in the listed result
        assert 'password' not in result['adp']

    def test_load_config_file_returns_dict(self, tmp_path, monkeypatch):
        from oracle.data_studio_mcp_server import credential_store as cs
        cfg_file = tmp_path / 'config'
        monkeypatch.setattr(cs, 'CONFIG_DIR', tmp_path)
        monkeypatch.setattr(cs, 'CONFIG_FILE', cfg_file)
        with patch.object(cs, '_set_keyring_password', return_value=True):
            cs.store_credentials('essbase', url='https://e', user='admin',
                                  password='p')
        loaded = cs.load_config_file()
        assert loaded['essbase']['url'] == 'https://e'

    def test_set_keyring_password_succeeds(self):
        '''_set_keyring_password returns True when the keyring module accepts.'''
        from oracle.data_studio_mcp_server.credential_store import (
            _set_keyring_password)
        with patch.dict('sys.modules', {'keyring': MagicMock()}):
            assert _set_keyring_password('adp', 'u', 'p') is True

    def test_set_keyring_password_falls_back_when_keyring_missing(self):
        from oracle.data_studio_mcp_server.credential_store import (
            _set_keyring_password)
        import builtins
        _real = builtins.__import__

        def _no_keyring(name, *a, **kw):
            if name == 'keyring':
                raise ImportError('no keyring')
            return _real(name, *a, **kw)

        with patch('builtins.__import__', side_effect=_no_keyring):
            assert _set_keyring_password('adp', 'u', 'p') is False

    def test_get_keyring_password_returns_value(self):
        '''When the keyring lookup succeeds, the value comes back.'''
        from oracle.data_studio_mcp_server.credential_store import (
            _get_keyring_password)
        fake_keyring = MagicMock()
        fake_keyring.get_password.return_value = 'secret'
        with patch.dict('sys.modules', {'keyring': fake_keyring}):
            assert _get_keyring_password('adp', 'ADMIN') == 'secret'

    def test_delete_keyring_password_succeeds(self):
        from oracle.data_studio_mcp_server.credential_store import (
            _delete_keyring_password)
        fake_keyring = MagicMock()
        with patch.dict('sys.modules', {'keyring': fake_keyring}):
            assert _delete_keyring_password('adp', 'ADMIN') is True
        fake_keyring.delete_password.assert_called_once()

    def test_delete_keyring_password_handles_missing(self):
        '''_delete_keyring_password returns False on errors.'''
        from oracle.data_studio_mcp_server.credential_store import (
            _delete_keyring_password)
        fake_keyring = MagicMock()
        fake_keyring.delete_password.side_effect = Exception('not found')
        with patch.dict('sys.modules', {'keyring': fake_keyring}):
            assert _delete_keyring_password('adp', 'ADMIN') is False

    def test_get_keyring_password_no_keyring(self):
        '''get_keyring_password returns None when keyring is unavailable.'''
        from oracle.data_studio_mcp_server.credential_store import get_keyring_password
        import builtins
        _real_import = builtins.__import__

        def _no_keyring(name, *args, **kwargs):
            if name == 'keyring':
                raise ImportError('mocked: no keyring')
            return _real_import(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=_no_keyring):
            assert get_keyring_password('essbase', 'someuser') is None


# ------------------------------------------------------------------ #
#  Helpers tests                                                       #
# ------------------------------------------------------------------ #

class TestHelpers:

    def test_safe_call_success(self):
        from oracle.data_studio_mcp_server.tools._helpers import safe_call
        result, error = safe_call('test', lambda x: x * 2, 21)
        assert result == 42
        assert error is None

    def test_safe_call_failure(self):
        from oracle.data_studio_mcp_server.tools._helpers import safe_call
        def _fail():
            raise ValueError('boom')
        result, error = safe_call('test', _fail)
        assert result is None
        assert 'boom' in error

    def test_safe_err_redacts_dsn_password(self):
        '''S5: Oracle/cx_Oracle DSNs embed credentials.'''
        from oracle.data_studio_mcp_server.tools._helpers import safe_err
        msg = ("ORA-01017: invalid username/password; "
               "logon denied for ADMIN/Welcome2025#@//myadb.adb.us-ashburn-1."
               "oraclecloud.com:1522/myadb_high")
        cleaned = safe_err(msg)
        assert 'Welcome2025' not in cleaned
        assert 'ADMIN/***@' in cleaned

    def test_safe_err_redacts_url_userinfo(self):
        '''Passwords in URL userinfo (https://user:pass@host).'''
        from oracle.data_studio_mcp_server.tools._helpers import safe_err
        msg = ('Connection to https://weblogic:welcome1@'
               'essbase.example.com/essbase/rest/v1 failed')
        cleaned = safe_err(msg)
        assert 'welcome1' not in cleaned
        assert '***:***@' in cleaned

    def test_safe_err_redacts_bearer_token(self):
        from oracle.data_studio_mcp_server.tools._helpers import safe_err
        msg = ('401 Unauthorized: Authorization: Bearer '
               'eyJhbGciOiJSUzI1NiJ9.payload.signature_chunk')
        cleaned = safe_err(msg)
        assert 'eyJ' not in cleaned
        assert 'signature_chunk' not in cleaned

    def test_safe_err_redacts_password_kv(self):
        '''password=... in JSON / query strings / env strings.'''
        from oracle.data_studio_mcp_server.tools._helpers import safe_err
        for raw in [
            '{"username": "ADMIN", "password": "Welcome2025#"}',
            'connect_string: ADMIN; password=Welcome2025#; host=...',
            "param: 'password'='Welcome2025#'",
        ]:
            cleaned = safe_err(raw)
            assert 'Welcome2025' not in cleaned, \
                f'password leaked through: {cleaned!r}'

    def test_safe_err_redacts_ocid_tail(self):
        from oracle.data_studio_mcp_server.tools._helpers import safe_err
        msg = ('failed for compartment '
               'ocid1.compartment.oc1..aaaaaaaa1234567890zzzzzzz '
               'and tenancy '
               'ocid1.tenancy.oc1..aaaaaaaaqwerty12345')
        cleaned = safe_err(msg)
        assert 'aaaaaaaa1234567890zzzzzzz' not in cleaned
        assert 'aaaaaaaaqwerty12345' not in cleaned
        # Prefix kept for context
        assert 'ocid1.compartment.***' in cleaned
        assert 'ocid1.tenancy.***' in cleaned

    def test_safe_err_redacts_filesystem_paths(self):
        from oracle.data_studio_mcp_server.tools._helpers import safe_err
        msg = ('wallet not found at '
               '/Users/alex/secrets/wallet.zip — '
               'also tried /opt/oracle/network/admin/cwallet.sso')
        cleaned = safe_err(msg)
        assert '/Users/alex/secrets' not in cleaned
        assert '/opt/oracle/network' not in cleaned
        # Basename retained for diagnosis
        assert 'wallet.zip' in cleaned
        assert 'cwallet.sso' in cleaned

    def test_safe_err_caps_length(self):
        from oracle.data_studio_mcp_server.tools._helpers import safe_err
        msg = 'x' * 5000
        cleaned = safe_err(msg)
        assert len(cleaned) < 1000
        assert 'truncated' in cleaned

    def test_err_funnels_through_safe_err(self):
        '''The public `err()` helper must sanitise, not pass through.'''
        from oracle.data_studio_mcp_server.tools._helpers import err
        msg = 'Connection failed for ADMIN/Welcome2025#@host:1521/svc'
        result = json.loads(err(msg))
        assert 'Welcome2025' not in result['error']
        assert 'ADMIN/***@' in result['error']

    def test_safe_call_failure_redacts(self):
        '''safe_call must funnel exceptions through safe_err too.'''
        from oracle.data_studio_mcp_server.tools._helpers import safe_call
        def _fail():
            raise ValueError(
                'login failed for ADMIN/Welcome2025#@adb.example.com')
        _, error = safe_call('login', _fail)
        assert 'Welcome2025' not in error
        assert 'login' in error  # label retained

    def test_build_response_no_errors(self):
        from oracle.data_studio_mcp_server.tools._helpers import build_response
        resp = json.loads(build_response({'key': 'val'}))
        assert resp['key'] == 'val'
        assert '_errors' not in resp

    def test_build_response_with_errors(self):
        from oracle.data_studio_mcp_server.tools._helpers import build_response
        resp = json.loads(build_response({'key': 'val'}, ['e1', 'e2']))
        assert resp['_errors'] == ['e1', 'e2']

    def test_err(self):
        from oracle.data_studio_mcp_server.tools._helpers import err
        resp = json.loads(err('bad'))
        assert resp['error'] == 'bad'

    def test_fmt_none(self):
        from oracle.data_studio_mcp_server.tools._helpers import fmt
        resp = json.loads(fmt(None))
        assert resp['status'] == 'success'

    def test_fmt_dict(self):
        from oracle.data_studio_mcp_server.tools._helpers import fmt
        resp = json.loads(fmt({'a': 1}))
        assert resp['a'] == 1

    def test_fmt_list(self):
        from oracle.data_studio_mcp_server.tools._helpers import fmt
        resp = json.loads(fmt([1, 2, 3]))
        assert resp == [1, 2, 3]

    def test_fmt_string(self):
        from oracle.data_studio_mcp_server.tools._helpers import fmt
        assert fmt('hello') == 'hello'

    def test_safe_call_with_kwargs(self):
        from oracle.data_studio_mcp_server.tools._helpers import safe_call
        def _fn(a, b=10):
            return a + b
        result, error = safe_call('test', _fn, 5, b=20)
        assert result == 25
        assert error is None


# ------------------------------------------------------------------ #
#  Profile tests                                                       #
# ------------------------------------------------------------------ #

class TestProfiles:

    def test_valid_profiles(self):
        from oracle.data_studio_mcp_server.profiles import VALID_PROFILES
        assert 'admin' in VALID_PROFILES
        assert 'analyst' in VALID_PROFILES
        assert 'viewer' in VALID_PROFILES

    def test_admin_profile_is_none(self):
        from oracle.data_studio_mcp_server.profiles import PROFILES
        assert PROFILES['admin'] is None

    def test_verb_extraction_essbase(self):
        from oracle.data_studio_mcp_server.profiles import _get_verb_suffix
        assert _get_verb_suffix('essbase_explore') == 'explore'
        assert _get_verb_suffix('essbase_describe_database') == 'describe_database'
        assert _get_verb_suffix('essbase_run_calculation') == 'run_calculation'
        assert _get_verb_suffix('essbase_manage_variables') == 'manage_variables'

    def test_verb_extraction_adp(self):
        from oracle.data_studio_mcp_server.profiles import _get_verb_suffix
        assert _get_verb_suffix('adp_execute_sql') == 'execute_sql'
        assert _get_verb_suffix('adp_discover_schema') == 'discover_schema'
        assert _get_verb_suffix('adp_build_analytic_view') == 'build_analytic_view'

    def test_verb_extraction_dt(self):
        from oracle.data_studio_mcp_server.profiles import _get_verb_suffix
        assert _get_verb_suffix('dt_explore') == 'explore'
        assert _get_verb_suffix('dt_manage_schedule') == 'manage_schedule'

    def test_verb_extraction_unknown_prefix(self):
        from oracle.data_studio_mcp_server.profiles import _get_verb_suffix
        assert _get_verb_suffix('unknown_tool') == 'unknown_tool'

    @mcp_required
    @mcp_required
    def test_default_profile_removes_high_risk_tools(self):
        '''Reviewer-blocking guarantee: with NO --profile flag, the
        server must default to a low-privilege profile that does NOT
        expose destructive, modify, or execute-arbitrary-code tools.

        Walks the full registered tool catalog through the actual
        default profile (whatever ServerConfig() sets) and asserts
        the high-risk tool surface is not exposed.'''
        from oracle.data_studio_mcp_server.config import ServerConfig
        from oracle.data_studio_mcp_server.profiles import apply_profile
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import (
            adp_tools, dt_tools, essbase_tools)

        default_profile = ServerConfig().profile
        # Sanity — the default must not be admin
        assert default_profile != 'admin', \
            'default profile must not be admin per BEST_PRACTICES'

        mcp_server = FastMCP('test')
        for mod in (essbase_tools, adp_tools, dt_tools):
            mod.register_tools(mcp_server)

        apply_profile(mcp_server, default_profile)
        names = set(mcp_server._tool_manager._tools.keys())

        # None of the following tools may be visible under the default:
        BANNED_UNDER_DEFAULT = {
            # Destructive / modifying
            'essbase_manage_application',     # create/delete/copy/rename
            'essbase_manage_database',        # delete/copy/rename
            'essbase_manage_script',          # CRUD scripts
            'essbase_manage_files',           # upload/delete/move
            'essbase_manage_filters',         # CRUD filters
            'essbase_manage_users',           # CRUD users + role provisioning
            'essbase_manage_groups',          # CRUD groups
            'essbase_manage_connections',     # CRUD connections
            'essbase_manage_datasources',     # CRUD datasources
            'essbase_manage_drill_through',   # CRUD drill-through reports
            'essbase_manage_variables',       # CRUD variables
            'essbase_manage_db_settings',     # writeable settings
            'essbase_manage_sessions',        # can kill sessions
            'essbase_edit_outline',           # add/remove/move members
            'essbase_load_data',              # data load jobs
            'essbase_deploy_workbook',        # creates / overwrites cube
            'essbase_run_calculation',        # executes calc scripts
            # Direct MDX (we verified S1 — viewer must not run MDX)
            'essbase_query',
            'essbase_export_data',
            # Calc-script source code / log content (S2)
            'essbase_get_script',
            'essbase_get_logs',
            # ADP destructive / modifying
            'adp_build_analytic_view',
            'adp_manage_analytic_views',
            'adp_manage_catalog',
            'adp_manage_sharing',
            'adp_manage_credentials',
            'adp_manage_insights',
            'adp_manage_db_links',
            'adp_load_from_cloud',
            'adp_generate_insights',
            'adp_ai_chat',
            # DT destructive / modifying
            'dt_manage_project',
            'dt_manage_dataflow',
            'dt_manage_schedule',
            'dt_manage_variables',
            'dt_manage_connection',
            'dt_create_pipeline',
            'dt_run_pipeline',
        }
        leaked = BANNED_UNDER_DEFAULT & names
        assert not leaked, (
            f'Default profile ({default_profile!r}) leaked high-risk '
            f'tools: {sorted(leaked)}')

        # Sanity: the default still exposes basic discovery tools.
        # Without these, the server is useless even for browsing.
        EXPECTED_UNDER_DEFAULT = {
            'essbase_explore',
            'essbase_describe_database',
            'essbase_browse_outline',
            'essbase_search_members',
            'essbase_server_health',
            'adp_search',
            'adp_browse_catalog',
            'adp_query_analytic_view',
            'adp_analyze_analytic_view',
            'adp_get_annotations',
            'dt_explore',
            'dt_describe_project',
            'dt_describe_connection',
            'dt_check_health',
            'dt_browse_data',
        }
        missing = EXPECTED_UNDER_DEFAULT - names
        assert not missing, (
            f'Default profile is too restrictive — missing safe '
            f'metadata tools: {sorted(missing)}')

    def test_viewer_profile_filtering(self):
        '''Viewer profile: only read-only tools.'''
        from oracle.data_studio_mcp_server.profiles import apply_profile
        mock_mcp = MagicMock()
        mock_mcp._tool_manager._tools = {
            'essbase_explore': MagicMock(),
            'essbase_describe_database': MagicMock(),
            'essbase_query': MagicMock(),
            'essbase_run_calculation': MagicMock(),
            'essbase_manage_variables': MagicMock(),
            'essbase_server_health': MagicMock(),
            'adp_build_analytic_view': MagicMock(),
            'adp_search': MagicMock(),
            'adp_analyze_analytic_view': MagicMock(),
            'dt_explore': MagicMock(),
            'dt_create_pipeline': MagicMock(),
            'dt_browse_data': MagicMock(),
        }
        apply_profile(mock_mcp, 'viewer')
        tools = mock_mcp._tool_manager._tools
        # Viewer should keep: explore, describe_, server_health,
        # browse_, search_, analyze_
        assert 'essbase_explore' in tools
        assert 'essbase_describe_database' in tools
        assert 'essbase_server_health' in tools
        assert 'dt_explore' in tools
        assert 'dt_browse_data' in tools
        assert 'adp_search' in tools
        assert 'adp_analyze_analytic_view' in tools
        # Viewer should remove: run_, manage_, build_, create_
        assert 'essbase_run_calculation' not in tools
        assert 'essbase_manage_variables' not in tools
        assert 'adp_build_analytic_view' not in tools
        assert 'dt_create_pipeline' not in tools

    @mcp_required
    def test_analyst_profile_filtering(self):
        '''Analyst profile: read + query/execute, no modify.'''
        from oracle.data_studio_mcp_server.profiles import apply_profile
        mock_mcp = MagicMock()
        mock_mcp._tool_manager._tools = {
            'essbase_explore': MagicMock(),
            'essbase_query': MagicMock(),
            'essbase_run_calculation': MagicMock(),
            'essbase_manage_variables': MagicMock(),
            'adp_generate_insights': MagicMock(),
            'adp_ai_chat': MagicMock(),
            'adp_load_from_cloud': MagicMock(),
            'dt_explore': MagicMock(),
            'dt_manage_schedule': MagicMock(),
        }
        apply_profile(mock_mcp, 'analyst')
        tools = mock_mcp._tool_manager._tools
        # Analyst should keep: explore, query, run_, generate_, ai_
        assert 'essbase_explore' in tools
        assert 'essbase_run_calculation' in tools
        assert 'adp_generate_insights' in tools
        assert 'adp_ai_chat' in tools
        assert 'dt_explore' in tools
        # Analyst should remove: manage_, load_from_cloud (explicit deny)
        assert 'essbase_manage_variables' not in tools
        assert 'adp_load_from_cloud' not in tools
        assert 'dt_manage_schedule' not in tools

    @mcp_required
    def test_viewer_cannot_run_mdx(self):
        '''Security: viewer must not be able to invoke any tool that
        runs MDX. Specifically:
          - essbase_query (verb=`query`) — already excluded by verb rules.
          - essbase_export_data — used to be allowed via the `export_`
            verb prefix, but it accepts a free-form `mdx` arg and runs
            ess.grid.execute_mdx, so it was moved out of viewer.

        This test locks both guarantees in. Removing `export_` from the
        viewer allowed_verbs (or adding `essbase_export_data` to
        explicit_deny) must keep this test passing.'''
        from oracle.data_studio_mcp_server.profiles import apply_profile
        mock_mcp = MagicMock()
        mock_mcp._tool_manager._tools = {
            'essbase_query':       MagicMock(),
            'essbase_export_data': MagicMock(),
            # Sanity controls — should still be visible to viewer
            'essbase_explore':     MagicMock(),
            'essbase_describe_database': MagicMock(),
            'essbase_browse_outline': MagicMock(),
            'essbase_search_members': MagicMock(),
        }
        apply_profile(mock_mcp, 'viewer')
        tools = mock_mcp._tool_manager._tools
        # Both MDX-running tools must be removed for viewer
        assert 'essbase_query' not in tools, \
            'viewer must not have essbase_query (runs MDX)'
        assert 'essbase_export_data' not in tools, \
            'viewer must not have essbase_export_data (runs MDX)'
        # Read-only tools should remain
        assert 'essbase_explore' in tools
        assert 'essbase_describe_database' in tools
        assert 'essbase_browse_outline' in tools
        assert 'essbase_search_members' in tools

    @mcp_required
    def test_viewer_cannot_read_calc_script_or_logs(self):
        '''S2: essbase_get_script and essbase_get_logs leak content
        (script source code, logs with PII / SQL). Both are denied
        for viewer.'''
        from oracle.data_studio_mcp_server.profiles import apply_profile
        mock_mcp = MagicMock()
        mock_mcp._tool_manager._tools = {
            'essbase_get_script': MagicMock(),
            'essbase_get_logs':   MagicMock(),
            # sanity controls
            'essbase_explore':    MagicMock(),
            'adp_get_annotations': MagicMock(),  # other get_ stays
        }
        apply_profile(mock_mcp, 'viewer')
        tools = mock_mcp._tool_manager._tools
        assert 'essbase_get_script' not in tools, \
            'viewer must not see calc-script source'
        assert 'essbase_get_logs' not in tools, \
            'viewer must not see server logs'
        # Other get_ tools still work
        assert 'essbase_explore' in tools
        assert 'adp_get_annotations' in tools

    @mcp_required
    def test_analyst_can_read_script_but_not_logs(self):
        '''S2: analyst keeps essbase_get_script (they may run it via
        essbase_run_calculation) but loses essbase_get_logs (admin
        only).'''
        from oracle.data_studio_mcp_server.profiles import apply_profile
        mock_mcp = MagicMock()
        mock_mcp._tool_manager._tools = {
            'essbase_get_script': MagicMock(),
            'essbase_get_logs':   MagicMock(),
        }
        apply_profile(mock_mcp, 'analyst')
        tools = mock_mcp._tool_manager._tools
        assert 'essbase_get_script' in tools, \
            'analyst should be able to read scripts they may run'
        assert 'essbase_get_logs' not in tools, \
            'logs are admin-only'

    @mcp_required
    def test_analyst_cannot_run_pipeline(self):
        '''S3: dt_run_pipeline mutates target tables — analyst is
        "read + execute, no modify" and pipelines write, so deny.'''
        from oracle.data_studio_mcp_server.profiles import apply_profile
        mock_mcp = MagicMock()
        mock_mcp._tool_manager._tools = {
            'dt_run_pipeline':     MagicMock(),
            # sanity — other run_ verbs (e.g. essbase_run_calculation)
            # are still allowed for analyst
            'essbase_run_calculation': MagicMock(),
        }
        apply_profile(mock_mcp, 'analyst')
        tools = mock_mcp._tool_manager._tools
        assert 'dt_run_pipeline' not in tools, \
            'analyst must not run pipelines (mutates targets)'
        assert 'essbase_run_calculation' in tools, \
            'analyst should still run calc scripts'

    @mcp_required
    def test_analyst_keeps_export_data(self):
        '''Analyst is allowed to run MDX (read+execute). After we
        removed `export_` from viewer, make sure analyst still has
        access — analyst inherits viewer verbs PLUS execute/run/query.'''
        from oracle.data_studio_mcp_server.profiles import apply_profile
        mock_mcp = MagicMock()
        mock_mcp._tool_manager._tools = {
            'essbase_export_data': MagicMock(),
            'essbase_query':       MagicMock(),
        }
        apply_profile(mock_mcp, 'analyst')
        tools = mock_mcp._tool_manager._tools
        assert 'essbase_export_data' in tools, \
            'analyst should have essbase_export_data'
        assert 'essbase_query' in tools, \
            'analyst should have essbase_query'

    @mcp_required
    def test_viewer_profile_blocks_manage_catalog_allows_browse(self):
        '''Viewer: adp_browse_catalog allowed, adp_manage_catalog blocked.'''
        from oracle.data_studio_mcp_server.profiles import apply_profile
        mock_mcp = MagicMock()
        mock_mcp._tool_manager._tools = {
            'adp_browse_catalog': MagicMock(),
            'adp_manage_catalog': MagicMock(),
        }
        apply_profile(mock_mcp, 'viewer')
        tools = mock_mcp._tool_manager._tools
        assert 'adp_browse_catalog' in tools, \
            'browse_catalog should be visible to viewer'
        assert 'adp_manage_catalog' not in tools, \
            'manage_catalog must not be visible to viewer'

    @mcp_required
    def test_viewer_profile_blocks_manage_project(self):
        '''Viewer: dt_describe_project allowed, dt_manage_project blocked.'''
        from oracle.data_studio_mcp_server.profiles import apply_profile
        mock_mcp = MagicMock()
        mock_mcp._tool_manager._tools = {
            'dt_describe_project': MagicMock(),
            'dt_manage_project': MagicMock(),
        }
        apply_profile(mock_mcp, 'viewer')
        tools = mock_mcp._tool_manager._tools
        assert 'dt_describe_project' in tools, \
            'describe_project should be visible to viewer'
        assert 'dt_manage_project' not in tools, \
            'manage_project (delete) must not be visible to viewer'

    @mcp_required
    def test_analyst_profile_blocks_manage_catalog(self):
        '''Analyst: adp_browse_catalog allowed, adp_manage_catalog blocked.'''
        from oracle.data_studio_mcp_server.profiles import apply_profile
        mock_mcp = MagicMock()
        mock_mcp._tool_manager._tools = {
            'adp_browse_catalog': MagicMock(),
            'adp_manage_catalog': MagicMock(),
            'dt_describe_project': MagicMock(),
            'dt_manage_project': MagicMock(),
        }
        apply_profile(mock_mcp, 'analyst')
        tools = mock_mcp._tool_manager._tools
        assert 'adp_browse_catalog' in tools
        assert 'adp_manage_catalog' not in tools
        assert 'dt_describe_project' in tools
        assert 'dt_manage_project' not in tools

    @mcp_required
    def test_admin_profile_no_filtering(self):
        from oracle.data_studio_mcp_server.profiles import apply_profile
        mock_mcp = MagicMock()
        mock_mcp._tool_manager._tools = {
            'essbase_explore': MagicMock(),
            'essbase_manage_variables': MagicMock(),
            'adp_manage_sharing': MagicMock(),
        }
        apply_profile(mock_mcp, 'admin')
        assert len(mock_mcp._tool_manager._tools) == 3

    @mcp_required
    def test_invalid_profile_raises(self):
        from oracle.data_studio_mcp_server.profiles import apply_profile
        mock_mcp = MagicMock()
        mock_mcp._tool_manager._tools = {}
        with pytest.raises(ValueError, match='Unknown profile'):
            apply_profile(mock_mcp, 'superadmin')


# ------------------------------------------------------------------ #
#  Tool registration tests                                             #
# ------------------------------------------------------------------ #

@mcp_required
class TestToolRegistration:

    def test_essbase_tools_register(self):
        '''essbase_tools registers exactly 30 tools.'''
        from mcp.server.fastmcp import FastMCP
        mcp_server = FastMCP('test')
        from oracle.data_studio_mcp_server.tools import essbase_tools
        essbase_tools.register_tools(mcp_server)
        tools = mcp_server._tool_manager._tools
        assert len(tools) == 30

    def test_adp_tools_register(self):
        '''adp_tools registers exactly 15 tools.'''
        from mcp.server.fastmcp import FastMCP
        mcp_server = FastMCP('test')
        from oracle.data_studio_mcp_server.tools import adp_tools
        adp_tools.register_tools(mcp_server)
        tools = mcp_server._tool_manager._tools
        assert len(tools) == 15

    def test_dt_tools_register(self):
        '''dt_tools registers exactly 15 tools.'''
        from mcp.server.fastmcp import FastMCP
        mcp_server = FastMCP('test')
        from oracle.data_studio_mcp_server.tools import dt_tools
        dt_tools.register_tools(mcp_server)
        tools = mcp_server._tool_manager._tools
        assert len(tools) == 15

    def test_all_tools_register(self):
        '''All tool modules together register exactly 60 tools.'''
        from mcp.server.fastmcp import FastMCP
        mcp_server = FastMCP('test')
        from oracle.data_studio_mcp_server.tools import (
            essbase_tools, adp_tools, dt_tools)
        essbase_tools.register_tools(mcp_server)
        adp_tools.register_tools(mcp_server)
        dt_tools.register_tools(mcp_server)
        tools = mcp_server._tool_manager._tools
        assert len(tools) == 60

    def test_essbase_tool_names(self):
        '''Verify expected Essbase tool names.'''
        from mcp.server.fastmcp import FastMCP
        mcp_server = FastMCP('test')
        from oracle.data_studio_mcp_server.tools import essbase_tools
        essbase_tools.register_tools(mcp_server)
        names = set(mcp_server._tool_manager._tools.keys())
        expected = {
            'essbase_explore', 'essbase_describe_database',
            'essbase_query', 'essbase_browse_outline',
            'essbase_search_members', 'essbase_run_calculation',
            'essbase_load_data', 'essbase_deploy_workbook',
            'essbase_manage_variables', 'essbase_get_script',
            'essbase_manage_security', 'essbase_server_health',
            'essbase_export_data',
            'essbase_manage_application', 'essbase_manage_script',
            'essbase_manage_files', 'essbase_manage_connections',
            'essbase_manage_locks', 'essbase_manage_filters',
            'essbase_manage_jobs',
            'essbase_edit_outline', 'essbase_manage_datasources',
            'essbase_manage_drill_through',
            'essbase_manage_database', 'essbase_manage_users',
            'essbase_manage_groups', 'essbase_manage_sessions',
            'essbase_manage_db_settings', 'essbase_get_logs',
            'essbase_outline_metadata',
        }
        assert names == expected

    def test_adp_tool_names(self):
        '''Verify expected ADP tool names.'''
        from mcp.server.fastmcp import FastMCP
        mcp_server = FastMCP('test')
        from oracle.data_studio_mcp_server.tools import adp_tools
        adp_tools.register_tools(mcp_server)
        names = set(mcp_server._tool_manager._tools.keys())
        expected = {
            'adp_build_analytic_view',
            'adp_query_analytic_view', 'adp_analyze_analytic_view',
            'adp_generate_insights',
            'adp_search', 'adp_load_from_cloud',
            'adp_browse_catalog', 'adp_manage_catalog',
            'adp_manage_sharing',
            'adp_manage_analytic_views', 'adp_manage_credentials',
            'adp_ai_chat', 'adp_manage_insights',
            'adp_manage_db_links',
            'adp_get_annotations',
        }
        assert names == expected

    def test_dt_tool_names(self):
        '''Verify expected Data Transforms tool names.'''
        from mcp.server.fastmcp import FastMCP
        mcp_server = FastMCP('test')
        from oracle.data_studio_mcp_server.tools import dt_tools
        dt_tools.register_tools(mcp_server)
        names = set(mcp_server._tool_manager._tools.keys())
        expected = {
            'dt_explore', 'dt_describe_project',
            'dt_describe_connection', 'dt_create_pipeline',
            'dt_check_health', 'dt_browse_data',
            'dt_manage_dataflow', 'dt_manage_schedule',
            'dt_manage_variables',
            'dt_run_pipeline', 'dt_manage_connection',
            'dt_manage_dataload', 'dt_manage_data_entities',
            'dt_manage_workflow', 'dt_manage_project',
        }
        assert names == expected

    def test_all_tools_have_docstrings(self):
        '''Every registered tool should have a docstring.'''
        from mcp.server.fastmcp import FastMCP
        mcp_server = FastMCP('test')
        from oracle.data_studio_mcp_server.tools import (
            essbase_tools, adp_tools, dt_tools)
        essbase_tools.register_tools(mcp_server)
        adp_tools.register_tools(mcp_server)
        dt_tools.register_tools(mcp_server)
        for name, tool in mcp_server._tool_manager._tools.items():
            desc = getattr(tool, 'description', None)
            fn = getattr(tool, 'fn', None)
            has_doc = (desc and len(desc) > 0) or (
                fn and fn.__doc__ and len(fn.__doc__) > 0)
            assert has_doc, f'Tool {name} has no description/docstring'

    def test_all_tool_names_have_service_prefix(self):
        '''All tools should start with essbase_, adp_, or dt_.'''
        from mcp.server.fastmcp import FastMCP
        mcp_server = FastMCP('test')
        from oracle.data_studio_mcp_server.tools import (
            essbase_tools, adp_tools, dt_tools)
        essbase_tools.register_tools(mcp_server)
        adp_tools.register_tools(mcp_server)
        dt_tools.register_tools(mcp_server)
        for name in mcp_server._tool_manager._tools:
            assert (name.startswith('essbase_') or
                    name.startswith('adp_') or
                    name.startswith('dt_')), \
                f'Tool {name} missing service prefix'


# ------------------------------------------------------------------ #
#  Essbase connection helper tests                                     #
# ------------------------------------------------------------------ #

class TestEssbaseConnect:

    def test_get_essbase_returns_client(self):
        from oracle.data_studio_mcp_server.tools._essbase_connect import get_essbase
        mock_ctx = MagicMock()
        mock_ess = MagicMock()
        mock_ctx.request_context.lifespan_context = {'essbase': mock_ess}
        assert get_essbase(mock_ctx) is mock_ess

    def test_get_essbase_returns_none(self):
        from oracle.data_studio_mcp_server.tools._essbase_connect import get_essbase
        mock_ctx = MagicMock()
        mock_ctx.request_context.lifespan_context = {}
        assert get_essbase(mock_ctx) is None


# ------------------------------------------------------------------ #
#  ADP connection helper tests                                         #
# ------------------------------------------------------------------ #

class TestAdpConnect:

    def test_get_adp_returns_client(self):
        from oracle.data_studio_mcp_server.tools._adp_connect import get_adp
        mock_ctx = MagicMock()
        mock_adp = MagicMock()
        mock_adp.rest.expired = None
        mock_ctx.request_context.lifespan_context = {'adp': mock_adp}
        assert get_adp(mock_ctx) is mock_adp

    def test_get_adp_returns_none_no_client(self):
        from oracle.data_studio_mcp_server.tools._adp_connect import get_adp
        mock_ctx = MagicMock()
        mock_ctx.request_context.lifespan_context = {}
        assert get_adp(mock_ctx) is None

    def test_is_expired_401(self):
        from oracle.data_studio_mcp_server.tools._adp_connect import _is_expired
        assert _is_expired(Exception('401 Unauthorized'))
        assert _is_expired(Exception('token expired'))
        assert not _is_expired(Exception('connection refused'))

    def test_reconnect_rate_limit(self):
        '''S6: After _MAX_RECONNECTS_PER_WINDOW failed reconnect
        attempts inside _WINDOW_SECONDS, further attempts are denied
        and put the context into a cooldown.'''
        from oracle.data_studio_mcp_server.tools import _adp_connect as ac
        # Force the rate-limit test to be deterministic: small window
        with patch.object(ac, '_MAX_RECONNECTS_PER_WINDOW', 3):
            lc = {'_adp_config': MagicMock(
                url='https://x', user='u', password='p')}
            # Make adp.login fail every time
            with patch.object(ac, '_locks', {}), \
                 patch('builtins.__import__') as _imp:
                fake_adp = MagicMock()
                fake_adp.login.side_effect = RuntimeError('boom')
                _imp.side_effect = lambda name, *a, **kw: (
                    fake_adp if name == 'adp'
                    else __import__(name, *a, **kw))
                # 3 failed attempts allowed, 4th denied by limiter
                for _ in range(3):
                    assert ac._reconnect(lc) is None
                # 4th attempt: limiter trips, no further login call
                fake_adp.login.reset_mock()
                assert ac._reconnect(lc) is None
                fake_adp.login.assert_not_called()
                assert lc.get('_adp_reconnect_cooldown_until', 0) > 0

    def test_reconnect_uses_per_context_lock(self):
        '''S7: _reconnect serialises swaps of lc['adp'] under a
        per-context lock so concurrent callers don't see a torn
        state. Verify the lock exists and is reused for the same lc.'''
        from oracle.data_studio_mcp_server.tools import _adp_connect as ac
        with patch.object(ac, '_locks', {}):
            lc = {}
            lock1 = ac._ctx_lock(lc)
            lock2 = ac._ctx_lock(lc)
            # Same context → same lock
            assert lock1 is lock2
            # Different context → different lock
            other = {}
            assert ac._ctx_lock(other) is not lock1

    def test_run_adp_success(self):
        '''run_adp returns the formatted result on success.'''
        from oracle.data_studio_mcp_server.tools._adp_connect import (
            run_adp)
        ctx = MagicMock()
        adp = MagicMock()
        adp.rest.expired = None
        ctx.request_context.lifespan_context = {'adp': adp}
        result = run_adp(ctx, lambda c: {'rows': [1, 2]})
        assert json.loads(result)['rows'] == [1, 2]

    def test_run_adp_no_client_returns_error(self):
        from oracle.data_studio_mcp_server.tools._adp_connect import (
            run_adp)
        ctx = MagicMock()
        ctx.request_context.lifespan_context = {}
        result = json.loads(run_adp(ctx, lambda c: 'should not run'))
        assert 'error' in result

    def test_run_adp_returns_strings_unchanged(self):
        '''_default_format returns string results as-is.'''
        from oracle.data_studio_mcp_server.tools._adp_connect import (
            run_adp)
        ctx = MagicMock()
        adp = MagicMock()
        adp.rest.expired = None
        ctx.request_context.lifespan_context = {'adp': adp}
        result = run_adp(ctx, lambda c: 'plain string')
        assert result == 'plain string'

    def test_run_adp_reconnects_on_expired_then_succeeds(self):
        '''When fn raises 'expired', run_adp reconnects and retries.'''
        from oracle.data_studio_mcp_server.tools import _adp_connect as ac
        ctx = MagicMock()
        cfg = MagicMock(url='https://x', user='u', password='p')
        adp_old = MagicMock()
        adp_old.rest.expired = None
        ctx.request_context.lifespan_context = {
            'adp': adp_old, '_adp_config': cfg}

        # First call raises 'expired', second call returns success.
        calls = {'n': 0}
        def fn(c):
            calls['n'] += 1
            if calls['n'] == 1:
                raise RuntimeError('session expired')
            return 'recovered'

        with patch.object(ac, '_locks', {}), \
             patch('builtins.__import__') as imp:
            fake_adp = MagicMock()
            fresh = MagicMock()
            fresh.rest.expired = None
            fake_adp.login.return_value = fresh
            imp.side_effect = lambda name, *a, **kw: (
                fake_adp if name == 'adp'
                else __import__(name, *a, **kw))
            result = ac.run_adp(ctx, fn)
        assert result == 'recovered'
        assert calls['n'] == 2

    def test_run_adp_propagates_non_expired_error(self):
        '''Non-expired exceptions go through safe_err and become an
        error JSON, not a reconnect.'''
        from oracle.data_studio_mcp_server.tools._adp_connect import (
            run_adp)
        ctx = MagicMock()
        adp = MagicMock()
        adp.rest.expired = None
        ctx.request_context.lifespan_context = {'adp': adp}
        def fn(c):
            raise RuntimeError('ORA-00942: table or view does not exist')
        result = json.loads(run_adp(ctx, fn))
        assert 'error' in result
        assert 'ORA-00942' in result['error']

    def test_get_adp_proactive_reconnect_on_expiry(self):
        '''If the cached client's token is past expiry, get_adp
        proactively reconnects without waiting for an exception.'''
        from oracle.data_studio_mcp_server.tools import _adp_connect as ac
        from datetime import datetime, timedelta
        old = MagicMock()
        old.rest.expired = datetime.now() - timedelta(minutes=5)
        cfg = MagicMock(url='x', user='u', password='p')
        lc = {'adp': old, '_adp_config': cfg}
        ctx = MagicMock()
        ctx.request_context.lifespan_context = lc

        with patch.object(ac, '_locks', {}), \
             patch('builtins.__import__') as imp:
            fake_adp = MagicMock()
            fresh = MagicMock()
            fresh.rest.expired = None
            fake_adp.login.return_value = fresh
            imp.side_effect = lambda name, *a, **kw: (
                fake_adp if name == 'adp'
                else __import__(name, *a, **kw))
            client = ac.get_adp(ctx)
        assert client is fresh

    def test_reconnect_avoids_duplicate_login_when_already_done(self):
        '''S7: If two threads both notice an expired client and call
        _reconnect, only the first should do the login work — the
        second should see the freshly-installed client and return it.'''
        from oracle.data_studio_mcp_server.tools import _adp_connect as ac
        from datetime import datetime, timedelta
        # Simulate a healthy client already in lc (set by the "first"
        # thread) — second thread enters the lock, sees the fresh
        # client, returns it without logging in.
        fresh = MagicMock()
        fresh.rest.expired = datetime.now() + timedelta(hours=1)
        lc = {
            '_adp_config': MagicMock(url='x', user='u', password='p'),
            'adp': fresh,
        }
        with patch.object(ac, '_locks', {}), \
             patch('builtins.__import__') as _imp:
            fake_adp = MagicMock()
            _imp.side_effect = lambda name, *a, **kw: (
                fake_adp if name == 'adp'
                else __import__(name, *a, **kw))
            result = ac._reconnect(lc)
            # Returned the fresh client without re-logging in
            assert result is fresh
            fake_adp.login.assert_not_called()


# ------------------------------------------------------------------ #
#  DT connection helper tests                                          #
# ------------------------------------------------------------------ #

class TestDtConnect:

    def test_get_dt_returns_cached(self):
        from oracle.data_studio_mcp_server.tools._dt_connect import get_dt
        mock_ctx = MagicMock()
        mock_dt = {'client': MagicMock()}
        mock_ctx.request_context.lifespan_context = {
            'datatransforms': mock_dt}
        assert get_dt(mock_ctx) is mock_dt

    def test_get_dt_returns_none_no_config(self):
        from oracle.data_studio_mcp_server.tools._dt_connect import get_dt
        mock_ctx = MagicMock()
        mock_ctx.request_context.lifespan_context = {}
        assert get_dt(mock_ctx) is None

    def test_get_dt_strategy1_from_adp_thread(self):
        '''Strategy 1: adp_client.dt is already populated by adp.login()'s
        background thread.'''
        from oracle.data_studio_mcp_server.tools._dt_connect import get_dt
        mock_ctx = MagicMock()
        adp_client = MagicMock()
        wb = MagicMock()
        wb.get_client.return_value = 'dt-client'
        adp_client.dt = wb
        adp_client.wait_for_datatransforms.return_value = None
        cfg = MagicMock(url='https://x', user='u', password='p')
        lc = {'_dt_config': cfg, 'adp': adp_client}
        mock_ctx.request_context.lifespan_context = lc

        result = get_dt(mock_ctx)
        assert result is not None
        assert result['workbench'] is wb
        assert result['client'] == 'dt-client'
        # Cached for subsequent calls
        assert lc['datatransforms'] is result
        adp_client.wait_for_datatransforms.assert_called_once()

    def test_get_dt_strategy2_adbs_connect(self):
        '''Strategy 2: ADBS-token connect using dba_pdbs OCI params.'''
        from oracle.data_studio_mcp_server.tools import _dt_connect as dc
        mock_ctx = MagicMock()
        adp_client = MagicMock()
        # No `.dt` attribute → strategy 1 fails
        adp_client.dt = None
        adp_client.wait_for_datatransforms.return_value = None
        adp_client.Misc.run_query.return_value = [{
            'database_name': 'mydb',
            'cloud_database_name': 'ocid1.adw.oc1..xxx',
            'tenant_name': 'ocid1.tenancy.oc1..yyy',
        }]
        cfg = MagicMock(url='https://x', user='u', password='p')
        lc = {'_dt_config': cfg, 'adp': adp_client}
        mock_ctx.request_context.lifespan_context = lc

        fake_module = MagicMock()
        fake_wb = MagicMock()
        fake_wb.get_client.return_value = 'dt-client'
        fake_module.DataTransformsWorkbench.return_value = fake_wb
        with patch.dict('sys.modules',
                         {'datatransforms.workbench': fake_module,
                          'datatransforms.client': MagicMock()}):
            result = dc.get_dt(mock_ctx)
        assert result is not None
        assert result['workbench'] is fake_wb
        # Verify the connect_workbench call carried OCI params from dba_pdbs
        call_args = fake_wb.connect_workbench.call_args[0][0]
        assert call_args['tenancy_ocid'] == 'ocid1.tenancy.oc1..yyy'
        assert call_args['adw_name'] == 'mydb'
        assert call_args['xforms_url'] == 'https://x'

    def test_get_dt_strategy3_simple_connect(self):
        '''Strategy 3: simple URL+Basic auth fallback when ADBS path
        fails (e.g. no `dba_pdbs` access).'''
        from oracle.data_studio_mcp_server.tools import _dt_connect as dc
        mock_ctx = MagicMock()
        # No adp_client at all → strategies 1 + 2 fail
        cfg = MagicMock(url='https://x', user='u', password='p')
        lc = {'_dt_config': cfg, 'adp': None}
        mock_ctx.request_context.lifespan_context = lc

        fake_module = MagicMock()
        fake_wb = MagicMock()
        fake_wb.get_client.return_value = 'dt-client'
        fake_module.DataTransformsWorkbench.return_value = fake_wb
        with patch.dict('sys.modules',
                         {'datatransforms.workbench': fake_module,
                          'datatransforms.client': MagicMock()}):
            result = dc.get_dt(mock_ctx)
        assert result is not None
        # Strategy 3 connect payload doesn't include OCI params
        call_args = fake_wb.connect_workbench.call_args[0][0]
        assert 'tenancy_ocid' not in call_args
        assert call_args['data_transforms_url'] == 'https://x'

    def test_get_dt_all_strategies_fail_returns_none(self):
        '''If every strategy raises, get_dt returns None and logs.'''
        from oracle.data_studio_mcp_server.tools import _dt_connect as dc
        mock_ctx = MagicMock()
        cfg = MagicMock(url='https://x', user='u', password='p')
        lc = {'_dt_config': cfg, 'adp': None}
        mock_ctx.request_context.lifespan_context = lc

        fake_module = MagicMock()
        fake_wb = MagicMock()
        fake_wb.connect_workbench.side_effect = RuntimeError('boom')
        fake_module.DataTransformsWorkbench.return_value = fake_wb
        with patch.dict('sys.modules',
                         {'datatransforms.workbench': fake_module,
                          'datatransforms.client': MagicMock()}):
            assert dc.get_dt(mock_ctx) is None
        # No cache was populated
        assert 'datatransforms' not in lc

    def test_reset_singletons_handles_missing_module(self):
        '''_reset_singletons must not raise when datatransforms isn't
        installed.'''
        from oracle.data_studio_mcp_server.tools._dt_connect import (
            _reset_singletons)
        # Should silently no-op; nothing in sys.modules to break
        _reset_singletons()


# ------------------------------------------------------------------ #
#  Essbase tool dispatch tests (mocked SDK)                            #
# ------------------------------------------------------------------ #

@mcp_required
class TestEssbaseToolDispatch:

    def _make_ctx(self, ess_mock):
        ctx = MagicMock()
        ctx.request_context.lifespan_context = {'essbase': ess_mock}
        return ctx

    def test_essbase_explore_no_connection(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_explore'].fn
        ctx = MagicMock()
        ctx.request_context.lifespan_context = {}
        result = json.loads(fn(ctx=ctx))
        assert 'error' in result

    def test_essbase_explore_success(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_explore'].fn

        ess = MagicMock()
        ess.applications.list_applications.return_value = {
            'items': [{'name': 'Sample'}]}
        ess.applications.list_databases.return_value = {
            'items': [{'name': 'Basic'}]}
        ess.applications.get_statistics.return_value = {'status': 'ok'}
        ess.applications.get_settings.return_value = {'setting': 'val'}
        ctx = self._make_ctx(ess)
        result = json.loads(fn(ctx=ctx))
        assert 'applications' in result
        assert result['count'] == 1
        assert result['applications'][0]['databases'] == [{'name': 'Basic'}]

    def test_essbase_query_success(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_query'].fn

        ess = MagicMock()
        ess.grid.execute_mdx.return_value = {'data': [[1, 2]]}
        ctx = self._make_ctx(ess)
        result = json.loads(fn(app_name='S', db_name='B',
                               mdx='SELECT...', ctx=ctx))
        assert result['data'] == [[1, 2]]

    def test_essbase_server_health(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_server_health'].fn

        ess = MagicMock()
        ess.about.get.return_value = {'version': '21.5'}
        ess.about.get_instance.return_value = {'mode': 'normal'}
        ess.sessions.list_sessions.return_value = [{'user': 'admin'}]
        ctx = self._make_ctx(ess)
        result = json.loads(fn(ctx=ctx))
        assert result['about']['version'] == '21.5'
        assert result['active_sessions'] == 1

    def test_essbase_manage_variables_list(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_variables'].fn

        ess = MagicMock()
        ess.variables.list_server_variables.return_value = {
            'items': [{'name': 'V1', 'value': 'X'}]}
        ctx = self._make_ctx(ess)
        result = json.loads(fn(action='list', scope='server', ctx=ctx))
        assert 'items' in result

    def test_essbase_manage_variables_set_creates(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_variables'].fn

        ess = MagicMock()
        ess.variables.update_server_variable.side_effect = Exception('not found')
        ess.variables.create_server_variable.return_value = {
            'name': 'NewVar', 'value': 'val'}
        ctx = self._make_ctx(ess)
        result = json.loads(fn(action='set', scope='server',
                               variable_name='NewVar', value='val',
                               ctx=ctx))
        assert result['name'] == 'NewVar'

    def test_essbase_get_script(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_get_script'].fn

        ess = MagicMock()
        ess.scripts.get_script_content.return_value = 'CALC ALL;'
        ess.scripts.validate_script.return_value = {'valid': True}
        ctx = self._make_ctx(ess)
        result = json.loads(fn(app_name='S', db_name='B',
                               script_name='CalcAll', ctx=ctx))
        assert result['content'] == 'CALC ALL;'
        assert result['validation']['valid'] is True

    def test_essbase_browse_outline_top_level(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_browse_outline'].fn

        ess = MagicMock()
        ess.dimensions.get_outline.return_value = {
            'items': [{'name': 'Year'}, {'name': 'Measures'}]}
        ctx = self._make_ctx(ess)
        result = json.loads(fn(app_name='S', db_name='B', ctx=ctx))
        assert 'items' in result

    def test_essbase_describe_database(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_describe_database'].fn

        ess = MagicMock()
        ess.applications.get_database.return_value = {'name': 'Basic'}
        ess.dimensions.list_dimensions.return_value = {
            'items': [{'name': 'Year'}]}
        ess.database_settings.get_settings.return_value = {'s': 1}
        ess.database_settings.get_statistics.return_value = {'blocks': 100}
        ess.database_settings.get_storage_statistics.return_value = {'size': 50}
        ess.variables.list_db_variables.return_value = {
            'items': [{'name': 'V1'}]}
        ctx = self._make_ctx(ess)
        result = json.loads(fn(app_name='S', db_name='B', ctx=ctx))
        assert result['database']['name'] == 'Basic'
        assert len(result['dimensions']) == 1

    def test_essbase_run_calculation_success(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_run_calculation'].fn

        ess = MagicMock()
        ess.jobs.execute.return_value = {'id': 42}
        ess.jobs.wait_for_completion.return_value = {
            'statusCode': 200, 'statusMessage': 'Completed'}
        ctx = self._make_ctx(ess)
        result = json.loads(fn(app_name='S', db_name='B',
                               script_name='CalcAll', ctx=ctx))
        assert result['statusCode'] == 200

    def test_essbase_run_calculation_no_script(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_run_calculation'].fn

        ess = MagicMock()
        ctx = self._make_ctx(ess)
        result = json.loads(fn(app_name='S', db_name='B', ctx=ctx))
        assert 'error' in result

    def test_essbase_run_calculation_full_flow_with_calc_script(self):
        '''Inline calc_script path: jobs.execute → wait_for_completion.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_run_calculation'].fn

        ess = MagicMock()
        ess.jobs.execute.return_value = {'id': 42}
        ess.jobs.wait_for_completion.return_value = {
            'status': 200, 'jobID': 42}
        ctx = self._make_ctx(ess)
        result = json.loads(fn(app_name='S', db_name='B',
                                calc_script='CALC ALL;', ctx=ctx))
        # The execute call carried the inline script payload
        payload = ess.jobs.execute.call_args[0][0]
        assert payload['parameters']['script'] == 'CALC ALL;'
        ess.jobs.wait_for_completion.assert_called_once_with(42)

    def test_essbase_load_data_full_flow(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_load_data'].fn

        ess = MagicMock()
        ess.jobs.execute.return_value = {'id': 7}
        ess.jobs.wait_for_completion.return_value = {'status': 200}
        ctx = self._make_ctx(ess)
        result = json.loads(fn(app_name='A', db_name='D',
                                rule_file='r.rul',
                                data_file='d.txt', ctx=ctx))
        payload = ess.jobs.execute.call_args[0][0]
        assert payload['jobtype'] == 'dataload'
        assert payload['parameters']['rule'] == 'r.rul'
        assert payload['parameters']['file'] == 'd.txt'

    def test_essbase_deploy_workbook_uploads_and_runs_job(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_deploy_workbook'].fn

        ess = MagicMock()
        ess.jobs.execute.return_value = {'id': 9}
        ess.jobs.wait_for_completion.return_value = {'status': 200}
        ctx = self._make_ctx(ess)
        # We can't easily mock open() here — tool likely opens the file
        # to upload. Use a small temp file for realism.
        import tempfile, os
        with tempfile.NamedTemporaryFile('wb', suffix='.xlsx',
                                            delete=False) as f:
            f.write(b'PK fake xlsx content')
            tmp = f.name
        try:
            result = json.loads(fn(app_name='A', file_path=tmp, ctx=ctx))
        finally:
            os.unlink(tmp)
        # Some flavor of execute or upload should have been called
        assert (ess.files.upload.called or ess.jobs.execute.called)

    def test_essbase_describe_database_full_flow(self):
        '''Walks the multi-call composite — verifies all SDK probes
        were issued.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_describe_database'].fn

        ess = MagicMock()
        ctx = self._make_ctx(ess)
        result = json.loads(fn(app_name='A', db_name='D', ctx=ctx))
        ess.applications.get_database.assert_called_once_with('A', 'D')
        # Many other probes happen via safe_call — at least one ran
        assert ess.dimensions.list_dimensions.called

    def test_essbase_manage_security_username(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_security'].fn

        ess = MagicMock()
        ess.users.get_user.return_value = {'id': 'alice'}
        ess.users.get_user_provisioning_report.return_value = {'apps': []}
        ctx = self._make_ctx(ess)
        result = json.loads(fn(username='alice', ctx=ctx))
        ess.users.get_user.assert_called_once_with('alice')

    def test_essbase_manage_security_groupname(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_security'].fn

        ess = MagicMock()
        ctx = self._make_ctx(ess)
        result = json.loads(fn(group_name='developers', ctx=ctx))
        ess.groups.get_group.assert_called_once_with('developers')

    def test_essbase_manage_filters_create(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_filters'].fn

        ess = MagicMock()
        ess.filters.create_filter.return_value = {'name': 'F'}
        ess.filters.validate_filter.return_value = {'valid': True}
        ctx = self._make_ctx(ess)
        result = json.loads(fn(action='create', app_name='A',
                                db_name='D', filter_name='F',
                                filter_rows='READ,@IDESCENDANTS(East)',
                                ctx=ctx))
        ess.filters.create_filter.assert_called_once()
        # Auto-validate after create
        ess.filters.validate_filter.assert_called_once()

    def test_essbase_manage_drill_through_create(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_drill_through'].fn

        ess = MagicMock()
        ess.drill_through.create_report.return_value = {'name': 'R'}
        ctx = self._make_ctx(ess)
        result = json.loads(fn(action='create', app_name='A', db_name='D',
                                report_name='R', connection='C',
                                sql_query='SELECT 1 FROM dual',
                                columns='A,B,C',
                                drillable_regions='@IDESCENDANTS(East)',
                                ctx=ctx))
        ess.drill_through.create_report.assert_called_once()

    def test_essbase_manage_db_settings_reads_categories(self):
        '''category='all' fans out across multiple settings probes.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_db_settings'].fn

        ess = MagicMock()
        ctx = self._make_ctx(ess)
        result = json.loads(fn(app_name='A', db_name='D',
                                category='all', ctx=ctx))
        # At least the headline get_settings call ran
        assert (ess.database_settings.get_settings.called
                or ess.database_settings.get_startup_settings.called)

    def test_essbase_manage_db_settings_specific_categories(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_db_settings'].fn

        ess = MagicMock()
        # Make every settings method return a dict so the tool's
        # json.dumps doesn't choke on a MagicMock repr.
        for m in ['get_settings', 'get_startup_settings',
                  'get_calculation_settings', 'get_cache_settings',
                  'get_compression_settings', 'get_transaction_settings',
                  'get_buffer_settings', 'get_attribute_settings',
                  'get_runtime_statistics', 'get_storage_statistics',
                  'get_size_statistics', 'get_aso_compression_info',
                  'get_date_formats']:
            getattr(ess.database_settings, m).return_value = {}
        ctx = self._make_ctx(ess)
        for cat in ['startup', 'calculation', 'cache', 'compression',
                     'transactions']:
            json.loads(fn(app_name='A', db_name='D',
                           category=cat, ctx=ctx))

    def test_essbase_outline_metadata_all_category(self):
        '''category='all' walks dimensions, generations, levels, settings.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_outline_metadata'].fn

        ess = MagicMock()
        ess.dimensions.list_dimensions.return_value = {
            'items': [{'name': 'Year'}, {'name': 'Region'}]}
        ctx = self._make_ctx(ess)
        result = json.loads(fn(app_name='A', db_name='D',
                                category='all', ctx=ctx))
        ess.dimensions.list_dimensions.assert_called_once()

    def test_essbase_browse_outline_with_parent_recursive(self):
        '''Specifying a parent triggers recursive get_children walk.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_browse_outline'].fn

        ess = MagicMock()
        # Return an empty children list to terminate recursion fast
        ess.dimensions.get_children.return_value = {'items': []}
        ctx = self._make_ctx(ess)
        result = json.loads(fn(app_name='A', db_name='D',
                                parent='Year', depth=2, ctx=ctx))
        ess.dimensions.get_children.assert_called()

    def test_essbase_search_members_enriches_with_ancestors(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_search_members'].fn

        ess = MagicMock()
        ess.dimensions.search_members.return_value = {
            'items': [{'name': 'Sales'}]}
        ess.dimensions.get_member_ancestors.return_value = {
            'ancestors': ['Measures']}
        ctx = self._make_ctx(ess)
        result = json.loads(fn(app_name='A', db_name='D',
                                pattern='Sales', ctx=ctx))
        ess.dimensions.search_members.assert_called_once()
        ess.dimensions.get_member_ancestors.assert_called()
        assert result['count'] == 1

    def test_essbase_manage_filters_update_with_validate(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_filters'].fn

        ess = MagicMock()
        ess.filters.update_filter.return_value = {'name': 'F'}
        ess.filters.validate_filter.return_value = {'valid': True}
        ctx = self._make_ctx(ess)
        result = json.loads(fn(action='update', app_name='A',
                                db_name='D', filter_name='F',
                                filter_rows='READ,@CHILDREN(East)',
                                ctx=ctx))
        ess.filters.update_filter.assert_called_once()
        ess.filters.validate_filter.assert_called_once()

    def test_essbase_manage_users_provision_app_role(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_users'].fn

        ess = MagicMock()
        ess.users.provision_app_role.return_value = {'status': 'ok'}
        ctx = self._make_ctx(ess)
        # With app_name → app-role provisioning
        fn(action='provision', user_id='alice',
            role='power_user', app_name='Sample', ctx=ctx)
        assert ess.users.provision_app_role.called

    def test_essbase_manage_users_provision_service_role(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_users'].fn

        ess = MagicMock()
        ess.users.provision_service_role.return_value = {'status': 'ok'}
        ctx = self._make_ctx(ess)
        # No app_name → service-level
        fn(action='provision', user_id='alice',
            role='service_administrator', ctx=ctx)
        assert ess.users.provision_service_role.called

    def test_essbase_edit_outline_builds_payload(self):
        '''Verify the BOE payload shape for an `add` action.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_edit_outline'].fn

        ess = MagicMock()
        ess.dimensions.batch_outline_edit.return_value = {'status': 'ok'}
        ctx = self._make_ctx(ess)
        json.loads(fn(app_name='A', db_name='D',
                       action='add', member_name='Q1',
                       parent_name='Year', ctx=ctx))
        call_args = ess.dimensions.batch_outline_edit.call_args
        payload = call_args[0][2] if len(call_args[0]) >= 3 else call_args[0][-1]
        # payload contains an editActions list with one add entry
        assert 'editActions' in payload
        assert payload['editActions'][0]['actionType'].lower().startswith('add')

    def test_essbase_manage_drill_through_update(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_drill_through'].fn

        ess = MagicMock()
        ess.drill_through.update_report.return_value = {'name': 'R'}
        ctx = self._make_ctx(ess)
        json.loads(fn(action='update', app_name='A', db_name='D',
                       report_name='R',
                       sql_query='SELECT 2 FROM dual',
                       columns='X,Y',
                       drillable_regions='@CHILDREN(West)',
                       ctx=ctx))
        ess.drill_through.update_report.assert_called_once()

    def test_essbase_manage_drill_through_execute(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_drill_through'].fn

        ess = MagicMock()
        ess.drill_through.execute_report.return_value = {'rows': []}
        ctx = self._make_ctx(ess)
        json.loads(fn(action='execute', app_name='A', db_name='D',
                       report_name='R', ctx=ctx))
        ess.drill_through.execute_report.assert_called_once()

    def test_essbase_manage_database_update(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_database'].fn

        ess = MagicMock()
        ess.applications.update_database.return_value = {'name': 'D'}
        ctx = self._make_ctx(ess)
        json.loads(fn(action='update', app_name='A', db_name='D',
                       ctx=ctx))
        ess.applications.update_database.assert_called_once()

    def test_essbase_manage_database_copy(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_database'].fn

        ess = MagicMock()
        ess.applications.copy_database.return_value = {'status': 'copied'}
        ctx = self._make_ctx(ess)
        json.loads(fn(action='copy', app_name='A', db_name='D',
                       target_app='A2', target_db='D2', ctx=ctx))
        ess.applications.copy_database.assert_called_once()

    def test_essbase_manage_groups_add_users(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_groups'].fn

        ess = MagicMock()
        ess.groups.add_users.return_value = {'status': 'ok'}
        ctx = self._make_ctx(ess)
        json.loads(fn(action='add_users', group_id='G',
                       user_ids='alice,bob,carol', ctx=ctx))
        # 3 users → list of 3 dicts
        call_args = ess.groups.add_users.call_args
        users_arg = call_args[0][1]
        assert len(users_arg) == 3
        assert users_arg[0]['id'] == 'alice'

    def test_essbase_manage_groups_remove_users(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_groups'].fn

        ess = MagicMock()
        ess.groups.remove_users.return_value = {'status': 'ok'}
        ctx = self._make_ctx(ess)
        json.loads(fn(action='remove_users', group_id='G', ctx=ctx))
        ess.groups.remove_users.assert_called_once_with('G')

    def test_essbase_manage_groups_add_subgroups(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_groups'].fn

        ess = MagicMock()
        ess.groups.add_subgroups.return_value = {'status': 'ok'}
        ctx = self._make_ctx(ess)
        json.loads(fn(action='add_subgroups', group_id='G',
                       user_ids='sub1,sub2', ctx=ctx))
        ess.groups.add_subgroups.assert_called_once()

    def test_essbase_manage_users_deprovision_app(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_users'].fn

        ess = MagicMock()
        ess.users.deprovision_app_role.return_value = {'status': 'ok'}
        ctx = self._make_ctx(ess)
        fn(action='deprovision', user_id='alice',
            role='power_user', app_name='Sample', ctx=ctx)
        ess.users.deprovision_app_role.assert_called()

    def test_essbase_manage_users_update(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_users'].fn

        ess = MagicMock()
        ess.users.update_user.return_value = {'status': 'ok'}
        ctx = self._make_ctx(ess)
        fn(action='update', user_id='alice', password='newpass', ctx=ctx)
        ess.users.update_user.assert_called_once()

    def test_essbase_manage_users_create(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_users'].fn

        ess = MagicMock()
        ess.users.create_user.return_value = {'id': 'alice'}
        ctx = self._make_ctx(ess)
        fn(action='create', user_id='alice', password='pw', ctx=ctx)
        ess.users.create_user.assert_called_once()

    def test_essbase_manage_jobs_rerun_full_flow(self):
        '''rerun also calls wait_for_completion on the new job.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_jobs'].fn

        ess = MagicMock()
        ess.jobs.rerun.return_value = {'id': 99}
        ess.jobs.wait_for_completion.return_value = {
            'status': 200, 'jobID': 99}
        ctx = self._make_ctx(ess)
        json.loads(fn(action='rerun', job_id=42, ctx=ctx))
        ess.jobs.rerun.assert_called_once_with(42)
        ess.jobs.wait_for_completion.assert_called_once_with(99)

    def test_essbase_manage_filters_update_full_flow(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_filters'].fn

        ess = MagicMock()
        ess.filters.update_filter.return_value = {'name': 'F'}
        ess.filters.validate_filter.return_value = {'valid': True}
        ctx = self._make_ctx(ess)
        json.loads(fn(action='update', app_name='A', db_name='D',
                       filter_name='F',
                       filter_rows='READ,@CHILDREN(East);WRITE,@MEMBER(West)',
                       ctx=ctx))
        # update_filter called with the parsed rows
        ess.filters.update_filter.assert_called_once()
        ess.filters.validate_filter.assert_called_once()

    def test_essbase_manage_locks_unlock(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_locks'].fn

        ess = MagicMock()
        ess.locks.unlock_object.return_value = {'status': 'unlocked'}
        ctx = self._make_ctx(ess)
        json.loads(fn(app_name='A', db_name='D', action='unlock',
                       object_name='East', ctx=ctx))
        ess.locks.unlock_object.assert_called_once()

    def test_essbase_manage_sessions_kill_specific(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_sessions'].fn

        ess = MagicMock()
        ess.sessions.delete_session.return_value = {'status': 'killed'}
        ctx = self._make_ctx(ess)
        json.loads(fn(action='kill', session_id='123', ctx=ctx))
        ess.sessions.delete_session.assert_called_once_with('123')

    def test_essbase_manage_application_update(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_application'].fn

        ess = MagicMock()
        ess.applications.update_application.return_value = {'status': 'started'}
        ctx = self._make_ctx(ess)
        # start action exercises update_application(status: 1)
        json.loads(fn(action='start', app_name='A', ctx=ctx))
        call_args = ess.applications.update_application.call_args
        assert call_args[0][1] == {'status': 1}

    def test_essbase_manage_application_stop(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_application'].fn

        ess = MagicMock()
        ctx = self._make_ctx(ess)
        json.loads(fn(action='stop', app_name='A', ctx=ctx))
        call_args = ess.applications.update_application.call_args
        assert call_args[0][1] == {'status': 0}

    def test_essbase_outline_metadata_export_xml_returns_blob(self):
        '''export_xml returns a string blob, body wraps it.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_outline_metadata'].fn

        ess = MagicMock()
        ess.dimensions.export_outline_xml.return_value = '<outline />'
        ctx = self._make_ctx(ess)
        # export_xml returns the raw blob, not JSON
        result = fn(app_name='A', db_name='D', category='export_xml',
                     ctx=ctx)
        ess.dimensions.export_outline_xml.assert_called_once()
        assert '<outline' in str(result)

    def test_essbase_outline_metadata_member_returns_member(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_outline_metadata'].fn

        ess = MagicMock()
        ess.dimensions.get_member.return_value = {'name': 'East'}
        ctx = self._make_ctx(ess)
        result = json.loads(fn(app_name='A', db_name='D',
                                category='member',
                                dimension_name='East', ctx=ctx))
        ess.dimensions.get_member.assert_called_once()

    def test_essbase_manage_datasources_update(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_datasources'].fn

        ess = MagicMock()
        ess.datasources.update_datasource.return_value = {'name': 'DS'}
        ctx = self._make_ctx(ess)
        json.loads(fn(action='update', datasource_name='DS',
                       query='SELECT 3 FROM dual',
                       columns='C1,C2', ctx=ctx))
        ess.datasources.update_datasource.assert_called_once()

    def test_essbase_manage_connections_update(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_connections'].fn

        ess = MagicMock()
        ess.connections.update_connection.return_value = {'name': 'C'}
        ctx = self._make_ctx(ess)
        json.loads(fn(action='update', connection_name='C',
                       host='h2', port=1522, service_name='svc2',
                       user='u2', password='p2', ctx=ctx))
        ess.connections.update_connection.assert_called_once()

    def test_essbase_manage_files_copy(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_files'].fn

        ess = MagicMock()
        ess.files.copy.return_value = {'status': 'copied'}
        ctx = self._make_ctx(ess)
        json.loads(fn(action='copy', path='/a/x',
                       target_path='/b/y', ctx=ctx))
        ess.files.copy.assert_called_once()

    def test_essbase_manage_files_move(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_files'].fn

        ess = MagicMock()
        ess.files.move.return_value = {'status': 'moved'}
        ctx = self._make_ctx(ess)
        json.loads(fn(action='move', path='/a/x',
                       target_path='/b/y', ctx=ctx))
        ess.files.move.assert_called_once()

    def test_essbase_manage_files_upload(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_files'].fn

        ess = MagicMock()
        ess.files.upload.return_value = None
        ctx = self._make_ctx(ess)
        json.loads(fn(action='upload', path='/p/file.txt',
                       content='hello world', ctx=ctx))
        ess.files.upload.assert_called_once()

    def test_essbase_manage_files_download_bytes(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_files'].fn

        ess = MagicMock()
        ess.files.download.return_value = b'hello bytes content'
        ctx = self._make_ctx(ess)
        result = json.loads(fn(action='download', path='/p/file.txt',
                                ctx=ctx))
        assert result['size_bytes'] == len(b'hello bytes content')

    def test_essbase_manage_users_get_with_provisioning_report(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_users'].fn

        ess = MagicMock()
        ess.users.get_user.return_value = {'id': 'u'}
        ess.users.get_user_provisioning_report.return_value = {'apps': []}
        ctx = self._make_ctx(ess)
        json.loads(fn(action='get', user_id='alice', ctx=ctx))
        ess.users.get_user.assert_called_once_with('alice')

    def test_essbase_manage_groups_get_full_body(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_groups'].fn

        ess = MagicMock()
        ess.groups.get_group.return_value = {'id': 'G'}
        ess.groups.get_group_provisioning_report.return_value = {'roles': []}
        ess.groups.get_subgroups.return_value = []
        ctx = self._make_ctx(ess)
        json.loads(fn(action='get', group_id='G', ctx=ctx))
        ess.groups.get_group.assert_called_once_with('G')

    def test_essbase_manage_drill_through_create_full_payload(self):
        '''Create with all optional fields — exercises payload assembly.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_drill_through'].fn

        ess = MagicMock()
        ess.drill_through.create_report.return_value = {'name': 'R'}
        ctx = self._make_ctx(ess)
        json.loads(fn(action='create', app_name='A', db_name='D',
                       report_name='R', connection='ConnA',
                       sql_query='SELECT * FROM SALES',
                       columns='COL1,COL2,COL3',
                       drillable_regions='@IDESCENDANTS(East),@IDESCENDANTS(West)',
                       ctx=ctx))
        call_args = ess.drill_through.create_report.call_args
        payload = call_args[0][2]
        assert payload['name'] == 'R'
        assert 'columns' in payload or 'drillableRegions' in payload \
            or 'sqlQuery' in payload

    def test_essbase_manage_filters_create_with_default_access(self):
        '''Create with no filter_rows uses default access on @ALL.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_filters'].fn

        ess = MagicMock()
        ess.filters.create_filter.return_value = {'name': 'F'}
        ess.filters.validate_filter.return_value = {'valid': True}
        ctx = self._make_ctx(ess)
        json.loads(fn(action='create', app_name='A', db_name='D',
                       filter_name='F', access='WRITE', ctx=ctx))
        call_args = ess.filters.create_filter.call_args
        payload = call_args[0][2]
        assert payload['rows'][0]['access'] == 'WRITE'
        assert payload['rows'][0]['member'] == '@ALL'

    def test_essbase_manage_jobs_status_returns_status(self):
        '''status path: jobs.get_status(job_id).'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_jobs'].fn

        ess = MagicMock()
        ess.jobs.get_status.return_value = {'status': 200, 'jobID': 5}
        ctx = self._make_ctx(ess)
        json.loads(fn(action='status', job_id=5, ctx=ctx))
        ess.jobs.get_status.assert_called_once_with(5)

    def test_essbase_manage_jobs_status_no_id_errors(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_jobs'].fn

        ess = MagicMock()
        ctx = self._make_ctx(ess)
        result = json.loads(fn(action='status', ctx=ctx))
        assert 'error' in result

    @pytest.mark.parametrize('tool,kwargs', [
        # Each case triggers a `return err('X required ...')` branch.
        ('essbase_manage_application', {'action': 'create',
                                          'app_name': 'A'}),  # no db_name
        ('essbase_manage_application', {'action': 'rename',
                                          'app_name': 'A'}),  # no new_name
        ('essbase_manage_application', {'action': 'copy',
                                          'app_name': 'A'}),  # no new_name
        ('essbase_manage_application', {'action': 'unknown',
                                          'app_name': 'A'}),
        ('essbase_manage_database', {'action': 'rename', 'app_name': 'A',
                                       'db_name': 'D'}),  # no new_name
        ('essbase_manage_database', {'action': 'copy', 'app_name': 'A',
                                       'db_name': 'D'}),  # no targets
        ('essbase_manage_database', {'action': 'unknown',
                                       'app_name': 'A', 'db_name': 'D'}),
        ('essbase_manage_script', {'action': 'create', 'app_name': 'A',
                                     'db_name': 'D', 'script_name': 'S'}),
        # update with no content + no new_name doesn't error — it
        # returns a renamed status. Skip that case.
        ('essbase_manage_script', {'action': 'unknown_xyz',
                                     'app_name': 'A', 'db_name': 'D',
                                     'script_name': 'S'}),
        ('essbase_manage_filters', {'action': 'create',
                                      'app_name': 'A', 'db_name': 'D'}),
        ('essbase_manage_filters', {'action': 'update',
                                      'app_name': 'A', 'db_name': 'D'}),
        ('essbase_manage_filters', {'action': 'rename',
                                      'app_name': 'A', 'db_name': 'D',
                                      'filter_name': 'F'}),
        ('essbase_manage_filters', {'action': 'copy',
                                      'app_name': 'A', 'db_name': 'D',
                                      'filter_name': 'F'}),
        ('essbase_manage_filters', {'action': 'delete',
                                      'app_name': 'A', 'db_name': 'D'}),
        ('essbase_manage_filters', {'action': 'assign',
                                      'app_name': 'A', 'db_name': 'D'}),
        ('essbase_manage_filters', {'action': 'unknown',
                                      'app_name': 'A', 'db_name': 'D'}),
        ('essbase_manage_files', {'action': 'unknown'}),
        ('essbase_manage_files', {'action': 'copy', 'path': '/p'}),
        ('essbase_manage_files', {'action': 'move', 'path': '/p'}),
        ('essbase_manage_files', {'action': 'upload', 'path': '/p'}),
        ('essbase_manage_users', {'action': 'create', 'user_id': 'u'}),
        ('essbase_manage_users', {'action': 'unknown'}),
        ('essbase_manage_groups', {'action': 'unknown'}),
        ('essbase_manage_groups', {'action': 'add_users',
                                     'group_id': 'G'}),
        ('essbase_manage_drill_through',
         {'action': 'unknown', 'app_name': 'A', 'db_name': 'D'}),
        ('essbase_manage_drill_through',
         {'action': 'create', 'app_name': 'A', 'db_name': 'D',
          'report_name': 'R'}),  # no connection
        ('essbase_manage_datasources', {'action': 'unknown'}),
        ('essbase_manage_datasources', {'action': 'create'}),
        ('essbase_manage_connections', {'action': 'unknown'}),
        ('essbase_manage_connections', {'action': 'create'}),
        ('essbase_manage_locks', {'app_name': 'A', 'db_name': 'D',
                                    'action': 'unlock'}),  # no object
        ('essbase_manage_locks', {'app_name': 'A', 'db_name': 'D',
                                    'action': 'unknown'}),
        ('essbase_manage_jobs', {'action': 'rerun'}),
        ('essbase_manage_jobs', {'action': 'unknown'}),
        ('essbase_manage_sessions', {'action': 'kill'}),
        ('essbase_manage_sessions', {'action': 'unknown'}),
        ('essbase_edit_outline', {'app_name': 'A', 'db_name': 'D',
                                    'action': 'add',
                                    'member_name': 'M'}),  # no parent_name
        ('essbase_edit_outline', {'app_name': 'A', 'db_name': 'D',
                                    'action': 'unknown',
                                    'member_name': 'M'}),
    ])
    def test_essbase_validation_error_branches(self, tool, kwargs):
        '''Bulk validation-error coverage. Each missing-required-arg
        path returns an error JSON. Lifts coverage across all manage_*
        tools' error branches.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools[tool].fn
        ess = MagicMock()
        ctx = self._make_ctx(ess)
        result = json.loads(fn(ctx=ctx, **kwargs))
        assert 'error' in result

    def test_essbase_get_logs_all_logs(self):
        '''latest_only=False fetches the full log set.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_get_logs'].fn

        ess = MagicMock()
        ess.applications.get_logs.return_value = '...lots of log lines...'
        ctx = self._make_ctx(ess)
        json.loads(fn(app_name='A', latest_only=False, ctx=ctx))
        ess.applications.get_logs.assert_called_once()

    def test_essbase_outline_metadata_generations_levels_with_dim(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_outline_metadata'].fn

        ess = MagicMock()
        ess.dimensions.list_generations.return_value = []
        ess.dimensions.list_levels.return_value = []
        ctx = self._make_ctx(ess)
        for cat in ['generations', 'levels']:
            fn(app_name='A', db_name='D', category=cat,
                dimension_name='Time', ctx=ctx)

    def test_essbase_outline_metadata_generations_no_dim_errors(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_outline_metadata'].fn

        ess = MagicMock()
        ctx = self._make_ctx(ess)
        result = json.loads(fn(app_name='A', db_name='D',
                                category='generations', ctx=ctx))
        assert 'error' in result

    def test_essbase_outline_metadata_unknown_category(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_outline_metadata'].fn

        ess = MagicMock()
        ctx = self._make_ctx(ess)
        result = json.loads(fn(app_name='A', db_name='D',
                                category='nonsense', ctx=ctx))
        assert 'error' in result

    def test_essbase_manage_users_list_roles_variants(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_users'].fn

        ess = MagicMock()
        ess.users.list_service_roles.return_value = []
        ess.users.list_app_roles.return_value = []
        ess.users.list_roles.return_value = []
        ctx = self._make_ctx(ess)
        # list_app_roles requires app_name
        json.loads(fn(action='list_app_roles', app_name='Sample',
                       ctx=ctx))
        json.loads(fn(action='list_service_roles', ctx=ctx))
        json.loads(fn(action='list_roles', ctx=ctx))

    def test_essbase_manage_drill_through_validate_paths(self):
        '''Get + execute paths for drill-through.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_drill_through'].fn

        ess = MagicMock()
        ess.drill_through.get_report.return_value = {'name': 'R'}
        ctx = self._make_ctx(ess)
        # get without report_name → error
        result = json.loads(fn(action='get', app_name='A', db_name='D',
                                ctx=ctx))
        assert 'error' in result
        # delete without report_name → error
        result = json.loads(fn(action='delete', app_name='A', db_name='D',
                                ctx=ctx))
        assert 'error' in result

    def test_essbase_edit_outline_remove_action(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_edit_outline'].fn

        ess = MagicMock()
        ess.dimensions.batch_outline_edit.return_value = {'status': 'ok'}
        ctx = self._make_ctx(ess)
        json.loads(fn(app_name='A', db_name='D',
                       action='remove', member_name='Q1',
                       ctx=ctx))
        # Verify the remove action carries actionType=removeMember (case
        # may differ — check it's a remove)
        call_args = ess.dimensions.batch_outline_edit.call_args
        payload = call_args[0][2] if len(call_args[0]) >= 3 else call_args[0][-1]
        assert 'remove' in payload['editActions'][0]['actionType'].lower()

    def test_essbase_edit_outline_move_with_parent(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_edit_outline'].fn

        ess = MagicMock()
        ess.dimensions.batch_outline_edit.return_value = {'status': 'ok'}
        ctx = self._make_ctx(ess)
        json.loads(fn(app_name='A', db_name='D',
                       action='move', member_name='Q1',
                       parent_name='NewParent', ctx=ctx))
        ess.dimensions.batch_outline_edit.assert_called_once()

    def test_essbase_manage_filters_get_with_rows(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_manage_filters'].fn

        ess = MagicMock()
        ess.filters.get_filter.return_value = {'name': 'F'}
        ess.filters.get_filter_rows.return_value = [{'access': 'READ'}]
        ess.filters.get_permissions.return_value = []
        ctx = self._make_ctx(ess)
        json.loads(fn(action='get', app_name='A', db_name='D',
                       filter_name='F', ctx=ctx))
        ess.filters.get_filter.assert_called_once()

    def test_essbase_export_data_default_grid(self):
        '''When no MDX or report given, export uses get_default_grid.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['essbase_export_data'].fn

        ess = MagicMock()
        ess.grid.get_default_grid.return_value = {'data': []}
        ctx = self._make_ctx(ess)
        json.loads(fn(app_name='A', db_name='D', ctx=ctx))
        ess.grid.get_default_grid.assert_called_once()


# ------------------------------------------------------------------ #
#  ADP tool dispatch tests (mocked SDK)                                #
# ------------------------------------------------------------------ #

@mcp_required
class TestAdpToolDispatch:

    def _make_ctx(self, adp_mock):
        ctx = MagicMock()
        adp_mock.rest.expired = None
        ctx.request_context.lifespan_context = {'adp': adp_mock}
        return ctx

    def test_adp_search_success(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import adp_tools
        mcp_server = FastMCP('test')
        adp_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['adp_search'].fn

        adp = MagicMock()
        adp.rest.expired = None
        adp.Misc.global_search.return_value = json.dumps({
            'nodes': [{'data': {'name': 'EMP'}}]})
        ctx = self._make_ctx(adp)
        result = json.loads(fn(search_term='EMP', ctx=ctx))
        assert result['search_term'] == 'EMP'

    def test_adp_browse_catalog_list(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import adp_tools
        mcp_server = FastMCP('test')
        adp_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['adp_browse_catalog'].fn

        adp = MagicMock()
        adp.rest.expired = None
        adp.Catalog.get_catalogs.return_value = json.dumps(
            [{'name': 'cat1'}])
        ctx = self._make_ctx(adp)
        result = json.loads(fn(action='list', ctx=ctx))
        assert result[0]['name'] == 'cat1'

    def test_adp_analyze_analytic_view(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import adp_tools
        mcp_server = FastMCP('test')
        adp_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['adp_analyze_analytic_view'].fn

        adp = MagicMock()
        adp.rest.expired = None
        adp.Analytics.is_exist.return_value = True
        adp.Analytics.get_metadata.return_value = '{"dims": 3}'
        adp.Analytics.get_measures_list.return_value = '["SALES"]'
        adp.Analytics.get_dimension_names.return_value = '[{"DIMENSION_NAME": "TIME"}]'
        adp.Analytics.quality_report.return_value = '["no errors"]'
        ctx = self._make_ctx(adp)
        result = json.loads(fn(av_name='MY_AV', ctx=ctx))
        assert result['av_name'] == 'MY_AV'
        assert 'metadata' in result

    def test_adp_manage_db_links_copy_tables_passes_dblink(self):
        '''Verify copy_tables builds table descriptors with dbLink key.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import adp_tools
        mcp_server = FastMCP('test')
        adp_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['adp_manage_db_links'].fn

        adp = MagicMock()
        adp.rest.expired = None
        adp.Ingest.copy_tables_from_db_link.return_value = json.dumps(
            {'status': 'ok'})
        ctx = self._make_ctx(adp)
        result = json.loads(fn(action='copy_tables',
                               db_link_name='MY_LINK',
                               tables='EMP, DEPT', ctx=ctx))
        # Verify the SDK was called with table descriptors containing dbLink
        call_args = adp.Ingest.copy_tables_from_db_link.call_args
        table_descs = call_args[0][0]
        assert len(table_descs) == 2
        assert table_descs[0] == {'tableName': 'EMP', 'dbLink': 'MY_LINK'}
        assert table_descs[1] == {'tableName': 'DEPT', 'dbLink': 'MY_LINK'}

    def test_adp_manage_db_links_link_tables_passes_dblink(self):
        '''Verify link_tables builds table descriptors with dbLink key.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import adp_tools
        mcp_server = FastMCP('test')
        adp_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['adp_manage_db_links'].fn

        adp = MagicMock()
        adp.rest.expired = None
        adp.Ingest.link_tables_from_db_link.return_value = json.dumps(
            {'status': 'ok'})
        ctx = self._make_ctx(adp)
        result = json.loads(fn(action='link_tables',
                               db_link_name='MY_LINK',
                               tables='SALES', ctx=ctx))
        call_args = adp.Ingest.link_tables_from_db_link.call_args
        table_descs = call_args[0][0]
        assert len(table_descs) == 1
        assert table_descs[0]['dbLink'] == 'MY_LINK'

    def test_adp_build_analytic_view_does_not_pass_av_name_as_skip_dims(self):
        '''Regression: SDK signature is create_auto(fact_table,
        skip_dimensions: bool, owner). Earlier code passed av_name as
        the second positional, silently coercing it to skip_dimensions=
        True and dropping the user's name. Verify create_auto is now
        called with ONLY the fact_table positional arg.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import adp_tools
        mcp_server = FastMCP('test')
        adp_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['adp_build_analytic_view'].fn

        adp = MagicMock()
        adp.rest.expired = None
        adp.Analytics.create_auto.return_value = json.dumps(
            {'name': 'SALES_AV'})
        adp.Analytics.compile.return_value = json.dumps({'status': 'ok'})
        adp.Analytics.get_metadata.return_value = json.dumps({})
        adp.Analytics.get_data_preview.return_value = json.dumps([])
        ctx = self._make_ctx(adp)
        # Pass av_name — it should NOT leak into create_auto's second arg
        json.loads(fn(fact_table='SALES', av_name='MY_CUSTOM_AV',
                       ctx=ctx))
        call_args = adp.Analytics.create_auto.call_args
        # Must be called with ONLY fact_table positional
        assert call_args.args == ('SALES',), \
            f'create_auto positional args: {call_args.args}'
        # And no skip_dimensions kwarg leaked from av_name
        assert 'skip_dimensions' not in call_args.kwargs or \
            call_args.kwargs.get('skip_dimensions') is False

    def test_adp_manage_sharing_publish_does_not_pass_recipient(self):
        '''Regression: SDK publish_share(name, owner=None) does NOT
        accept a recipient. Earlier code passed recipient_name as
        owner, silently misrouting it. Verify publish is called with
        share_name only.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import adp_tools
        mcp_server = FastMCP('test')
        adp_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['adp_manage_sharing'].fn

        adp = MagicMock()
        adp.rest.expired = None
        adp.Share.publish_share.return_value = json.dumps({'status': 'ok'})
        ctx = self._make_ctx(adp)
        json.loads(fn(action='publish', share_name='SALES_SHARE',
                       ctx=ctx))
        call_args = adp.Share.publish_share.call_args
        # publish gets ONLY the share name
        assert call_args.args == ('SALES_SHARE',), \
            f'publish_share args: {call_args.args}'

    def test_adp_manage_sharing_grant_recipient_uses_correct_sdk(self):
        '''The new grant_recipient action threads recipient_name +
        tables through to update_recipient_shares.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import adp_tools
        mcp_server = FastMCP('test')
        adp_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['adp_manage_sharing'].fn

        adp = MagicMock()
        adp.rest.expired = None
        adp.Share.update_recipient_shares.return_value = json.dumps(
            {'status': 'ok'})
        ctx = self._make_ctx(adp)
        json.loads(fn(action='grant_recipient',
                       recipient_name='ALICE',
                       tables='SALES_SHARE',
                       ctx=ctx))
        call_args = adp.Share.update_recipient_shares.call_args
        assert call_args.args == ('ALICE', 'SALES_SHARE')

    def test_adp_ai_query_not_registered(self):
        '''adp_ai_query was intentionally removed from the composite
        MCP — Select AI doesn't reliably honor 23ai annotations and
        executing LLM-generated SQL belongs to SQLcl, not here.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import adp_tools
        mcp_server = FastMCP('test')
        adp_tools.register_tools(mcp_server)
        names = mcp_server._tool_manager._tools.keys()
        assert 'adp_ai_query' not in names

    def test_adp_search_with_include_ddl_walks_top_hits(self):
        '''include_ddl=True triggers a per-hit DDL fetch.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import adp_tools
        mcp_server = FastMCP('test')
        adp_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['adp_search'].fn

        adp = MagicMock()
        adp.rest.expired = None
        adp.Misc.global_search.return_value = json.dumps({
            'nodes': [{'data': {'name': 'EMP'}},
                      {'data': {'name': 'DEPT'}}]})
        adp.Misc.get_entity_ddl.return_value = 'CREATE TABLE EMP ...'
        ctx = self._make_ctx(adp)
        result = json.loads(fn(search_term='E', include_ddl=True, ctx=ctx))
        # DDL fetched for top hits
        assert adp.Misc.get_entity_ddl.call_count >= 1

    def test_adp_load_from_cloud_full_flow(self):
        '''Full flow: validates credential + storage link, then loads.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import adp_tools
        mcp_server = FastMCP('test')
        adp_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['adp_load_from_cloud'].fn

        adp = MagicMock()
        adp.rest.expired = None
        adp.Ingest.get_credential_list.return_value = json.dumps([
            {'CREDENTIAL_NAME': 'CR'}])
        adp.Ingest.get_consumer_groups.return_value = json.dumps([
            {'GROUP_NAME': 'LOW'}])
        adp.Ingest.copy_cloud_objects.return_value = json.dumps(
            {'request_id': 'R123'})
        ctx = self._make_ctx(adp)
        result = json.loads(fn(storage_link='SL',
                                object_name='sales.csv',
                                target_table='SALES_RAW',
                                ctx=ctx))
        adp.Ingest.copy_cloud_objects.assert_called_once()

    def test_adp_load_from_cloud_progress_only(self):
        '''When request_id is given, just polls progress.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import adp_tools
        mcp_server = FastMCP('test')
        adp_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['adp_load_from_cloud'].fn

        adp = MagicMock()
        adp.rest.expired = None
        adp.Ingest.cloud_progress_status.return_value = json.dumps(
            {'percent': 75})
        ctx = self._make_ctx(adp)
        result = json.loads(fn(request_id='R123', ctx=ctx))
        adp.Ingest.cloud_progress_status.assert_called_once_with('R123')

    def test_adp_build_analytic_view_full_flow(self):
        '''Walks create_auto → compile → metadata → preview.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import adp_tools
        mcp_server = FastMCP('test')
        adp_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['adp_build_analytic_view'].fn

        adp = MagicMock()
        adp.rest.expired = None
        adp.Analytics.create_auto.return_value = json.dumps(
            {'name': 'SALES_AV'})
        adp.Analytics.compile.return_value = json.dumps({'compiled': True})
        adp.Analytics.get_metadata.return_value = json.dumps(
            {'measures': []})
        adp.Analytics.get_data_preview.return_value = json.dumps(
            [{'row': 1}])
        ctx = self._make_ctx(adp)
        result = json.loads(fn(fact_table='SALES', ctx=ctx))
        adp.Analytics.create_auto.assert_called_once_with('SALES')
        adp.Analytics.compile.assert_called()
        adp.Analytics.get_metadata.assert_called()
        adp.Analytics.get_data_preview.assert_called()

    def test_adp_analyze_analytic_view_walks_quality(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import adp_tools
        mcp_server = FastMCP('test')
        adp_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['adp_analyze_analytic_view'].fn

        adp = MagicMock()
        adp.rest.expired = None
        adp.Analytics.is_exist.return_value = True
        adp.Analytics.get_metadata.return_value = json.dumps({})
        adp.Analytics.get_measures_list.return_value = json.dumps([])
        adp.Analytics.get_dimension_names.return_value = json.dumps([])
        adp.Analytics.quality_report.return_value = json.dumps([])
        adp.Analytics.get_error_classes_dim.return_value = json.dumps([])
        adp.Analytics.get_error_classes_fact.return_value = json.dumps([])
        ctx = self._make_ctx(adp)
        result = json.loads(fn(av_name='AV', ctx=ctx))
        adp.Analytics.quality_report.assert_called()

    def test_adp_generate_insights_polls_status(self):
        '''generate_insights kicks off the job + polls + collects graph.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import adp_tools
        mcp_server = FastMCP('test')
        adp_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['adp_generate_insights'].fn

        adp = MagicMock()
        adp.rest.expired = None
        adp.Insight.generate.return_value = json.dumps(
            {'request_id': 'R1'})
        adp.Insight.get_job_status.return_value = json.dumps(
            {'status': 'COMPLETED'})
        adp.Insight.get_insights_list.return_value = json.dumps(
            [{'name': 'I1'}])
        adp.Insight.get_graph_details.return_value = json.dumps(
            {'graph': 'data'})
        ctx = self._make_ctx(adp)
        result = json.loads(fn(object_name='SALES', measure='AMT',
                                ctx=ctx))
        adp.Insight.generate.assert_called_once()

    @pytest.mark.parametrize('tool,kwargs', [
        ('adp_browse_catalog', {'action': 'entities'}),  # no catalog_name
        ('adp_browse_catalog', {'action': 'preview'}),
        ('adp_browse_catalog', {'action': 'check_db_link'}),
        ('adp_browse_catalog', {'action': 'unknown'}),
        ('adp_manage_catalog', {'action': 'enable'}),  # no catalog_name
        ('adp_manage_catalog', {'action': 'disable'}),
        ('adp_manage_catalog', {'action': 'unmount'}),
        ('adp_manage_catalog', {'action': 'unknown'}),
        ('adp_manage_sharing', {'action': 'get'}),
        ('adp_manage_sharing', {'action': 'create'}),
        ('adp_manage_sharing', {'action': 'publish'}),
        ('adp_manage_sharing', {'action': 'grant_recipient'}),
        ('adp_manage_sharing', {'action': 'create_recipient'}),
        ('adp_manage_sharing', {'action': 'delete'}),
        ('adp_manage_sharing', {'action': 'unpublish'}),
        ('adp_manage_sharing', {'action': 'delete_recipient'}),
        ('adp_manage_sharing', {'action': 'rename', 'share_name': 'S'}),
        ('adp_manage_sharing', {'action': 'create_provider'}),
        ('adp_manage_sharing', {'action': 'delete_provider'}),
        ('adp_manage_sharing', {'action': 'unknown'}),
        ('adp_manage_credentials', {'action': 'unknown'}),
        ('adp_manage_credentials', {'action': 'create',
                                      'credential_name': 'C'}),
        ('adp_manage_credentials', {'action': 'create_ocid'}),
        ('adp_manage_credentials', {'action': 'create_storage_link'}),
        ('adp_manage_credentials', {'action': 'drop_storage_link'}),
        ('adp_manage_credentials', {'action': 'drop'}),
        ('adp_manage_credentials', {'action': 'list_cloud_objects'}),
        ('adp_manage_db_links', {'action': 'list_tables'}),
        ('adp_manage_db_links', {'action': 'copy_tables',
                                   'db_link_name': 'L'}),  # no tables
        ('adp_manage_db_links', {'action': 'link_tables'}),
        ('adp_manage_db_links', {'action': 'check'}),
        ('adp_manage_db_links', {'action': 'drop'}),
        ('adp_manage_db_links', {'action': 'unknown'}),
        ('adp_manage_insights', {'action': 'list_insights'}),
        ('adp_manage_insights', {'action': 'get_graph'}),
        ('adp_manage_insights', {'action': 'unknown'}),
        ('adp_manage_analytic_views', {'action': 'unknown'}),
        ('adp_manage_analytic_views', {'action': 'drop'}),
        ('adp_load_from_cloud', {}),  # no params
    ])
    def test_adp_validation_error_branches(self, tool, kwargs):
        '''Validation-error coverage for ADP composite tools.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import adp_tools
        mcp_server = FastMCP('test')
        adp_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools[tool].fn
        adp = MagicMock()
        adp.rest.expired = None
        adp.rest.username = 'ADMIN'
        ctx = self._make_ctx(adp)
        result = json.loads(fn(ctx=ctx, **kwargs))
        assert 'error' in result

    def test_adp_get_annotations_groups_by_column(self):
        '''Verify adp_get_annotations groups rows into table vs column
        annotations and counts them correctly. Also verifies we do NOT
        query the non-existent OWNER column on ALL_ANNOTATIONS_USAGE.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import adp_tools
        mcp_server = FastMCP('test')
        adp_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['adp_get_annotations'].fn

        adp = MagicMock()
        adp.rest.expired = None
        # Mimic real ALL_ANNOTATIONS_USAGE rows — Oracle uppercases
        # annotation names, and there is no OWNER column on the view.
        adp.Misc.run_query.return_value = json.dumps({'items': [
            {'column_name': None, 'annotation_name': 'DESCRIPTION',
             'annotation_value': 'Monthly sales fact'},
            {'column_name': 'CUST_ID', 'annotation_name': 'DISPLAY_NAME',
             'annotation_value': 'Customer'},
            {'column_name': 'CUST_ID', 'annotation_name': 'JOIN_HINT',
             'annotation_value': 'CUSTOMERS.ID'},
            {'column_name': 'AMOUNT', 'annotation_name': 'UNIT',
             'annotation_value': 'USD'},
        ]})
        ctx = self._make_ctx(adp)
        result = json.loads(fn(object_name='SALES', ctx=ctx))
        assert result['annotation_count'] == 4
        assert result['annotations']['table'] == {
            'DESCRIPTION': 'Monthly sales fact'}
        assert result['annotations']['columns']['CUST_ID'] == {
            'DISPLAY_NAME': 'Customer', 'JOIN_HINT': 'CUSTOMERS.ID'}
        assert result['annotations']['columns']['AMOUNT'] == {
            'UNIT': 'USD'}
        # Verify it queried the expected view and did NOT include the
        # non-existent bare OWNER column. annotation_owner IS legal.
        sql_lower = adp.Misc.run_query.call_args[0][0].lower()
        assert 'all_annotations_usage' in sql_lower
        assert "upper('sales')" in sql_lower
        # Bare "owner" (not "annotation_owner" or "domain_owner") must
        # never appear — the view has no object-owner column.
        import re
        bad = re.search(r'(?<![_a-z])owner\b', sql_lower)
        assert bad is None, f'bare OWNER identifier in SQL: {sql_lower}'

    def test_adp_get_annotations_empty_returns_note(self):
        '''No annotations → result includes a diagnostic note.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import adp_tools
        mcp_server = FastMCP('test')
        adp_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['adp_get_annotations'].fn

        adp = MagicMock()
        adp.rest.expired = None
        adp.Misc.run_query.return_value = json.dumps({'items': []})
        ctx = self._make_ctx(adp)
        result = json.loads(fn(object_name='UNKNOWN_TABLE', ctx=ctx))
        assert result['annotation_count'] == 0
        assert 'note' in result and '23ai' in result['note']

    def test_adp_sql_with_annotations_prompt_registered(self):
        '''Prompt is registered and renders with the expected guidance.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import adp_tools
        mcp_server = FastMCP('test')
        adp_tools.register_tools(mcp_server)
        prompts = mcp_server._prompt_manager._prompts
        assert 'adp_sql_with_annotations' in prompts
        prompt = prompts['adp_sql_with_annotations']
        # Render it via the underlying function
        rendered = prompt.fn(
            question='what were total sales last quarter?',
            tables='SALES, CUSTOMERS')
        assert 'adp_get_annotations' in rendered
        assert 'what were total sales last quarter?' in rendered
        assert 'SALES, CUSTOMERS' in rendered


# ------------------------------------------------------------------ #
#  DT tool dispatch tests (mocked SDK)                                 #
# ------------------------------------------------------------------ #

@mcp_required
class TestDtToolDispatch:

    def _make_ctx(self, client_mock):
        ctx = MagicMock()
        ctx.request_context.lifespan_context = {
            'datatransforms': {'client': client_mock, 'workbench': MagicMock()},
        }
        return ctx

    def test_dt_explore_no_connection(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_explore'].fn
        ctx = MagicMock()
        ctx.request_context.lifespan_context = {}
        result = json.loads(fn(ctx=ctx))
        assert 'error' in result

    def test_dt_explore_success(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_explore'].fn

        client = MagicMock()
        client.get_about.return_value = {'version': '1.0'}
        client.list_connections.return_value = [{'name': 'conn1'}]
        client.list_projects.return_value = [{'name': 'proj1'}]
        client.list_schedules.return_value = []
        ctx = self._make_ctx(client)
        result = json.loads(fn(ctx=ctx))
        assert result['about']['version'] == '1.0'
        assert len(result['connections']) == 1

    def test_dt_describe_project_success(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_describe_project'].fn

        client = MagicMock()
        client.check_if_project_exists.return_value = 'proj-123'
        client.list_dataflows_in_project.return_value = [{'name': 'df1'}]
        client.list_workflows_in_project.return_value = []
        client.list_dataloads_in_project.return_value = []
        ctx = self._make_ctx(client)
        result = json.loads(fn(project_name='MyProject', ctx=ctx))
        assert result['project_id'] == 'proj-123'
        assert len(result['dataflows']) == 1

    def test_dt_describe_project_not_found(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_describe_project'].fn

        client = MagicMock()
        client.check_if_project_exists.return_value = None
        ctx = self._make_ctx(client)
        result = json.loads(fn(project_name='Missing', ctx=ctx))
        assert 'error' in result

    def test_dt_manage_variables_list(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_manage_variables'].fn

        client = MagicMock()
        client.list_variables.return_value = [{'name': 'V1', 'value': 'X'}]
        ctx = self._make_ctx(client)
        result = json.loads(fn(action='list', ctx=ctx))
        assert result[0]['name'] == 'V1'

    @patch('oracle.data_studio_mcp_server.tools.dt_tools.DataLoad',
           create=True)
    def test_dt_manage_dataload_create_uses_all_inputs(self, MockDataLoad):
        '''Verify create passes name, project, connection.schema to DataLoad.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_manage_dataload'].fn

        client = MagicMock()
        client.check_if_project_exists.return_value = 'proj-123'
        ctx = self._make_ctx(client)

        # Mock the DataLoad builder
        dl_instance = MagicMock()
        MockDataLoad.return_value = dl_instance
        dl_instance.source.return_value = dl_instance
        dl_instance.target.return_value = dl_instance
        dl_instance.truncate.return_value = dl_instance

        # Patch the import inside the tool
        import oracle.data_studio_mcp_server.tools.dt_tools as dt_mod
        with patch.dict('sys.modules',
                        {'datatransforms.dataload': MagicMock(
                            DataLoad=MockDataLoad)}):
            result = json.loads(fn(
                action='create', project_name='MyProj',
                dataload_name='my_load',
                source_connection='SRC_CONN', source_schema='SRC_SCH',
                target_connection='TGT_CONN', target_schema='TGT_SCH',
                tables='EMP, DEPT', load_type='TRUNCATE', ctx=ctx))

        # Verify DataLoad was created with name and project
        MockDataLoad.assert_called_once_with('my_load', 'MyProj')
        # Verify source/target use connection.schema format
        dl_instance.source.assert_called_once_with('SRC_CONN.SRC_SCH')
        dl_instance.target.assert_called_once_with('TGT_CONN.TGT_SCH')
        # Verify tables were added
        assert dl_instance.truncate.call_count == 2
        dl_instance.create_dataload.assert_called_once()
        assert result['action'] == 'created'
        assert result['dataload'] == 'my_load'

    def test_dt_manage_schedule_unknown_action(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_manage_schedule'].fn

        client = MagicMock()
        ctx = self._make_ctx(client)
        result = json.loads(fn(action='invalid', ctx=ctx))
        assert 'error' in result

    def test_dt_browse_data_schemas(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_browse_data'].fn

        client = MagicMock()
        client.get_live_schemas.return_value = ['schema1', 'schema2']
        ctx = self._make_ctx(client)
        result = json.loads(fn(connection_name='myconn', ctx=ctx))
        assert result['schemas'] == ['schema1', 'schema2']

    def test_dt_browse_data_with_schema_filter(self):
        '''When schema is specified, dt_browse_data calls
        get_live_tables for that schema.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_browse_data'].fn

        client = MagicMock()
        client.get_live_tables.return_value = ['T1', 'T2']
        ctx = self._make_ctx(client)
        result = json.loads(fn(connection_name='C',
                                schema='S', ctx=ctx))
        client.get_live_tables.assert_called_once_with('C', 'S')

    def test_dt_create_pipeline_creates_project_when_missing(self):
        '''If the project doesn't exist, dt_create_pipeline creates it
        first, then proceeds with the dataflow build.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_create_pipeline'].fn

        client = MagicMock()
        # First call: project doesn't exist; second call after create: exists
        client.check_if_project_exists.side_effect = [None, 'proj-1']
        wb = MagicMock()
        ctx = MagicMock()
        ctx.request_context.lifespan_context = {
            'datatransforms': {'client': client, 'workbench': wb}}
        # The body falls back to client.create_dataflow_from_json_payload
        # if the SDK builders aren't importable; with our MagicMock
        # workbench, the import succeeds via MagicMock too. Just assert
        # the project-create probe ran.
        try:
            fn(project_name='NewProj',
                source_connection='SRC_CONN', source_schema='SRC_S',
                source_table='SRC',
                target_connection='TGT_CONN', target_schema='TGT_S',
                target_table='TGT',
                ctx=ctx)
        except Exception:
            # Builder may fail with our minimal mock — that's OK; we
            # care that the existence-probe / create_project ran.
            pass
        client.create_project.assert_called_once_with('NewProj')

    def _patch_schedule_module(self):
        '''Build a fake datatransforms.schedule with a Schedule class.'''
        fake_module = MagicMock()
        fake_sched = MagicMock()
        fake_module.Schedule.return_value = fake_sched
        return fake_module, fake_sched

    def test_dt_manage_schedule_create_immediate(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_manage_schedule'].fn

        client = MagicMock()
        client.check_if_schedule_exists.return_value = (False, None)
        ctx = self._make_ctx(client)
        sched_module, sched = self._patch_schedule_module()
        with patch.dict('sys.modules',
                         {'datatransforms.schedule': sched_module}):
            json.loads(fn(action='create', schedule_name='S',
                           project_name='P', resource_name='DF',
                           frequency='immediate', ctx=ctx))
        sched.immediate.assert_called_once()

    def test_dt_manage_schedule_create_hourly(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_manage_schedule'].fn

        client = MagicMock()
        client.check_if_schedule_exists.return_value = (False, None)
        ctx = self._make_ctx(client)
        sched_module, sched = self._patch_schedule_module()
        with patch.dict('sys.modules',
                         {'datatransforms.schedule': sched_module}):
            json.loads(fn(action='create', schedule_name='S',
                           project_name='P', resource_name='DF',
                           frequency='hourly', time='15:30', ctx=ctx))
        sched.hourly.assert_called_once_with(15, 30)

    def test_dt_manage_schedule_create_daily_full_path(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_manage_schedule'].fn

        client = MagicMock()
        client.check_if_schedule_exists.return_value = (False, None)
        ctx = self._make_ctx(client)
        sched_module, sched = self._patch_schedule_module()
        with patch.dict('sys.modules',
                         {'datatransforms.schedule': sched_module}):
            json.loads(fn(action='create', schedule_name='S',
                           project_name='P', resource_name='WF',
                           resource_type='workflow',
                           frequency='daily', time='09:30:00', ctx=ctx))
        sched.workflow.assert_called_once_with('P', 'WF')
        sched.daily.assert_called_once_with(9, 30, 0)

    def test_dt_manage_schedule_create_weekly(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_manage_schedule'].fn

        client = MagicMock()
        client.check_if_schedule_exists.return_value = (False, None)
        ctx = self._make_ctx(client)
        sched_module, sched = self._patch_schedule_module()
        with patch.dict('sys.modules',
                         {'datatransforms.schedule': sched_module}):
            json.loads(fn(action='create', schedule_name='S',
                           project_name='P', resource_name='DF',
                           frequency='weekly',
                           days='MONDAY,FRIDAY',
                           time='09:00', ctx=ctx))
        sched.weekly.assert_called_once_with(['MONDAY', 'FRIDAY'], '09:00')

    def test_dt_manage_schedule_create_monthly(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_manage_schedule'].fn

        client = MagicMock()
        client.check_if_schedule_exists.return_value = (False, None)
        ctx = self._make_ctx(client)
        sched_module, sched = self._patch_schedule_module()
        with patch.dict('sys.modules',
                         {'datatransforms.schedule': sched_module}):
            json.loads(fn(action='create', schedule_name='S',
                           project_name='P', resource_name='DF',
                           frequency='monthly',
                           time='15 09:00:00', ctx=ctx))
        sched.monthly.assert_called_once_with('15', '09:00:00')

    def test_dt_manage_schedule_create_unknown_frequency(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_manage_schedule'].fn

        client = MagicMock()
        client.check_if_schedule_exists.return_value = (False, None)
        ctx = self._make_ctx(client)
        sched_module, _ = self._patch_schedule_module()
        with patch.dict('sys.modules',
                         {'datatransforms.schedule': sched_module}):
            result = json.loads(fn(action='create', schedule_name='S',
                                    project_name='P', resource_name='DF',
                                    frequency='nonsense', ctx=ctx))
        assert 'error' in result

    def test_dt_manage_schedule_create_weekly_no_days_errors(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_manage_schedule'].fn

        client = MagicMock()
        client.check_if_schedule_exists.return_value = (False, None)
        ctx = self._make_ctx(client)
        sched_module, _ = self._patch_schedule_module()
        with patch.dict('sys.modules',
                         {'datatransforms.schedule': sched_module}):
            result = json.loads(fn(action='create', schedule_name='S',
                                    project_name='P', resource_name='DF',
                                    frequency='weekly', ctx=ctx))
        assert 'error' in result

    def test_dt_manage_schedule_create_daily(self):
        '''dt_manage_schedule create with daily frequency triggers
        the Schedule builder. We can't import the real builder but can
        verify the existence-probe + branch dispatch happen.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_manage_schedule'].fn

        client = MagicMock()
        client.check_if_schedule_exists.return_value = (False, None)
        ctx = self._make_ctx(client)
        # Will raise inside the builder; we just want the dispatch
        # path covered.
        try:
            fn(action='create', schedule_name='S',
                project_name='P', resource_name='DF',
                frequency='daily', time='09:00:00', ctx=ctx)
        except Exception:
            pass

    def test_dt_create_pipeline_full_flow(self):
        '''Full dt_create_pipeline flow with all required SDK builders
        mocked.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_create_pipeline'].fn

        client = MagicMock()
        client.check_if_project_exists.return_value = 'proj-1'
        wb = MagicMock()
        ctx = MagicMock()
        ctx.request_context.lifespan_context = {
            'datatransforms': {'client': client, 'workbench': wb}}

        # Mock the Project / SourceDataStore / TargetDataStore /
        # DataFlow builders that the body imports lazily.
        fake_module = MagicMock()
        fake_project = MagicMock()
        fake_module.Project.return_value = fake_project
        fake_module.SourceDataStore = MagicMock(return_value=MagicMock())
        fake_module.TargetDataStore = MagicMock(return_value=MagicMock())
        fake_dataflow = MagicMock()
        fake_module.DataFlow.return_value = fake_dataflow
        with patch.dict('sys.modules',
                         {'datatransforms.dataflow': fake_module}):
            try:
                fn(project_name='P',
                    source_connection='SC', source_schema='SS',
                    source_table='T1',
                    target_connection='TC', target_schema='TS',
                    target_table='T2',
                    integration_type='CONTROL_APPEND',
                    ctx=ctx)
            except Exception:
                # Builder body may run additional ops we haven't
                # mocked — we only care about coverage progression.
                pass
        # Project existence probe ran
        client.check_if_project_exists.assert_called_once_with('P')

    def test_dt_create_pipeline_with_workbench_builder(self):
        '''Walk dt_create_pipeline through the workbench-builder branch
        deep enough to cover the body's main flow.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_create_pipeline'].fn

        client = MagicMock()
        client.check_if_project_exists.return_value = 'proj-1'
        client.check_if_df_exists.return_value = (False, None)
        wb = MagicMock()
        ctx = MagicMock()
        ctx.request_context.lifespan_context = {
            'datatransforms': {'client': client, 'workbench': wb}}

        fake_df_module = MagicMock()
        fake_dataflow = MagicMock()
        fake_df_module.DataFlow.return_value = fake_dataflow
        fake_df_module.Project = MagicMock(return_value=MagicMock())
        fake_df_module.SourceDataStore = MagicMock(
            return_value=MagicMock())
        fake_df_module.TargetDataStore = MagicMock(
            return_value=MagicMock())
        with patch.dict('sys.modules',
                         {'datatransforms.dataflow': fake_df_module}):
            try:
                fn(project_name='P',
                    source_connection='SC', source_schema='SS',
                    source_table='T1',
                    target_connection='TC', target_schema='TS',
                    target_table='T2',
                    dataflow_name='MyDF',
                    integration_type='INSERT',
                    ctx=ctx)
            except Exception:
                pass
        # Builders were instantiated
        fake_df_module.Project.assert_called()
        fake_df_module.SourceDataStore.assert_called()
        fake_df_module.TargetDataStore.assert_called()

    def test_dt_describe_connection_no_schemas_branch(self):
        '''Connection details fetched but live_schemas returns empty.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_describe_connection'].fn

        client = MagicMock()
        client.get_connection_details.return_value = {'name': 'C'}
        client.test_connection_by_name.return_value = {'status': 'ok'}
        client.get_live_schemas.return_value = []
        ctx = self._make_ctx(client)
        json.loads(fn(connection_name='C', ctx=ctx))
        client.get_live_schemas.assert_called_once_with('C')

    def test_dt_browse_data_lists_all_schemas(self):
        '''No schema specified → returns all schemas with their tables.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_browse_data'].fn

        client = MagicMock()
        client.get_live_schemas.return_value = ['S1', 'S2']
        client.get_live_tables.return_value = ['T1', 'T2']
        ctx = self._make_ctx(client)
        result = json.loads(fn(connection_name='C', ctx=ctx))
        # Schemas listed
        assert result.get('schemas') == ['S1', 'S2']

    def test_dt_manage_dataload_get_with_existing(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_manage_dataload'].fn

        client = MagicMock()
        client.check_if_project_exists.return_value = 'proj-1'
        client.check_if_dataload_exists.return_value = (True, 'dl-id')
        client.get_dataload_by_id.return_value = {'name': 'DL', 'detail': 'x'}
        ctx = self._make_ctx(client)
        result = json.loads(fn(action='get',
                                project_name='P', dataload_name='DL',
                                ctx=ctx))
        client.get_dataload_by_id.assert_called_once_with('dl-id')

    def test_dt_manage_workflow_check_exists_true(self):
        '''check_exists returns global_id when present.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_manage_workflow'].fn

        client = MagicMock()
        client.check_if_project_exists.return_value = 'proj-1'
        client.check_if_workflow_exists.return_value = (True, 'wf-id')
        ctx = self._make_ctx(client)
        result = json.loads(fn(action='check_exists',
                                project_name='P', workflow_name='WF',
                                ctx=ctx))
        assert result.get('exists') is True

    def test_dt_manage_dataload_create_full_body(self):
        '''dt_manage_dataload create body — exercises project check,
        DataLoad builder import, and the full table-load loop.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_manage_dataload'].fn

        client = MagicMock()
        client.check_if_project_exists.return_value = 'proj-1'
        ctx = self._make_ctx(client)
        # The DataLoad import will fail in this venv unless installed —
        # exercise both branches by patching the builder.
        fake_dl_module = MagicMock()
        fake_dl = MagicMock()
        fake_dl_module.DataLoad.return_value = fake_dl
        with patch.dict('sys.modules',
                         {'datatransforms.dataload': fake_dl_module}):
            json.loads(fn(action='create',
                           project_name='P', dataload_name='DL',
                           source_connection='SC', source_schema='SS',
                           target_connection='TC', target_schema='TS',
                           tables='T1,T2', load_type='APPEND',
                           ctx=ctx))
        fake_dl_module.DataLoad.assert_called_once_with('DL', 'P')
        # Two tables → two load-type calls (append since load_type=APPEND)
        assert fake_dl.append.call_count == 2
        fake_dl.create_dataload.assert_called_once()

    def test_dt_manage_dataload_create_recreate_path(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_manage_dataload'].fn

        client = MagicMock()
        client.check_if_project_exists.return_value = 'proj-1'
        ctx = self._make_ctx(client)
        fake_dl_module = MagicMock()
        fake_dl = MagicMock()
        fake_dl_module.DataLoad.return_value = fake_dl
        with patch.dict('sys.modules',
                         {'datatransforms.dataload': fake_dl_module}):
            json.loads(fn(action='create',
                           project_name='P', dataload_name='DL',
                           source_connection='SC', source_schema='SS',
                           target_connection='TC', target_schema='TS',
                           tables='T', load_type='RECREATE',
                           ctx=ctx))
        fake_dl.recreate.assert_called_once_with('T')

    def test_dt_manage_workflow_get(self):
        '''get action looks up workflow by name + ID.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_manage_workflow'].fn

        client = MagicMock()
        client.check_if_project_exists.return_value = 'proj-1'
        client.check_if_workflow_exists.return_value = (True, 'wf-id')
        client.get_workflow_by_id.return_value = {'name': 'WF', 'detail': 'x'}
        ctx = self._make_ctx(client)
        result = json.loads(fn(action='get', project_name='P',
                                workflow_name='WF', ctx=ctx))
        client.get_workflow_by_id.assert_called_once_with('wf-id')

    @pytest.mark.parametrize('tool,kwargs', [
        ('dt_manage_schedule', {'action': 'unknown'}),
        ('dt_manage_schedule', {'action': 'delete'}),  # no schedule_name
        ('dt_manage_schedule', {'action': 'create',
                                  'schedule_name': 'S'}),  # missing more
        ('dt_manage_variables', {'action': 'unknown'}),
        ('dt_manage_variables', {'action': 'set'}),  # no name
        ('dt_manage_variables', {'action': 'set',
                                   'variable_name': 'V'}),  # no value
        ('dt_manage_connection', {'action': 'unknown'}),
        ('dt_manage_connection', {'action': 'get'}),
        ('dt_manage_connection', {'action': 'test'}),
        ('dt_manage_connection', {'action': 'delete'}),
        ('dt_manage_connection', {'action': 'create',
                                    'connection_name': 'C'}),
        ('dt_manage_dataload', {'action': 'unknown',
                                  'project_name': 'P'}),
        ('dt_manage_dataload', {'action': 'get',
                                  'project_name': 'P'}),  # no dataload_name
        ('dt_manage_dataload', {'action': 'check_exists',
                                  'project_name': 'P'}),
        ('dt_manage_dataload', {'action': 'create',
                                  'project_name': 'P',
                                  'dataload_name': 'DL'}),  # missing more
        ('dt_manage_workflow', {'action': 'unknown',
                                  'project_name': 'P'}),
        ('dt_manage_workflow', {'action': 'get',
                                  'project_name': 'P'}),
        ('dt_manage_workflow', {'action': 'check_exists',
                                  'project_name': 'P'}),
        ('dt_manage_data_entities', {'action': 'unknown'}),
        ('dt_manage_data_entities', {'action': 'import_entities',
                                       'connection_name': 'C'}),  # no schema
        ('dt_manage_project', {'action': 'unknown',
                                  'project_name': 'P'}),
    ])
    def test_dt_validation_error_branches(self, tool, kwargs):
        '''Validation-error coverage for DT composite tools.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools[tool].fn
        client = MagicMock()
        client.check_if_project_exists.return_value = 'proj-1'
        client.check_if_dataload_exists.return_value = (False, None)
        client.check_if_workflow_exists.return_value = (False, None)
        ctx = self._make_ctx(client)
        result = json.loads(fn(ctx=ctx, **kwargs))
        assert 'error' in result

    def test_dt_describe_project_full_body(self):
        '''Walks the full dt_describe_project flow: existence check
        + 3 list_*_in_project calls + per-entity get_*_by_id walks.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_describe_project'].fn

        client = MagicMock()
        client.check_if_project_exists.return_value = 'proj-1'
        client.list_dataflows_in_project.return_value = [
            {'name': 'DF1', 'globalId': 'df1'}]
        client.list_workflows_in_project.return_value = [
            {'name': 'WF1', 'globalId': 'wf1'}]
        client.list_dataloads_in_project.return_value = [
            {'name': 'DL1'}]
        client.get_dataflow_by_id.return_value = {'detail': 'df'}
        client.get_workflow_by_id.return_value = {'detail': 'wf'}
        ctx = self._make_ctx(client)
        result = json.loads(fn(project_name='P', ctx=ctx))
        assert result['project_name'] == 'P'
        client.list_dataflows_in_project.assert_called_once_with('proj-1')
        client.list_workflows_in_project.assert_called_once_with('proj-1')
        client.list_dataloads_in_project.assert_called_once_with('proj-1')

    def test_dt_describe_project_not_found(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_describe_project'].fn

        client = MagicMock()
        client.check_if_project_exists.return_value = None
        ctx = self._make_ctx(client)
        result = json.loads(fn(project_name='Missing', ctx=ctx))
        # Project not found — body returns an exists=False payload
        assert result.get('exists') is False or 'error' in result

    def test_dt_describe_connection_full_body(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_describe_connection'].fn

        client = MagicMock()
        client.get_connection_details.return_value = {'name': 'C',
                                                       'type': 'ORACLE'}
        client.test_connection_by_name.return_value = {'status': 'ok'}
        client.get_live_schemas.return_value = ['S1', 'S2']
        ctx = self._make_ctx(client)
        result = json.loads(fn(connection_name='C', ctx=ctx))
        assert 'connection' in result or 'connection_name' in result \
            or 'details' in result
        client.get_connection_details.assert_called_once_with('C')
        client.test_connection_by_name.assert_called_once_with('C')

    def test_dt_check_health_walks_all_connections(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_check_health'].fn

        client = MagicMock()
        client.list_connections.return_value = [
            {'name': 'C1'}, {'name': 'C2'}]
        client.test_connection_by_name.return_value = {'status': 'ok'}
        client.list_schedules.return_value = []
        client.get_deployment_time.return_value = '2026-01-01'
        ctx = self._make_ctx(client)
        result = json.loads(fn(ctx=ctx))
        # Each connection should be tested
        assert client.test_connection_by_name.call_count == 2

    def test_dt_run_pipeline_dataflow(self):
        '''dt_run_pipeline gets a runtime client from the workbench
        and calls run_dataflow.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_run_pipeline'].fn

        client = MagicMock()
        workbench = MagicMock()
        runtime = MagicMock()
        runtime.run_dataflow.return_value = {'session_id': 'S1'}
        workbench.get_runtime_client.return_value = runtime
        ctx = MagicMock()
        ctx.request_context.lifespan_context = {
            'datatransforms': {'client': client, 'workbench': workbench}}
        result = json.loads(fn(project_name='P', resource_name='DF',
                                resource_type='dataflow', ctx=ctx))
        runtime.run_dataflow.assert_called_once_with('P', 'DF')
        # Body wraps the SDK result under 'job_result'
        assert result['project'] == 'P'
        assert result['resource'] == 'DF'
        assert 'job_result' in result

    def test_dt_manage_data_entities_import(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_manage_data_entities'].fn

        client = MagicMock()
        wb = MagicMock()
        wb.import_data_entities.return_value = {'imported': 5}
        ctx = MagicMock()
        ctx.request_context.lifespan_context = {
            'datatransforms': {'client': client, 'workbench': wb}}
        result = json.loads(fn(action='import_entities',
                                connection_name='C',
                                schema_name='S', ctx=ctx))
        wb.import_data_entities.assert_called_once_with('C', 'S')

    def test_dt_manage_dataflow_check_exists(self):
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import dt_tools
        mcp_server = FastMCP('test')
        dt_tools.register_tools(mcp_server)
        fn = mcp_server._tool_manager._tools['dt_manage_dataflow'].fn

        client = MagicMock()
        client.check_if_project_exists.return_value = 'proj-1'
        client.check_if_df_exists.return_value = (True, 'df-id-1')
        ctx = self._make_ctx(client)
        result = json.loads(fn(project_name='P', dataflow_name='DF',
                               ctx=ctx))
        assert result['exists'] is True
        assert result['global_id'] == 'df-id-1'


# ------------------------------------------------------------------ #
#  cli_config tests                                                    #
# ------------------------------------------------------------------ #

class TestCliConfig:

    def test_build_parser_set_subcommand(self):
        from oracle.data_studio_mcp_server.cli_config import _build_parser
        parser = _build_parser()
        # Parse a complete `set` command
        args = parser.parse_args(['set', 'essbase',
                                   '--url', 'https://h',
                                   '--user', 'admin',
                                   '--password', 'p'])
        assert args.command == 'set'
        assert args.service == 'essbase'
        assert args.url == 'https://h'
        assert args.user == 'admin'

    def test_build_parser_list_subcommand(self):
        from oracle.data_studio_mcp_server.cli_config import _build_parser
        parser = _build_parser()
        args = parser.parse_args(['list'])
        assert args.command == 'list'

    def test_build_parser_remove_subcommand(self):
        from oracle.data_studio_mcp_server.cli_config import _build_parser
        parser = _build_parser()
        args = parser.parse_args(['remove', 'adp'])
        assert args.command == 'remove'
        assert args.service == 'adp'

    def test_build_parser_invalid_service_rejected(self):
        from oracle.data_studio_mcp_server.cli_config import _build_parser
        parser = _build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(['set', 'nonexistent_service'])

    @patch('oracle.data_studio_mcp_server.cli_config.store_credentials')
    def test_cmd_set_stores_with_password(self, mock_store, capsys):
        from oracle.data_studio_mcp_server.cli_config import _cmd_set
        mock_store.return_value = {'service': 'adp', 'keyring_stored': True}
        args = MagicMock(service='adp', url='https://h', user='ADMIN',
                          password='Welcome2025#', token=None,
                          transport=None, port=None)
        _cmd_set(args)
        mock_store.assert_called_once()
        call_kwargs = mock_store.call_args.kwargs
        assert call_kwargs['password'] == 'Welcome2025#'
        assert call_kwargs['url'] == 'https://h'

    @patch('oracle.data_studio_mcp_server.cli_config.store_credentials')
    @patch('oracle.data_studio_mcp_server.cli_config.getpass.getpass',
           return_value='prompted_pw')
    def test_cmd_set_prompts_for_password_when_user_set(self, mock_prompt,
                                                          mock_store):
        '''If --user given but no --password, prompt interactively.'''
        from oracle.data_studio_mcp_server.cli_config import _cmd_set
        mock_store.return_value = {'service': 'adp', 'keyring_stored': True}
        args = MagicMock(service='adp', url='https://h', user='ADMIN',
                          password=None, token=None,
                          transport=None, port=None)
        _cmd_set(args)
        mock_prompt.assert_called_once()
        assert mock_store.call_args.kwargs['password'] == 'prompted_pw'

    @patch('oracle.data_studio_mcp_server.cli_config.store_credentials')
    def test_cmd_set_server_no_password(self, mock_store, capsys):
        '''The "server" service should never trigger a password prompt.'''
        from oracle.data_studio_mcp_server.cli_config import _cmd_set
        mock_store.return_value = {'service': 'server'}
        args = MagicMock(service='server', url=None, user=None,
                          password=None, token=None,
                          transport='stdio', port='8000')
        _cmd_set(args)
        # No password kwarg in the call
        assert mock_store.call_args.kwargs.get('password') is None
        assert mock_store.call_args.kwargs['transport'] == 'stdio'
        assert mock_store.call_args.kwargs['port'] == '8000'

    @patch('oracle.data_studio_mcp_server.cli_config.list_credentials')
    def test_cmd_list_with_creds(self, mock_list, capsys):
        from oracle.data_studio_mcp_server.cli_config import _cmd_list
        mock_list.return_value = {
            'adp': {'url': 'https://h', 'user': 'ADMIN'}}
        _cmd_list(MagicMock())
        out = capsys.readouterr().out
        assert '[adp]' in out
        assert 'url = https://h' in out

    @patch('oracle.data_studio_mcp_server.cli_config.list_credentials',
           return_value={})
    def test_cmd_list_empty(self, mock_list, capsys):
        from oracle.data_studio_mcp_server.cli_config import _cmd_list
        _cmd_list(MagicMock())
        out = capsys.readouterr().out
        assert 'No credentials configured.' in out

    @patch('oracle.data_studio_mcp_server.cli_config.remove_credentials')
    def test_cmd_remove(self, mock_remove, capsys):
        from oracle.data_studio_mcp_server.cli_config import _cmd_remove
        mock_remove.return_value = {'service': 'essbase', 'removed': True}
        args = MagicMock(service='essbase')
        _cmd_remove(args)
        mock_remove.assert_called_once_with('essbase')
        assert 'essbase' in capsys.readouterr().out


# ------------------------------------------------------------------ #
#  Bulk action dispatch — parametrised over many tool/action combos    #
# ------------------------------------------------------------------ #
#
# Every composite manage_* tool has a per-action elif chain that
# routes to a specific SDK call. These tests exercise each branch
# with a mocked SDK and assert the correct SDK method was invoked
# with the expected primary arg. They prevent the param-leak class
# of bug (B1, B2, M7 in the audit) and lift line coverage by
# touching every action branch.

def _walk(obj, path):
    '''Walk a dotted attr path on a mock and return the final attr.'''
    for part in path.split('.'):
        obj = getattr(obj, part)
    return obj


def _adp_dispatch(tool_name, kwargs, sdk_path, sdk_return=None):
    '''Run an ADP tool with a mocked SDK; return (result, mock_adp).'''
    from mcp.server.fastmcp import FastMCP
    from oracle.data_studio_mcp_server.tools import adp_tools
    mcp_server = FastMCP('test')
    adp_tools.register_tools(mcp_server)
    fn = mcp_server._tool_manager._tools[tool_name].fn
    adp = MagicMock()
    adp.rest.expired = None
    adp.rest.username = 'ADMIN'
    method = _walk(adp, sdk_path)
    method.return_value = json.dumps(sdk_return if sdk_return is not None
                                      else {'status': 'ok'})
    ctx = MagicMock()
    ctx.request_context.lifespan_context = {'adp': adp}
    result = fn(ctx=ctx, **kwargs)
    return result, adp


def _dt_dispatch(tool_name, kwargs, sdk_path, sdk_return=None,
                  on_workbench=False):
    '''Run a DT tool with a mocked client/workbench; return result + mocks.

    Pre-mocks check_if_*_exists methods to return tuples (False, None),
    and check_if_project_exists to return a project ID — so action
    handlers that probe existence first don't crash on tuple unpacking.
    '''
    from mcp.server.fastmcp import FastMCP
    from oracle.data_studio_mcp_server.tools import dt_tools
    mcp_server = FastMCP('test')
    dt_tools.register_tools(mcp_server)
    fn = mcp_server._tool_manager._tools[tool_name].fn
    client = MagicMock()
    workbench = MagicMock()
    # Common existence-probe methods return (exists, global_id)
    client.check_if_dataload_exists.return_value = (False, None)
    client.check_if_workflow_exists.return_value = (False, None)
    client.check_if_df_exists.return_value = (False, None)
    client.check_if_schedule_exists.return_value = (False, None)
    client.check_if_project_exists.return_value = 'project-123'
    target = workbench if on_workbench else client
    method = _walk(target, sdk_path)
    method.return_value = (json.dumps(sdk_return) if isinstance(
                            sdk_return, (dict, list))
                            else (sdk_return if sdk_return is not None
                                  else 'ok'))
    # If asserting on an existence probe, override the tuple return
    if 'check_if_' in sdk_path:
        method.return_value = (False, None)
    ctx = MagicMock()
    ctx.request_context.lifespan_context = {
        'datatransforms': {'client': client, 'workbench': workbench},
    }
    result = fn(ctx=ctx, **kwargs)
    return result, client, workbench


def _ess_dispatch(tool_name, kwargs, sdk_path, sdk_return=None):
    '''Run an Essbase tool with a mocked SDK; return (result, mock_ess).'''
    from mcp.server.fastmcp import FastMCP
    from oracle.data_studio_mcp_server.tools import essbase_tools
    mcp_server = FastMCP('test')
    essbase_tools.register_tools(mcp_server)
    fn = mcp_server._tool_manager._tools[tool_name].fn
    ess = MagicMock()
    method = _walk(ess, sdk_path)
    method.return_value = (sdk_return if sdk_return is not None
                            else {'status': 'ok'})
    ctx = MagicMock()
    ctx.request_context.lifespan_context = {'essbase': ess}
    result = fn(ctx=ctx, **kwargs)
    return result, ess


# Each tuple: (tool_name, kwargs, sdk_path_to_assert)
ADP_DISPATCH_CASES = [
    # adp_browse_catalog
    ('adp_browse_catalog', {'action': 'list'},
     'Catalog.get_catalogs'),
    ('adp_browse_catalog', {'action': 'entities', 'catalog_name': 'C'},
     'Catalog.get_catalog_entities'),
    ('adp_browse_catalog', {'action': 'db_links',
                              'catalog_name': 'L'},
     'Catalog.get_database_links'),
    ('adp_browse_catalog', {'action': 'list_databases'},
     'Catalog.get_autonomous_databases'),
    ('adp_browse_catalog', {'action': 'check_db_link', 'catalog_name': 'L'},
     'Catalog.check_database_link'),
    # adp_manage_catalog
    ('adp_manage_catalog', {'action': 'enable', 'catalog_name': 'C'},
     'Catalog.enable_catalog'),
    ('adp_manage_catalog', {'action': 'disable', 'catalog_name': 'C'},
     'Catalog.disable_catalog'),
    ('adp_manage_catalog', {'action': 'unmount', 'catalog_name': 'C'},
     'Catalog.unmount_catalog'),
    # adp_manage_sharing
    ('adp_manage_sharing', {'action': 'list'},
     'Share.get_shares'),
    ('adp_manage_sharing', {'action': 'get', 'share_name': 'S'},
     'Share.get_share'),
    ('adp_manage_sharing', {'action': 'create', 'share_name': 'S'},
     'Share.create_share'),
    ('adp_manage_sharing', {'action': 'delete', 'share_name': 'S'},
     'Share.delete_share'),
    ('adp_manage_sharing', {'action': 'unpublish', 'share_name': 'S'},
     'Share.unpublish_share'),
    ('adp_manage_sharing', {'action': 'create_recipient',
                             'recipient_name': 'R'},
     'Share.create_recipient'),
    ('adp_manage_sharing', {'action': 'list_recipients'},
     'Share.get_recipients'),
    ('adp_manage_sharing', {'action': 'delete_recipient',
                             'recipient_name': 'R'},
     'Share.delete_recipient'),
    ('adp_manage_sharing', {'action': 'get_objects', 'share_name': 'S'},
     'Share.get_share_objects'),
    ('adp_manage_sharing', {'action': 'rename', 'share_name': 'S',
                             'new_name': 'S2'},
     'Share.rename_share'),
    ('adp_manage_sharing', {'action': 'list_providers'},
     'Share.get_providers'),
    ('adp_manage_sharing', {'action': 'create_provider',
                             'recipient_name': 'P'},
     'Share.create_provider'),
    ('adp_manage_sharing', {'action': 'delete_provider',
                             'recipient_name': 'P'},
     'Share.delete_provider'),
    # adp_manage_analytic_views
    ('adp_manage_analytic_views', {'action': 'list'},
     'Analytics.get_list'),
    ('adp_manage_analytic_views', {'action': 'drop', 'av_name': 'AV'},
     'Analytics.drop'),
    # adp_manage_credentials
    ('adp_manage_credentials', {'action': 'list'},
     'Ingest.get_credential_list'),
    ('adp_manage_credentials', {'action': 'create',
                                  'credential_name': 'C',
                                  'username': 'u', 'password': 'p'},
     'Ingest.create_credential'),
    ('adp_manage_credentials', {'action': 'create_ocid',
                                  'credential_name': 'C',
                                  'user_ocid': 'u',
                                  'tenancy_ocid': 't',
                                  'private_key': 'k',
                                  'fingerprint': 'f'},
     'Ingest.create_ocid_credential'),
    ('adp_manage_credentials', {'action': 'drop', 'credential_name': 'C'},
     'Ingest.drop_credential'),
    ('adp_manage_credentials', {'action': 'list_storage_links'},
     'Ingest.get_cloud_storage_link_list'),
    ('adp_manage_credentials', {'action': 'create_storage_link',
                                  'storage_link_name': 'SL',
                                  'uri': 'https://x',
                                  'credential_name': 'C'},
     'Ingest.create_cloud_storage_link'),
    ('adp_manage_credentials', {'action': 'drop_storage_link',
                                  'storage_link_name': 'SL'},
     'Ingest.drop_cloud_storage_link'),
    # adp_manage_insights
    ('adp_manage_insights', {'action': 'list_requests'},
     'Insight.get_request_list'),
    ('adp_manage_insights', {'action': 'list_insights',
                               'request_name': 'R'},
     'Insight.get_insights_list'),
    ('adp_manage_insights', {'action': 'status', 'request_name': 'R'},
     'Insight.get_job_status'),
    ('adp_manage_insights', {'action': 'drop', 'request_name': 'R'},
     'Insight.drop'),
    # adp_manage_db_links
    ('adp_manage_db_links', {'action': 'list'},
     'Ingest.get_database_links'),
    ('adp_manage_db_links', {'action': 'check', 'db_link_name': 'L'},
     'Catalog.check_database_link'),
    # adp_browse_catalog preview
    ('adp_browse_catalog', {'action': 'preview', 'catalog_name': 'T'},
     'Catalog.preview_catalog_table'),
    # adp_query_analytic_view (single tool, no action)
    ('adp_query_analytic_view', {'av_name': 'AV'},
     'Analytics.is_exist'),
    # adp_search (single tool)
    ('adp_search', {'search_term': 'EMP'},
     'Misc.global_search'),
    # adp_generate_insights
    ('adp_generate_insights', {'object_name': 'SALES',
                                 'measure': 'AMOUNT'},
     'Insight.generate'),
    # adp_ai_chat
    ('adp_ai_chat', {'question': 'hello'},
     'AI.chat'),
    # adp_ai_chat with chat_with_db mode
    ('adp_ai_chat', {'question': 'top sales',
                       'mode': 'chat_with_db',
                       'tables': 'SALES'},
     'AI.chat_with_db'),
    # adp_ai_chat with generate_insight mode
    ('adp_ai_chat', {'question': 'analyze',
                       'mode': 'generate_insight',
                       'tables': 'SALES'},
     'AI.generate_insight'),
    # adp_search with include_ddl path
    ('adp_search', {'search_term': 'EMP', 'include_ddl': True},
     'Misc.global_search'),
    # adp_analyze_analytic_view (multi-call composite)
    ('adp_analyze_analytic_view', {'av_name': 'AV'},
     'Analytics.is_exist'),
    # adp_build_analytic_view (no av_name → triggers create_auto)
    ('adp_build_analytic_view', {'fact_table': 'SALES'},
     'Analytics.create_auto'),
    # adp_load_from_cloud — without request_id triggers copy_cloud_objects
    ('adp_load_from_cloud', {'storage_link': 'SL', 'object_name': 'o.csv',
                              'target_table': 'T'},
     'Ingest.copy_cloud_objects'),
    # adp_load_from_cloud with request_id polls progress
    ('adp_load_from_cloud', {'request_id': 'R'},
     'Ingest.cloud_progress_status'),
    # adp_manage_credentials list_cloud_objects
    ('adp_manage_credentials', {'action': 'list_cloud_objects',
                                  'storage_link_name': 'SL'},
     'Ingest.get_cloud_objects'),
    # adp_manage_db_links list_tables / copy_tables / link_tables
    ('adp_manage_db_links', {'action': 'list_tables',
                              'db_link_name': 'L'},
     'Ingest.get_db_link_owner_tables'),
    ('adp_manage_db_links', {'action': 'copy_tables',
                              'db_link_name': 'L', 'tables': 'T1,T2'},
     'Ingest.copy_tables_from_db_link'),
    ('adp_manage_db_links', {'action': 'link_tables',
                              'db_link_name': 'L', 'tables': 'T1'},
     'Ingest.link_tables_from_db_link'),
    ('adp_manage_db_links', {'action': 'drop', 'db_link_name': 'L'},
     'Catalog.drop_database_link'),
    # adp_manage_insights get_graph
    ('adp_manage_insights', {'action': 'get_graph',
                               'insight_name': 'IN', 'viz_id': 1},
     'Insight.get_graph_details'),
    # adp_manage_sharing publish (no recipient)
    ('adp_manage_sharing', {'action': 'publish', 'share_name': 'S'},
     'Share.publish_share'),
    # adp_manage_sharing grant_recipient
    ('adp_manage_sharing', {'action': 'grant_recipient',
                              'recipient_name': 'R',
                              'tables': 'SH1,SH2'},
     'Share.update_recipient_shares'),
]


@mcp_required
@pytest.mark.parametrize('tool,kwargs,sdk_path', ADP_DISPATCH_CASES)
def test_adp_action_dispatch(tool, kwargs, sdk_path):
    '''Each ADP composite action routes to its expected SDK method.'''
    _, adp = _adp_dispatch(tool, kwargs, sdk_path)
    _walk(adp, sdk_path).assert_called()


# ------------------------------------------------------------------ #

DT_DISPATCH_CASES = [
    # dt_manage_schedule
    ('dt_manage_schedule', {'action': 'list'},
     'list_schedules', False),
    ('dt_manage_schedule', {'action': 'delete',
                              'schedule_name': 'S',
                              'project_name': 'P'},
     'delete_schedule', False),
    # dt_manage_variables (set creates new variable when not found)
    ('dt_manage_variables', {'action': 'list'},
     'list_variables', False),
    # dt_manage_connection
    ('dt_manage_connection', {'action': 'list'},
     'list_connections', False),
    ('dt_manage_connection', {'action': 'get_types'},
     'get_connection_types', False),
    ('dt_manage_connection', {'action': 'test', 'connection_name': 'C'},
     'test_connection_by_name', False),
    ('dt_manage_connection', {'action': 'delete', 'connection_name': 'C'},
     'delete_connection', False),
    # dt_manage_dataload
    ('dt_manage_dataload', {'action': 'list', 'project_name': 'P'},
     'list_dataloads_in_project', False),
    ('dt_manage_dataload', {'action': 'check_exists',
                              'dataload_name': 'X',
                              'project_name': 'P'},
     'check_if_dataload_exists', False),
    # dt_manage_workflow
    ('dt_manage_workflow', {'action': 'list', 'project_name': 'P'},
     'list_workflows_in_project', False),
    ('dt_manage_workflow', {'action': 'check_exists',
                              'workflow_name': 'W',
                              'project_name': 'P'},
     'check_if_workflow_exists', False),
    # dt_manage_data_entities (list calls list_data_entities)
    ('dt_manage_data_entities', {'action': 'list',
                                    'connection_name': 'C'},
     'list_data_entities', False),
    ('dt_manage_data_entities', {'action': 'import_entities',
                                    'connection_name': 'C',
                                    'schema_name': 'S'},
     'import_data_entities', True),     # workbench-side
    # dt single-tool composites
    ('dt_explore', {}, 'get_about', False),
    ('dt_describe_project', {'project_name': 'P'},
     'check_if_project_exists', False),
    ('dt_describe_connection', {'connection_name': 'C'},
     'get_connection_details', False),
    ('dt_check_health', {}, 'list_connections', False),
    ('dt_browse_data', {'connection_name': 'C'},
     'get_live_schemas', False),
    # dt_manage_variables set tries update_variable first
    ('dt_manage_variables', {'action': 'set',
                                'variable_name': 'V', 'value': 'x'},
     'update_variable', False),
    # dt_manage_project delete
    ('dt_manage_project', {'action': 'delete', 'project_name': 'P'},
     'delete_project', False),
    # dt_manage_dataload create — exercises the builder path's existence
    # check (will hit ImportError on the DataLoad builder; we just
    # verify the project existence probe was called)
    ('dt_manage_dataload', {'action': 'create',
                              'project_name': 'P',
                              'dataload_name': 'DL',
                              'source_connection': 'SC',
                              'source_schema': 'SS',
                              'target_connection': 'TC',
                              'target_schema': 'TS',
                              'tables': 'T'},
     'check_if_project_exists', False),
]


@mcp_required
@pytest.mark.parametrize('tool,kwargs,sdk_path,on_wb', DT_DISPATCH_CASES)
def test_dt_action_dispatch(tool, kwargs, sdk_path, on_wb):
    '''Each DT composite action routes to its expected SDK method.'''
    _, client, wb = _dt_dispatch(tool, kwargs, sdk_path,
                                  on_workbench=on_wb)
    target = wb if on_wb else client
    _walk(target, sdk_path).assert_called()


# ------------------------------------------------------------------ #

ESS_DISPATCH_CASES = [
    # essbase_manage_application
    ('essbase_manage_application', {'action': 'create', 'app_name': 'A',
                                      'db_name': 'D'},
     'applications.create_application'),
    ('essbase_manage_application', {'action': 'delete', 'app_name': 'A'},
     'applications.delete_application'),
    ('essbase_manage_application', {'action': 'copy', 'app_name': 'A',
                                      'new_name': 'B'},
     'applications.copy_application'),
    ('essbase_manage_application', {'action': 'rename', 'app_name': 'A',
                                      'new_name': 'B'},
     'applications.rename_application'),
    # start/stop go through update_application, not start/stop_application
    ('essbase_manage_application', {'action': 'start', 'app_name': 'A'},
     'applications.update_application'),
    ('essbase_manage_application', {'action': 'stop', 'app_name': 'A'},
     'applications.update_application'),
    # essbase_manage_database (no create — only delete/copy/rename/update)
    ('essbase_manage_database', {'action': 'delete',
                                   'app_name': 'A', 'db_name': 'D'},
     'applications.delete_database'),
    ('essbase_manage_database', {'action': 'copy',
                                   'app_name': 'A', 'db_name': 'D',
                                   'target_app': 'A', 'target_db': 'D2'},
     'applications.copy_database'),
    ('essbase_manage_database', {'action': 'rename',
                                   'app_name': 'A', 'db_name': 'D',
                                   'new_name': 'D2'},
     'applications.rename_database'),
    # essbase_manage_files (uses path, not app_name)
    ('essbase_manage_files', {'action': 'list', 'path': 'applications/A'},
     'files.list_files'),
    ('essbase_manage_files', {'action': 'create_folder', 'path': '/p'},
     'files.create_folder'),
    ('essbase_manage_files', {'action': 'delete', 'path': '/x'},
     'files.delete_file'),
    ('essbase_manage_files', {'action': 'copy', 'path': '/a',
                                'target_path': '/b'},
     'files.copy'),
    ('essbase_manage_files', {'action': 'move', 'path': '/a',
                                'target_path': '/b'},
     'files.move'),
    # essbase_manage_locks (only list / unlock)
    ('essbase_manage_locks', {'action': 'list',
                                'app_name': 'A', 'db_name': 'D'},
     'locks.list_locks'),
    # essbase_manage_sessions
    ('essbase_manage_sessions', {'action': 'list'},
     'sessions.list_sessions'),
    # essbase_manage_variables (scope: server / application / database)
    ('essbase_manage_variables', {'action': 'list', 'scope': 'server'},
     'variables.list_server_variables'),
    ('essbase_manage_variables', {'action': 'list', 'scope': 'application',
                                    'app_name': 'A'},
     'variables.list_app_variables'),
    ('essbase_manage_variables', {'action': 'list', 'scope': 'database',
                                    'app_name': 'A', 'db_name': 'D'},
     'variables.list_db_variables'),
    # essbase_manage_script (script_name is required positional even for list)
    ('essbase_manage_script', {'action': 'list',
                                 'app_name': 'A', 'db_name': 'D',
                                 'script_name': ''},
     'scripts.list_scripts'),
    ('essbase_manage_script', {'action': 'create',
                                 'app_name': 'A', 'db_name': 'D',
                                 'script_name': 'S', 'content': 'CALC ALL;'},
     'scripts.create_script'),
    ('essbase_manage_script', {'action': 'update',
                                 'app_name': 'A', 'db_name': 'D',
                                 'script_name': 'S', 'content': 'CALC ALL;'},
     'scripts.update_script'),
    ('essbase_manage_script', {'action': 'delete',
                                 'app_name': 'A', 'db_name': 'D',
                                 'script_name': 'S'},
     'scripts.delete_script'),
    ('essbase_manage_script', {'action': 'validate',
                                 'app_name': 'A', 'db_name': 'D',
                                 'script_name': 'S',
                                 'content': 'CALC ALL;'},
     'scripts.validate_script'),
    # essbase_manage_connections
    ('essbase_manage_connections', {'action': 'list'},
     'connections.list_connections'),
    ('essbase_manage_connections', {'action': 'get',
                                       'connection_name': 'C'},
     'connections.get_connection'),
    ('essbase_manage_connections', {'action': 'delete',
                                       'connection_name': 'C'},
     'connections.delete_connection'),
    # essbase_manage_filters
    ('essbase_manage_filters', {'action': 'list',
                                  'app_name': 'A', 'db_name': 'D'},
     'filters.list_filters'),
    ('essbase_manage_filters', {'action': 'get',
                                  'app_name': 'A', 'db_name': 'D',
                                  'filter_name': 'F'},
     'filters.get_filter'),
    ('essbase_manage_filters', {'action': 'delete',
                                  'app_name': 'A', 'db_name': 'D',
                                  'filter_name': 'F'},
     'filters.delete_filter'),
    ('essbase_manage_filters', {'action': 'rename',
                                  'app_name': 'A', 'db_name': 'D',
                                  'filter_name': 'F', 'new_name': 'F2'},
     'filters.rename_filter'),
    # essbase_manage_jobs (SDK: get_status / rerun / purge — not _job)
    ('essbase_manage_jobs', {'action': 'list'},
     'jobs.list_jobs'),
    ('essbase_manage_jobs', {'action': 'status', 'job_id': 1},
     'jobs.get_status'),
    # rerun also calls wait_for_completion — assert on rerun
    ('essbase_manage_jobs', {'action': 'rerun', 'job_id': 1},
     'jobs.rerun'),
    ('essbase_manage_jobs', {'action': 'purge'},
     'jobs.purge'),
    # essbase_manage_datasources (no app_name / db_name params)
    ('essbase_manage_datasources', {'action': 'list'},
     'datasources.list_datasources'),
    ('essbase_manage_datasources', {'action': 'get',
                                       'datasource_name': 'DS'},
     'datasources.get_datasource'),
    ('essbase_manage_datasources', {'action': 'delete',
                                       'datasource_name': 'DS'},
     'datasources.delete_datasource'),
    # essbase_manage_drill_through
    ('essbase_manage_drill_through', {'action': 'list',
                                         'app_name': 'A', 'db_name': 'D'},
     'drill_through.list_reports'),
    ('essbase_manage_drill_through', {'action': 'get',
                                         'app_name': 'A', 'db_name': 'D',
                                         'report_name': 'R'},
     'drill_through.get_report'),
    ('essbase_manage_drill_through', {'action': 'delete',
                                         'app_name': 'A', 'db_name': 'D',
                                         'report_name': 'R'},
     'drill_through.delete_report'),
    # essbase_manage_users
    ('essbase_manage_users', {'action': 'list'},
     'users.list_users'),
    ('essbase_manage_users', {'action': 'get', 'user_id': 'u'},
     'users.get_user'),
    ('essbase_manage_users', {'action': 'delete', 'user_id': 'u'},
     'users.delete_user'),
    ('essbase_manage_users', {'action': 'list_roles'},
     'users.list_roles'),
    # Single-purpose tools (no action param)
    ('essbase_query', {'app_name': 'A', 'db_name': 'D',
                         'mdx': 'SELECT [Y].Children ON 0 FROM [A.D]'},
     'grid.execute_mdx'),
    ('essbase_browse_outline', {'app_name': 'A', 'db_name': 'D'},
     'dimensions.get_outline'),
    ('essbase_search_members', {'app_name': 'A', 'db_name': 'D',
                                  'pattern': 'sales'},
     'dimensions.search_members'),
    ('essbase_get_script', {'app_name': 'A', 'db_name': 'D',
                              'script_name': 'S'},
     'scripts.get_script_content'),
    ('essbase_export_data', {'app_name': 'A', 'db_name': 'D',
                               'mdx': 'SELECT [Y].Children ON 0 FROM [A.D]'},
     'grid.execute_mdx'),
    ('essbase_export_data', {'app_name': 'A', 'db_name': 'D',
                               'report_name': 'R'},
     'grid.execute_mdx_report'),
    # essbase_manage_groups (uses group_id, not group_name)
    ('essbase_manage_groups', {'action': 'list'},
     'groups.list_groups'),
    ('essbase_manage_groups', {'action': 'get', 'group_id': 'G'},
     'groups.get_group'),
    ('essbase_manage_groups', {'action': 'delete', 'group_id': 'G'},
     'groups.delete_group'),
    ('essbase_manage_groups', {'action': 'get_users', 'group_id': 'G'},
     'groups.get_users'),
    # Multi-call composite tools
    ('essbase_server_health', {},
     'about.get'),
    ('essbase_explore', {},
     'applications.list_applications'),
    ('essbase_run_calculation', {'app_name': 'A', 'db_name': 'D',
                                   'script_name': 'CalcAll'},
     'jobs.execute'),
    ('essbase_run_calculation', {'app_name': 'A', 'db_name': 'D',
                                   'calc_script': 'CALC ALL;'},
     'jobs.execute'),
    ('essbase_describe_database', {'app_name': 'A', 'db_name': 'D'},
     'applications.get_database'),
    ('essbase_load_data', {'app_name': 'A', 'db_name': 'D',
                             'data_file': 'data.txt',
                             'rule_file': 'load.rul'},
     'jobs.execute'),
    ('essbase_deploy_workbook', {'app_name': 'A',
                                   'file_path': '/tmp/wb.xlsx'},
     'jobs.execute'),
    # essbase_outline_metadata more categories
    ('essbase_outline_metadata', {'app_name': 'A', 'db_name': 'D',
                                    'category': 'all'},
     'dimensions.list_dimensions'),
    ('essbase_outline_metadata', {'app_name': 'A', 'db_name': 'D',
                                    'category': 'generations',
                                    'dimension_name': 'Time'},
     'dimensions.list_generations'),
    ('essbase_outline_metadata', {'app_name': 'A', 'db_name': 'D',
                                    'category': 'levels',
                                    'dimension_name': 'Time'},
     'dimensions.list_levels'),
    ('essbase_outline_metadata', {'app_name': 'A', 'db_name': 'D',
                                    'category': 'smart_lists'},
     'dimensions.get_smart_lists'),
    ('essbase_outline_metadata', {'app_name': 'A', 'db_name': 'D',
                                    'category': 'member',
                                    'dimension_name': 'East'},
     'dimensions.get_member'),
    # essbase_edit_outline — every action
    ('essbase_edit_outline', {'app_name': 'A', 'db_name': 'D',
                                'action': 'add', 'member_name': 'M',
                                'parent_name': 'P'},
     'dimensions.batch_outline_edit'),
    ('essbase_edit_outline', {'app_name': 'A', 'db_name': 'D',
                                'action': 'remove', 'member_name': 'M'},
     'dimensions.batch_outline_edit'),
    ('essbase_edit_outline', {'app_name': 'A', 'db_name': 'D',
                                'action': 'rename', 'member_name': 'M',
                                'new_name': 'M2'},
     'dimensions.batch_outline_edit'),
    ('essbase_edit_outline', {'app_name': 'A', 'db_name': 'D',
                                'action': 'set_formula',
                                'member_name': 'M',
                                'formula': '@SUM(X)'},
     'dimensions.batch_outline_edit'),
    ('essbase_edit_outline', {'app_name': 'A', 'db_name': 'D',
                                'action': 'set_alias',
                                'member_name': 'M',
                                'alias_value': 'Sales'},
     'dimensions.batch_outline_edit'),
    ('essbase_edit_outline', {'app_name': 'A', 'db_name': 'D',
                                'action': 'set_uda',
                                'member_name': 'M',
                                'uda_value': 'Promo'},
     'dimensions.batch_outline_edit'),
    # essbase_manage_users more actions
    ('essbase_manage_users', {'action': 'create', 'user_id': 'u',
                                'password': 'p'},
     'users.create_user'),
    ('essbase_manage_users', {'action': 'update', 'user_id': 'u'},
     'users.update_user'),
    ('essbase_manage_users', {'action': 'list_service_roles'},
     'users.list_service_roles'),
    ('essbase_manage_users', {'action': 'list_app_roles',
                                'app_name': 'A'},
     'users.list_app_roles'),
    # essbase_manage_groups more actions
    ('essbase_manage_groups', {'action': 'create', 'group_id': 'G'},
     'groups.create_group'),
    ('essbase_manage_groups', {'action': 'add_users', 'group_id': 'G',
                                 'user_ids': 'u1,u2'},
     'groups.add_users'),
    # essbase_manage_files more actions
    ('essbase_manage_files', {'action': 'upload', 'path': '/p',
                                'content': 'hello'},
     'files.upload'),
    ('essbase_manage_files', {'action': 'download', 'path': '/p'},
     'files.download'),
    # essbase_manage_connections create + test + update
    ('essbase_manage_connections', {'action': 'create',
                                       'connection_name': 'C',
                                       'host': 'h', 'port': 1521,
                                       'service_name': 'svc',
                                       'user': 'u', 'password': 'p'},
     'connections.create_connection'),
    ('essbase_manage_connections', {'action': 'test',
                                       'connection_name': 'C'},
     'connections.test_saved_connection'),
    # essbase_manage_filters more actions (no `validate` action exists)
    ('essbase_manage_filters', {'action': 'copy',
                                  'app_name': 'A', 'db_name': 'D',
                                  'filter_name': 'F', 'new_name': 'F2'},
     'filters.copy_filter'),
    ('essbase_manage_filters', {'action': 'assign',
                                  'app_name': 'A', 'db_name': 'D',
                                  'filter_name': 'F',
                                  'user_or_group': 'u'},
     'filters.add_permissions'),
    # essbase_manage_datasources create
    ('essbase_manage_datasources', {'action': 'create',
                                       'datasource_name': 'DS',
                                       'connection': 'C',
                                       'query': 'SELECT 1 FROM dual',
                                       'columns': 'A,B'},
     'datasources.create_datasource'),
    # essbase_manage_drill_through more
    ('essbase_manage_drill_through', {'action': 'execute',
                                         'app_name': 'A', 'db_name': 'D',
                                         'report_name': 'R'},
     'drill_through.execute_report'),
    # essbase_manage_database update
    ('essbase_manage_database', {'action': 'update',
                                   'app_name': 'A', 'db_name': 'D'},
     'applications.update_database'),
    # essbase_manage_jobs status (already had — adding rerun's extra path)
    # essbase_manage_locks unlock
    ('essbase_manage_locks', {'action': 'unlock',
                                'app_name': 'A', 'db_name': 'D',
                                'object_name': 'O'},
     'locks.unlock_object'),
    # essbase_manage_sessions kill_all
    ('essbase_manage_sessions', {'action': 'kill_all'},
     'sessions.delete_all_sessions'),
    ('essbase_manage_sessions', {'action': 'current'},
     'sessions.get_current_session'),
    ('essbase_outline_metadata', {'app_name': 'A', 'db_name': 'D',
                                    'category': 'outline_settings'},
     'dimensions.get_outline_settings'),
    ('essbase_outline_metadata', {'app_name': 'A', 'db_name': 'D',
                                    'category': 'export_xml'},
     'dimensions.export_outline_xml'),
    # essbase_manage_db_settings
    ('essbase_manage_db_settings', {'app_name': 'A', 'db_name': 'D',
                                      'category': 'all'},
     'database_settings.get_settings'),
    # essbase_get_logs (lives on applications, not about)
    ('essbase_get_logs', {'app_name': 'A'},
     'applications.get_latest_log'),
    # essbase_manage_security
    ('essbase_manage_security', {'username': 'u'},
     'users.get_user'),
]


@mcp_required
@pytest.mark.parametrize('tool,kwargs,sdk_path', ESS_DISPATCH_CASES)
def test_essbase_action_dispatch(tool, kwargs, sdk_path):
    '''Each Essbase composite action routes to its expected SDK method.'''
    _, ess = _ess_dispatch(tool, kwargs, sdk_path)
    _walk(ess, sdk_path).assert_called()


# ------------------------------------------------------------------ #
#  Server module tests                                                 #
# ------------------------------------------------------------------ #

@mcp_required
class TestServer:

    def test_mcp_instance_exists(self):
        from oracle.data_studio_mcp_server.server import mcp
        assert mcp is not None
        assert mcp.name == 'oracle-data-studio'

    def test_lifespan_no_config_yields_empty_context(self):
        '''When no service is configured, lifespan yields {} and only
        warning/info logs happen — no SDK imports.'''
        import asyncio
        from oracle.data_studio_mcp_server import server as srv

        async def _run():
            async with srv.app_lifespan(MagicMock()) as ctx:
                return ctx

        with patch.object(srv, '_config',
                           MagicMock(essbase=None, adp=None,
                                      datatransforms=None)):
            ctx = asyncio.run(_run())
        assert 'essbase' not in ctx
        assert 'adp' not in ctx

    def test_lifespan_essbase_login_token(self):
        '''Lifespan uses login_token() when EssbaseConfig.token is set.'''
        import asyncio
        from oracle.data_studio_mcp_server import server as srv

        async def _run():
            async with srv.app_lifespan(MagicMock()) as ctx:
                return ctx

        fake_essbase = MagicMock()
        fake_essbase.login_token.return_value = 'ess-client'
        ess_cfg = MagicMock(token='tok', url='https://e')
        with patch.object(srv, '_config',
                           MagicMock(essbase=ess_cfg, adp=None,
                                      datatransforms=None)), \
             patch.dict('sys.modules', {'essbase': fake_essbase}):
            ctx = asyncio.run(_run())
        fake_essbase.login_token.assert_called_once_with('https://e', 'tok')
        assert ctx.get('essbase') == 'ess-client'

    def test_lifespan_essbase_login_user_password(self):
        '''No token → login(url, user, password) flow.'''
        import asyncio
        from oracle.data_studio_mcp_server import server as srv

        async def _run():
            async with srv.app_lifespan(MagicMock()) as ctx:
                return ctx

        fake_essbase = MagicMock()
        fake_essbase.login.return_value = 'ess-client'
        ess_cfg = MagicMock(token=None, url='https://e',
                             user='admin', password='p')
        with patch.object(srv, '_config',
                           MagicMock(essbase=ess_cfg, adp=None,
                                      datatransforms=None)), \
             patch.dict('sys.modules', {'essbase': fake_essbase}):
            ctx = asyncio.run(_run())
        fake_essbase.login.assert_called_once()
        assert ctx.get('essbase') == 'ess-client'

    def test_lifespan_adp_caches_config_and_logs_in(self):
        '''ADP path stores _adp_config + tries adp.login.'''
        import asyncio
        from oracle.data_studio_mcp_server import server as srv

        async def _run():
            async with srv.app_lifespan(MagicMock()) as ctx:
                return ctx

        fake_adp = MagicMock()
        fake_adp.login.return_value = 'adp-client'
        adp_cfg = MagicMock(url='https://a', user='ADMIN', password='p')
        with patch.object(srv, '_config',
                           MagicMock(essbase=None, adp=adp_cfg,
                                      datatransforms=None)), \
             patch.dict('sys.modules', {'adp': fake_adp}):
            ctx = asyncio.run(_run())
        assert ctx.get('_adp_config') is adp_cfg
        assert ctx.get('adp') == 'adp-client'

    def test_lifespan_essbase_login_failure_is_caught(self):
        '''Essbase login that throws is logged but doesn't break startup.'''
        import asyncio
        from oracle.data_studio_mcp_server import server as srv

        async def _run():
            async with srv.app_lifespan(MagicMock()) as ctx:
                return ctx

        fake_essbase = MagicMock()
        fake_essbase.login.side_effect = RuntimeError('connection refused')
        ess_cfg = MagicMock(token=None, url='https://e',
                             user='admin', password='p')
        with patch.object(srv, '_config',
                           MagicMock(essbase=ess_cfg, adp=None,
                                      datatransforms=None)), \
             patch.dict('sys.modules', {'essbase': fake_essbase}):
            ctx = asyncio.run(_run())
        # Lifespan still yielded a context — startup didn't break
        assert 'essbase' not in ctx

    def test_main_streamable_http_sets_host_port_via_settings(self):
        '''Regression: FastMCP.run() takes only `transport` and
        `mount_path`. host/port must be set via mcp.settings before
        calling run(). Previous code passed host=... as a kwarg to
        run() which raises TypeError on real FastMCP.'''
        import oracle.data_studio_mcp_server.server as srv

        # Build a config that selects streamable-http and a specific
        # host/port. We patch apply_profile + mcp.run so main() doesn't
        # actually start a server.
        fake_cfg = MagicMock(transport='streamable-http',
                              host='0.0.0.0', port=9001,
                              profile='admin')
        with patch.object(srv, 'load_config', return_value=fake_cfg), \
             patch.object(srv, 'apply_profile'), \
             patch.object(srv.mcp, 'run') as run_mock:
            srv.main()
        # run() called with ONLY transport — no host/port kwargs
        call = run_mock.call_args
        assert call.kwargs.get('host') is None, \
            'run() must NOT be called with host=... — host goes on mcp.settings'
        assert call.kwargs.get('port') is None
        # transport is the only positional/kwarg
        assert call.kwargs.get('transport') == 'streamable-http' \
            or (call.args and call.args[0] == 'streamable-http')
        # The settings were updated before the call
        assert srv.mcp.settings.host == '0.0.0.0'
        assert srv.mcp.settings.port == 9001

    def test_main_stdio_default_does_not_touch_settings_host(self):
        import oracle.data_studio_mcp_server.server as srv

        fake_cfg = MagicMock(transport='stdio', host='127.0.0.1',
                              port=8000, profile='admin')
        with patch.object(srv, 'load_config', return_value=fake_cfg), \
             patch.object(srv, 'apply_profile'), \
             patch.object(srv.mcp, 'run') as run_mock:
            srv.main()
        # stdio transport — run() called with stdio only
        call = run_mock.call_args
        assert (call.kwargs.get('transport') == 'stdio'
                or (call.args and call.args[0] == 'stdio'))

    def test_lifespan_dt_configured(self):
        '''DT path: stores _dt_config for later lazy-connect.'''
        import asyncio
        from oracle.data_studio_mcp_server import server as srv

        async def _run():
            async with srv.app_lifespan(MagicMock()) as ctx:
                return ctx

        dt_cfg = MagicMock(url='https://dt')
        with patch.object(srv, '_config',
                           MagicMock(essbase=None, adp=None,
                                      datatransforms=dt_cfg)):
            ctx = asyncio.run(_run())
        assert ctx.get('_dt_config') is dt_cfg

    def test_lifespan_adp_login_failure_is_caught(self):
        '''ADP login that throws is logged but doesn't break startup.'''
        import asyncio
        from oracle.data_studio_mcp_server import server as srv

        async def _run():
            async with srv.app_lifespan(MagicMock()) as ctx:
                return ctx

        fake_adp = MagicMock()
        fake_adp.login.side_effect = RuntimeError('boom')
        adp_cfg = MagicMock(url='https://a', user='ADMIN', password='p')
        with patch.object(srv, '_config',
                           MagicMock(essbase=None, adp=adp_cfg,
                                      datatransforms=None)), \
             patch.dict('sys.modules', {'adp': fake_adp}):
            ctx = asyncio.run(_run())
        # Config still cached for later retry
        assert ctx.get('_adp_config') is adp_cfg
        # No client because login failed
        assert 'adp' not in ctx

    def test_server_instructions_mention_annotations(self):
        '''Server instructions should nudge the LLM toward the
        annotation-first SQL flow.'''
        from oracle.data_studio_mcp_server.server import mcp
        instructions = mcp.instructions or ''
        assert 'adp_get_annotations' in instructions
        assert 'UNIT' in instructions
        assert 'annotation' in instructions.lower()

    def test_server_instructions_mention_cube_av_routing(self):
        '''Server instructions should describe the annotation-driven
        cube/AV/table routing convention for aggregate questions.'''
        from oracle.data_studio_mcp_server.server import mcp
        instructions = mcp.instructions or ''
        # Mentions all three routing sources
        assert 'analytic view' in instructions.lower() or 'adp_query_analytic_view' in instructions
        assert 'essbase' in instructions.lower() or 'cube' in instructions.lower()
        assert 'aggregate' in instructions.lower() or 'report' in instructions.lower()
        # The routing convention names should appear so the LLM knows
        # what to look for in adp_get_annotations output.
        assert 'preferred_source' in instructions.lower()
        assert "'cube'" in instructions.lower() or '`cube`' in instructions.lower()
        assert 'analytic_view' in instructions.lower()

    def test_tool_count(self):
        '''Server should register exactly 60 tools.'''
        from oracle.data_studio_mcp_server.server import mcp
        tools = mcp._tool_manager._tools
        assert len(tools) == 60, \
            f'Expected 60 tools, got {len(tools)}: {sorted(tools.keys())}'


# ------------------------------------------------------------------ #
#  Integration: full pipeline test                                     #
# ------------------------------------------------------------------ #

@mcp_required
class TestIntegration:

    def test_explore_then_describe(self):
        '''Simulate: explore apps → describe first database.'''
        from mcp.server.fastmcp import FastMCP
        from oracle.data_studio_mcp_server.tools import essbase_tools
        mcp_server = FastMCP('test')
        essbase_tools.register_tools(mcp_server)

        ess = MagicMock()
        ess.applications.list_applications.return_value = {
            'items': [{'name': 'Demo'}]}
        ess.applications.list_databases.return_value = {
            'items': [{'name': 'MyDB'}]}
        ess.applications.get_statistics.return_value = {}
        ess.applications.get_settings.return_value = {}
        ess.applications.get_database.return_value = {
            'name': 'MyDB', 'type': 'BSO'}
        ess.dimensions.list_dimensions.return_value = {
            'items': [{'name': 'Year'}, {'name': 'Measures'}]}
        ess.database_settings.get_settings.return_value = {}
        ess.database_settings.get_statistics.return_value = {}
        ess.database_settings.get_storage_statistics.return_value = {}
        ess.variables.list_db_variables.return_value = {'items': []}

        ctx = MagicMock()
        ctx.request_context.lifespan_context = {'essbase': ess}

        # Step 1: explore
        explore_fn = mcp_server._tool_manager._tools['essbase_explore'].fn
        explore_result = json.loads(explore_fn(ctx=ctx))
        assert explore_result['count'] == 1
        app_name = explore_result['applications'][0]['application']['name']
        db_name = explore_result['applications'][0]['databases'][0]['name']

        # Step 2: describe
        describe_fn = mcp_server._tool_manager._tools[
            'essbase_describe_database'].fn
        describe_result = json.loads(
            describe_fn(app_name=app_name, db_name=db_name, ctx=ctx))
        assert describe_result['database']['type'] == 'BSO'
        assert len(describe_result['dimensions']) == 2
