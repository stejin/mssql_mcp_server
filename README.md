# Microsoft SQL Server MCP Server

A Model Context Protocol (MCP) server that enables secure interaction with Microsoft SQL Server databases. This server allows AI assistants to list tables, read data, and execute SQL queries through a controlled interface, making database exploration and analysis safer and more structured.

<a href="https://glama.ai/mcp/servers/29cpe19k30">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/29cpe19k30/badge" alt="Microsoft SQL Server Server MCP server" />
</a>

## Features

- List available SQL Server tables as resources
- Read table contents
- Execute SQL queries with proper error handling
- Secure database access through environment variables
- Comprehensive logging
- Automatic system dependency installation
- **Azure SQL Support**: Enhanced support for Azure SQL Database and Managed Instance
- **Multiple Driver Options**: Both pymssql and pyodbc drivers supported
- **Microsoft Entra ID Authentication**: Complete support for modern Azure authentication methods
  - Service Principal authentication
  - Managed Identity authentication (system and user-assigned)
  - Integrated authentication
  - Password authentication
  - Interactive/Default authentication with automatic token handling

## Installation

The package will automatically install required system dependencies (like FreeTDS) when installed through MCP:

```bash
pip install mssql-mcp-server
```

## Configuration

Set the following environment variables:

```bash
MSSQL_SERVER=localhost
MSSQL_USER=your_username
MSSQL_PASSWORD=your_password
MSSQL_DATABASE=your_database
```

### Azure SQL Database / Managed Instance

For Azure SQL, use the full server name with port:

```bash
MSSQL_SERVER=your-server.database.windows.net,1433
MSSQL_USER=your_username
MSSQL_PASSWORD=your_password
MSSQL_DATABASE=your_database
```

### Driver Selection

This server supports both `pymssql` and `pyodbc` drivers:

- **pymssql** (default): Lighter weight, good for basic SQL Server connections
- **pyodbc**: Better Azure SQL support, more robust for cloud scenarios

For Azure SQL Database or Managed Instance, use the pyodbc version:

```bash
python src/mssql_mcp_server/server_pyodbc.py
```

## Microsoft Entra ID Authentication

The enhanced server (`server_enhanced.py`) supports multiple Microsoft Entra ID authentication methods for Azure SQL Database and Managed Instance.

### Installation

Install additional dependencies for Entra ID support:

```bash
pip install azure-identity azure-core pyodbc
```

### Authentication Methods

#### 1. Windows Authentication (Trusted Connection)

For on-premises SQL Server on domain-joined Windows machines:

```bash
export MSSQL_AUTH_METHOD="windows"
export MSSQL_SERVER="your-server\INSTANCE"  # or just "your-server"
export MSSQL_DATABASE="your_database"
```

**Note:** Uses the currently logged-in Windows user credentials. No username/password required.

#### 2. Service Principal Authentication

Recommended for applications and automation:

```bash
export MSSQL_AUTH_METHOD="entra_service_principal"
export MSSQL_SERVER="your-server.database.windows.net,1433"
export MSSQL_CLIENT_ID="your-app-client-id"
export MSSQL_CLIENT_SECRET="your-app-client-secret"
export MSSQL_DATABASE="your_database"
```

#### 3. Managed Identity Authentication

For Azure VMs, Container Instances, App Service:

```bash
# System-assigned managed identity
export MSSQL_AUTH_METHOD="entra_managed_identity"
export MSSQL_SERVER="your-server.database.windows.net,1433"
export MSSQL_DATABASE="your_database"

# User-assigned managed identity
export MSSQL_AUTH_METHOD="entra_managed_identity"
export MSSQL_CLIENT_ID="user-assigned-identity-client-id"
export MSSQL_SERVER="your-server.database.windows.net,1433"
export MSSQL_DATABASE="your_database"
```

#### 4. Interactive/Default Authentication

Uses DefaultAzureCredential chain (recommended for development):

```bash
export MSSQL_AUTH_METHOD="entra_interactive"
export MSSQL_SERVER="your-server.database.windows.net,1433"
export MSSQL_DATABASE="your_database"
```

#### 5. Entra ID Password Authentication

For user credentials with Entra ID:

```bash
export MSSQL_AUTH_METHOD="entra_password"
export MSSQL_SERVER="your-server.database.windows.net,1433"
export MSSQL_USER="user@yourdomain.com"
export MSSQL_PASSWORD="your_entra_password"
export MSSQL_DATABASE="your_database"
```

#### 6. Entra ID Integrated Authentication

For domain-joined Windows machines connecting to Azure SQL:

```bash
export MSSQL_AUTH_METHOD="entra_integrated"
export MSSQL_SERVER="your-server.database.windows.net,1433"
export MSSQL_DATABASE="your_database"
```

### Using Enhanced Server

```bash
# Run the enhanced server with Entra ID support
python src/mssql_mcp_server/server_enhanced.py
```

### Claude Desktop Configuration Examples

#### Windows Authentication (On-Premises)

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

#### Entra ID Service Principal (Azure SQL)

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

### Testing Authentication

Test all authentication methods:

```bash
python test_entra_auth.py
```

See [examples/entra_id_configs.md](examples/entra_id_configs.md) for complete configuration examples.

## Usage

### With Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mssql": {
      "command": "uv",
      "args": [
        "--directory", 
        "path/to/mssql_mcp_server",
        "run",
        "mssql_mcp_server"
      ],
      "env": {
        "MSSQL_SERVER": "localhost",
        "MSSQL_USER": "your_username",
        "MSSQL_PASSWORD": "your_password",
        "MSSQL_DATABASE": "your_database"
      }
    }
  }
}
```

### As a standalone server

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python -m mssql_mcp_server
```

## Development

```bash
# Clone the repository
git clone https://github.com/RichardHan/mssql_mcp_server.git
cd mssql_mcp_server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest
```

## Security Considerations

- Never commit environment variables or credentials
- Use a database user with minimal required permissions
- Consider implementing query whitelisting for production use
- Monitor and log all database operations

## Security Best Practices

This MCP server requires database access to function. For security:

1. **Create a dedicated SQL Server login** with minimal permissions
2. **Never use sa credentials** or administrative accounts
3. **Restrict database access** to only necessary operations
4. **Enable logging** for audit purposes
5. **Regular security reviews** of database access

See [SQL Server Security Configuration Guide](SECURITY.md) for detailed instructions on:
- Creating a restricted SQL Server login
- Setting appropriate permissions
- Monitoring database access
- Security best practices

⚠️ IMPORTANT: Always follow the principle of least privilege when configuring database access.

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request