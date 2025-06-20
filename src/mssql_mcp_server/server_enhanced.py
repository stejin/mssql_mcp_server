import asyncio
import logging
import os
import struct
from typing import Optional, Dict, Any
import pyodbc
from mcp.server import Server
from mcp.types import Resource, Tool, TextContent
from pydantic import AnyUrl

# Optional Azure imports for Entra ID authentication
try:
    from azure.identity import (
        DefaultAzureCredential,
        ClientSecretCredential,
        ManagedIdentityCredential,
        UsernamePasswordCredential,
        InteractiveBrowserCredential
    )
    from azure.core.exceptions import ClientAuthenticationError
    AZURE_AUTH_AVAILABLE = True
except ImportError:
    AZURE_AUTH_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mssql_mcp_server_enhanced")

class AuthenticationMethod:
    """Authentication method constants."""
    SQL = "sql"
    ENTRA_INTEGRATED = "entra_integrated"
    ENTRA_PASSWORD = "entra_password"
    ENTRA_SERVICE_PRINCIPAL = "entra_service_principal"
    ENTRA_MANAGED_IDENTITY = "entra_managed_identity"
    ENTRA_INTERACTIVE = "entra_interactive"

def get_db_config() -> Dict[str, Any]:
    """Get database configuration from environment variables with support for multiple auth methods."""
    config = {
        # Basic connection settings
        "server": os.getenv("MSSQL_SERVER"),
        "database": os.getenv("MSSQL_DATABASE"),
        "auth_method": os.getenv("MSSQL_AUTH_METHOD", AuthenticationMethod.SQL).lower(),
        
        # SQL Server Authentication
        "user": os.getenv("MSSQL_USER"),
        "password": os.getenv("MSSQL_PASSWORD"),
        
        # Entra ID Authentication
        "client_id": os.getenv("MSSQL_CLIENT_ID"),
        "client_secret": os.getenv("MSSQL_CLIENT_SECRET"),
        "tenant_id": os.getenv("MSSQL_TENANT_ID"),
        
        # Connection options
        "connection_timeout": int(os.getenv("MSSQL_CONNECTION_TIMEOUT", "30")),
        "encrypt": os.getenv("MSSQL_ENCRYPT", "yes").lower() in ("yes", "true", "1"),
        "trust_server_certificate": os.getenv("MSSQL_TRUST_SERVER_CERTIFICATE", "no").lower() in ("yes", "true", "1"),
    }
    
    # Validate required fields
    if not config["server"] or not config["database"]:
        logger.error("Missing required database configuration: MSSQL_SERVER and MSSQL_DATABASE are required")
        raise ValueError("Missing required database configuration")
    
    # Validate auth-specific requirements
    auth_method = config["auth_method"]
    if auth_method == AuthenticationMethod.SQL:
        if not config["user"] or not config["password"]:
            logger.error("SQL Authentication requires MSSQL_USER and MSSQL_PASSWORD")
            raise ValueError("SQL Authentication requires MSSQL_USER and MSSQL_PASSWORD")
    
    elif auth_method == AuthenticationMethod.ENTRA_PASSWORD:
        if not config["user"] or not config["password"]:
            logger.error("Entra ID Password Authentication requires MSSQL_USER and MSSQL_PASSWORD")
            raise ValueError("Entra ID Password Authentication requires MSSQL_USER and MSSQL_PASSWORD")
    
    elif auth_method == AuthenticationMethod.ENTRA_SERVICE_PRINCIPAL:
        if not config["client_id"] or not config["client_secret"]:
            logger.error("Entra ID Service Principal Authentication requires MSSQL_CLIENT_ID and MSSQL_CLIENT_SECRET")
            raise ValueError("Entra ID Service Principal Authentication requires MSSQL_CLIENT_ID and MSSQL_CLIENT_SECRET")
    
    elif auth_method == AuthenticationMethod.ENTRA_MANAGED_IDENTITY:
        # client_id is optional for user-assigned managed identity
        pass
    
    elif auth_method not in [AuthenticationMethod.ENTRA_INTEGRATED, AuthenticationMethod.ENTRA_INTERACTIVE]:
        logger.error(f"Unsupported authentication method: {auth_method}")
        raise ValueError(f"Unsupported authentication method: {auth_method}")
    
    return config

def get_sql_auth_connection(config: Dict[str, Any]) -> pyodbc.Connection:
    """Create connection using SQL Server Authentication."""
    conn_string = f'''DRIVER={{ODBC Driver 17 for SQL Server}};
SERVER={config["server"]};
DATABASE={config["database"]};
UID={config["user"]};
PWD={config["password"]};
Encrypt={"yes" if config["encrypt"] else "no"};
TrustServerCertificate={"yes" if config["trust_server_certificate"] else "no"};
Connection Timeout={config["connection_timeout"]};'''
    
    logger.info(f"Connecting with SQL Authentication to {config['server']}/{config['database']} as {config['user']}")
    return pyodbc.connect(conn_string)

def get_entra_integrated_connection(config: Dict[str, Any]) -> pyodbc.Connection:
    """Create connection using Entra ID Integrated Authentication."""
    if not AZURE_AUTH_AVAILABLE:
        raise ImportError("Azure authentication libraries not available. Install azure-identity.")
    
    conn_string = f'''DRIVER={{ODBC Driver 17 for SQL Server}};
SERVER={config["server"]};
DATABASE={config["database"]};
Authentication=ActiveDirectoryIntegrated;
Encrypt={"yes" if config["encrypt"] else "no"};
TrustServerCertificate={"yes" if config["trust_server_certificate"] else "no"};
Connection Timeout={config["connection_timeout"]};'''
    
    logger.info(f"Connecting with Entra ID Integrated Authentication to {config['server']}/{config['database']}")
    return pyodbc.connect(conn_string)

def get_entra_password_connection(config: Dict[str, Any]) -> pyodbc.Connection:
    """Create connection using Entra ID Username/Password Authentication."""
    if not AZURE_AUTH_AVAILABLE:
        raise ImportError("Azure authentication libraries not available. Install azure-identity.")
    
    conn_string = f'''DRIVER={{ODBC Driver 17 for SQL Server}};
SERVER={config["server"]};
DATABASE={config["database"]};
UID={config["user"]};
PWD={config["password"]};
Authentication=ActiveDirectoryPassword;
Encrypt={"yes" if config["encrypt"] else "no"};
TrustServerCertificate={"yes" if config["trust_server_certificate"] else "no"};
Connection Timeout={config["connection_timeout"]};'''
    
    logger.info(f"Connecting with Entra ID Password Authentication to {config['server']}/{config['database']} as {config['user']}")
    return pyodbc.connect(conn_string)

def get_entra_service_principal_connection(config: Dict[str, Any]) -> pyodbc.Connection:
    """Create connection using Entra ID Service Principal Authentication."""
    if not AZURE_AUTH_AVAILABLE:
        raise ImportError("Azure authentication libraries not available. Install azure-identity.")
    
    conn_string = f'''DRIVER={{ODBC Driver 17 for SQL Server}};
SERVER={config["server"]};
DATABASE={config["database"]};
UID={config["client_id"]};
PWD={config["client_secret"]};
Authentication=ActiveDirectoryServicePrincipal;
Encrypt={"yes" if config["encrypt"] else "no"};
TrustServerCertificate={"yes" if config["trust_server_certificate"] else "no"};
Connection Timeout={config["connection_timeout"]};'''
    
    logger.info(f"Connecting with Entra ID Service Principal Authentication to {config['server']}/{config['database']} as {config['client_id']}")
    return pyodbc.connect(conn_string)

def get_entra_managed_identity_connection(config: Dict[str, Any]) -> pyodbc.Connection:
    """Create connection using Entra ID Managed Identity Authentication."""
    if not AZURE_AUTH_AVAILABLE:
        raise ImportError("Azure authentication libraries not available. Install azure-identity.")
    
    if config.get("client_id"):
        # User-assigned managed identity
        conn_string = f'''DRIVER={{ODBC Driver 17 for SQL Server}};
SERVER={config["server"]};
DATABASE={config["database"]};
Authentication=ActiveDirectoryMsi;
UID={config["client_id"]};
Encrypt={"yes" if config["encrypt"] else "no"};
TrustServerCertificate={"yes" if config["trust_server_certificate"] else "no"};
Connection Timeout={config["connection_timeout"]};'''
        logger.info(f"Connecting with Entra ID User-Assigned Managed Identity to {config['server']}/{config['database']} (Client ID: {config['client_id']})")
    else:
        # System-assigned managed identity
        conn_string = f'''DRIVER={{ODBC Driver 17 for SQL Server}};
SERVER={config["server"]};
DATABASE={config["database"]};
Authentication=ActiveDirectoryMsi;
Encrypt={"yes" if config["encrypt"] else "no"};
TrustServerCertificate={"yes" if config["trust_server_certificate"] else "no"};
Connection Timeout={config["connection_timeout"]};'''
        logger.info(f"Connecting with Entra ID System-Assigned Managed Identity to {config['server']}/{config['database']}")
    
    return pyodbc.connect(conn_string)

def get_entra_interactive_connection(config: Dict[str, Any]) -> pyodbc.Connection:
    """Create connection using Entra ID Interactive Authentication with access token."""
    if not AZURE_AUTH_AVAILABLE:
        raise ImportError("Azure authentication libraries not available. Install azure-identity.")
    
    try:
        # Get access token using DefaultAzureCredential (supports multiple auth flows)
        credential = DefaultAzureCredential()
        token = credential.get_token("https://database.windows.net/")
        
        # Convert token to the format expected by pyodbc
        token_bytes = token.token.encode("UTF-16-LE")
        token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
        
        conn_string = f'''DRIVER={{ODBC Driver 17 for SQL Server}};
SERVER={config["server"]};
DATABASE={config["database"]};
Encrypt={"yes" if config["encrypt"] else "no"};
TrustServerCertificate={"yes" if config["trust_server_certificate"] else "no"};
Connection Timeout={config["connection_timeout"]};'''
        
        logger.info(f"Connecting with Entra ID Interactive/Default Authentication to {config['server']}/{config['database']}")
        return pyodbc.connect(conn_string, attrs_before={1256: token_struct})  # SQL_COPT_SS_ACCESS_TOKEN
        
    except Exception as e:
        logger.error(f"Failed to authenticate with DefaultAzureCredential: {e}")
        raise

def get_connection() -> pyodbc.Connection:
    """Create database connection based on configured authentication method."""
    config = get_db_config()
    auth_method = config["auth_method"]
    
    try:
        if auth_method == AuthenticationMethod.SQL:
            return get_sql_auth_connection(config)
        elif auth_method == AuthenticationMethod.ENTRA_INTEGRATED:
            return get_entra_integrated_connection(config)
        elif auth_method == AuthenticationMethod.ENTRA_PASSWORD:
            return get_entra_password_connection(config)
        elif auth_method == AuthenticationMethod.ENTRA_SERVICE_PRINCIPAL:
            return get_entra_service_principal_connection(config)
        elif auth_method == AuthenticationMethod.ENTRA_MANAGED_IDENTITY:
            return get_entra_managed_identity_connection(config)
        elif auth_method == AuthenticationMethod.ENTRA_INTERACTIVE:
            return get_entra_interactive_connection(config)
        else:
            raise ValueError(f"Unsupported authentication method: {auth_method}")
    
    except Exception as e:
        logger.error(f"Failed to connect using {auth_method} authentication: {e}")
        raise

# Initialize server
app = Server("mssql_mcp_server_enhanced")

@app.list_resources()
async def list_resources() -> list[Resource]:
    """List SQL Server tables as resources."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        # Query to get user tables from the current database
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        tables = cursor.fetchall()
        logger.info(f"Found {len(tables)} tables")
        
        resources = []
        for table in tables:
            resources.append(
                Resource(
                    uri=f"mssql://{table[0]}/data",
                    name=f"Table: {table[0]}",
                    mimeType="text/plain",
                    description=f"Data in table: {table[0]}"
                )
            )
        cursor.close()
        conn.close()
        return resources
    except Exception as e:
        logger.error(f"Failed to list resources: {str(e)}")
        return []

@app.read_resource()
async def read_resource(uri: AnyUrl) -> str:
    """Read table contents."""
    uri_str = str(uri)
    logger.info(f"Reading resource: {uri_str}")
    
    if not uri_str.startswith("mssql://"):
        raise ValueError(f"Invalid URI scheme: {uri_str}")
        
    parts = uri_str[8:].split('/')
    table = parts[0]
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        # Use TOP 100 for MSSQL (equivalent to LIMIT in MySQL)
        cursor.execute(f"SELECT TOP 100 * FROM [{table}]")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        # Convert rows to strings, handling None values
        result = []
        for row in rows:
            row_str = ",".join(str(col) if col is not None else "NULL" for col in row)
            result.append(row_str)
        
        cursor.close()
        conn.close()
        return "\n".join([",".join(columns)] + result)
                
    except Exception as e:
        logger.error(f"Database error reading resource {uri}: {str(e)}")
        raise RuntimeError(f"Database error: {str(e)}")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available SQL Server tools."""
    logger.info("Listing tools...")
    return [
        Tool(
            name="execute_sql",
            description="Execute an SQL query on the SQL Server",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The SQL query to execute"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_auth_info",
            description="Get information about the current authentication method and connection",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute SQL commands or get authentication info."""
    logger.info(f"Calling tool: {name} with arguments: {arguments}")
    
    if name == "get_auth_info":
        try:
            config = get_db_config()
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get connection and authentication info
            cursor.execute("SELECT @@VERSION, DB_NAME(), SYSTEM_USER, USER_NAME(), HOST_NAME()")
            result = cursor.fetchone()
            
            auth_info = f"""Authentication Information:
Method: {config['auth_method']}
Server: {config['server']}
Database: {result[1] if result else 'Unknown'}
System User: {result[2] if result else 'Unknown'}
Database User: {result[3] if result else 'Unknown'}
Host: {result[4] if result else 'Unknown'}
Azure Auth Available: {AZURE_AUTH_AVAILABLE}
SQL Server Version: {result[0][:100] if result else 'Unknown'}..."""
            
            cursor.close()
            conn.close()
            return [TextContent(type="text", text=auth_info)]
            
        except Exception as e:
            logger.error(f"Error getting auth info: {e}")
            return [TextContent(type="text", text=f"Error getting authentication info: {str(e)}")]
    
    elif name == "execute_sql":
        query = arguments.get("query")
        if not query:
            raise ValueError("Query is required")
        
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(query)
            
            # Special handling for table listing queries
            if query.strip().upper().startswith("SELECT") and "INFORMATION_SCHEMA.TABLES" in query.upper():
                # Check if this is a simple table listing vs. other queries on INFORMATION_SCHEMA.TABLES
                if "TABLE_NAME" in query.upper() and "COUNT(*)" not in query.upper():
                    # This is a table listing query
                    tables = cursor.fetchall()
                    config = get_db_config()
                    result = ["Tables_in_" + config["database"]]  # Header
                    result.extend([str(table[0]) for table in tables])  # Ensure string conversion
                    cursor.close()
                    conn.close()
                    return [TextContent(type="text", text="\n".join(result))]
                # For other INFORMATION_SCHEMA.TABLES queries (like COUNT), fall through to regular SELECT handling
            
            # Regular SELECT queries (including those that didn't match special handling above)
            if query.strip().upper().startswith("SELECT"):
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    
                    # Create header row
                    result_lines = [",".join(columns)]
                    
                    # Convert data rows
                    for row in rows:
                        # Convert each column value to string, handling None values
                        row_values = []
                        for col in row:
                            if col is None:
                                row_values.append("NULL")
                            else:
                                row_values.append(str(col))
                        result_lines.append(",".join(row_values))
                    
                    cursor.close()
                    conn.close()
                    return [TextContent(type="text", text="\n".join(result_lines))]
                else:
                    cursor.close()
                    conn.close()
                    return [TextContent(type="text", text="Query executed successfully (no results returned)")]
            
            # Non-SELECT queries
            else:
                conn.commit()
                affected_rows = cursor.rowcount
                cursor.close()
                conn.close()
                return [TextContent(type="text", text=f"Query executed successfully. Rows affected: {affected_rows}")]
                    
        except Exception as e:
            logger.error(f"Error executing SQL '{query}': {e}")
            return [TextContent(type="text", text=f"Error executing query: {str(e)}")]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    """Main entry point to run the MCP server."""
    from mcp.server.stdio import stdio_server
    
    logger.info("Starting Enhanced MSSQL MCP server with Entra ID support...")
    
    # Log available authentication methods
    logger.info(f"Azure authentication libraries available: {AZURE_AUTH_AVAILABLE}")
    
    config = get_db_config()
    logger.info(f"Authentication method: {config['auth_method']}")
    logger.info(f"Database config: {config['server']}/{config['database']}")
    
    # Test connection on startup
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION, DB_NAME(), SYSTEM_USER")
        result = cursor.fetchone()
        logger.info(f"✅ Connection test successful!")
        logger.info(f"Connected to: {result[1]} as {result[2]}")
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"❌ Database connection test failed: {e}")
        raise
    
    async with stdio_server() as (read_stream, write_stream):
        try:
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
        except Exception as e:
            logger.error(f"Server error: {str(e)}", exc_info=True)
            raise

if __name__ == "__main__":
    asyncio.run(main())

