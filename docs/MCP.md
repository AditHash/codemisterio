# CodeMisterio MCP Client Design

> **Status:** Planned feature, targeted for v0.2. Configuration and CLI commands below are illustrative, not implemented.

CodeMisterio will act as a **Model Context Protocol (MCP) client**. Users will connect external MCP servers to expand available tools, resources, and prompts while retaining CodeMisterio's independent authorization, context budget and audit controls.

Official MCP references:
- [Specification](https://modelcontextprotocol.io/specification)
- [Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [2026-07-28 protocol release](https://blog.modelcontextprotocol.io/posts/2026-07-28/)

The 2026-07-28 specification revised core message flow and transport behavior; compatibility with older deployed servers must be handled by an actively maintained SDK and explicit interoperability tests. Do not assume all remote servers speak the latest revision.

## 1. Scope and release stages

**v0.1: foundation only**

- Unify built-in tool registration, schemas, dispatch, permission checks, cancellation, and structured results.
- Define the extension points MCP will use without requiring an MCP server to run coding tasks.

**v0.2: working MCP client**

- Configure, enable/disable, list and inspect approved MCP servers.
- Connect to **local stdio** servers, starting subprocesses under a controlled environment.
- Connect to **remote Streamable HTTP** MCP endpoints over configured URLs.
- Discover tools, validate arguments, dispatch calls and return normalized model-visible results.
- Support MCP resources and prompts as separate, explicit features with their own trust and context policy.
- Handle protocol/SDK version compatibility, connection timeouts, server failures and safe shutdown.
- Support credentials supplied through environment/key storage for local servers and authenticated HTTP where SDK capabilities permit; advanced interactive OAuth flows may need staged delivery.
- Provide offline fake-server contract tests and opt-in real-server compatibility tests.

**Post-v0.2 improvements**

- More robust HTTP OAuth login and token refresh UX, connection health/status, re-discovery and notifications.
- Remote security posture checks, tool catalogs and version-aware interoperability matrices.
- Optional advanced MCP protocol features only where beneficial to coding workflows.

## 2. Proposed user experience

Example *future* CLI:

~~~bash
codemisterio mcp add filesystem --command "uvx" --args "example-mcp-server"
codemisterio mcp add docs --url "https://example.com/mcp"
codemisterio mcp list
codemisterio mcp inspect docs
codemisterio mcp disable docs
codemisterio mcp remove docs
~~~

Commands and server executable names above are **illustrations**, not documentation for currently available packages or a working CLI. Command definitions should avoid ambiguous shell-string interpolation; use executable + argument-vector boundaries for stdio.

Example proposed project/user configuration (illustration):

~~~json
{
  "mcpServers": {
    "docs": {
      "transport": "streamable-http",
      "url": "https://example.com/mcp",
      "enabled": false
    },
    "local-tools": {
      "transport": "stdio",
      "command": "python",
      "args": ["-m", "example_mcp_server"],
      "env": {
        "EXAMPLE_TOKEN": "${env:CODEMISTERIO_EXAMPLE_TOKEN}"
      },
      "enabled": false
    }
  }
}
~~~

Use references to user-controlled secrets, not plaintext values committed in repositories. Default to disabled until an individual server is explicitly approved.

## 3. Tool registry integration

~~~text
                       CodeMisterio Agent Loop
                               |
                        Tool Registry
                          /         \
                 Built-in tools     MCP client manager
                                         |
                            +------------+-------------+
                            |                          |
                       stdio server              HTTP server
                            |                          |
                     discovered tools           discovered tools
                            +------------+-------------+
                                         |
                                Permission Engine
                                         |
                                   Tool Dispatcher
                                         |
                                Normalized ToolResult
~~~

This diagram depicts logical registration; **every** execution, built-in or MCP, must pass policy evaluation before dispatch.

Proposed namespacing: `mcp.<server_id>.<tool_name>`. Do not allow MCP servers to overwrite built-ins, override global instructions, or register privileged functions without user authorization. Display original server/tool IDs in CLI prompts.

Treat tools, resources, and prompts as different interfaces:

- **Tools:** callable effects; require argument validation and policy checks each time.
- **Resources:** untrusted external content; apply user consent, URI validation and context budgets.
- **Prompts:** untrusted templates/instructions; never silently install them as higher-priority system instructions.

A successful MCP handshake or tool call does not constitute approval to act on arbitrary user accounts.

## 4. Transport and lifecycle

**Local stdio**

- Launch executable and arguments without shell interpretation.
- Explicit cwd, constrained env vars, stdout/protocol isolation, captured bounded stderr and process ownership.
- Server starts/stops with configured lifetime; cancellation and timeouts propagate.
- Initial server install/execution requires affirmative trust in its package and command.

**Remote Streamable HTTP**

- Validate endpoint scheme and origin, enforce TLS for nonlocal connections, apply network restrictions and request deadlines.
- Configure authentication without printing access tokens.
- Prevent automatic redirects to unapproved origins; avoid forwarding credentials across origins.
- Use current MCP SDK transport/version negotiation rather than assuming earlier GET/SSE or session behavior.
- Implement retries conservatively; never replay mutating tool calls without user approval and idempotency assurance.

## 5. Trust and security

MCP servers are independently executable programs or remote services: installing one can be equivalent to granting a new application access to part of the machine.

- Never auto-install or launch a newly discovered MCP server from model instructions or repository text.
- Display its command, destination, capabilities and permission scope for approval.
- Model-requested tool calls are checked against the same approval engine as built-in tools.
- Do not assume JSON Schema or a tool description reveals all actual side effects.
- Limit which directories, credentials and network endpoints a server can access; prefer process/VM containment when possible.
- Do not pass all environment variables into local MCP subprocesses.
- Treat MCP output as untrusted, vulnerable to prompt injection and misleading claims.
- Name collisions, stale server metadata, compromised servers and malicious tool arguments must be tested.
- A project-level config may propose MCP servers, but never auto-run them without explicit consent.
- Never persist raw tokens in session history or show secrets in logs.

## 6. Implementation checklist

- [ ] Choose an SDK version tested against the current protocol and compatible deployed servers.
- [ ] Add server configuration schema with explicit enable state.
- [ ] Add local stdio process manager with cleanup, bounded stderr, and cancellation.
- [ ] Add remote HTTP client, secure authentication references, and origin protection.
- [ ] Discover tools on connection and register uniquely namespaced adapters.
- [ ] Make tool calls pass runtime schema checks and permission decisions.
- [ ] Implement resources and prompts with lower-trust handling.
- [ ] Handle reconnects, missing servers and protocol errors without corrupting agent runs.
- [ ] Build unit/contract tests using a local fake MCP server.
- [ ] Add at least one remote-server compatibility test and document any unsupported features.
- [ ] Implement honest CLI `mcp list/inspect/enable/disable/remove` UX.
- [ ] Record tool/source provenance, redacted audit records and bounded output.

**Acceptance demo:** A user explicitly enables an example local server and a remote test server. CodeMisterio lists their tools, safely invokes an approved tool through its normal agent loop, refuses an unauthorized operation, and continues working if one MCP server disconnects.

See [TOOLS.md](TOOLS.md) and [../ARCHITECTURE.md](../ARCHITECTURE.md) for the core tool and permission architecture.
