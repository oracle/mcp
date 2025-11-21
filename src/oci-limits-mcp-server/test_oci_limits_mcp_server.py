"""
Test module for OCI Limits MCP Server

Tests the core functionality of the OCI service limits and quota policies server
"""

import json
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestOCILimitsMCPServer(unittest.TestCase):
    """Test cases for OCI Limits MCP Server"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock OCI clients to avoid requiring actual OCI configuration
        self.mock_config = {
            'tenancy': 'ocid1.tenancy.oc1..test',
            'region': 'us-ashburn-1'
        }
        
    @patch('oci.config.from_file')
    @patch('oci.identity.IdentityClient')
    @patch('oci.limits.LimitsClient')
    @patch('oci.usage_api.UsageapiClient')
    @patch('oci.monitoring.MonitoringClient')
    @patch('oci.resource_search.ResourceSearchClient')
    def test_server_initialization(self, mock_resource_search, mock_monitoring, mock_usage_api, 
                                 mock_limits_client, mock_identity_client, mock_config):
        """Test that the server initializes properly with mocked OCI clients"""
        # Mock the config
        mock_config.return_value = self.mock_config
        
        # Mock the clients
        mock_identity = Mock()
        mock_limits = Mock()
        mock_identity_client.return_value = mock_identity
        mock_limits_client.return_value = mock_limits
        mock_usage_api.return_value = Mock()
        mock_monitoring.return_value = Mock()
        mock_resource_search.return_value = Mock()
        
        # Import the module after patching
        import oci_limits_mcp_server
        
        # Verify that the module can be imported successfully
        self.assertIsNotNone(oci_limits_mcp_server)
        
    @patch('oci.config.from_file')
    @patch('oci.identity.IdentityClient')
    @patch('oci.limits.LimitsClient')
    @patch('oci.usage_api.UsageapiClient')
    @patch('oci.monitoring.MonitoringClient')
    @patch('oci.resource_search.ResourceSearchClient')
    def test_format_error_response(self, mock_resource_search, mock_monitoring, mock_usage_api, 
                                 mock_limits_client, mock_identity_client, mock_config):
        """Test error response formatting"""
        # Mock all the clients to avoid initialization errors
        mock_config.return_value = self.mock_config
        mock_identity_client.return_value = Mock()
        mock_limits_client.return_value = Mock()
        mock_usage_api.return_value = Mock()
        mock_monitoring.return_value = Mock()
        mock_resource_search.return_value = Mock()
        
        import oci_limits_mcp_server
        
        # Test format_error_response function directly
        error_msg = "Test error"
        context = {"test": "context"}
        result = oci_limits_mcp_server.format_error_response(error_msg, context)
        
        # Parse JSON response
        parsed = json.loads(result)
        self.assertEqual(parsed["error"], error_msg)
        self.assertEqual(parsed["test"], "context")

    @patch('oci.config.from_file')
    @patch('oci.identity.IdentityClient')
    @patch('oci.limits.LimitsClient')
    @patch('oci.usage_api.UsageapiClient')
    @patch('oci.monitoring.MonitoringClient')
    @patch('oci.resource_search.ResourceSearchClient')
    def test_mcp_tools_exist(self, mock_resource_search, mock_monitoring, mock_usage_api, 
                           mock_limits_client, mock_identity_client, mock_config):
        """Test that MCP tools are properly registered"""
        # Mock all the clients
        mock_config.return_value = self.mock_config
        mock_identity_client.return_value = Mock()
        mock_limits_client.return_value = Mock()
        mock_usage_api.return_value = Mock()
        mock_monitoring.return_value = Mock()
        mock_resource_search.return_value = Mock()
        
        import oci_limits_mcp_server
        
        # Check that the MCP server instance exists
        self.assertIsNotNone(oci_limits_mcp_server.mcp)
        
        # Check that tools are registered
        # This is a basic test to ensure the module loads correctly
        # The actual FastMCP testing would require more complex setup
        self.assertTrue(hasattr(oci_limits_mcp_server, 'mcp'))

    def test_client_initialization_error(self):
        """Test graceful handling of OCI client initialization errors"""
        with patch('oci.config.from_file', side_effect=Exception("Config not found")):
            # Import should not raise an exception
            import oci_limits_mcp_server
            
            # The module should still be importable
            self.assertIsNotNone(oci_limits_mcp_server)
            
            # Check that error handling works
            self.assertIsNone(oci_limits_mcp_server.identity_client)
            self.assertIsNone(oci_limits_mcp_server.limits_client)

if __name__ == '__main__':
    unittest.main()
