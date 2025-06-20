from . import server, server_enhanced
import asyncio
import os

def main():
    """Main entry point for the package."""
    # Use enhanced server by default, fall back to basic server if Azure libs not available
    try:
        # Check if enhanced server can be used
        from .server_enhanced import AZURE_AUTH_AVAILABLE
        asyncio.run(server_enhanced.main())
    except ImportError:
        # Fall back to basic server if enhanced dependencies not available
        asyncio.run(server.main())

# Expose important items at package level
__all__ = ['main', 'server', 'server_enhanced']
