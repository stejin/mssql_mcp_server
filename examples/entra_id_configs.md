# Microsoft Entra ID Authentication Examples

This document provides configuration examples for using the enhanced MSSQL MCP server with different Microsoft Entra ID authentication methods.

## Prerequisites

1. Install the enhanced dependencies:
   ```bash
   pip install azure-identity azure-core pyodbc
   ```

2. Ensure ODBC Driver 17 for SQL Server is installed

## Configuration Methods

### 1. Windows Authentication (Trusted Connection)

For on-premises SQL Server on domain-joined Windows machines:

```bash
export MSSQL_AUTH_METHOD="windows"
export MSSQL_SERVER="your-server\SQLEXPRESS"  # or just "your-server"
export MSSQL_DATABASE="your_database"
```

**Claude Desktop Config:**
```json
{
  "mcpServers": {
    "mssql": {
      "command": "python",
      "args": ["C:\\path\\to\\mssql_mcp_server\\src\\mssql_mcp_server\\server_enhanced.py"],
      "env": {
        "MSSQL_AUTH_METHOD": "windows",
        "MSSQL_SERVER": "your-server\\SQLEXPRESS",
        "MSSQL_DATABASE": "your_database"
      }
    }
  }
}
```

**Note:**
- Uses the currently logged-in Windows user credentials
- No username/password required
- Works with on-premises SQL Server
- Requires domain-joined Windows machine or local SQL Server authentication

### 2. SQL Server Authentication (Default)

Traditional username/password authentication:

```bash
export MSSQL_AUTH_METHOD="sql"
export MSSQL_SERVER="your-server.database.windows.net,1433"
export MSSQL_USER="your_username"
export MSSQL_PASSWORD="your_password"
export MSSQL_DATABASE="your_database"
```

**Claude Desktop Config:**
```json
{
  "mcpServers": {
    "mssql": {
      "command": "python",
      "args": ["src/mssql_mcp_server/server_enhanced.py"],
      "env": {
        "MSSQL_AUTH_METHOD": "sql",
        "MSSQL_SERVER": "your-server.database.windows.net,1433",
        "MSSQL_USER": "your_username",
        "MSSQL_PASSWORD": "your_password",
        "MSSQL_DATABASE": "your_database"
      }
    }
  }
}
```

### 3. Entra ID Password Authentication

Username/password with Entra ID:

```bash
export MSSQL_AUTH_METHOD="entra_password"
export MSSQL_SERVER="your-server.database.windows.net,1433"
export MSSQL_USER="user@yourdomain.com"
export MSSQL_PASSWORD="your_entra_password"
export MSSQL_DATABASE="your_database"
```

**Claude Desktop Config:**
```json
{
  "mcpServers": {
    "mssql": {
      "command": "python",
      "args": ["src/mssql_mcp_server/server_enhanced.py"],
      "env": {
        "MSSQL_AUTH_METHOD": "entra_password",
        "MSSQL_SERVER": "your-server.database.windows.net,1433",
        "MSSQL_USER": "user@yourdomain.com",
        "MSSQL_PASSWORD": "your_entra_password",
        "MSSQL_DATABASE": "your_database"
      }
    }
  }
}
```

### 4. Entra ID Service Principal Authentication

Application-based authentication:

```bash
export MSSQL_AUTH_METHOD="entra_service_principal"
export MSSQL_SERVER="your-server.database.windows.net,1433"
export MSSQL_CLIENT_ID="your-app-client-id"
export MSSQL_CLIENT_SECRET="your-app-client-secret"
export MSSQL_TENANT_ID="your-tenant-id"  # Optional
export MSSQL_DATABASE="your_database"
```

**Claude Desktop Config:**
```json
{
  "mcpServers": {
    "mssql": {
      "command": "python",
      "args": ["src/mssql_mcp_server/server_enhanced.py"],
      "env": {
        "MSSQL_AUTH_METHOD": "entra_service_principal",
        "MSSQL_SERVER": "your-server.database.windows.net,1433",
        "MSSQL_CLIENT_ID": "your-app-client-id",
        "MSSQL_CLIENT_SECRET": "your-app-client-secret",
        "MSSQL_DATABASE": "your_database"
      }
    }
  }
}
```

### 5. Entra ID Managed Identity Authentication

For Azure VMs, Container Instances, App Service, etc.:

**System-Assigned Managed Identity:**
```bash
export MSSQL_AUTH_METHOD="entra_managed_identity"
export MSSQL_SERVER="your-server.database.windows.net,1433"
export MSSQL_DATABASE="your_database"
```

**User-Assigned Managed Identity:**
```bash
export MSSQL_AUTH_METHOD="entra_managed_identity"
export MSSQL_SERVER="your-server.database.windows.net,1433"
export MSSQL_CLIENT_ID="user-assigned-identity-client-id"
export MSSQL_DATABASE="your_database"
```

### 6. Entra ID Integrated Authentication

For domain-joined Windows machines:

```bash
export MSSQL_AUTH_METHOD="entra_integrated"
export MSSQL_SERVER="your-server.database.windows.net,1433"
export MSSQL_DATABASE="your_database"
```

### 7. Entra ID Interactive/Default Authentication

Uses DefaultAzureCredential with access token:

```bash
export MSSQL_AUTH_METHOD="entra_interactive"
export MSSQL_SERVER="your-server.database.windows.net,1433"
export MSSQL_DATABASE="your_database"
```

This method tries multiple authentication methods in order:
1. Environment variables (if set)
2. Managed Identity (if running on Azure)
3. Azure CLI (if logged in)
4. Visual Studio (if logged in)
5. Visual Studio Code (if logged in)
6. Interactive browser (as fallback)

## Additional Configuration Options

### Connection Security

```bash
# Encryption (default: yes)
export MSSQL_ENCRYPT="yes"

# Trust server certificate (default: no)
export MSSQL_TRUST_SERVER_CERTIFICATE="no"

# Connection timeout in seconds (default: 30)
export MSSQL_CONNECTION_TIMEOUT="30"
```

### Complete Example with Security Options

```bash
export MSSQL_AUTH_METHOD="entra_service_principal"
export MSSQL_SERVER="myserver.database.windows.net,1433"
export MSSQL_CLIENT_ID="12345678-1234-1234-1234-123456789abc"
export MSSQL_CLIENT_SECRET="your-secret-here"
export MSSQL_DATABASE="MyDatabase"
export MSSQL_ENCRYPT="yes"
export MSSQL_TRUST_SERVER_CERTIFICATE="no"
export MSSQL_CONNECTION_TIMEOUT="60"
```

## Testing Authentication

Use the enhanced server's built-in authentication test tool:

```python
# Run the server and use the get_auth_info tool
python src/mssql_mcp_server/server_enhanced.py
```

The server will test the connection on startup and provide detailed authentication information.

## Troubleshooting

### Common Issues

1. **Azure libraries not found**: Install `azure-identity` and `azure-core`
2. **ODBC Driver missing**: Install "ODBC Driver 17 for SQL Server"
3. **Service Principal permissions**: Ensure the app registration has database access
4. **Managed Identity not configured**: Set up managed identity in Azure portal
5. **Token refresh issues**: The server automatically handles token refresh

### Debugging

Enable detailed logging by setting the log level:

```python
import logging
logging.getLogger("azure").setLevel(logging.DEBUG)
logging.getLogger("mssql_mcp_server_enhanced").setLevel(logging.DEBUG)
```

## Azure SQL Database Setup

### For Service Principal Authentication

1. **Create App Registration in Entra ID:**
   ```bash
   # Using Azure CLI
   az ad app create --display-name "MSSQL MCP Server"
   az ad sp create-for-rbac --name "MSSQL MCP Server"
   ```

2. **Create Database User for Service Principal:**
   ```sql
   -- Connect to your Azure SQL Database as admin
   CREATE USER [your-app-name] FROM EXTERNAL PROVIDER;
   ALTER ROLE db_datareader ADD MEMBER [your-app-name];
   -- Add additional roles as needed
   ```

### For Managed Identity Authentication

1. **Enable Managed Identity on your Azure resource**
2. **Create Database User for Managed Identity:**
   ```sql
   -- For system-assigned managed identity
   CREATE USER [your-vm-name] FROM EXTERNAL PROVIDER;
   ALTER ROLE db_datareader ADD MEMBER [your-vm-name];
   
   -- For user-assigned managed identity
   CREATE USER [your-identity-name] FROM EXTERNAL PROVIDER;
   ALTER ROLE db_datareader ADD MEMBER [your-identity-name];
   ```

## Security Best Practices

1. **Use least privilege**: Grant only necessary database permissions
2. **Rotate secrets**: Regularly rotate client secrets for service principals
3. **Use managed identities**: Prefer managed identities over service principals when possible
4. **Monitor access**: Enable Azure SQL auditing and monitoring
5. **Secure connection strings**: Never log or expose connection strings with secrets

