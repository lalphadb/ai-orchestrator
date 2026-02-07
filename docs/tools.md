# Tools Reference

32 built-in tools organized by category. All tools return a standardized `ToolResult`:

```json
{
  "success": true,
  "data": {},
  "error": { "code": "E_*", "message": "...", "recoverable": true },
  "meta": { "duration_ms": 42, "sandbox": false }
}
```

## System (5)

| Tool | Description |
|------|-------------|
| `execute_command` | Shell execution with allowlist/blocklist |
| `get_system_info` | OS, CPU, memory, disk info |
| `get_datetime` | Current date/time in multiple formats |
| `list_llm_models` | Available Ollama models with categorization |
| `get_audit_log` | Command execution audit trail |

## Filesystem (5)

| Tool | Description |
|------|-------------|
| `read_file` | Read file with path traversal protection |
| `write_file` | Write file within workspace |
| `list_directory` | List directory contents |
| `search_files` | Glob-based file search |
| `search_directory` | Directory search with depth limits |

## QA (7)

| Tool | Description |
|------|-------------|
| `git_status` | Git working tree status |
| `git_diff` | Staged/unstaged changes |
| `run_tests` | pytest (backend) or npm test (frontend) |
| `run_lint` | ruff (backend) or eslint (frontend) |
| `run_format` | black (backend) formatting check |
| `run_build` | Build backend deps or frontend assets |
| `run_typecheck` | mypy (backend) or tsc (frontend) |

## Network (1)

| Tool | Description |
|------|-------------|
| `http_request` | HTTP GET/POST with SSRF protection |

## Utility (1)

| Tool | Description |
|------|-------------|
| `calculate` | Safe math expression evaluation |

## Governance (4)

| Tool | Description |
|------|-------------|
| `get_action_history` | Past governance decisions |
| `get_pending_verifications` | Actions awaiting approval |
| `rollback_action` | Rollback a previous action |

## Memory (3)

| Tool | Description |
|------|-------------|
| `memory_remember` | Store information in ChromaDB |
| `memory_recall` | Retrieve similar memories |
| `memory_context` | Get contextual memories for a query |

## Runbooks (3)

| Tool | Description |
|------|-------------|
| `list_runbooks` | Available runbooks |
| `get_runbook` | Get runbook content |
| `search_runbooks` | Search runbooks by keyword |

## Web (2)

| Tool | Description |
|------|-------------|
| `web_search` | Web search via external API |
| `web_read` | Read and extract web page content |

## Error Codes

**Recoverable** (trigger auto-recovery):
- `E_FILE_NOT_FOUND`, `E_DIR_NOT_FOUND`, `E_PATH_NOT_FOUND`

**Fatal** (stop execution):
- `E_PERMISSION`, `E_CMD_NOT_ALLOWED`, `E_PATH_FORBIDDEN`
- `E_WRITE_DISABLED`, `E_URL_FORBIDDEN`, `E_GOVERNANCE_DENIED`
