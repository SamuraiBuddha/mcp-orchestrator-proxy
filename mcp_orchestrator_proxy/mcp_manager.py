"""MCP connection and execution manager"""

import asyncio
import subprocess
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class MCPConnection:
    """Manages a connection to a single MCP server"""
    
    def __init__(self, name: str, command: str, args: list):
        self.name = name
        self.command = command
        self.args = args
        self.process = None
        self.reader = None
        self.writer = None
    
    async def connect(self):
        """Start the MCP process and establish communication"""
        try:
            # Start the MCP process
            self.process = await asyncio.create_subprocess_exec(
                self.command,
                *self.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            logger.info(f"Started MCP {self.name}")
            
        except Exception as e:
            logger.error(f"Failed to start MCP {self.name}: {str(e)}")
            raise
    
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Call a tool on this MCP"""
        if not self.process:
            await self.connect()
        
        # Send JSON-RPC request
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": params
            },
            "id": 1
        }
        
        # Write request
        self.process.stdin.write(json.dumps(request).encode() + b"\n")
        await self.process.stdin.drain()
        
        # Read response
        response_line = await self.process.stdout.readline()
        response = json.loads(response_line.decode())
        
        if "error" in response:
            raise Exception(f"MCP error: {response['error']['message']}")
        
        return response.get("result")
    
    async def disconnect(self):
        """Stop the MCP process"""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            self.process = None

class MCPManager:
    """Manages connections to multiple MCP servers"""
    
    def __init__(self, registry_path: str = "config/registry.json"):
        self.connections: Dict[str, MCPConnection] = {}
        
        # Load registry
        registry_file = Path(registry_path)
        if not registry_file.exists():
            registry_file = Path(__file__).parent.parent / "config" / "registry.json"
        
        with open(registry_file, 'r') as f:
            self.registry = json.load(f)
    
    async def get_connection(self, mcp_name: str) -> MCPConnection:
        """Get or create a connection to an MCP"""
        if mcp_name not in self.connections:
            mcp_config = self.registry["mcps"].get(mcp_name)
            if not mcp_config:
                raise ValueError(f"Unknown MCP: {mcp_name}")
            
            conn = MCPConnection(
                name=mcp_name,
                command=mcp_config["command"],
                args=mcp_config["args"]
            )
            
            self.connections[mcp_name] = conn
        
        return self.connections[mcp_name]
    
    async def execute_tool(self, mcp_name: str, tool_name: str, params: Dict[str, Any]) -> Any:
        """Execute a tool on a specific MCP"""
        try:
            conn = await self.get_connection(mcp_name)
            result = await conn.call_tool(tool_name, params)
            return result
            
        except Exception as e:
            logger.error(f"Tool execution failed: {str(e)}")
            # Fallback or retry logic here
            raise
    
    async def get_tool_documentation(self, mcp_name: str, tool_name: str) -> str:
        """Get documentation for a specific tool"""
        mcp_config = self.registry["mcps"].get(mcp_name, {})
        tools = mcp_config.get("tools", {})
        tool_config = tools.get(tool_name, {})
        
        doc = f"**{tool_name}** (from {mcp_name})\n\n"
        doc += f"Description: {tool_config.get('description', 'No description')}\n\n"
        
        if "parameters" in tool_config:
            doc += "Parameters:\n"
            for param, info in tool_config["parameters"].items():
                doc += f"  • {param}: {info.get('description', '')}\n"
        
        if "examples" in tool_config:
            doc += "\nExamples:\n"
            for example in tool_config["examples"]:
                doc += f"  • {example}\n"
        
        return doc
    
    async def shutdown(self):
        """Disconnect all MCP connections"""
        for conn in self.connections.values():
            await conn.disconnect()