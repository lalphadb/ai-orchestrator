# Security

## Principles

AI Orchestrator follows a **fail-closed** security posture:
- Sandbox mode by default
- Mandatory input validation
- Tool restrictions per agent
- Governance approval for sensitive actions

## Authentication

- JWT tokens with configurable expiration
- HttpOnly cookies (no localStorage token storage)
- WebSocket authenticated via query parameter
- SECRET_KEY required in production (auto-generated in test mode)

## Command Execution

**Allowlist** (~185 safe commands): python, git, npm, pytest, docker, etc.

**Blocklist** (~31 dangerous commands): bash, sh, rm -rf, chmod, eval, nc, etc.

**Pattern detection** blocks injection attempts: `$()`, backticks, `| bash`, `; rm`, `curl | bash`, `/dev/tcp/`

## SSRF Protection

All HTTP requests are filtered against:
- Localhost (127.0.0.0/8)
- Private networks (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
- Link-local (169.254.0.0/16 - cloud metadata)
- Loopback, multicast, reserved IPs

## Prompt Injection Detection

Incoming prompts are analyzed for injection patterns before execution.

## Governance

The governance system enforces approval for sensitive actions:
- SENSITIVE and CRITICAL actions require justification
- Fail-closed: blocked by default without justification
- All actions logged with audit trail

## Agent Isolation

Each agent has a declared set of `allowed_tools`. The registry validates tool access before execution.

| Agent | Allowed Tools |
|-------|---------------|
| system.health | read_file, list_directory, execute_command |
| web.researcher | web_search, web_read |
| self_improve | read_file, write_file, patch_file, run_tests, git_* |

## Filesystem Security

- All operations restricted to WORKSPACE_DIR
- Path traversal protection (.. detection, symlink resolution)
- Canonical path validation
- Write operations can be globally disabled

## Audit Logging

All tool executions, file modifications, and security events are logged.
