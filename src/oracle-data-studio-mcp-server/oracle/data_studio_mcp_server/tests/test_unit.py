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
        assert cfg.profile == 'admin'
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
#  Server module tests                                                 #
# ------------------------------------------------------------------ #

@mcp_required
class TestServer:

    def test_mcp_instance_exists(self):
        from oracle.data_studio_mcp_server.server import mcp
        assert mcp is not None
        assert mcp.name == 'oracle-data-studio'

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
