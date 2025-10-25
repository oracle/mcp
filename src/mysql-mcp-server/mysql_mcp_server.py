"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
"""

import contextlib
import json
import re
from typing import Optional, Union

import oci
from fastmcp import FastMCP
from mysql import connector
from mysql.connector.abstracts import MySQLConnectionAbstract

from utils import DatabaseConnectionError, get_ssh_command, load_mysql_config, Mode, OciInfo

MIN_CONTEXT_SIZE = 10
DEFAULT_CONTEXT_SIZE = 20
MAX_CONTEXT_SIZE = 100

###############################################################
# Start setup
###############################################################

# Load config
config: Optional[dict] = None
config_error_msg: Optional[str] = None
try:
    config = load_mysql_config()
except Exception as e:
    config_error_msg = json.dumps({
        "error" : f"Error loading config. Fix configuration file and try restarting MCP server {str(e)}."
    })

# Setup oci connection if applicable
oci_info: Optional[OciInfo] = None  # None if not available, otherwise OCI config info
oci_error_msg: Optional[str] = None # None if OCI available, otherwise a json formatted string
try:
    oci_info = OciInfo()
except Exception as e:
    oci_error_msg = json.dumps({
        "error" : "object store unavailable. If object store is required, the MCP server must be restarted with a valid"
                 f" OCI config. OCI connection attempt yielded error {str(e)}."
    })

# Create mcp server
mcp = FastMCP("MySQL")

###############################################################
# Finish setup
###############################################################

def _validate_name(name: str) -> str:
    """
    Validate that the string is a legal SQL identifier (letters, digits, underscores).

    Args:
        name: Name (schema, table, or column) to validate.

    Returns:
        The validated name.

    Raises:
        ValueError: If the name does not meet format requirements.
    """
    # Accepts only letters, digits, and underscores; change as needed
    if not (isinstance(name, str) and re.match(r"^[A-Za-z0-9_]+$", name)):
        raise ValueError(f"Unsupported name format {name}")

    return name


def _get_mode(connection_id: str) -> Mode:
    """
    Resolve the current provider Mode for a given connection.

    Raises:
        Exception: If the provider cannot be fetched or the value is unrecognized.

    Returns:
        Mode: The resolved provider mode.
    """
    provider_result = _execute_sql_tool(
        connection_id, "SELECT @@rapid_cloud_provider;"
    )
    if check_error(provider_result):
        raise Exception(
            f"Exception occurred while fetching cloud provider {str(provider_result)}"
        )

    provider = fetch_one(provider_result)

    return Mode.from_string(provider)


def get_error(json_str: Optional[str]) -> Optional[str]:
    """
    Fetches the "error" field at the top level.

    Args:
        json_str (Optional[str]): JSON-encoded string representing a result object (may be None). If not json formatted, then there is assumed to be no error.

    Returns:
        Optional[str]: An error if an error was present
    """
    if json_str is None:
        return None

    try:
        payload = json.loads(json_str)
    except json.JSONDecodeError:
        return None

    if isinstance(payload, dict):
        return payload.get("error", None)
    else:
        return None


def check_error(json_str: Optional[str]) -> bool:
    """
    Check if the provided JSON string contains an "error" field at the top level.

    Args:
        json_str (Optional[str]): JSON-encoded string representing a result object (may be None). If not json formatted, then there is assumed to be no error.

    Returns:
        bool: True if the loaded object has an "error" field; False otherwise.

    Note:
        Assumes the JSON string, if provided, decodes to a top-level dict.
    """
    return get_error(json_str) is not None


def fetch_one(json_str: str) -> str:
    result = json.loads(json_str)

    if len(result) != 1:
        raise Exception(
            json.dumps(
                {
                    "error": f"Unexpected response invalid number of rows actual {len(result)}, expected 1"
                }
            )
        )

    return result[0][0]


@contextlib.contextmanager
def _get_database_connection_cm(connection_id: str):
    """
    Context manager for a MySQLConnection using configuration from load_mysql_config().

    Yields:
        mysql.connector.MySQLConnection: An active connection, automatically closed after the block.

    Raises:
        DatabaseConnectionError: If the connection could not be established or connection_id is invalid.
    """
    conn = _get_db_connection(connection_id)
    try:
        yield conn
    finally:
        conn.close()


def _get_db_connection(connection_id: str) -> MySQLConnectionAbstract:
    if config_error_msg is not None:
        raise DatabaseConnectionError("Configuration file is not loaded")

    if connection_id not in config["server_infos"]:
        raise DatabaseConnectionError(
            f"Connection '{connection_id}' is not a valid connection. "
            "Use list_all_connections() to see available connections."
        )

    connection_info = config["server_infos"][connection_id]
    if "database" not in connection_info:
        raise DatabaseConnectionError("Database must be specified in config.")

    try:
        conn = connector.connect(**connection_info)
    except Exception as e:
        raise DatabaseConnectionError(
            f"Connection failed with error: {e}. "
            "Request assistance from a database administrator, or use list_all_connections() to find a different database connection."
        ) from e

    return conn


@mcp.tool()
def list_all_connections() -> str:
    """
    [MCP Tool] List configured connection keys, validate connectivity, and report mode.

    Args:
        None

    Returns:
        str: JSON-encoded object:
            {
              "valid keys": [{"key": string, "mode": "MYSQL_AI" | "OCI"}],
              "invalid keys": [{"key": string, "error": string, "hint": string}]
            }

    Notes:
        - Attempts to open a connection for each configured key and records success/failure.
        - For valid connections, also resolves the provider Mode via _get_mode.

    MCP usage example:
        - name: list_all_connections
          arguments: {}
    """
    if config_error_msg is not None:
        return config_error_msg

    valid_keys, invalid_keys = [], []
    for connection_id in config["server_infos"].keys():
        try:
            with _get_database_connection_cm(connection_id):
                valid_keys.append(
                    {"key": connection_id, "mode": _get_mode(connection_id).value}
                )
        except Exception as e:
            invalid_keys.append(
                {
                    "key": connection_id,
                    "error": str(e),
                    "hint": f"Bastion/jump host may be down. Try starting it with {get_ssh_command(config)}"
                }
            )
    return json.dumps({"valid keys": valid_keys, "invalid keys": invalid_keys})


@mcp.tool()
def execute_sql_tool_by_connection_id(
    connection_id: str, sql_script: str, params: list = None
) -> str:
    """
    Execute a SQL script on the specified database connection.

    Args:
        connection_id (str): The key identifying the database connection to use.
        sql_script (str): The SQL statement to execute. Can be a query or a DML/DDL statement.
        params (list, optional): List of parameters to use for parameterized SQL scripts. If None, executes with no bind variables.

    Returns:
        str: JSON-encoded result of the query—if rows are returned, their content as a list; otherwise, null.
            In case of error, returns a JSON object with fields: "error", "sql_script", and "params".

    Example:
        result = execute_sql_tool_by_connection_id("my_conn", "SELECT * FROM users WHERE id = %s", [42])
    """
    return _execute_sql_tool(connection_id, sql_script, params=params)


def _execute_sql_tool(
    connection: Union[str, MySQLConnectionAbstract],
    sql_script: str,
    params: list = None,
) -> str:
    """
    Execute a SQL script on the specified database connection.

    Args:
        connection: Union[str, MySQLConnectionAbstract]: Information defining the database connection to use. Allows for reusing a db connection.
        sql_script (str): The SQL statement to execute. Can be a query or a DML/DDL statement.
        params (list, optional): List of parameters to use for parameterized SQL scripts. If None, executes with no bind variables.

    Returns:
        str: JSON-encoded result of the query—if rows are returned, their content as a list; otherwise, null.
            In case of error, returns a JSON object with fields: "error", "sql_script", and "params".

    Example:
        result = _execute_sql_tool("my_conn", "SELECT * FROM users WHERE id = %s", [42])
    """
    should_close = False
    if isinstance(connection, str):
        should_close = True
        try:
            db_connection = _get_db_connection(connection)
        except Exception as e:
            return json.dumps(
                {"error": f"unable to establish a database connection {str(e)}"}
            )
    else:
        db_connection = connection

    try:
        with db_connection.cursor() as cursor:
            results = []
            cursor.execute(sql_script, params or [])

            # Read results from possibly multiple statements
            while True:
                if cursor.with_rows:
                    results.extend(cursor.fetchall())

                # Move to the next result set
                if not cursor.nextset():
                    break

            if len(results) == 0:
                results = None

            db_connection.commit()

            return json.dumps(results)

    except Exception as e:
        return json.dumps(
            {
                "error": f"Error executing SQL: {str(e)}",
                "sql_script": sql_script,
                "params": params,
            }
        )
    finally:
        if should_close:
            db_connection.close()


@mcp.tool()
def ml_generate(connection_id: str, question: str) -> str:
    """
    [MCP Tool] Submit a question to HeatWave GenAI ML_GENERATE and return the generated text.

    Args:
        connection_id (str): MySQL connection key.
        question (str): Prompt text for the LLM.

    Returns:
        str: On success, the generated text (plain string). On failure, a JSON-encoded error object.

    Notes:
        - Uses SELECT sys.ML_GENERATE(%s, NULL) with parameter binding.
        - Prefer ask_ml_rag for retrieval-augmented answers.

    MCP usage example:
        - name: ml_generate
          arguments: {"connection_id": "example_local_server", "question": "Summarize the latest logs."}
    """
    ml_generate_call = "SELECT sys.ML_GENERATE(%s, NULL)"
    response = _execute_sql_tool(
        connection_id,
        ml_generate_call,
        params=[
            question,
        ],
    )

    if check_error(response):
        return json.dumps({"error": f"Error with ML_GENERATE: {response}"})

    try:
        response_data = fetch_one(response)
        response_data = json.loads(response_data)
        return response_data["text"]
    except:
        return json.dumps({"error": "Unexpected response format from ML_GENERATE"})


@mcp.tool()
def ragify_column(
    connection_id: str,
    table_name: str,
    input_column_name: str,
    embedding_column_name: str,
) -> str:
    """
    [MCP Tool] Create or populate a VECTOR column with embeddings from a source text column.

    Summary:
        Uses HeatWave ML_EMBED_TABLE to embed <table>.<input_column_name> into <table>.<embedding_column_name>.

    Danger:
        Issues DDL/DML. Ensure you have authorization and backups.

    Args:
        connection_id (str): MySQL connection key for the target database.
        table_name (str): Unqualified target table name in the current schema.
        input_column_name (str): Unqualified source text column to embed.
        embedding_column_name (str): Unqualified VECTOR column name to store embeddings (created or populated).

    Returns:
        str: Plain success string (e.g., "Successfully embedded '<input>' into '<embedding>' on table <table>").
             On failure, a JSON error object: {"error": "<details>"}.

    Implementation details:
        - Qualifies identifiers with the active schema from the current connection.
        - Invokes: CALL sys.ML_EMBED_TABLE(<schema>.<table>.<input_column_name>, <schema>.<table>.<embedding_column_name>, NULL)
        - Behavior depends on server configuration and HeatWave ML privileges.

    MCP usage example:
        - name: ragify_column
          arguments: {
            "connection_id": "example_local_server",
            "table_name": "docs",
            "input_column_name": "body",
            "embedding_column_name": "embedding"
          }
    """
    with _get_database_connection_cm(connection_id) as db_connection:
        schema = db_connection.database
        qualified_table_name = f"{schema}.{table_name}"

        qualified_text_column_name = f"{qualified_table_name}.{input_column_name}"
        vector_store_column_name = f"{qualified_table_name}.{embedding_column_name}"
        embed_query = "CALL sys.ML_EMBED_TABLE(%s, %s, NULL);"

        response = _execute_sql_tool(
            db_connection,
            embed_query,
            params=[qualified_text_column_name, vector_store_column_name],
        )
        if check_error(response):
            return json.dumps(
                {
                    "error": f"Error with ML_EMBED_TABLE: {response}",
                }
            )

        return f"Successfully added embedding column {input_column_name} to table {table_name}"


@mcp.tool()
def list_vector_store_files_local(connection_id: str) -> str:
    """
    [MCP Tool] List files in the server's secure_file_priv directory for local vector-store loading (MySQL AI mode only).

    Args:
        connection_id (str): MySQL connection key.

    Returns:
        str: JSON-encoded list of relative file names on success; otherwise a JSON error object.

    Notes:
        - Requires provider mode LCL (MySQL AI). For non-MySQL AI providers, use object storage based loaders.

    MCP usage example:
        - name: list_vector_store_files_local
          arguments: {"connection_id": "example_local_server"}
    """
    try:
        mode = _get_mode(connection_id)

        if mode != Mode.MYSQL_AI:
            raise Exception(
                f"Connection is {mode} not MySQL AI use list_vector_store_files_object_store"
            )

        result_str = _execute_sql_tool(
            connection_id,
            "SELECT LIST_FILES(CONCAT('file://', @@secure_file_priv), NULL);",
        )
        result = fetch_one(result_str)
        result = json.loads(result)

        return json.dumps([elem["name"][len("file://") :] for elem in result])
    except Exception as e:
        return json.dumps({"error": f"Error with LIST_FILES: {str(e)}"})


@mcp.tool()
def load_vector_store_local(connection_id: str, file_path: str) -> str:
    """
    [MCP Tool] Load local documents (secure_file_priv) into a MySQL AI vector store.

    Args:
        connection_id (str): MySQL connection key.
        file_path (str): Absolute path under secure_file_priv (use get_secure_file_priv_directory).

    Returns:
        str: JSON-encoded result or JSON error object: {"error": <str>}.

    Notes:
        - Wraps CALL sys.vector_store_load("file://...", NULL). The file must be in secure_file_priv

    MCP usage example:
        - name: load_vector_store_local
          arguments: {"connection_id": "example_local_server", "file_path": "/path/in/secure_file_priv/doc.pdf"}
    """
    try:
        mode = _get_mode(connection_id)

        if mode != Mode.MYSQL_AI:
            raise Exception(
                f"Connection is {mode} not MySQL AI try load_vector_store_oci"
            )

        with _get_database_connection_cm(connection_id) as db_connection:
            file_path = f"file://{file_path}"
            db_connection.autocommit = True
            return _execute_sql_tool(
                db_connection,
                "CALL sys.vector_store_load(%s, NULL);",
                params=[file_path],
            )
    except Exception as e:
        return json.dumps({"error": f"Error with VECTOR_STORE_LOAD: {str(e)}"})


@mcp.tool()
def load_vector_store_oci(
    connection_id: str,
    namespace: str,
    bucket_name: str,
    document_prefix: str,
) -> str:
    """
    [MCP Tool] Load documents from OCI Object Storage into a HeatWave vector store.

    Purpose:
        Load documents from object storage into a vector store for similarity search and RAG.
        The document_prefix can be a file name, a directory/prefix, or a partial prefix.

    Examples (assuming these objects exist in the bucket):
        heatwave-en-ml-9.2.0.pdf
        sample_files/document1.pdf
        sample_files/document2.pdf
        sample_files/documents_345.docx

        Valid document_prefix values:
            'heatwave-en-ml'
            'heatwave-en-ml-9.2.0.pdf'
            'sample_files/'
            'sample_files/document2.pdf'
            'sample_files/doc'

    Args:
        connection_id (str): MySQL connection key (display name of a MySQL-type connection).
        namespace (str): OCI Object Storage namespace.
        bucket_name (str): OCI Object Storage bucket name.
        document_prefix (str): File name or prefix/path used to select documents to load.

    Returns:
        str: JSON-encoded result string from the CALL if successful (often null) or a JSON error object:
             {"error": "<details>"}.

    Notes:
        - Requires an OCI-mode connection (Mode.OCI); for MySQL AI (local) use load_vector_store_local.
        - Wraps:
            CALL sys.vector_store_load('oci://<bucket_name>@<namespace>/<document_prefix>', NULL)
        - Ensure the MySQL DB has IAM/network permissions to access the specified objects in OCI Object Storage.
    """
    try:
        mode = _get_mode(connection_id)

        if mode != Mode.OCI:
            raise Exception(f"Connection is {mode} not OCI try load_vector_store_local")

        file_path = f"oci://{bucket_name}@{namespace}/{document_prefix}"

        return _execute_sql_tool(
            connection_id,
            "CALL sys.vector_store_load(%s, NULL);",
            params=[file_path],
        )
    except Exception as e:
        return json.dumps({"error": f"Error with VECTOR_STORE_LOAD: {str(e)}"})


@mcp.tool()
def ask_ml_rag_vector_store(connection_id: str, question: str, context_size: int = DEFAULT_CONTEXT_SIZE) -> str:
    """
    [MCP Tool] Retrieve segments from the default vector store (skip_generate=true).

    Args:
        connection_id (str): MySQL connection key.
        question (str): Natural language query.
        context_size (int): between (inclusive) 10 and 100, the context size for RAG. Try increasing if RAG call
            does not provide sufficient relevant documents.

    Returns:
        str: Scalar result from SELECT @response (often JSON). On error, a JSON-encoded object.

    Implementation details:
        - Equivalent to ask_ml_rag(connection_id, question).

    MCP usage example:
        - name: ask_ml_rag_vector_store
          arguments: {"connection_id": "example_local_server", "question": "Find information about refunds."}
    """
    if context_size < MIN_CONTEXT_SIZE or MAX_CONTEXT_SIZE < context_size:
        return json.dumps({"error": f"Error choose a context_size in [{MIN_CONTEXT_SIZE}, {MAX_CONTEXT_SIZE}]"})

    return _ask_ml_rag_helper(
        connection_id, question, f"JSON_OBJECT('skip_generate', true, 'n_citations', {context_size})"
    )


@mcp.tool()
def ask_ml_rag_innodb(
    connection_id: str, question: str, segment_col: str, embedding_col: str, context_size: int = DEFAULT_CONTEXT_SIZE
) -> str:
    """
    [MCP Tool] Retrieve segments from InnoDB tables using specified segment and embedding columns.

    Summary:
        Restricts ML_RAG to only consider tables that include:
          - segment_col: the source text column (e.g., created via ragify_column)
          - embedding_col: the corresponding VECTOR column (e.g., 'embedding')
        Both names must be unqualified.

    Args:
        connection_id (str): MySQL connection key.
        question (str): Natural language query.
        segment_col (str): Unqualified text column name (segment).
        embedding_col (str): Unqualified VECTOR column name containing embeddings.
        context_size (int): between (inclusive) 10 and 100, the context size for RAG. Try increasing if RAG call
            does not provide sufficient relevant documents.

    Returns:
        str: Scalar result from SELECT @response (often JSON). On error, a JSON-encoded object.

    Implementation details:
        - Uses options: JSON_OBJECT('skip_generate', true, 'segment', '<segment_col>', 'segment_embedding', '<embedding_col>')
        - Retrieval-only; use ml_generate to produce text from retrieved context.

    MCP usage example:
        - name: ask_ml_rag_innodb
          arguments: {"connection_id": "example_local_server", "question": "Search product docs", "segment_col": "body", "embedding_col": "embedding"}
    """
    if context_size < MIN_CONTEXT_SIZE or MAX_CONTEXT_SIZE < context_size:
        return json.dumps({"error": f"Error choose a context_size in [{MIN_CONTEXT_SIZE}, {MAX_CONTEXT_SIZE}]"})

    try:
        # prevent possible injection
        _validate_name(segment_col)
        _validate_name(embedding_col)
    except Exception as e:
        return json.dumps({"error": f"Error validating names {str(e)}"})

    return _ask_ml_rag_helper(
        connection_id,
        question,
        f"JSON_OBJECT('skip_generate', true, 'n_citations', {context_size}, 'vector_store_columns', "
        f"JSON_OBJECT('segment', '{segment_col}', 'segment_embedding', '{embedding_col}'))",
    )


def _ask_ml_rag_helper(connection_id: str, question: str, options_json_str: str) -> str:
    """
    Internal helper for ML_RAG retrieval calls.

    Args:
        connection_id (str): MySQL connection key.
        question (str): Natural language question.
        options_json_str (str): JSON_OBJECT(...) string specifying ML_RAG options.

    Returns:
        str: Scalar result from SELECT @response (often JSON). On error, a JSON-encoded object.

    Implementation details:
        - Sets @options, invokes ML_RAG, then reads @response in the same session.
    """
    with _get_database_connection_cm(connection_id) as db_connection:
        # Execute the heatwave chat query
        set_response = _execute_sql_tool(db_connection, "SET @options = NULL;")
        if check_error(set_response):
            return json.dumps({"error": f"Error with ML_RAG: {set_response}"})

        rag_response = _execute_sql_tool(
            db_connection,
            f"CALL sys.ML_RAG(%s, @response, {options_json_str});",
            params=[question],
        )
        if check_error(rag_response):
            return json.dumps({"error": f"Error with ML_RAG: {rag_response}"})

        fetch_response = _execute_sql_tool(db_connection, "SELECT @response;")
        if check_error(fetch_response):
            return json.dumps({"error": f"Error with ML_RAG: {fetch_response}"})

        try:
            return fetch_one(fetch_response)
        except:
            return json.dumps({"error": "Unexpected response format from ML_GENERATE"})


@mcp.tool()
def heatwave_ask_help(connection_id: str, question: str) -> str:
    """
    [MCP Tool] Ask natural language questions about MySQL HeatWave AutoML via NL2ML.
    This tool should be prioritized for HeatWave AutoML syntax when trying to call ML stored procedures.

    Args:
        connection_id (str): MySQL connection key (Mode.OCI required for NL2ML).
        question (str): Natural language question about HeatWave AutoML.

    Returns:
        str: JSON string like {"text": "..."} on success; otherwise a JSON error object.

    Notes:
        - Wraps: CALL sys.NL2ML(%s, @nl2ml_response); SELECT @nl2ml_response
        - Answers are grounded in HeatWave AutoML docs and may include executable SQL you can copy/paste.
        - For retrieval-only over vector stores, prefer ask_ml_rag_vector_store or ask_ml_rag_innodb.

    MCP usage example:
        - name: heatwave_ask_help
          arguments: {"connection_id": "example_oci_server", "question": "What tasks does ML_TRAIN support?"}

    Example interactions:
        Q: Is there any limit on the size of the training table?
        A: Yes, the table used to train a model cannot exceed 10 GB, 100 million rows, or 1017 columns.

        Q: Give me a training query for email spam detection.
        A: CALL sys.ML_TRAIN('mlcorpus.emails', 'spam_label', JSON_OBJECT('task','classification'), @email_spam_model);
    """
    try:
        mode = _get_mode(connection_id)

        if mode != Mode.OCI:
            raise Exception(f"Connection is {mode} which does not support NL2ML")

        nl2ml_call = "call sys.NL2ML(%s, @nl2ml_response); select @nl2ml_response"

        response = _execute_sql_tool(
            connection_id,
            nl2ml_call,
            params=[question],
        )
        if check_error(response):
            raise Exception(f"Exception occured while executing NL2ML call {response}")

        return fetch_one(response)
    except Exception as e:
        return json.dumps({"error": f"Error with NL2ML: {str(e)}"})


"""
Object store
"""


def verify_compartment_access(compartments):
    access_report = {}

    for compartment in compartments:
        access_report[compartment.name] = {
            "compartment_id": compartment.id,
            "object_storage": False,
            "databases": False,
            "errors": []
        }

        # Test Object Storage
        try:
            namespace = oci_info.object_storage_client.get_namespace().data
            list_buckets_response = oci_info.object_storage_client.list_buckets(
                namespace_name=namespace, compartment_id=compartment.id
            )
            access_report[compartment.name]["object_storage"] = True
        except Exception as e:
            access_report[compartment.name]["errors"].append(f"Object Storage: {str(e)}")

    return access_report

@mcp.tool()
def list_all_compartments() -> str:
    """
    [MCP Tool] List all compartments in the tenancy.

    Args:
        None

    Returns:
        str: Stringified per-compartment access report:
             {
               "<compartment_name>": {
                 "compartment_id": "<ocid>",
                 "object_storage": true|false,
                 "databases": true|false,
                 "errors": [ "<error strings>" ]
               },
               ...
             }
             If OCI is not configured, unavailable, or an error occurs, returns:
             {"error": "<details>"}.

    Notes:
        - Uses PROFILE_NAME env var (default "DEFAULT") to select OCI CLI profile for authentication.
        - If OCI is not available (oci_info is None), an error JSON is returned.
        - Enumerates compartments via IdentityClient.list_compartments() and verifies Object Storage access to populate object_storage and errors fields.
    """
    if oci_error_msg is not None:
        return oci_error_msg

    compartments = []
    try:
        compartments = oci_info.identity_client.list_compartments(
            oci_info.tenancy_id
        ).data
    except Exception as e:
        return json.dumps({"error": f"Error with list_compartments: {str(e)}"})

    access_report = verify_compartment_access(compartments)

    return str(access_report)


def _get_compartment_by_name(
    compartment_name: str,
) -> Optional[oci.identity.models.Compartment]:
    """
    Internal helper to get a compartment by name.

    Args:
        compartment_name (str): Case-insensitive compartment name to look up.

    Returns:
        oci.identity.models.Compartment | None:
            - Compartment object if found
            - None if not found

    Notes:
        - Searches accessible compartments in subtree and includes the root tenancy.
        - Intended for internal use by Object Storage helpers.
        - May raise exception
    """
    if oci_error_msg is not None:
        return None

    compartments = oci_info.identity_client.list_compartments(
        compartment_id=oci_info.tenancy_id,
        compartment_id_in_subtree=True,
        access_level="ACCESSIBLE",
        lifecycle_state="ACTIVE",
    )
    compartments.data.append(
        oci_info.identity_client.get_compartment(
            compartment_id=oci_info.tenancy_id
        ).data
    )

    # Search for the compartment by name
    for compartment in compartments.data:
        if compartment.name.lower() == compartment_name.lower():
            return compartment

    return None


@mcp.tool()
def object_storage_list_buckets(
    compartment_name: str = None, compartment_id: str = None
) -> str:
    """
    [MCP Tool] List all accessible Object Storage buckets in a compartment.

    Args:
        compartment_name (str, optional): Case-insensitive compartment name to resolve to an OCID.
        compartment_id (str, optional): Compartment OCID. If provided, takes precedence over name resolution.

    Returns:
        str: Stringified list of oci.object_storage.models.BucketSummary objects on success.
             On error, a JSON object: {"error": "<details>"}.

    Notes:
        - Resolves the compartment by name when provided, otherwise uses compartment_id directly.
        - Uses the account's Object Storage namespace and lists all buckets within the compartment.
        - Pair with list_all_compartments to discover compartment names/OCIDs.
    """
    if oci_error_msg is not None:
        return oci_error_msg

    try:
        if compartment_id is None and compartment_name:
            comp = _get_compartment_by_name(compartment_name)
            if comp and not isinstance(comp, str):
                compartment_id = comp.id
        namespace = oci_info.object_storage_client.get_namespace().data
        list_buckets_response = oci_info.object_storage_client.list_buckets(
            namespace_name=namespace, compartment_id=compartment_id
        )
        return str(list_buckets_response.data)
    except Exception as e:
        return json.dumps({"error": f"Error listing buckets: {str(e)}"})


@mcp.tool()
def object_storage_list_objects(namespace: str, bucket_name: str) -> str:
    """
    [MCP Tool] List objects stored in an OCI Object Storage bucket.

    Args:
        namespace (str): Object Storage namespace for the tenancy.
        bucket_name (str): Name of the bucket to list objects from.

    Returns:
        str: Stringified list of oci.object_storage.models.ObjectSummary objects on success.
             On error, a JSON object: {"error": "<details>"}.

    Notes:
        - Use together with object_storage_list_buckets to find buckets and with list_all_compartments to enumerate compartments.
        - Requires valid OCI configuration (PROFILE_NAME env or default profile).
    """
    if oci_error_msg is not None:
        return oci_error_msg

    try:
        # List objects in a specified bucket
        list_object_response = oci_info.object_storage_client.list_objects(
            namespace_name=namespace, bucket_name=bucket_name
        )
    except Exception as e:
        return json.dumps(
            {"error": f"Error with listing objects in a specified bucket: {str(e)}"}
        )

    return str(list_object_response.data.objects)


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")
