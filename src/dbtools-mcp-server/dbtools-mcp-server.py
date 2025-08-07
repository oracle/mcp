"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
"""

import os.path

import requests
import json
import oci
from oci.signer import Signer
from oci.resource_search.models import StructuredSearchDetails


from fastmcp import FastMCP

MODEL_NAME = os.getenv("MODEL_NAME", "MINILM_L12_V2")
MODEL_EMBEDDING_DIMENSION = int(os.getenv("MODEL_EMBEDDING_DIMENSION", "384"))
mcp = FastMCP("oci")


profile_name = os.getenv("PROFILE_NAME", "DEFAULT")

config = oci.config.from_file(profile_name=profile_name)
identity_client = oci.identity.IdentityClient(config)

search_client = oci.resource_search.ResourceSearchClient(config)
database_client = oci.database.DatabaseClient(config)
dbtools_client = oci.database_tools.DatabaseToolsClient(config)
vault_client = oci.vault.VaultsClient(config)
secrets_client = oci.secrets.SecretsClient(config)
ords_endpoint = dbtools_client.base_client._endpoint.replace("https://", "https://sql.")
object_storage_client = oci.object_storage.ObjectStorageClient(config)
auth_signer = Signer(
    tenancy=config['tenancy'],
    user=config['user'],
    fingerprint=config['fingerprint'],
    private_key_file_location=config['key_file'],
    pass_phrase=config['pass_phrase']
)
tenancy_id = os.getenv("TENANCY_ID_OVERRIDE", config['tenancy'])

@mcp.tool()
def list_all_compartments() -> str:
    """List all compartments in a tenancy with clear formatting"""
    compartments = identity_client.list_compartments(tenancy_id).data
    compartments.append(identity_client.get_compartment(compartment_id=tenancy_id).data)
    return str(compartments)

def get_compartment_by_name(compartment_name: str):
    """Internal function to get compartment by name with caching"""
    compartments = identity_client.list_compartments(
        compartment_id=tenancy_id,
        compartment_id_in_subtree=True,
        access_level="ACCESSIBLE",
        lifecycle_state="ACTIVE"
    )
    compartments.data.append(identity_client.get_compartment(compartment_id=tenancy_id).data)

    # Search for the compartment by name
    for compartment in compartments.data:
        if compartment.name.lower() == compartment_name.lower():
            return compartment

    return None

@mcp.tool()
def get_compartment_by_name_tool(name: str) -> str:
    """Return a compartment matching the provided name"""
    compartment = get_compartment_by_name(name)
    if compartment:
        return str(compartment)
    else:
        return json.dumps({"error": f"Compartment '{name}' not found."})

@mcp.tool()
def list_autonomous_databases(compartment_name: str) -> str:
    """List all databases in a given compartment name"""
    compartment = get_compartment_by_name(compartment_name)
    if not compartment:
        return json.dumps({"error": f"Compartment '{compartment_name}' not found. Use list_compartment_names() to see available compartments."})
    
    databases = database_client.list_autonomous_databases(compartment_id=compartment.id).data
    return str(databases)

@mcp.tool()
def list_all_databases() -> str:
    """List all databases in the tenancy"""
    search_details = StructuredSearchDetails(
        query="query autonomousdatabase, database, pluggabledatabase, mysqldbsystem resources",
        type="Structured",
        matching_context_type="NONE"
    )
    results = search_client.search_resources(search_details=search_details, tenant_id=config['tenancy']).data
    return str(results)

@mcp.tool()
def list_dbtools_connection_tool(compartment_name: str) -> str:
    """List all dbtools connections in a given compartment"""
    compartment = get_compartment_by_name(compartment_name)
    if not compartment:
        return json.dumps({"error": f"Compartment '{compartment_name}' not found. Use list_compartment_names() to see available compartments."})
    
    connections = dbtools_client.list_database_tools_connections(compartment_id=compartment.id).data
    return str(connections)

@mcp.tool()
def list_all_connections() -> str:
    """List all database connections across all compartments"""
    search_details = StructuredSearchDetails(
        query="query databasetoolsconnection resources",
        type="Structured",
        matching_context_type="NONE"
    )
    search_results = search_client.search_resources(search_details=search_details, tenant_id=config['tenancy']).data
    
    if not hasattr(search_results, 'items'):
        return json.dumps([])

    # Get full details for each connection
    detailed_results = []
    for item in search_results.items:
        try:
            connection = dbtools_client.get_database_tools_connection(item.identifier).data
            detailed_results.append(connection)
        except Exception as e:
            # If we can't get details for a connection, include error info
            detailed_results.append({
                "error": f"Error getting details for connection {item.display_name}: {str(e)}",
                "search_result": item.identifier
            })
    
    return str(detailed_results)

@mcp.tool()
def get_dbtools_connection_by_name_tool(display_name: str) -> str:
    """Get a dbtools connection for a given connection name"""
    search_details = StructuredSearchDetails(
        query=f"query databasetoolsconnection resources where displayName =~ '{display_name}'",
        type="Structured",
        matching_context_type="NONE"
    )
    search_results = search_client.search_resources(search_details=search_details, tenant_id=config['tenancy']).data
    
    if not hasattr(search_results, 'items') or len(search_results.items) == 0:
        return json.dumps({
            "error": f"No connection found with name '{display_name}'",
            "suggestion": "Use list_all_connections() to see available connections"
        })

    # Get the first matching connection's OCID
    connection_id = search_results.items[0].identifier
    
    # Get the full connection details
    connection = dbtools_client.get_database_tools_connection(connection_id).data
    return str(connection)

def get_minimal_connection_by_name(dbtools_connection_display_name: str):
    """
    Internal function to get minimal connection information from a display name.
    Returns a dictionary with connection details like id, type, and connection string.
    """
    search_details = StructuredSearchDetails(
        query=f"query databasetoolsconnection resources return allAdditionalFields where displayName =~ '{dbtools_connection_display_name}'",
        type="Structured",
        matching_context_type="NONE"
    )
    try:
        resp = search_client.search_resources(search_details=search_details, tenant_id=config['tenancy']).data
        
        if not hasattr(resp, 'items') or len(resp.items) == 0:
            return None
        
        item = resp.items[0]
        
        # Extract key information from the search result
        connection_info = {
            'id': item.identifier,
            'display_name': item.display_name,
            'time_created': item.time_created,
            'compartment_id': item.compartment_id,
            'lifecycle_state': item.lifecycle_state
        }
        
        # Extract additional fields if available
        if hasattr(item, 'additional_details') and item.additional_details:
            additional = item.additional_details
            if isinstance(additional, dict):
                connection_info.update({
                    'type': additional.get('type'),
                    'connection_string': additional.get('connectionString')
                })
        return connection_info
    except Exception as e:
        print(f"Error in get_minimal_connection_by_name: {str(e)}")
        return None

def execute_sql_tool_by_connection_id(connection_id: str, sql_script: str, binds: list = None) -> str:
    """Internal function to execute a SQL script using a connection ID with optional bind variables"""
    try:
        execute_sql_endpoint = f"{ords_endpoint}/ords/{connection_id}/_/sql"
        
        # Prepare the request payload
        payload = {
            "statementText": sql_script
        }
        if binds:
            payload["binds"] = binds
            
        response = requests.post(
            execute_sql_endpoint,
            json=payload,
            auth=auth_signer,
            headers={"Content-Type": "application/json"}
        )
        
        # Try to format JSON response if possible
        try:
            return json.dumps(response.json(), indent=2)
        except:
            return response.text
    except Exception as e:
        return json.dumps({
            "error": f"Error executing SQL: {str(e)}",
            "sql_script": sql_script,
            "binds": binds
        })

@mcp.tool()
def execute_sql_tool(dbtools_connection_display_name: str, sql_script: str) -> str:
    """Execute SQL statements on a dbtools connection. When
    Substitition char & is used in a string value, it must be escaped like this: ''&''
    WARNING: This tool can perform destructive operations on the database, 
    user permission must be explicitely requested by the client before executing.
    """
    connection_info = get_minimal_connection_by_name(dbtools_connection_display_name)
    
    if connection_info is None:
        return json.dumps({
            "error": f"No connection found with name '{dbtools_connection_display_name}'",
            "suggestion": "Use list_all_connections() to see available connections"
        })
    
    return execute_sql_tool_by_connection_id(connection_info['id'], sql_script)

@mcp.tool()
def get_table_info(dbtools_connection_display_name: str, table_name: str) -> str:
    """
    Get detailed schema information about a specific database table.
    
    Supports ORACLE_DATABASE and MYSQL database types.
    """
    connection_info = get_minimal_connection_by_name(dbtools_connection_display_name)
    
    if connection_info is None:
        return json.dumps({
            "error": f"No connection found with name '{dbtools_connection_display_name}'",
            "suggestion": "Use list_all_connections() to see available connections"
        })
    
    try:
        # Get database type from the connection info
        db_type = connection_info.get('type')
        
        if db_type == 'ORACLE_DATABASE':
            # First try with all_tab_columns (includes system views)
            column_sql = f"""
            WITH pk_columns AS (
                SELECT column_name
                FROM all_cons_columns acc
                JOIN all_constraints ac ON acc.constraint_name = ac.constraint_name
                    AND acc.owner = ac.owner
                WHERE ac.table_name = '{table_name.upper()}'
                AND ac.constraint_type = 'P'
            )
            SELECT 
                c.column_name,
                c.data_type,
                c.data_length,
                c.nullable,
                c.data_default,
                cc.comments,
                CASE WHEN pk.column_name IS NOT NULL THEN 1 ELSE 0 END as is_primary_key,
                t.num_rows
            FROM all_tab_columns c
            LEFT JOIN all_col_comments cc 
                ON cc.table_name = c.table_name 
                AND cc.column_name = c.column_name
                AND cc.owner = c.owner
            LEFT JOIN pk_columns pk 
                ON pk.column_name = c.column_name
            LEFT JOIN all_tables t 
                ON t.table_name = c.table_name
                AND t.owner = c.owner
            WHERE c.table_name = '{table_name.upper()}'
            ORDER BY c.column_id
            """
        elif db_type == 'MYSQL':
            column_sql = f"""
            SELECT 
                c.column_name,
                c.data_type,
                c.character_maximum_length as data_length,
                c.is_nullable as nullable,
                c.column_default as data_default,
                c.column_comment as comments,
                CASE WHEN tc.constraint_type = 'PRIMARY KEY' THEN 1 ELSE 0 END as is_primary_key,
                t.table_rows as num_rows
            FROM information_schema.columns c
            LEFT JOIN information_schema.key_column_usage kcu 
                ON kcu.table_schema = c.table_schema
                AND kcu.table_name = c.table_name 
                AND kcu.column_name = c.column_name
            LEFT JOIN information_schema.table_constraints tc
                ON tc.table_schema = kcu.table_schema
                AND tc.table_name = kcu.table_name
                AND tc.constraint_name = kcu.constraint_name
            LEFT JOIN information_schema.tables t
                ON t.table_schema = c.table_schema
                AND t.table_name = c.table_name
            WHERE c.table_name = '{table_name}'
                AND c.table_schema = database()
            ORDER BY c.ordinal_position
            """
        else:
            return json.dumps({
                "error": f"Unsupported database type: {db_type}",
                "supported_types": ["ORACLE_DATABASE", "MYSQL"]
            })
        
        result = execute_sql_tool_by_connection_id(connection_info['id'], column_sql)
        
        try:
            raw_data = json.loads(result)
            if not raw_data.get('items') or not raw_data['items'][0].get('resultSet'):
                return json.dumps({
                    "error": "No data returned from query",
                    "raw_result": result
                })
            
            # Extract column data
            columns = []
            primary_keys = []
            row_count = 0
            
            for col in raw_data['items'][0]['resultSet'].get('items', []):
                column = {
                    "name": col['column_name'],
                    "type": col['data_type'],
                    "length": int(col['data_length']) if col['data_length'] is not None else None,
                    "nullable": col['nullable'] == 'Y' if db_type == 'ORACLE_DATABASE' else col['nullable'] == 'YES',
                    "default": col['data_default'].strip() if col['data_default'] else None,
                    "comment": col['comments']
                }
                columns.append(column)
                
                if col['is_primary_key'] == 1:
                    primary_keys.append(col['column_name'])
                
                # Get row count from first row (it's the same for all rows)
                if row_count == 0:
                    row_count = col['num_rows'] or 0
            
            if len(columns) == 0:
                return json.dumps({
                    "error": "No columns found for table",
                    "table": table_name
                })
            # Build the final response
            response = {
                "table_name": table_name.upper() if db_type == 'ORACLE_DATABASE' else table_name,
                "columns": columns,
                "primary_key": primary_keys,
                "row_count": row_count
            }
            
            return json.dumps(response, indent=2)
            
        except json.JSONDecodeError:
            return json.dumps({
                "error": "Failed to parse SQL response",
                "raw_result": result
            })
        except Exception as e:
            return json.dumps({
                "error": f"Error processing results: {str(e)}",
                "raw_result": result
            })
            
    except Exception as e:
        return json.dumps({
            "error": f"Error getting table info: {str(e)}",
            "connection": dbtools_connection_display_name,
            "table": table_name
        })

@mcp.tool()
def list_tables(dbtools_connection_display_name: str) -> str:
    """
    List all tables in the database with basic information (name, row count, comments).
    
    Supports ORACLE_DATABASE and MYSQL database types.
    """
    connection_info = get_minimal_connection_by_name(dbtools_connection_display_name)
    
    if connection_info is None:
        return json.dumps({
            "error": f"No connection found with name '{dbtools_connection_display_name}'",
            "suggestion": "Use list_all_connections() to see available connections"
        })
    
    try:
        # Get database type from the connection info
        db_type = connection_info.get('type')
        
        if db_type == 'ORACLE_DATABASE':
            sql_script = """
            SELECT table_name, num_rows, comments
            FROM user_tables
            LEFT JOIN user_tab_comments USING (table_name)
            ORDER BY table_name
            """
        elif db_type == 'MYSQL':
            sql_script = """
            SELECT 
                table_name,
                table_rows as num_rows,
                table_comment as comments
            FROM information_schema.tables 
            WHERE table_schema = database()
            ORDER BY table_name
            """
        else:
            return json.dumps({
                "error": f"Unsupported database type: {db_type}",
                "supported_types": ["ORACLE_DATABASE", "MYSQL"]
            })
        
        # Execute SQL and get the response
        response = execute_sql_tool_by_connection_id(connection_info['id'], sql_script)
        
        # Parse the response to extract just the table items
        try:
            response_json = json.loads(response)
            # Navigate to the items array in the complex response structure
            if response_json['items'] and len(response_json['items']) > 0:
                first_statement = response_json['items'][0]
                if 'resultSet' in first_statement and 'items' in first_statement['resultSet']:
                    # Extract just the table items
                    tables = first_statement['resultSet']['items']
                    return json.dumps(tables, indent=2)
            
            # If we couldn't find the expected structure, return an empty array
            return json.dumps([])
            
        except Exception as e:
            return json.dumps({
                "error": f"Error parsing SQL results: {str(e)}",
                "raw_response": response[:200] + "..." if len(response) > 200 else response
            })
            
    except Exception as e:
        return json.dumps({
            "error": f"Error listing tables: {str(e)}",
            "connection": dbtools_connection_display_name
        })

@mcp.tool()
def bootstrap_reports(dbtools_connection_display_name: str) -> str:
    """
    Ensures the 'report_definitions' table exists in the current user's schema.
    Each database schema gets its own report_definitions table, allowing users
    to manage their reports independently.

    The table stores:
    - name: Unique report identifier
    - description: Optional report description
    - time_created/updated: Timestamps
    - sql_definition: JSON with SQL query and bind parameters
    - text_vector: VECTOR(MODEL_EMBEDDING_DIMENSION) for semantic similarity search

    Note: This tool operates only in the current user's schema, identified by
    SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA'). It will not affect report_definitions
    tables in other schemas.

    Args:
        dbtools_connection_display_name: The name of the database connection

    Returns:
        JSON string with:
        - ok (bool): True if operation succeeded
        - message (str): Human readable status message
        - error (str, optional): Error message if operation failed
        - step (str, optional): Step where error occurred

    Example sql_definition format:
    {
        "sql": "select id from employees where hire_date = :hire_date and age > :age",
        "binds": [
            {"name": "hire_date"},
            {"name": "age"}
        ]
    }
    """
    try:
        connection_info = get_minimal_connection_by_name(dbtools_connection_display_name)
        if connection_info is None:
            return json.dumps({
                "ok": False,
                "error": f"No connection found with name '{dbtools_connection_display_name}'",
                "step": "connection"
            })
        
        # Verify database type early
        db_type = connection_info.get('type', 'ORACLE_DATABASE')
        if db_type != 'ORACLE_DATABASE':
            return json.dumps({
                "ok": False,
                "error": f"Unsupported database type: {db_type}. This tool only supports Oracle databases.",
                "step": "validate_type"
            })

        # Check if table exists in current schema
        check_sql = """
            SELECT owner, table_name 
            FROM all_tables 
            WHERE table_name = 'REPORT_DEFINITIONS'
            AND owner = SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA')
        """
        check_result = execute_sql_tool_by_connection_id(connection_info['id'], check_sql)
        
        try:
            check_data = json.loads(check_result)
            result_set = check_data.get("items", [{}])[0].get("resultSet", {})
            if result_set.get("items"):
                schema = result_set["items"][0].get("owner", "current schema")
                return json.dumps({
                    "ok": True,
                    "message": f"Table 'report_definitions' exists in schema {schema}"
                })
        except json.JSONDecodeError:
            return json.dumps({
                "ok": False,
                "error": "Invalid response format while checking table existence",
                "step": "check_table"
            })

        # Create table if it doesn't exist
        ddl = """
          CREATE TABLE report_definitions (
              name VARCHAR(4000) PRIMARY KEY,
              description VARCHAR(4000),
              time_created TIMESTAMP(6),
              time_updated TIMESTAMP(6),
              sql_definition json,
              text_vector VECTOR({MODEL_EMBEDDING_DIMENSION})
          )
        """

        create_resp = execute_sql_tool(dbtools_connection_display_name, ddl)
        try:
            create_data = json.loads(create_resp)
            if "error" in create_data:
                return json.dumps({
                    "ok": False,
                    "error": create_data["error"],
                    "step": "create_table"
                })
            
            current_schema = None
            try:
                # Get current schema for the success message
                schema_sql = "SELECT SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA') as schema FROM DUAL"
                schema_result = execute_sql_tool_by_connection_id(connection_info['id'], schema_sql)
                schema_data = json.loads(schema_result)
                result_set = schema_data.get("items", [{}])[0].get("resultSet", {})
                if result_set.get("items"):
                    current_schema = result_set["items"][0].get("schema")
            except Exception:
                pass

            schema_msg = f" in schema {current_schema}" if current_schema else ""
            return json.dumps({
                "ok": True,
                "message": f"Table 'report_definitions' created{schema_msg}"
            })

        except json.JSONDecodeError:
            return json.dumps({
                "ok": False,
                "error": "Invalid response format while creating table",
                "step": "create_table"
            })

    except Exception as e:
        return json.dumps({
            "ok": False,
            "error": str(e),
            "step": "unknown"
        })

@mcp.tool()
def create_report(dbtools_connection_display_name: str, name: str, sql_query: str, description: str = None, bind_parameters: list = None) -> str:
    """
    Create a new report definition in the report_definitions table.
    
    Args:
        dbtools_connection_display_name: The name of the database connection
        name: Unique name for the report
        sql_query: The SQL query to execute
        description: Optional description of what the report does
        bind_parameters: Optional list of bind parameter names, e.g. ["customer_id", "start_date"]
    """
    connection_info = get_minimal_connection_by_name(dbtools_connection_display_name)
    if connection_info is None:
        return json.dumps({"error": f"No connection found with name '{dbtools_connection_display_name}'"})    

    # Check if table exists first
    bootstrap_result = bootstrap_reports(dbtools_connection_display_name)
    try:
        result = json.loads(bootstrap_result)
        if "error" in result:
            return bootstrap_result
    except:
        return bootstrap_result

    # Prepare the SQL definition JSON
    sql_definition = {
        "sql": sql_query
    }
    if bind_parameters:
        sql_definition["binds"] = [{
            "name": param
        } for param in bind_parameters]

    # Generate text embedding from name and description
    text_to_embed = name
    if description:
        text_to_embed = f"{name}. {description}"
    
    # Insert the new report using direct SQL to avoid bind variable issues
    insert_sql = f"""
        INSERT INTO report_definitions (
            name,
            description,
            time_created,
            time_updated,
            sql_definition,
            text_vector
        ) VALUES (
            '{name}',
            '{description or ""}',
            SYSTIMESTAMP,
            SYSTIMESTAMP,
            '{json.dumps(sql_definition).replace("'", "''")}',
            VECTOR_EMBEDDING({MODEL_NAME} USING '{text_to_embed.replace("'", "''") if text_to_embed else ""}' AS data)
        )"""

    result = execute_sql_tool_by_connection_id(connection_info['id'], insert_sql)
    try:
        # Check for errors
        json_result = json.loads(result)
        if "error" in json_result:
            return json.dumps({
                "error": "Failed to create report",
                "details": json_result["error"]
            })
    except:
        pass

    return json.dumps({
        "ok": True,
        "execute_output": result,
        "message": f"Report '{name}' created successfully",
        "report": {
            "name": name,
            "description": description,
            "sql_definition": sql_definition,
            "text_to_embed": text_to_embed
        }
    })

@mcp.tool()
def execute_report(dbtools_connection_display_name: str, report_name: str, bind_values: dict = None) -> str:
    """
    Execute a report by its name with optional bind parameter values.
    
    Args:
        dbtools_connection_display_name: The name of the database connection
        report_name: Name of the report to execute
        bind_values: Optional dictionary of bind parameter values, e.g. {"year": 2024, "rating": 8.5}
    """
    connection_info = get_minimal_connection_by_name(dbtools_connection_display_name)
    if connection_info is None:
        return json.dumps({"error": f"No connection found with name '{dbtools_connection_display_name}'"})    

    # Get the report definition
    get_report_sql = """
        SELECT sql_definition
        FROM report_definitions
        WHERE name = :name"""
    
    get_report_binds = [{"name": "name", "data_type": "VARCHAR", "value": report_name}]
    
    result = execute_sql_tool_by_connection_id(connection_info['id'], get_report_sql, get_report_binds)
    try:
        json_result = json.loads(result)
        if "error" in json_result:
            return json.dumps({
                "error": "Failed to get report definition",
                "details": json_result["error"]
            })
        
        # Extract the first row's sql_definition
        if "items" not in json_result or not json_result["items"]:
            return json.dumps({"error": f"Report '{report_name}' not found"})
            
        sql_definition = json_result["items"][0]["resultSet"]["items"][0]["sql_definition"]
    except Exception as e:
        return json.dumps({
            "error": "Failed to parse report definition",
            "details": str(e),
            "response": result
        })

    # Prepare the binds if needed
    binds = None
    if "binds" in sql_definition and bind_values:
        binds = []
        for bind_def in sql_definition["binds"]:
            bind_name = bind_def["name"]
            if bind_name not in bind_values:
                return json.dumps({
                    "error": f"Missing required bind parameter: {bind_name}",
                    "required_binds": [b["name"] for b in sql_definition["binds"]]
                })
            
            # Infer data type from the value
            value = bind_values[bind_name]
            if isinstance(value, int):
                data_type = "NUMBER"
            elif isinstance(value, float):
                data_type = "NUMBER"
            elif isinstance(value, str):
                data_type = "VARCHAR"
            else:
                data_type = "VARCHAR"
                value = str(value)
            
            binds.append({
                "name": bind_name,
                "data_type": data_type,
                "value": value
            })

    # Execute the report
    return execute_sql_tool_by_connection_id(connection_info['id'], sql_definition["sql"], binds)

@mcp.tool()
def get_report(dbtools_connection_display_name: str, report_name: str) -> str:
    """
    Retrieve a single report definition by name.
    Returns the report's name, description, creation/update times, and SQL definition.
    This is only supported for Oracle databases.
    
    Args:
        dbtools_connection_display_name: The name of the database connection
        report_name: Name of the report to retrieve
    """
    connection_info = get_minimal_connection_by_name(dbtools_connection_display_name)
    if connection_info is None:
        return json.dumps({"error": f"No connection found with name '{dbtools_connection_display_name}'"})    

    # Get the report definition
    get_report_sql = """
        SELECT 
            name,
            description,
            TO_CHAR(time_created, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as time_created,
            TO_CHAR(time_updated, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as time_updated,
            sql_definition
        FROM report_definitions
        WHERE name = :name"""
    
    get_report_binds = [{"name": "name", "data_type": "VARCHAR", "value": report_name}]
    
    result = execute_sql_tool_by_connection_id(connection_info['id'], get_report_sql, get_report_binds)
    try:
        json_result = json.loads(result)
        if "error" in json_result:
            return json.dumps({
                "error": "Failed to get report definition",
                "details": json_result["error"]
            })
        
        # Extract the first row
        if "items" not in json_result or not json_result["items"]:
            return json.dumps({"error": f"Report '{report_name}' not found"})
        report = json_result["items"][0]["resultSet"]["items"][0]
        sql_definition = report["sql_definition"]
        
        return json.dumps({
            "name": report["name"],
            "description": report["description"],
            "time_created": report["time_created"],
            "time_updated": report["time_updated"],
            "sql_query": sql_definition["sql"],
            "bind_parameters": [bind["name"] for bind in sql_definition.get("binds", [])] if "binds" in sql_definition else None
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": "Failed to parse report definition",
            "details": str(e),
            "response": result
        })

@mcp.tool()
def delete_report(dbtools_connection_display_name: str, report_name: str) -> str:
    """
    Delete a report definition by name.
    This is only supported for Oracle databases.
    
    Args:
        dbtools_connection_display_name: The name of the database connection
        report_name: Name of the report to delete
    """
    connection_info = get_minimal_connection_by_name(dbtools_connection_display_name)
    if connection_info is None:
        return json.dumps({"error": f"No connection found with name '{dbtools_connection_display_name}'"})    

    # First check if the report exists
    get_report_sql = """
        SELECT name FROM report_definitions WHERE name = :name"""
    
    get_report_binds = [{"name": "name", "data_type": "VARCHAR", "value": report_name}]
    
    result = execute_sql_tool_by_connection_id(connection_info['id'], get_report_sql, get_report_binds)
    try:
        json_result = json.loads(result)
        if "error" in json_result:
            return json.dumps({
                "error": "Failed to check report existence",
                "details": json_result["error"]
            })
        
        if "items" not in json_result or not json_result["items"]:
            return json.dumps({"error": f"Report '{report_name}' not found"})
    except Exception as e:
        return json.dumps({
            "error": "Failed to check report existence",
            "details": str(e)
        })

    # Delete the report
    delete_sql = """
        DELETE FROM report_definitions
        WHERE name = :name"""
    
    delete_binds = [{"name": "name", "data_type": "VARCHAR", "value": report_name}]
    
    result = execute_sql_tool_by_connection_id(connection_info['id'], delete_sql, delete_binds)
    try:
        json_result = json.loads(result)
        if "error" in json_result:
            return json.dumps({
                "error": "Failed to delete report",
                "details": json_result["error"]
            })
        
        return json.dumps({
            "ok": True,
            "message": f"Report '{report_name}' deleted successfully"
        })
    except Exception as e:
        return json.dumps({
            "error": "Failed to delete report",
            "details": str(e)
        })

@mcp.tool()
def list_reports(dbtools_connection_display_name: str) -> str:
    """
    List all reports from the report_definitions table.
    Returns report name, description, and creation/update times.
    This is only supported for Oracle databases.
    """
    connection_info = get_minimal_connection_by_name(dbtools_connection_display_name)
    if connection_info is None:
        return json.dumps({"error": f"No connection found with name '{dbtools_connection_display_name}'"})    

    # Check if table exists first
    bootstrap_result = bootstrap_reports(dbtools_connection_display_name)
    try:
        result = json.loads(bootstrap_result)
        if "error" in result:
            return bootstrap_result
    except:
        return bootstrap_result

    # Query the reports
    sql = """
    SELECT 
        name,
        description,
        TO_CHAR(time_created, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as time_created,
        TO_CHAR(time_updated, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as time_updated
    FROM report_definitions
    ORDER BY name
    """
    
    return execute_sql_tool_by_connection_id(connection_info['id'], sql)

@mcp.tool()
def find_matching_reports(dbtools_connection_display_name: str, search_text: str, limit: int = 5) -> str:
    """
    Find reports similar to the given search text using vector similarity search.
    
    Args:
        dbtools_connection_display_name: The name of the database connection
        search_text: Text to find similar reports for
        limit: Maximum number of similar reports to return (default: 5)
    
    Returns:
        JSON string containing the matched reports sorted by similarity score
    """
    connection_info = get_minimal_connection_by_name(dbtools_connection_display_name)
    if connection_info is None:
        return json.dumps({"error": f"No connection found with name '{dbtools_connection_display_name}'"})

    # Check if table exists
    bootstrap_result = bootstrap_reports(dbtools_connection_display_name)
    try:
        result = json.loads(bootstrap_result)
        if "error" in result:
            return bootstrap_result
    except:
        return bootstrap_result

    # Query similar reports using vector similarity
    query = f"""
        SELECT 
            r.name as "name",
            r.description as "description",
            TO_CHAR(r.time_created, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as "time_created",
            TO_CHAR(r.time_updated, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as "time_updated",
            r.sql_definition as "sql_definition",
            ROUND(1 - VECTOR_DISTANCE(r.text_vector, 
                VECTOR_EMBEDDING({MODEL_NAME} USING :search_text AS data)), 4) as "similarity_score"
        FROM report_definitions r
        WHERE r.text_vector IS NOT NULL
            AND 1 - VECTOR_DISTANCE(r.text_vector, 
                VECTOR_EMBEDDING({MODEL_NAME} USING :search_text AS data)) > 0.3
        ORDER BY "similarity_score" DESC
        FETCH FIRST :limit ROWS ONLY
    """

    binds = [
        {"name": "search_text", "data_type": "VARCHAR", "value": search_text},
        {"name": "limit", "data_type": "NUMBER", "value": limit}
    ]

    result = execute_sql_tool_by_connection_id(connection_info['id'], query, binds)
    try:
        # Parse the results
        json_result = json.loads(result)
        if "error" in json_result:
            return json.dumps({
                "error": "Failed to find matching reports",
                "details": json_result["error"]
            })
        
        # Extract the reports from the result
        reports = []
        if "items" in json_result and json_result["items"] and "resultSet" in json_result["items"][0]:
            result_set = json_result["items"][0]["resultSet"]
            if "items" in result_set:
                for item in result_set["items"]:
                    # Handle sql_definition which may already be parsed as JSON
                    sql_def = item["sql_definition"]
                    if isinstance(sql_def, str):
                        try:
                            sql_def = json.loads(sql_def)
                        except:
                            pass
                    
                    reports.append({
                        "name": item["name"],
                        "description": item["description"],
                        "time_created": item["time_created"],
                        "time_updated": item["time_updated"],
                        "sql_definition": sql_def,
                        "similarity_score": float(item["similarity_score"])
                    })

        return json.dumps({
            "ok": True,
            "reports": reports,
            "message": f"Found {len(reports)} similar reports for '{search_text}'"
        })
    except Exception as e:
        return json.dumps({
            "error": "Failed to process results",
            "details": str(e)
        })


@mcp.tool()
def ragify_column(dbtools_connection_display_name: str, table_name: str, column_names: list[str], vector_column_name: str) -> str:
    """
    Create a new VECTOR column in the given table name and populate it with embeddings generated from one or more source columns. 
    This integrates the specified column(s) into a RAG (Retrieval Augmented Generation) system.
    The new vector column will have the name specified by `vector_column_name`.
    The embeddings are generated by concatenating the string representations of the values in the `column_names` list.
    The new vector column can be used to find similarities, e.g.: 
    "VECTOR_DISTANCE({vector_column_name}, VECTOR_EMBEDDING({MODEL_NAME} USING 'some text' AS data))"
    WARNING: This operation modifies the table structure and updates data. Ensure backups exist. User permission must be explicitely requested by the client.
    
    Args:
        dbtools_connection_display_name: The display name of the DBTools connection.
        table_name: The name of the table to modify.
        column_names: A list of column names whose values will be concatenated and used to generate embeddings.
        vector_column_name: The desired name for the new VECTOR column.
        
    Returns:
        A JSON string indicating the status (success, warning, error) and details of the operation.
    """
    # vector_column_name = f"{column_name}_vector" # Removed: now provided as argument
    # NOTE: Embedding dimension (MODEL_EMBEDDING_DIMENSION) and model name ({MODEL_NAME}) are hardcoded.

    if not column_names:
        return json.dumps({"status": "error", "message": "column_names list cannot be empty."}) 

    # 1. Add the vector column
    alter_sql = f"ALTER TABLE {table_name} ADD ({vector_column_name} VECTOR({MODEL_EMBEDDING_DIMENSION}))"
    print(f"Executing ALTER TABLE statement: {alter_sql}")
    
    alter_result_str = execute_sql_tool(dbtools_connection_display_name, alter_sql)
    try:
        # Try to parse the response and log specific errors if possible
        alter_result = json.loads(alter_result_str)
        if alter_result.get("items") and len(alter_result["items"]) > 0 and alter_result["items"][0].get("errorCode", 0) != 0:
             error_message = alter_result['items'][0].get('errorMessage')
             print(f"Warning during ALTER TABLE: {error_message}. Proceeding anyway.")
        # If no error code, assume success or non-critical issue, proceed silently.
    except json.JSONDecodeError:
        # Handle non-JSON response
        print(f"Warning: Non-JSON response during ALTER TABLE: {alter_result_str}. Proceeding anyway.")
    except Exception as e:
        print(f"Warning: Exception occurred during ALTER TABLE or response handling: {e}. Proceeding anyway.")
        
    # Regardless of ALTER outcome/warnings, proceed to COMMENT and UPDATE
    pass # Proceed to COMMENT and UPDATE steps

    # 2. Add a comment to the vector column indicating source columns
    comment_text = f"Vector embedding generated from columns: {', '.join(column_names)}"
    # Ensure comment text isn't too long for Oracle's limit (4000 bytes, but play safe)
    comment_text = comment_text[:3900] 
    comment_sql = f"COMMENT ON COLUMN {table_name}.{vector_column_name} IS '{comment_text}'"
    print(f"Executing COMMENT ON COLUMN statement: {comment_sql}")
    
    comment_result_str = execute_sql_tool(dbtools_connection_display_name, comment_sql)
    # Basic check for comment result - less critical, so just print errors
    try:
        comment_result = json.loads(comment_result_str)
        if comment_result.get("items") and len(comment_result["items"]) > 0 and comment_result["items"][0].get("errorCode", 0) != 0:
             print(f"Warning: Error during COMMENT ON COLUMN: {comment_result['items'][0].get('errorMessage')}")
    except Exception as e:
        print(f"Warning: Could not parse COMMENT ON COLUMN response or other error: {e}")
        print(f"COMMENT response raw: {comment_result_str}")

    # Construct the concatenation expression for the source columns
    # Using COALESCE to handle potential NULLs gracefully, replacing them with empty strings
    # Concatenating with a space separator
    concatenated_columns = " || ' ' || ".join([f"COALESCE(TO_CHAR({col}), '')" for col in column_names])
    
    # Construct the WHERE clause to only update rows where at least one source column is not null
    where_clause_conditions = [f"{col} IS NOT NULL" for col in column_names]
    where_clause = " OR ".join(where_clause_conditions)

    # 3. Populate the vector column
    update_sql = f"UPDATE {table_name}\nSET {vector_column_name} = VECTOR_EMBEDDING({MODEL_NAME} USING ({concatenated_columns}) AS data)\nWHERE {where_clause}"
    print(f"Executing UPDATE statement: {update_sql}")

    update_result_str = execute_sql_tool(dbtools_connection_display_name, update_sql)
    try:
        update_result = json.loads(update_result_str)
         # Check for errors in the response items
        if update_result.get("items") and len(update_result["items"]) > 0 and update_result["items"][0].get("errorCode", 0) != 0:
             print(f"Error during UPDATE: {update_result['items'][0].get('errorMessage')}")
             # Even if update fails, the column was likely added. Return the update error.
             return json.dumps({"status": "error", "step": "UPDATE", "details": update_result})
        
        # If both steps seemed okay (or ALTER had non-fatal error like column exists), return success message + final result
        return json.dumps({"status": "success", "details": update_result})

    except json.JSONDecodeError:
         print(f"Non-JSON response during UPDATE: {update_result_str}")
         # If ALTER reported 'column exists', this non-JSON might be less critical, but still report as warning.
         return json.dumps({"status": "warning", "step": "UPDATE", "message": "ALTER TABLE step completed (possibly with warnings like 'column exists'), but UPDATE step returned non-JSON response.", "details": update_result_str})
    except Exception as e:
        print(f"Unexpected error parsing UPDATE response: {e}")
        return json.dumps({"status": "error", "step": "UPDATE", "details": f"Unexpected error: {str(e)}"})

@mcp.tool()
def heatwave_ask_help(dbtools_connection_display_name: str, question: str) -> str:
    """
    Ask natural language questions to machine learning help tool to get answers about heatwave ML (AutoML).
    The tool returns answers based on HeatWave AutoML documentation and can return executable MySQL queries that
    can be executed using sql execution tool.
    This tool should be prioritized for HeatWave AutoML syntax when trying to call ML stored procedures.
    The provided dbtools_connection_display_name is that of a dbtools connection of type MySQL
    """
    connection_info = get_minimal_connection_by_name(dbtools_connection_display_name)
    
    if connection_info is None:
        return json.dumps({
            "error": f"No connection found with name '{dbtools_connection_display_name}'",
            "suggestion": "Use list_all_connections() to see available connections"
        })
    
    try:
        # Verify this is a MySQL connection
        if connection_info.get('type') != 'MYSQL':
            return json.dumps({
                "error": "This connection is not a MySQL database. Heatwave ask help tool is only available for MySQL databases.",
                "suggestion": "Please provide a MySQL database connection."
            })
            
        # Execute the heatwave chat query
        nl2ml_call = f"call sys.NL2ML('{question}', @nl2ml_response); select @nl2ml_response"
        response = execute_sql_tool_by_connection_id(connection_info['id'], nl2ml_call)
        
        # return response
    
        # Parse the response
        if isinstance(response, str):
            response_data = json.loads(response)
            if 'items' in response_data and len(response_data['items']) > 0:
                json_column_name = response_data['items'][1]['resultSet']['metadata'][0]['jsonColumnName']
            return json.loads(response_data['items'][1]['resultSet']['items'][0][json_column_name])["text"]
            
        return json.dumps({"error": "Unexpected response format from Heatwave ask help"})
    except Exception as e:
        return json.dumps({"error": f"Error with Heatwave ask help: {str(e)}"})



@mcp.tool()
def heatwave_load_vector_store(dbtools_connection_display_name: str, namespace: str, bucket_name: str, document_prefix: str, schema_name: str, table_name: str) -> str:
    """
    Load documents from object storage into a vector store that can be used for similarity search and retrieval augmented generation (RAG). The path can be a file name, a prefix, or a full path.
    
    For example, assuming these files exist:
    heatwave-en-ml-9.2.0.pdf
    sample_files/document1.pdf
    sample_files/document2.pdf
    sample_files/documents_345.docx

    The following are valid definitions for document_prefix:
    'heatwave-en-ml'
    'heatwave-en-ml-9.2.0.pdf'
    'sample_files/'
    'sample_files/document2.pdf'
    'sample_files/doc'

    The provided dbtools_connection_display_name is that of a dbtools connection of type MySQL
    """
    connection_info = get_minimal_connection_by_name(dbtools_connection_display_name)
    
    if connection_info is None:
        return json.dumps({
            "error": f"No connection found with name '{dbtools_connection_display_name}'",
            "suggestion": "Use list_all_connections() to see available connections"
        })
    
    try:
        # Verify this is a MySQL connection
        if connection_info.get('type') != 'MYSQL':
            return json.dumps({
                "error": "This connection is not a MySQL database. Heatwave load vector store is only available for MySQL databases.",
                "suggestion": "Please provide a MySQL database connection."
            })
            
        vsload = f"SET @vsl_options=JSON_OBJECT('schema_name', '{schema_name}', 'table_name', '{table_name}'); CALL sys.VECTOR_STORE_LOAD('oci://{bucket_name}@{namespace}/{document_prefix}', @vsl_options);"
        response = execute_sql_tool_by_connection_id(connection_info['id'], vsload)
        
        return response
    
    except Exception as e:
        return json.dumps({"error": f"Error with VECTOR_STORE_LOAD: {str(e)}"})

@mcp.tool()
def object_storage_list_buckets(compartment_name: str) -> str:
    """
    List all accessible object store buckets. 
    """
    compartment = get_compartment_by_name(compartment_name)
    if not compartment:
        return json.dumps({"error": f"Compartment '{compartment_name}' not found. Use list_compartment_names() to see available compartments."})

    namespace = object_storage_client.get_namespace().data

    try:
        # List buckets in the specified compartment
        list_buckets_response = object_storage_client.list_buckets(namespace_name = namespace,
                                                                   compartment_id = compartment.id
                                                                   )
    except Exception as e:
        return json.dumps({"error": f"Error with listing available buckets in a compartment: {str(e)}"})

    return str(list_buckets_response.data)


@mcp.tool()
def object_storage_list_objects(namespace: str, bucket_name: str) -> str:
    """
    List objects / files which are stored in a given object store bucket
    """
    try:
        # List objects in a specified bucket
        list_object_response = object_storage_client.list_objects(namespace_name = namespace,
                                                                  bucket_name = bucket_name
                                                                  )
    except Exception as e:
        return json.dumps({"error": f"Error with listing objects in a specified bucket: {str(e)}"})

    return str(list_object_response.data.objects)

@mcp.tool()
def heatwave_ask_ml_rag(dbtools_connection_display_name: str, question: str) -> str:
    """
    Ask ml_rag - retrieveal augmented generation tool a question
    ** This is the preferred tool for answering questions using vector stores and similarity search **
    This tool will use existing vector stores to do similarity search to find relevant segments. 
    The segments can then be used as context to answer user's question - the tool does not use LLM to generate a response.
    Instead, MCP Host LLM should use the retreived context to generate the response.
    The provided dbtools_connection_display_name is that of a dbtools connection of type MySQL
    """
    connection_info = get_minimal_connection_by_name(dbtools_connection_display_name)
    
    if connection_info is None:
        return json.dumps({
            "error": f"No connection found with name '{dbtools_connection_display_name}'",
            "suggestion": "Use list_all_connections() to see available connections"
        })
    
    try:
        # Verify this is a MySQL connection
        if connection_info.get('type') != 'MYSQL':
            return json.dumps({
                "error": "This connection is not a MySQL database. Heatwave ML_RAG is only available for MySQL databases.",
                "suggestion": "Please provide a MySQL database connection."
            })
            
        # Execute the heatwave chat query
        ask_ml_rag = f"set @options = NULL; call sys.ml_rag('{question}', @response, JSON_OBJECT('skip_generate', true)); SELECT @response;"
        response = execute_sql_tool_by_connection_id(connection_info['id'], ask_ml_rag)
        
        # Parse the response
        if isinstance(response, str):
            response_data = json.loads(response)
            if 'items' in response_data and len(response_data['items']) > 0:
                json_column_name = response_data['items'][2]['resultSet']['metadata'][0]['jsonColumnName']
            return json.loads(response_data['items'][2]['resultSet']['items'][0][json_column_name])
            
        return json.dumps({"error": "Unexpected response format from Heatwave ML_RAG"})
    except Exception as e:
        return json.dumps({"error": f"Error with ML_RAG: {str(e)}"})

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
