# MCP Orchestrator Proxy 🚀

**Full execution proxy for MCP servers - spawns and controls MCPs directly!**

This is the **proxy version** of MCP Orchestrator that actually executes MCP tools by spawning and managing MCP servers as subprocesses. Perfect for server/NAS deployments where you have full control over the environment.

## Architecture Difference

### Standard MCP Orchestrator (Discovery Only)
```
Claude → Orchestrator → "Use tool X from MCP Y" → Claude → MCP
```

### MCP Orchestrator Proxy (Full Execution)
```
Claude → Orchestrator Proxy → Spawns MCP → Executes Tool → Returns Result
```

## Key Features

- **Spawns MCP Servers**: Launches MCP servers as child processes
- **Direct Execution**: Executes tools and returns results directly
- **Process Management**: Handles MCP lifecycle (start/stop/restart)
- **Connection Pooling**: Reuses MCP connections for efficiency
- **Error Recovery**: Can restart failed MCPs automatically
- **Full Control**: Perfect for environments where you control everything

## When to Use This Version

### ✅ Use Proxy Version For:
- **NAS/Server Deployments**: Where you control the full environment
- **Docker Containers**: Running orchestrator in its own container
- **CI/CD Pipelines**: Automated workflows that need MCP execution
- **Multi-User Systems**: Shared MCP infrastructure
- **Resource Management**: When you need to control MCP resource usage
- **Security Isolation**: Running MCPs in controlled environments

### ❌ Use Standard Version For:
- **Claude Desktop**: Where MCPs are already managed
- **Simple Discovery**: When you just need to find tools
- **Lightweight Usage**: Minimal overhead scenarios

## Installation

```bash
git clone https://github.com/SamuraiBuddha/mcp-orchestrator-proxy.git
cd mcp-orchestrator-proxy
pip install -e .
```

## Configuration

The proxy version uses the same `config/registry.json` but with additional fields:

```json
{
  "mcps": {
    "comfyui": {
      "description": "AI image generation",
      "command": "python",
      "args": ["-m", "mcp_comfyui"],
      "env": {
        "COMFYUI_URL": "http://localhost:8188"
      },
      "startup_timeout": 30,
      "health_check": {
        "method": "tool_call",
        "tool": "get_status"
      }
    }
  }
}
```

## Usage Examples

### Basic Usage

```python
# The orchestrator proxy handles everything
result = execute("generate a robot logo", {"style": "cyberpunk"})
# Actually spawns ComfyUI MCP, calls generate_image, returns the result
```

### With Docker

```dockerfile
FROM python:3.10

# Install orchestrator proxy
RUN pip install mcp-orchestrator-proxy

# Install all your MCP servers
RUN pip install mcp-comfyui mcp-github mcp-memory

# Configure
COPY config/registry.json /app/config/

# Run orchestrator as MCP server
CMD ["python", "-m", "mcp_orchestrator_proxy"]
```

### NAS Deployment

```yaml
version: '3.8'

services:
  orchestrator-proxy:
    image: mcp-orchestrator-proxy
    volumes:
      - ./config:/app/config
      - /var/run/docker.sock:/var/run/docker.sock  # For Docker MCPs
    environment:
      - PYTHONPATH=/app
    ports:
      - "8080:8080"  # REST API endpoint
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

## Advanced Features

### Process Management

The proxy version includes advanced process management:

```python
# MCPs are started on-demand
first_call = execute("generate image", {})  # Starts ComfyUI MCP

# Subsequent calls reuse the connection
second_call = execute("generate another", {})  # Reuses existing process

# Automatic cleanup on idle
# MCPs shut down after 5 minutes of inactivity
```

### Health Checks

```python
# Built-in health monitoring
{
  "health_check": {
    "interval": 30,
    "timeout": 5,
    "retries": 3
  }
}
```

### Resource Limits

```python
# Per-MCP resource constraints
{
  "resources": {
    "max_memory": "2G",
    "max_cpu": "1.0",
    "max_instances": 3
  }
}
```

## Architecture Details

### Process Spawning
```python
# Each MCP runs in its own process
MCP Process
├── stdin  (JSON-RPC requests)
├── stdout (JSON-RPC responses)  
└── stderr (logs/errors)
```

### Connection Pooling
```python
# Connections are reused for efficiency
orchestrator.connections = {
  "comfyui": <Active Process>,
  "github": <Active Process>,
  "memory": <Idle - will shutdown>
}
```

### Error Recovery
```python
# Automatic restart on failure
if process.returncode != 0:
    await restart_mcp(mcp_name)
    retry_count += 1
```

## Security Considerations

Since this version spawns processes:

1. **Sandboxing**: Run in containers/VMs for isolation
2. **Resource Limits**: Set memory/CPU limits
3. **Allowed Commands**: Whitelist MCP commands
4. **Network Isolation**: Control MCP network access
5. **Audit Logging**: Log all executions

## Performance

- **Startup Time**: ~1-3s for first tool call (spawning MCP)
- **Subsequent Calls**: <100ms (reusing connection)
- **Memory**: Base 50MB + memory per active MCP
- **Concurrent MCPs**: Limited by system resources

## Monitoring

Built-in metrics:
- Active MCP count
- Tool execution times
- Error rates
- Resource usage
- Connection pool stats

## Migration from Standard Version

1. Same configuration format
2. Same tool interface  
3. Additional process management features
4. Works as drop-in replacement

## Future Enhancements

- [ ] Kubernetes operator for MCP orchestration
- [ ] gRPC interface for high-performance calls
- [ ] Distributed MCP execution across nodes
- [ ] MCP hot-reloading
- [ ] WebSocket streaming for long operations
- [ ] Built-in caching layer
- [ ] Multi-tenancy support

## Contributing

This proxy version is ideal for advanced deployments. Contributions welcome for:
- Additional health check strategies
- Resource management improvements
- Distribution/scaling features
- Security enhancements

## License

MIT License - Perfect for server deployments!

---

*For simpler Claude Desktop integration, use the [standard MCP Orchestrator](https://github.com/SamuraiBuddha/mcp-orchestrator)*
