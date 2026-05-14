"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from unittest.mock import mock_open, patch

import oci

from oracle.oci_opensearch_mcp_server import client_factory


class TestClientFactory:
    @patch("oracle.oci_opensearch_mcp_server.client_factory.oci.opensearch.OpensearchClusterClient")
    @patch("oracle.oci_opensearch_mcp_server.client_factory.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_opensearch_mcp_server.client_factory.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_opensearch_mcp_server.client_factory.open",
        new_callable=mock_open,
        read_data="SECURITY_TOKEN",
    )
    @patch("oracle.oci_opensearch_mcp_server.client_factory.os.path.exists")
    @patch("oracle.oci_opensearch_mcp_server.client_factory.oci.config.from_file")
    @patch("oracle.oci_opensearch_mcp_server.client_factory.os.getenv")
    def test_get_opensearch_cluster_client_with_profile_env_uses_security_token_signer(
        self,
        mock_getenv,
        mock_from_file,
        mock_exists,
        mock_open_file,
        mock_load_private_key,
        mock_security_token_signer,
        mock_client,
    ):
        mock_getenv.side_effect = lambda k, default=None: (
            "MYPROFILE" if k == "OCI_CONFIG_PROFILE" else default
        )
        mock_exists.return_value = True
        config = {
            "key_file": "/abs/path/to/key.pem",
            "security_token_file": "/abs/path/to/token",
        }
        mock_from_file.return_value = config
        private_key_obj = object()
        mock_load_private_key.return_value = private_key_obj

        result = client_factory.get_opensearch_cluster_client()

        mock_from_file.assert_called_once_with(
            file_location=oci.config.DEFAULT_LOCATION,
            profile_name="MYPROFILE",
        )
        mock_open_file.assert_called_once_with("/abs/path/to/token", "r", encoding="utf-8")
        mock_security_token_signer.assert_called_once_with("SECURITY_TOKEN", private_key_obj)
        args, kwargs = mock_client.call_args
        passed_config = args[0]
        assert passed_config is config
        assert passed_config["additional_user_agent"].startswith("oci-opensearch-mcp/")
        assert kwargs["signer"] == mock_security_token_signer.return_value
        assert result == mock_client.return_value

    @patch("oracle.oci_opensearch_mcp_server.client_factory.oci.signer.Signer")
    @patch("oracle.oci_opensearch_mcp_server.client_factory.os.path.exists")
    @patch("oracle.oci_opensearch_mcp_server.client_factory.oci.signer.load_private_key_from_file")
    def test_build_signer_without_token_file_uses_api_key_signer(
        self, mock_load_private_key, mock_exists, mock_signer
    ):
        mock_exists.return_value = False
        mock_load_private_key.return_value = object()
        config = {
            "tenancy": "ocid1.tenancy.oc1..tenant1",
            "user": "ocid1.user.oc1..user1",
            "fingerprint": "fingerprint",
            "key_file": "/abs/path/to/key.pem",
        }

        signer = client_factory.build_signer(config)

        mock_signer.assert_called_once_with(
            tenancy="ocid1.tenancy.oc1..tenant1",
            user="ocid1.user.oc1..user1",
            fingerprint="fingerprint",
            private_key_file_location="/abs/path/to/key.pem",
            pass_phrase=None,
        )
        assert signer == mock_signer.return_value

    @patch("oracle.oci_opensearch_mcp_server.client_factory.oci.signer.Signer")
    @patch("oracle.oci_opensearch_mcp_server.client_factory.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_opensearch_mcp_server.client_factory.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_opensearch_mcp_server.client_factory.open",
        new_callable=mock_open,
        read_data="\n",
    )
    @patch("oracle.oci_opensearch_mcp_server.client_factory.os.path.exists")
    def test_build_signer_with_empty_token_file_falls_back_without_loading_private_key_for_token(
        self,
        mock_exists,
        mock_open_file,
        mock_load_private_key,
        mock_security_token_signer,
        mock_signer,
    ):
        mock_exists.return_value = True
        config = {
            "tenancy": "ocid1.tenancy.oc1..tenant1",
            "user": "ocid1.user.oc1..user1",
            "fingerprint": "fingerprint",
            "key_file": "/abs/path/to/key.pem",
            "security_token_file": "/abs/path/to/token",
        }

        signer = client_factory.build_signer(config)

        mock_open_file.assert_called_once_with("/abs/path/to/token", "r", encoding="utf-8")
        mock_load_private_key.assert_not_called()
        mock_security_token_signer.assert_not_called()
        mock_signer.assert_called_once()
        assert signer == mock_signer.return_value
