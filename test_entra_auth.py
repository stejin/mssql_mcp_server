#!/usr/bin/env python3
"""
Comprehensive test script for Microsoft Entra ID authentication methods.
Tests all supported authentication types with the enhanced MCP server.
"""

import os
import sys
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_authentication_method(auth_config: Dict[str, str], method_name: str) -> bool:
    """Test a specific authentication method."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing {method_name}")
    logger.info(f"{'='*60}")
    
    # Set environment variables
    original_env = {}
    for key, value in auth_config.items():
        original_env[key] = os.environ.get(key)
        if value is not None:
            os.environ[key] = value
        elif key in os.environ:
            del os.environ[key]
    
    try:
        # Import and test the enhanced server
        from src.mssql_mcp_server.server_enhanced import get_connection, get_db_config
        
        # Show configuration
        config = get_db_config()
        logger.info(f"Configuration:")
        logger.info(f"  Server: {config['server']}")
        logger.info(f"  Database: {config['database']}")
        logger.info(f"  Auth Method: {config['auth_method']}")
        
        # Test connection
        conn = get_connection()
        cursor = conn.cursor()
        
        # Test basic queries
        cursor.execute("SELECT @@VERSION, DB_NAME(), SYSTEM_USER, USER_NAME()")
        result = cursor.fetchone()
        
        logger.info(f"✅ SUCCESS - Connected to {result[1]} as {result[2]}")
        logger.info(f"   Database User: {result[3]}")
        logger.info(f"   SQL Server Version: {result[0][:80]}...")
        
        # Test table listing
        cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
        table_count = cursor.fetchone()[0]
        logger.info(f"   Found {table_count} tables")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ FAILED - {method_name}: {str(e)}")
        return False
    
    finally:
        # Restore original environment
        for key, value in original_env.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]

def main():
    """Run all authentication tests."""
    print("Microsoft Entra ID Authentication Test Suite")
    print("=" * 60)
    
    # Check if Azure libraries are available
    try:
        import azure.identity
        import azure.core
        print("✅ Azure authentication libraries available")
    except ImportError as e:
        print(f"❌ Azure libraries missing: {e}")
        print("Install with: pip install azure-identity azure-core")
        return
    
    # Check if pyodbc is available
    try:
        import pyodbc
        print("✅ pyodbc available")
    except ImportError:
        print("❌ pyodbc missing. Install with: pip install pyodbc")
        return
    
    # Base configuration - modify these for your environment
    base_config = {
        "MSSQL_SERVER": "your-server.database.windows.net,1433",
        "MSSQL_DATABASE": "your_database",
        "MSSQL_ENCRYPT": "yes",
        "MSSQL_TRUST_SERVER_CERTIFICATE": "no",
        "MSSQL_CONNECTION_TIMEOUT": "30"
    }
    
    print(f"\nBase Configuration:")
    print(f"Server: {base_config['MSSQL_SERVER']}")
    print(f"Database: {base_config['MSSQL_DATABASE']}")
    
    # Test cases
    test_cases = []
    
    # 1. SQL Server Authentication
    if input("\nTest SQL Server Authentication? (y/n): ").lower() == 'y':
        sql_user = input("SQL Username: ")
        sql_password = input("SQL Password: ")
        test_cases.append({
            "config": {
                **base_config,
                "MSSQL_AUTH_METHOD": "sql",
                "MSSQL_USER": sql_user,
                "MSSQL_PASSWORD": sql_password
            },
            "name": "SQL Server Authentication"
        })
    
    # 2. Entra ID Password Authentication
    if input("\nTest Entra ID Password Authentication? (y/n): ").lower() == 'y':
        entra_user = input("Entra ID Username (user@domain.com): ")
        entra_password = input("Entra ID Password: ")
        test_cases.append({
            "config": {
                **base_config,
                "MSSQL_AUTH_METHOD": "entra_password",
                "MSSQL_USER": entra_user,
                "MSSQL_PASSWORD": entra_password
            },
            "name": "Entra ID Password Authentication"
        })
    
    # 3. Entra ID Service Principal Authentication
    if input("\nTest Entra ID Service Principal Authentication? (y/n): ").lower() == 'y':
        client_id = input("Client ID: ")
        client_secret = input("Client Secret: ")
        tenant_id = input("Tenant ID (optional): ") or None
        config = {
            **base_config,
            "MSSQL_AUTH_METHOD": "entra_service_principal",
            "MSSQL_CLIENT_ID": client_id,
            "MSSQL_CLIENT_SECRET": client_secret
        }
        if tenant_id:
            config["MSSQL_TENANT_ID"] = tenant_id
        test_cases.append({
            "config": config,
            "name": "Entra ID Service Principal Authentication"
        })
    
    # 4. Entra ID Managed Identity Authentication
    if input("\nTest Entra ID Managed Identity Authentication? (y/n): ").lower() == 'y':
        identity_type = input("Identity type (system/user): ").lower()
        config = {
            **base_config,
            "MSSQL_AUTH_METHOD": "entra_managed_identity"
        }
        if identity_type == "user":
            client_id = input("User-assigned identity Client ID: ")
            config["MSSQL_CLIENT_ID"] = client_id
        test_cases.append({
            "config": config,
            "name": f"Entra ID Managed Identity ({identity_type}-assigned)"
        })
    
    # 5. Entra ID Integrated Authentication
    if input("\nTest Entra ID Integrated Authentication? (y/n): ").lower() == 'y':
        test_cases.append({
            "config": {
                **base_config,
                "MSSQL_AUTH_METHOD": "entra_integrated"
            },
            "name": "Entra ID Integrated Authentication"
        })
    
    # 6. Entra ID Interactive/Default Authentication
    if input("\nTest Entra ID Interactive/Default Authentication? (y/n): ").lower() == 'y':
        test_cases.append({
            "config": {
                **base_config,
                "MSSQL_AUTH_METHOD": "entra_interactive"
            },
            "name": "Entra ID Interactive/Default Authentication"
        })
    
    # Run tests
    results = []
    for test_case in test_cases:
        success = test_authentication_method(test_case["config"], test_case["name"])
        results.append({
            "name": test_case["name"],
            "success": success
        })
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST RESULTS SUMMARY")
    print(f"{'='*60}")
    
    for result in results:
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        print(f"{status}: {result['name']}")
    
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")

if __name__ == "__main__":
    main()

