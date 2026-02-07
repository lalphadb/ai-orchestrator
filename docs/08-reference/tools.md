# Tools Reference

AI Orchestrator provides 18 built-in tools for the ReAct engine, enabling autonomous task execution with security controls and automatic error recovery.

## Overview

All tools follow a standardized contract (`ToolResult`) that enables consistent error handling, performance monitoring, and automatic recovery from common failures.

**Key Features:**
- Unified result format across all tools
- Automatic timing and metrics collection
- Built-in security controls (allowlists, workspace isolation)
- Recoverable error classification
- Audit logging for all operations

## Tool Categories

### System Tools (5)

#### execute_command
**Description:** Executes shell commands in a secure environment with strict allowlist enforcement

**Category:** system

**Parameters:**
- `command` (string) - Command to execute
- `timeout` (int, optional) - Timeout in seconds (default: 30)
- `role` (string, optional) - Execution role: viewer, operator, admin (default: operator)

**Returns:** ToolResult with stdout, stderr, and return code

**Security:**
- Allowlist of ~185 safe commands (python, git, npm, pytest, docker, etc.)
- Blocklist of ~31 dangerous commands (bash, rm -rf, chmod, etc.)
- No shell injection via pattern detection
- Workspace isolation
- Full audit logging

**Example:**
```python
result = await execute_command("pytest backend/tests/ -v", timeout=60)
# {"success": true, "data": {"stdout": "...", "stderr": "", "returncode": 0}}
```

---

#### get_system_info
**Description:** Returns system information and resource usage

**Category:** system

**Parameters:** None

**Returns:** ToolResult with OS, CPU, memory, disk, and workspace information

**Example:**
```python
result = get_system_info()
# {"success": true, "data": {"os": "Linux", "cpu_count": 8, "memory_total_gb": 16, ...}}
```

---

#### get_datetime
**Description:** Returns current date and time in multiple formats

**Category:** utility

**Parameters:** None

**Returns:** ToolResult with datetime (ISO 8601), date, time, and Unix timestamp

**Example:**
```python
result = get_datetime()
# {"success": true, "data": {"datetime": "2026-01-28T15:30:00", "date": "2026-01-28", ...}}
```

---

#### list_llm_models
**Description:** Lists available LLM models with automatic categorization

**Category:** system

**Parameters:** None

**Returns:** ToolResult with models grouped by category (general, code, vision, embedding, cloud)

**Categories:**
- **general** - General-purpose models (qwen, mistral, llama, deepseek-chat)
- **code** - Code-specialized models (deepseek-coder, codellama, codegemma, starcoder)
- **vision** - Vision-capable models (llava, bakllava)
- **embedding** - Embedding models (bge-m3, qwen3-embedding)
- **cloud** - Cloud models (kimi-k2:1t-cloud, moonshot-v1)

**Example:**
```python
result = list_llm_models()
# {"success": true, "data": {"models": {"code": ["deepseek-coder:33b", ...], ...}}}
```

---

#### get_audit_log
**Description:** Retrieves command execution audit log entries

**Category:** system

**Parameters:**
- `last_n` (int, optional) - Number of entries to retrieve (default: 20)

**Returns:** ToolResult with audit entries including timestamp, command, user, role, and result

**Example:**
```python
result = get_audit_log(last_n=10)
# {"success": true, "data": {"entries": [...], "count": 10}}
```

---

### Filesystem Tools (5)

#### read_file
**Description:** Reads file content with path traversal protection

**Category:** filesystem

**Parameters:**
- `path` (string) - File path (relative to workspace or absolute within workspace)

**Returns:** ToolResult with file content, size, and line count

**Security:**
- Path validation against traversal attacks (.., symlinks)
- Workspace isolation
- Canonical path resolution

**Example:**
```python
result = read_file("backend/main.py")
# {"success": true, "data": {"content": "...", "path": "/workspace/backend/main.py", "size": 1024, "lines": 50}}
```

---

#### write_file
**Description:** Writes content to a file within the workspace

**Category:** filesystem

**Parameters:**
- `path` (string) - File path (relative to workspace or absolute within workspace)
- `content` (string) - Content to write
- `append` (bool, optional) - Append mode (default: false)

**Returns:** ToolResult with written path, size, and mode

**Security:**
- Write operations limited to WORKSPACE_DIR only
- Path traversal protection
- Can be globally disabled via WORKSPACE_ALLOW_WRITE config

**Example:**
```python
result = write_file("output/result.txt", "Hello World", append=False)
# {"success": true, "data": {"path": "/workspace/output/result.txt", "size": 11, "mode": "write"}}
```

---

#### list_directory
**Description:** Lists directory contents with metadata

**Category:** filesystem

**Parameters:**
- `path` (string, optional) - Directory path (default: current directory)

**Returns:** ToolResult with entries list (name, is_dir, size) and count

**Security:** Path traversal protection, workspace isolation

**Example:**
```python
result = list_directory("backend/app")
# {"success": true, "data": {"path": "/workspace/backend/app", "entries": [{...}], "count": 15}}
```

---

#### search_files
**Description:** Searches for files matching a pattern using glob

**Category:** filesystem

**Parameters:**
- `pattern` (string) - Glob pattern (e.g., "*.py", "**/*.json")
- `path` (string, optional) - Base directory to search (default: current directory)

**Returns:** ToolResult with matches (max 100), count, pattern, and base path

**Example:**
```python
result = search_files("*.py", "backend/app")
# {"success": true, "data": {"pattern": "*.py", "path": "/workspace/backend/app", "matches": [...], "count": 42}}
```

---

#### search_directory
**Description:** Secure directory search with allowlist and depth limits

**Category:** filesystem

**Parameters:**
- `name` (string) - Directory name to search for (exact or partial match)
- `base` (string, optional) - Base directory (default: WORKSPACE_DIR, must be in allowlist)
- `max_depth` (int, optional) - Maximum search depth (default: 3, max: 3)

**Returns:** ToolResult with found directories (max 5 results)

**Security:**
- Base path must be in SEARCH_ALLOWED_BASES allowlist
- Maximum depth: 3 levels
- Maximum results: 5 directories
- Prevents unbounded filesystem scanning

**Auto-Recovery:** Automatically called when tools return E_DIR_NOT_FOUND errors

**Example:**
```python
result = search_directory("tests", base="/workspace", max_depth=2)
# {"success": true, "data": {"query": "tests", "base": "/workspace", "matches": [...], "count": 3}}
```

---

### QA Tools (7)

Quality assurance tools for automated testing, linting, and verification.

#### git_status
**Description:** Shows Git working tree status in the workspace

**Category:** qa

**Parameters:** None

**Returns:** ToolResult with git status output

**Example:**
```python
result = git_status()
# {"success": true, "data": {"stdout": "On branch main\nYour branch is up to date...", ...}}
```

---

#### git_diff
**Description:** Shows Git differences for staged or unstaged changes

**Category:** qa

**Parameters:**
- `staged` (bool, optional) - Show staged changes only (default: false, shows unstaged)

**Returns:** ToolResult with git diff output

**Example:**
```python
result = git_diff(staged=True)
# {"success": true, "data": {"stdout": "diff --git a/file.py...", ...}}
```

---

#### run_tests
**Description:** Executes test suites for backend (pytest) or frontend (npm test)

**Category:** qa

**Parameters:**
- `target` (string) - Test target: backend, frontend, or all

**Returns:** ToolResult with test execution output and results

**Example:**
```python
result = await run_tests(target="backend")
# {"success": true, "data": {"stdout": "===== test session starts =====...", ...}}
```

---

#### run_lint
**Description:** Runs linter checks (ruff for backend, npm lint for frontend)

**Category:** qa

**Parameters:**
- `target` (string) - Lint target: backend, frontend, or all

**Returns:** ToolResult with linter output and issues found

**Example:**
```python
result = await run_lint(target="backend")
# {"success": true, "data": {"stdout": "All checks passed!", ...}}
```

---

#### run_format
**Description:** Checks or applies code formatting (black for backend)

**Category:** qa

**Parameters:**
- `target` (string) - Format target: backend, frontend, or all
- `check_only` (bool, optional) - Only check without applying (default: true)

**Returns:** ToolResult with formatting check/application results

**Example:**
```python
result = await run_format(target="backend", check_only=True)
# {"success": true, "data": {"stdout": "All files formatted correctly", ...}}
```

---

#### run_build
**Description:** Builds the project (backend dependencies, frontend assets)

**Category:** qa

**Parameters:**
- `target` (string) - Build target: backend, frontend, or all

**Returns:** ToolResult with build output and status

**Example:**
```python
result = await run_build(target="frontend")
# {"success": true, "data": {"stdout": "vite v5.0.0 building for production...", ...}}
```

---

#### run_typecheck
**Description:** Runs type checking (mypy for backend, tsc for frontend)

**Category:** qa

**Parameters:**
- `target` (string) - Typecheck target: backend or frontend

**Returns:** ToolResult with type checking results

**Example:**
```python
result = await run_typecheck(target="backend")
# {"success": true, "data": {"stdout": "Success: no issues found", ...}}
```

---

### Network Tools (1)

#### http_request
**Description:** Performs HTTP requests with SSRF protection

**Category:** network

**Parameters:**
- `url` (string) - Target URL
- `method` (string, optional) - HTTP method: GET or POST (default: GET)
- `data` (dict, optional) - JSON payload for POST requests

**Returns:** ToolResult with status code, headers, and body (max 10KB)

**Security (Anti-SSRF):**
- Blocks localhost (127.0.0.1, ::1, localhost)
- Blocks private IP ranges (10.x, 172.16-31.x, 192.168.x)
- Blocks link-local IPs (169.254.x - cloud metadata services)
- Blocks loopback, multicast, reserved IPs
- 30-second timeout
- Response body limited to 10KB

**Example:**
```python
result = await http_request("https://api.example.com/data", method="GET")
# {"success": true, "data": {"status_code": 200, "headers": {...}, "body": "..."}}
```

---

### Utility Tools (1)

#### calculate
**Description:** Evaluates mathematical expressions safely

**Category:** utility

**Parameters:**
- `expression` (string) - Mathematical expression (supports +, -, *, /, //, %, **, unary -)

**Returns:** ToolResult with expression and computed result

**Security:** Safe evaluation using AST parsing (no eval(), no arbitrary code execution)

**Example:**
```python
result = calculate("(2 + 3) * 4 ** 2")
# {"success": true, "data": {"expression": "(2 + 3) * 4 ** 2", "result": 80}}
```

---

## Tool Result Contract

All tools return a standardized `ToolResult` structure:

```python
{
  "success": bool,           # True if operation succeeded
  "data": dict | None,       # Result data (null on failure)
  "error": {                 # Error details (null on success)
    "code": str,             # Error code (e.g., E_FILE_NOT_FOUND)
    "message": str,          # Human-readable error message
    "recoverable": bool      # True if automatic recovery is possible
  } | None,
  "meta": {                  # Metadata about execution
    "duration_ms": int,      # Execution time in milliseconds
    "command": str,          # Command executed (for execute_command)
    "sandbox": bool          # Whether executed in Docker sandbox
  }
}
```

---

## Error Codes

### Recoverable Errors
These errors trigger automatic recovery attempts by the ReAct engine:

- **E_FILE_NOT_FOUND** - File does not exist (auto-recovery: suggests similar filenames)
- **E_DIR_NOT_FOUND** - Directory does not exist (auto-recovery: calls search_directory)
- **E_PATH_NOT_FOUND** - Path not found (auto-recovery: searches for alternatives)

### Fatal Errors
These errors stop execution immediately:

- **E_PERMISSION** - Permission denied (cannot recover)
- **E_CMD_NOT_ALLOWED** - Command not in allowlist (security violation)
- **E_PATH_FORBIDDEN** - Path outside workspace or sensitive path (security violation)
- **E_WRITE_DISABLED** - Write operations disabled in configuration
- **E_URL_FORBIDDEN** - URL blocked by SSRF protection (security violation)

### Other Errors

- **E_TOOL_EXEC** - Tool execution exception
- **E_READ_ERROR** - File read error
- **E_WRITE_ERROR** - File write error
- **E_LIST_ERROR** - Directory listing error
- **E_SEARCH_ERROR** - File search error
- **E_HTTP_TIMEOUT** - HTTP request timeout
- **E_HTTP_ERROR** - HTTP request error
- **E_HTTP_METHOD** - Unsupported HTTP method
- **E_CALC_ERROR** - Mathematical calculation error
- **E_AUDIT_ERROR** - Audit log retrieval error
- **E_INVALID_PATH** - Invalid path format

---

## Auto-Recovery System

When a tool returns a recoverable error, the ReAct engine automatically:

1. **Extracts Context** - Parses the error message to identify the missing path/file
2. **Searches Alternatives** - Calls `search_directory()` or similar recovery tools
3. **Injects Suggestions** - Adds alternatives to the next LLM prompt
4. **Logs Recovery** - Records the recovery attempt in `tools_used` with `auto_recovery: true`
5. **Retries** - Lets the LLM retry with the suggested alternatives

**Example Recovery Flow:**
```
User Request: "Read tests/test_api.py"
↓
Tool Call: read_file("tests/test_api.py")
↓
Error: E_DIR_NOT_FOUND "Directory not found: tests"
↓
Auto-Recovery: search_directory("tests", base="/workspace", max_depth=3)
↓
Suggestions: ["backend/tests", "frontend/tests"]
↓
LLM Retry: read_file("backend/tests/test_api.py")
↓
Success!
```

---

## Security Model

### Command Execution Security

**Allowlist (~185 commands):**
```python
# System utilities
ls, cat, grep, find, pwd, cd, mkdir, touch, cp, mv, rm (safe variants)

# Development tools
python, python3, pip, node, npm, yarn, pnpm
git, pytest, ruff, black, mypy, eslint, prettier

# DevOps tools
docker, docker-compose, kubectl, helm
curl, wget (with URL validation)

# Build tools
make, cmake, cargo, go
```

**Blocklist (~31 dangerous commands):**
```python
bash, sh, zsh, ksh           # Shell interpreters
rm -rf /                      # Destructive operations
chmod, chown                  # Permission modifications
eval, exec                    # Code execution
nc, netcat                    # Network listeners
mkfifo                        # Named pipes (reverse shells)
perl -e, python -c            # One-liners
```

**Pattern Detection:**
```python
# Blocks command injection attempts
$()           # Command substitution
`cmd`         # Backtick execution
| bash        # Pipe to shell
; rm          # Command chaining
curl | bash   # Download and execute
/dev/tcp/     # Reverse shells
```

### Filesystem Security

**Workspace Isolation:**
- All file operations restricted to `WORKSPACE_DIR`
- Path traversal protection (`..` detection, symlink resolution)
- Canonical path validation
- Sensitive path blocking (`/etc/`, `/root/`)

**Write Protection:**
- Write operations can be globally disabled
- All writes logged to audit trail
- Atomic operations with parent directory creation

### Network Security

**SSRF Protection:**
- Blocks localhost and loopback addresses
- Blocks private IP ranges (RFC 1918)
- Blocks link-local IPs (cloud metadata: 169.254.x)
- DNS resolution with IP validation
- 30-second request timeout
- 10KB response size limit

---

## Usage Example

```python
from app.services.react_engine.tools import BUILTIN_TOOLS

# Get a tool
read_file_tool = BUILTIN_TOOLS.get("read_file")

# Execute synchronously
result = read_file_tool["func"]("backend/main.py")

if result["success"]:
    print(f"File content: {result['data']['content']}")
    print(f"Execution time: {result['meta']['duration_ms']}ms")
else:
    error = result["error"]
    print(f"Error {error['code']}: {error['message']}")

    if error["recoverable"]:
        print("Auto-recovery will attempt to fix this")
    else:
        print("Fatal error - stopping execution")

# Execute asynchronously (for async tools)
result = await BUILTIN_TOOLS.get("execute_command")["func"]("pytest backend/tests/")
```

---

## Metrics and Monitoring

All tool executions are automatically tracked with Prometheus metrics:

```promql
# Tool execution count
ai_orchestrator_tool_execution_total{tool_name="read_file", success="true"}

# Tool execution duration
ai_orchestrator_tool_execution_duration_seconds{tool_name="execute_command"}

# Error rate by code
rate(ai_orchestrator_tool_execution_total{success="false"}[5m])
```

Metrics are exposed at `/metrics` and visualized in Grafana dashboards.

---

## Tool Registry

Tools are registered in `backend/app/services/react_engine/tools.py`:

```python
BUILTIN_TOOLS = ToolRegistry()

BUILTIN_TOOLS.register(
    "execute_command",
    execute_command,
    "Exécute une commande shell (sandbox Docker par défaut, allowlist obligatoire)",
    "system",
    {"command": "string", "timeout": "int (optional, default=30)"}
)
```

**Registry Operations:**
- `BUILTIN_TOOLS.get(name)` - Get tool by name
- `BUILTIN_TOOLS.list()` - List all tools
- `BUILTIN_TOOLS.list_by_category(category)` - List tools in a category
- `BUILTIN_TOOLS.get_categories()` - Get all categories

---

## Configuration

Key settings in `backend/app/core/config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `WORKSPACE_DIR` | `/home/lalpha/orchestrator-workspace` | Workspace isolation root |
| `WORKSPACE_ALLOW_WRITE` | `True` | Enable/disable write operations |
| `COMMAND_ALLOWLIST` | `[...]` | ~185 allowed commands |
| `COMMAND_BLOCKLIST` | `[...]` | ~31 blocked commands |
| `TIMEOUT_COMMAND_DEFAULT` | `30` | Default command timeout (seconds) |
| `TIMEOUT_HTTP_REQUEST` | `30` | HTTP request timeout (seconds) |
| `EXECUTE_MODE` | `"local"` | Execution mode: local, docker |

---

## Related Documentation

- [Workflow Conventions](../02-architecture/workflow.md) - ReAct engine workflow
- [Security Model](../04-security/architecture.md) - Security layers and controls
- [API Reference](../03-api/rest.md) - REST API for tool management
- [Configuration Guide](../05-operations/configuration.md) - Environment variables

---

**Last Updated:** 2026-01-28
**Version:** 7.1
