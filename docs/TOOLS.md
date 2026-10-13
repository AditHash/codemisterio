# CodeMisterio Tool Catalog and Execution Contract

> **Status:** Design specification. None of the tools below are shipped merely because they are listed here. Milestone assignments are targets, not release promises.

CodeMisterio is a coding **CLI built on LangChain Deep Agents**, not just a text generator. Use Deep Agents filesystem, search, shell and planning tools wherever appropriate; add CodeMisterio wrappers/tools only for missing capabilities, policy enforcement and verified event reporting. Useful coding tools must work without requiring users to install third-party MCP servers. External MCP tools complement the built-ins; they do not replace them.

## 1. Shared tool execution interface

Every built-in or MCP-discovered tool passes through this pipeline:

~~~text
Deep Agents tool call
  -> canonical name + JSON Schema argument validation
  -> availability and capability check
  -> permission + workspace/sandbox policy
  -> bounded executor (timeout, output size, cancellation)
  -> before/after evidence capture (diffs, exit status, process state)
  -> normalized result + correlated ActivityEvent
  -> model observation + **live CLI activity display**
~~~

Tool specifications should declare: stable ID/name, provider-agnostic description, JSON Schema, permissions and resource scope, idempotency/retry safety, source (built-in or server ID), and supported execution environment. Tool results include call ID, status, duration, structured output or bounded text, and optionally named artifacts. Tools must not be invoked based on unvalidated model-generated arguments.

### Namespace rules

- Built-ins use `files.*`, `search.*`, `patch.*`, `shell.*`, `git.*`, `tests.*`, `diagnostics.*`, `browser.*`, `desktop.*`.
- MCP tools use an internal ID such as `mcp.<server-id>.<tool-name>`; display a friendly name but keep the unique server identity.
- Reject or explicitly disambiguate duplicate MCP server IDs and tool names. No external tool may impersonate a built-in.
- Permission checks follow the actual operation, not the text of a tool description.
- Tool calls are not inherently safe because a remote MCP server labeled them “read-only.”

## 2. Required coding-tool capabilities: v0.1

Implement these with **Deep Agents built-ins and instrumented backends when possible**, and CodeMisterio tools only when those are insufficient. Names below are conceptual CodeMisterio IDs, not a claim that they are the literal Deep Agents tool names.

| Category | Proposed tools | Behavior |
| --- | --- | --- |
| Workspace | `files.list`, `files.read`, `files.stat` | Enumerate and read allowed workspace paths with line numbers and size caps |
| Search | `search.glob`, `search.grep` | File and text search using deterministic local implementations, with bounded matches |
| Editing | `patch.apply`, `files.write` | Apply targeted diffs / create or replace files, with approval and dirty-worktree safeguards |
| Shell | `shell.run` | Run bounded development commands with working directory, timeout, exit code, stdout/stderr, cancellation |
| Git | `git.status`, `git.diff`, `git.log` | Read repository state, staged/unstaged changes and recent history |
| Tests | `tests.run` | Discover or invoke a selected test command and return machine-readable verification evidence |
| Managed processes | `process.start`, `process.stop`, `process.restart`, `process.health` | Track actual process lifecycle, PID, output and independent readiness checks |
| Live events | `activity.stream` (internal bridge, not model tool) | Render verified creates/edits/deletes, actual diff lines, process lifecycle, command output and status |

### v0.1 behaviors

- **Activity streaming is mandatory:** before/after instrumented filesystem writes, accurate unified-diff hunks/line numbers, command output, process lifecycle and explicit failures. Consult [ACTIVITY_STREAM.md](ACTIVITY_STREAM.md).
- Deep Agents graph/tool events are not automatically evidence of actual changes. Capture file/process effects at the backend/executor boundary.
- The raw Deep Agents host shell backend is not isolated: configure real command safety/approvals and treat virtual path settings as insufficient sandboxing.

- All file access is scoped to the selected workspace by default. Resolve paths and symlinks before enforcing boundaries.
- Search ignores generated/large files and respects ignore rules by default; allow explicit safe override for relevant files.
- Patch application checks expected context so changes fail rather than silently overwriting concurrent user edits.
- `shell.run` is not equivalent to unrestricted access; authorization, sandboxing, environment filtering and timeouts remain essential.
- `tests.run` invokes only allowed test commands. It can start with Python/pytest fixtures; language-general autodetection comes later.
- Results distinguish **passed**, **failed**, **not run**, **timed out**, and **blocked by policy**.
- Write/delete operations are not automatically retryable.

## 3. Useful built-in tools: v0.2

| Category | Proposed tools | Behavior |
| --- | --- | --- |
| File operations | `files.move`, `files.mkdir`, `files.delete` | Scoped filesystem changes, heightened permissions for deletion |
| Git operations | `git.branch`, `git.checkout`, `git.stage`, `git.commit` | Controlled branch/commit workflow, never auto-push without explicit authorization |
| Diagnostics | `diagnostics.lint`, `diagnostics.typecheck`, `diagnostics.format_check` | Discover project tooling (Ruff, mypy, ESLint, etc.) and capture results |
| Project discovery | `project.inspect` | Inspect manifests (pyproject, package.json, Cargo.toml, etc.), detect likely test/build commands |
| Web/fetch | `web.fetch` | Retrieve bounded, approved HTTP resources; respect network policy; no implicit credential access |
| MCP | `mcp.*` (dynamic) | Discover and invoke approved tools from local and remote MCP servers, as described in [MCP.md](MCP.md) |

Additional tools should only be added if they solve a real coding task more reliably than using existing primitives.

## 4. Later built-in tool packs

**v0.3 — Browser / computer use**

- `browser.navigate`, `browser.inspect`, `browser.click`, `browser.fill`, `browser.screenshot`, `browser.console`.
- Optional `desktop.screenshot`, `desktop.click`, `desktop.type`, `desktop.keypress`, `desktop.scroll` in an isolated VM.
- Prefer Playwright/DOM-level assertions over coordinate clicking; require explicit opt-in and independent policy checks.

**v0.4 — Advanced engineering**

- `code.symbols`, `code.references` / optional LSP-backed operations.
- `tests.coverage`, `tests.generate` workflows, `git.worktree`, structured dependency/security scanners.
- Bounded subagent delegation with separate budgets and permission scope.

Do not expose unavailable tools or claim they are functional in CLI help output.

## 5. Permissions and environment model

Suggested baseline:

| Tool effect | Default policy |
| --- | --- |
| Read workspace files; Git read-only | Allow, except sensitive files excluded by policy |
| Bounded search; read-only diagnostics | Allow within scoped workspace |
| Modify workspace files | Ask, unless workspace-scoped auto-edit is explicitly enabled |
| Shell commands, installs, or network side effects | Policy-sensitive: allow narrow known-safe commands, ask for other operations |
| Git commit/branch mutation | Ask |
| Destructive operations, force pushes, publishing, credentials | Strong approval or deny |
| MCP tool execution | Evaluate the server's trust level **and** the actual tool effect |
| Browser/desktop control | Off until explicitly enabled; use isolation |

A tool may indirectly launch child processes or use the network. Simple allowlists or string matching do not make shell execution safe; use process/environment isolation as appropriate. Credentials must not be printed to tool output or stored in audit logs.

## 6. Tool lifecycle and reliability

- Validate schema + payload size before execution.
- Resolve permissions **per call**, including MCP tools; no global “trust all tools” switch.
- Use deadlines, output caps, process cleanup and cancellation propagation.
- Retain exit codes, stderr, relevant logs and artifact references for debugging.
- Avoid logging source files, screenshots or credentials by default in telemetry.
- Detect duplicate side-effecting calls after interrupted sessions.
- Provide clear CLI feedback for missing dependencies (`rg`, `git`, `pytest`, browser driver, etc.).
- Unit-test tools with temporary repositories and denied/malformed cases.

## 7. Tool acceptance tests

A tool is ready only when it has:

1. A documented schema and permission classification.
2. Deterministic success tests and at least one failure/abuse test.
3. Cancellation or bounded timeout behavior where applicable.
4. Safe behavior on dirty worktrees and workspace escapes where relevant.
5. A result contract consumed by both model adapter and CLI, including clear failure states.

See [../PLAN.md](../PLAN.md) for release gates, [ACTIVITY_STREAM.md](ACTIVITY_STREAM.md) for real-time verified events and [MCP.md](MCP.md) for extension support.
