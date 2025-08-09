"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
"""

import unittest
import json
import sys
import os
import importlib.util
import warnings
from pathlib import Path

class TestDbtoolsMcpServer(unittest.TestCase):
    """
    Functional tests for dbtools-mcp-server.py
    
    These tests call the actual tool functions and validate their output.
    Prerequisites:
    1. A working OCI CLI setup with access to an OCI account
    2. A working Oracle connection named 'adminuseroracle' (update cls.oracle_connection if using a different name)
    3. A working MySQL connection named 'simonmysql' (update cls.mysql_connection if using a different name)
    
    Note: These tests require a valid OCI config file and access to OCI resources.
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up test class - load the dbtools-mcp-server module dynamically"""
        # Suppress the datetime.utcnow() deprecation warning from OCI SDK
        warnings.filterwarnings("ignore", category=DeprecationWarning, 
                               message="datetime.datetime.utcnow.*")
        
        # Path to the server file
        server_path = os.path.join(os.path.dirname(__file__), "dbtools-mcp-server.py")
        
        # Check if file exists
        if not os.path.exists(server_path):
            raise FileNotFoundError(f"Server file not found at {server_path}")
        
        # Load the module dynamically
        spec = importlib.util.spec_from_file_location("dbtools_mcp_server", server_path)
        cls.server_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.server_module)
        
        # Store the module for direct access to functions
        cls.module = cls.server_module
        
        # Specific connection names for testing
        cls.oracle_connection = os.getenv("ORACLE_CONNECTION_NAME", "oracleconn1")
        cls.mysql_connection = os.getenv("MYSQL_CONNECTION_NAME", "mysqlconn1")
    
    def setUp(self):
        """Set up test case - verify OCI config exists"""
        # Check if OCI config file exists
        oci_config_path = os.path.expanduser("~/.oci/config")
        self.assertTrue(os.path.exists(oci_config_path), 
                        "OCI config file not found. Tests require a valid OCI configuration.")
        
        # Print test name as a header
        print(f"\n{'=' * 70}")
        print(f"Running test: {self._testMethodName}")
        print(f"{'=' * 70}")
    
    def test_list_all_compartments(self):
        """Test listing all compartments"""
        print("About to call list_all_compartments() to list all compartments in the tenancy")
        str_result = self.module.list_all_compartments()
        
        # Verify we got a list of compartments
        self.assertIsNotNone(str_result)

        result = json.loads(str_result)
        
        # Print how many compartments we found
        print(f"Found {len(result)} compartments")
        
        # Print first few compartment names if available
        if len(result) > 0:
            print("First few compartments:")
            for i, comp in enumerate(result[:3]):
                print(f"  {i+1}. {comp['name']} (ID: {comp['id']})")
    
    def test_get_compartment_by_name(self):
        """Test getting a compartment by name"""
        # First get all compartments
        print("About to call list_all_compartments() to find a compartment name for testing")
        all_compartments_str = self.module.list_all_compartments()
        all_compartments = json.loads(all_compartments_str)
        
        # If we have any compartments, test with the first one's name
        if len(all_compartments) > 0:
            first_compartment = all_compartments[0]
            print(first_compartment)
            compartment_name = first_compartment['name']
            
            print(f"About to call get_compartment_by_name_tool('{compartment_name}')")
            # Now try to get this compartment by name
            result = json.loads(self.module.get_compartment_by_name_tool(compartment_name))
            
            # Verify we got a result
            self.assertIsNotNone(result)
            self.assertEqual(result['name'], compartment_name)
            
            print(f"Successfully retrieved compartment: {result['name']} (ID: {result['id']})")
        else:
            self.skipTest("No compartments found to test with")
    
    def test_list_all_databases(self):
        """Test listing all databases"""
        print("About to call list_all_databases() to list all databases in the tenancy")
        result = self.module.list_all_databases()
        
        # Just verify we get a result - could be empty if no databases
        self.assertIsNotNone(result)
        
        # Try to print some information about the results
        if hasattr(result, 'items') and result.items:
            print(f"Found {len(result.items)} database resources")
            # Print first few database names if available
            for i, db in enumerate(result.items[:3]):
                print(f"  {i+1}. {db.display_name} (Type: {db.resource_type})")
        else:
            print("No databases found or empty result")
    
    def test_list_all_connections(self):
        """Test listing all connections"""
        print("About to call list_all_connections() to list all database connections")
        result = self.module.list_all_connections()
        
        # Just verify we get a result - could be empty if no connections
        self.assertIsNotNone(result)
        
        # Print how many connections we found
        if isinstance(result, list):
            print(f"Found {len(result)} database connections")
            # Print first few connection names if available
            for i, conn in enumerate(result[:3]):
                if hasattr(conn, 'display_name'):
                    print(f"  {i+1}. {conn.display_name}")
                else:
                    print(f"  {i+1}. {type(conn)} (no display_name attribute)")
        else:
            print(f"Result is not a list: {type(result)}")
    
    # Tests for Oracle connection - adminuseroracle
    
    def test_oracle_connection_details(self):
        """Test getting details for the Oracle database connection"""
        connection_name = self.oracle_connection
        print(f"About to call get_dbtools_connection_by_name_tool('{connection_name}')")
        
        result = self.module.get_dbtools_connection_by_name_tool(connection_name)
        
        # Check if we got an error response (JSON string)
        if isinstance(result, str) and result.startswith('{'):
            result_dict = json.loads(result)
            if 'error' in result_dict:
                self.fail(f"Error getting connection: {result_dict['error']}")
        
        # Otherwise, we should have a connection object
        self.assertIsNotNone(result)
        
        if hasattr(result, 'display_name'):
            print(f"Found connection: {result.display_name}")
            print(f"Type: {result.type}")
            self.assertEqual(result.display_name, connection_name)
        else:
            print(f"Connection details: {result}")
    
    def test_oracle_list_tables(self):
        """Test listing tables from Oracle connection"""
        connection_name = self.oracle_connection
        print(f"About to call list_tables('{connection_name}')")
        
        # Get a list of all tables
        result = self.module.list_tables(connection_name)
        # Verify we got a result
        self.assertIsNotNone(result)
        
        # Try to parse the result as JSON if it's a string
        if isinstance(result, str):
            try:
                # Parse the result to find table names
                tables = json.loads(result)
                
                # Verify we got a list
                self.assertIsInstance(tables, list, "Result should be a JSON array")
                
                if len(tables) > 0:
                    print("Found tables:")
                    table_names = []
                    
                    # Extract and print details of first few tables
                    for i, table in enumerate(tables[:333]):
                        # Verify table has required fields
                        self.assertIn('table_name', table, "Each table should have a table_name field")
                        self.assertIn('num_rows', table, "Each table should have a num_rows field")
                        self.assertIn('comments', table, "Each table should have a comments field")
                        
                        table_name = table['table_name']
                        num_rows = table['num_rows']
                        print(f"  {i+1}. {table_name} ({num_rows} rows)")
                        table_names.append(table_name)
                    
                    # Save the table names for the get_table_info test
                    self.oracle_table_names = table_names
                else:
                    print("No tables found")
                    
            except json.JSONDecodeError:
                print(f"Could not parse result as JSON: {result[:100]}...")
                self.fail("Failed to parse JSON response")
            except Exception as e:
                print(f"Error processing tables: {str(e)}")
                self.fail(f"Error processing tables: {str(e)}")
        else:
            print(f"Received non-string result: {type(result)}")
            self.fail("Expected string result")
    
    def test_oracle_get_table_info(self):
        """Test getting schema info for a specific table from Oracle connection"""
        connection_name = self.oracle_connection
        test_table = "ALL_TABLES"
        
        print(f"\nAbout to call get_table_info('{connection_name}', '{test_table}')")
        
        # Get detailed info about this table
        table_info = self.module.get_table_info(connection_name, test_table)
        self.assertIsNotNone(table_info)
        
        # Print some details about the table
        print(f"Details for table {test_table}:")
        if isinstance(table_info, str):
            try:
                table_dict = json.loads(table_info)
                
                # Validate the structure
                self.assertIn('table_name', table_dict, "Response should have table_name")
                self.assertIn('columns', table_dict, "Response should have columns")
                self.assertIn('primary_key', table_dict, "Response should have primary_key")
                self.assertIn('row_count', table_dict, "Response should have row_count")
                
                # Print table info
                print(f"Table: {table_dict['table_name']}")
                print(f"Number of rows: {table_dict['row_count']}")
                if table_dict['primary_key']:
                    print(f"Primary key(s): {', '.join(table_dict['primary_key'])}")
                else:
                    print("Primary key(s): None")
                print("\nColumns:")
                for col in table_dict['columns']:
                    nullable = "NULL" if col['nullable'] else "NOT NULL"
                    default = f" DEFAULT {col['default']}" if col['default'] else ""
                    print(f"  - {col['name']} ({col['type']}{default}) - {nullable}")
                    if col['comment']:
                        print(f"    Comment: {col['comment']}")
                
                # Verify we have at least one column
                self.assertGreater(len(table_dict['columns']), 0, "Table should have at least one column")
                
            except json.JSONDecodeError:
                print(f"Could not parse table info: {table_info[:100]}...")
                self.fail("Failed to parse JSON response")
            except Exception as e:
                print(f"Error processing table info: {str(e)}")
                self.fail(f"Error processing table info: {str(e)}")
        else:
            print(f"Received non-string result: {type(table_info)}")
            self.fail("Expected string result")
    
    def test_oracle_execute_sql(self):
        """Test executing SQL on Oracle connection"""
        connection_name = self.oracle_connection
        test_sql = "SELECT 1 AS TEST_VALUE FROM DUAL"
        
        print(f"About to call execute_sql_tool('{connection_name}', '{test_sql}')")
        result = self.module.execute_sql_tool(connection_name, test_sql)
        
        # Verify we got a result
        self.assertIsNotNone(result)
        
        # Try to parse the result as JSON
        try:
            result_dict = json.loads(result)
            
            # Check for error
            if 'error' in result_dict:
                self.fail(f"Error executing SQL: {result_dict['error']}")
            
            # Check for expected DUAL result
            if 'items' in result_dict and len(result_dict['items']) > 0:
                print("SQL execution successful")
                print(f"Result: {result_dict['items'][0]}")
                
                # Check for TEST_VALUE = 1
                if 'TEST_VALUE' in result_dict['items'][0]:
                    self.assertEqual(result_dict['items'][0]['TEST_VALUE'], 1)
                    print("Verified TEST_VALUE = 1")
        except json.JSONDecodeError:
            print(f"Could not parse result as JSON: {result[:100]}...")
            self.fail("Failed to parse SQL execution result as JSON")
    
    # Test for MySQL HeatWave connection - simonmysql
    
    def test_mysql_connection_details(self):
        """Test getting details for the MySQL database connection"""
        connection_name = self.mysql_connection
        print(f"About to call get_dbtools_connection_by_name_tool('{connection_name}')")
        
        result = self.module.get_dbtools_connection_by_name_tool(connection_name)
        
        # Check if we got an error response (JSON string)
        if isinstance(result, str) and result.startswith('{'):
            result_dict = json.loads(result)
            if 'error' in result_dict:
                self.fail(f"Error getting connection: {result_dict['error']}")
        
        # Otherwise, we should have a connection object
        self.assertIsNotNone(result)
        
        if hasattr(result, 'display_name'):
            print(f"Found connection: {result.display_name}")
            print(f"Type: {result.type}")
            self.assertEqual(result.display_name, connection_name)
        else:
            print(f"Connection details: {result}")
    
    def test_mysql_list_tables(self):
        """Test listing tables from MySQL connection"""
        connection_name = self.mysql_connection
        
        print(f"\nAbout to call list_tables('{connection_name}')")
        
        # Get list of tables
        result = self.module.list_tables(connection_name)
        self.assertIsNotNone(result)
        
        if isinstance(result, str):
            try:
                tables = json.loads(result)
                
                # Verify we got a list
                self.assertIsInstance(tables, list, "Result should be a JSON array")
                
                if len(tables) > 0:
                    print("Found tables:")
                    table_names = []
                    
                    # Extract and print details of tables
                    for i, table in enumerate(tables):
                        # Verify table has required fields
                        self.assertIn('table_name', table, "Each table should have a table_name field")
                        self.assertIn('num_rows', table, "Each table should have a num_rows field")
                        self.assertIn('comments', table, "Each table should have a comments field")
                        
                        table_name = table['table_name']
                        num_rows = table['num_rows']
                        print(f"  {i+1}. {table_name} ({num_rows} rows)")
                        table_names.append(table_name)
                    
                    # Save the table names for the get_table_info test
                    self.mysql_table_names = table_names
                else:
                    print("No tables found")
                    
            except json.JSONDecodeError:
                print(f"Could not parse result as JSON: {result[:100]}...")
                self.fail("Failed to parse JSON response")
            except Exception as e:
                print(f"Error processing tables: {str(e)}")
                self.fail(f"Error processing tables: {str(e)}")
        else:
            print(f"Received non-string result: {type(result)}")
            self.fail("Expected string result")
    
    def test_mysql_get_table_info(self):
        """Test getting schema info for a specific table from MySQL connection"""
        connection_name = self.mysql_connection
        
        # First, get a list of tables using list_tables if we don't have them already
        if not hasattr(self, 'mysql_table_names') or not self.mysql_table_names:
            print("Calling list_tables first to get available tables")
            self.test_mysql_list_tables()
        
        # Skip if we still don't have table names
        if not hasattr(self, 'mysql_table_names') or not self.mysql_table_names:
            self.skipTest("No tables found to test with")
            return
        
        test_table = self.mysql_table_names[0]  # Use first table from the list
        print(f"\nAbout to call get_table_info('{connection_name}', '{test_table}')")
        
        # Get detailed info about this table
        table_info = self.module.get_table_info(connection_name, test_table)
        self.assertIsNotNone(table_info)
        
        # Print some details about the table
        print(f"Details for table {test_table}:")
        if isinstance(table_info, str):
            try:
                table_dict = json.loads(table_info)
                
                # Validate the structure
                self.assertIn('table_name', table_dict, "Response should have table_name")
                self.assertIn('columns', table_dict, "Response should have columns")
                self.assertIn('primary_key', table_dict, "Response should have primary_key")
                self.assertIn('row_count', table_dict, "Response should have row_count")
                
                # Print table info
                print(f"Table: {table_dict['table_name']}")
                print(f"Number of rows: {table_dict['row_count']}")
                if table_dict['primary_key']:
                    print(f"Primary key(s): {', '.join(table_dict['primary_key'])}")
                else:
                    print("Primary key(s): None")
                print("\nColumns:")
                for col in table_dict['columns']:
                    nullable = "NULL" if col['nullable'] else "NOT NULL"
                    default = f" DEFAULT {col['default']}" if col['default'] else ""
                    print(f"  - {col['name']} ({col['type']}{default}) - {nullable}")
                    if col['comment']:
                        print(f"    Comment: {col['comment']}")
                
                # Verify we have at least one column
                self.assertGreater(len(table_dict['columns']), 0, "Table should have at least one column")
                
            except json.JSONDecodeError:
                print(f"Could not parse table info: {table_info[:100]}...")
                self.fail("Failed to parse JSON response")
            except Exception as e:
                print(f"Error processing table info: {str(e)}")
                self.fail(f"Error processing table info: {str(e)}")
        else:
            print(f"Received non-string result: {type(table_info)}")
            self.fail("Expected string result")
    
    def test_mysql_heatwave_chat(self):
        """Test the HeatWave chat functionality with MySQL connection"""
        connection_name = self.mysql_connection
        test_question = "What are the benefits of MySQL HeatWave?"
        
        print(f"About to call ask_heatwave_chat_tool('{connection_name}', '{test_question}')")
        
        # This test may fail if HeatWave is not configured
        try:
            result = self.module.ask_heatwave_chat_tool(connection_name, test_question)
            
            # Verify we got a result
            self.assertIsNotNone(result)
            
            # Check if we got an error response (JSON string)
            if isinstance(result, str) and result.startswith('{'):
                try:
                    result_dict = json.loads(result)
                    if 'error' in result_dict:
                        print(f"HeatWave chat error: {result_dict['error']}")
                        self.skipTest("HeatWave chat returned an error - may not be configured")
                except json.JSONDecodeError:
                    # If it's not JSON, it's probably a successful text response
                    pass
            
            # If we got here, we have a successful response
            print(f"HeatWave chat response (first 200 chars):\n{result[:200]}...")
            
            # Make sure we got a non-empty string
            self.assertTrue(isinstance(result, str) and len(result) > 0)
            
        except Exception as e:
            print(f"Error testing HeatWave chat: {str(e)}")
            self.skipTest(f"HeatWave chat test failed with exception: {str(e)}")
    
    def test_connection_not_found(self):
        """Test behavior when connection is not found"""
        # Use a name that's unlikely to exist
        fake_connection_name = "this_connection_does_not_exist_12345"
        
        print(f"About to call get_dbtools_connection_by_name_tool('{fake_connection_name}')")
        # Try to get details for this connection
        result = self.module.get_dbtools_connection_by_name_tool(fake_connection_name)
        
        # Should return a JSON error
        result_dict = json.loads(result)
        self.assertIn("error", result_dict)
        self.assertIn("No connection found", result_dict["error"])
        
        print(f"Correctly received error: {result_dict['error']}")
    
    def test_autonomous_databases_with_invalid_compartment(self):
        """Test listing databases with an invalid compartment name"""
        # Use a name that's unlikely to exist
        fake_compartment_name = "this_compartment_does_not_exist_12345"
        
        print(f"About to call list_autonomous_databases('{fake_compartment_name}')")
        # Try to list databases in this compartment
        result = self.module.list_autonomous_databases(fake_compartment_name)
        
        # Should return a JSON error
        result_dict = json.loads(result)
        self.assertIn("error", result_dict)
        self.assertIn("Compartment", result_dict["error"])
        
        print(f"Correctly received error: {result_dict['error']}")
    
    def test_execute_sql_with_invalid_connection(self):
        """Test executing SQL with an invalid connection name"""
        # Use a name that's unlikely to exist
        fake_connection_name = "this_connection_does_not_exist_12345"
        test_sql = "SELECT 1 FROM DUAL"
        
        print(f"About to call execute_sql_tool('{fake_connection_name}', '{test_sql}')")
        # Try to execute a simple SQL query
        result = self.module.execute_sql_tool(fake_connection_name, test_sql)
        
        # Should return a JSON error
        result_dict = json.loads(result)
        self.assertIn("error", result_dict)
        self.assertIn("No connection found", result_dict["error"])
        
        print(f"Correctly received error: {result_dict['error']}")
    
    def tearDown(self):
        """Clean up after each test"""
        print(f"{'=' * 70}")
        print(f"Completed test: {self._testMethodName}")
        print(f"{'=' * 70}\n")


if __name__ == "__main__":
    print("Starting dbtools-mcp-server functional tests")
    print("These tests will call real OCI services using your OCI configuration")
    print("Make sure your OCI config file is properly set up at ~/.oci/config")
    
    # Check if a specific test name was provided as an argument
    if len(sys.argv) > 1:
        # The first argument after the script name is the test to run
        test_name = sys.argv[1]
        print(f"\nRunning specific test: {test_name}")
        
        # Create a test suite with just the specified test
        suite = unittest.TestSuite()
        try:
            suite.addTest(TestDbtoolsMcpServer(test_name))
            runner = unittest.TextTestRunner()
            runner.run(suite)
        except ValueError:
            print(f"Error: Test '{test_name}' not found. Available tests:")
            for name in unittest.defaultTestLoader.getTestCaseNames(TestDbtoolsMcpServer):
                print(f"  - {name}")
    else:
        # Run all tests
        print("\nRunning all tests...")
        unittest.main()
