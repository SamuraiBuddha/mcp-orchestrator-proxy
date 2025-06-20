#!/usr/bin/env python3
"""Entry point for running mcp_orchestrator_proxy as a module."""

import asyncio
from .server import main

if __name__ == "__main__":
    asyncio.run(main())