# CodeMisterio Architecture

> **Status:** Proposed architecture, not a description of a working implementation. Changes to these choices should be recorded as short design decisions in this document or linked issues.

## 1. Product boundary and framework decision

CodeMisterio is a local-first, extensible **agentic coding CLI** that inspects codebases, modifies files, executes development commands, runs tests, manages opt-in development processes, and reports verified results in real time.

**Architecture decision (October 2026):** LangChain **Deep Agents** is the main agent runtime. CodeMisterio will **not** implement a competing custom tool-calling loop. Deep Agents provides planning options, context management, filesystem and shell abstractions, skills, subagents, middleware and human-in-the-loop flows. Its underlying **LangGraph** runtime supplies streaming and checkpointing. **LangChain** provides model integrations. CodeMisterio adds a coding-specific CLI, model/config policy, extra tools, MCP integrations, process management, file-change evidence, live activity timeline and user-centered workflows.

Four reference repositories:
- [LangChain](https://github.com/langchain-ai/langchain) — model integrations and tooling.
- [Deep Agents](https://github.com/langchain-ai/deepagents) — primary agent framework.
- [LangGraph CUA](https://github.com/langchain-ai/langgraph-cua-py) — optional computer-use backend, not the core runtime.
- [Open SWE](https://github.com/langchain-ai/open-swe) — reference implementation of Deep Agents-based engineering automation; not an additional required dependency.

Primary interface: interactive local CLI; richer TUI, remote sandboxes and headless automation are later phases. The runtime must remain useful without MCP servers, browser automation or a hosted service.

## 2. Core principles

1. **Use Deep Agents, extend via supported APIs:** customize prompts, middleware, backends, tools, skills, model selection, approvals and checkpoints before considering a fork.
2. **Inspectable, evidence-driven CLI:** stream significant actions as they happen; never substitute LLM narration for verified file/process state.
3. **Provider-agnostic by default:** use LangChain chat models and detect feature availability rather than inventing parity across vendors.
4. **One execution policy:** Deep Agents native tools, CodeMisterio built-ins and MCP tools must all respect workspace/sandbox permissions.
5. **Deterministic tools first:** Git diffs, shell exit codes, pytest reports and Playwright assertions beat unverified model assumptions.
6. **Preserve developer control:** explicit workspace, visible edits, approval interrupts, cancellation, managed process lifecycle and truthful summaries.
7. **No premature duplication:** reuse Deep Agents context management, filesystem tools, task orchestration and state rather than reimplementing them.
8. **Cross-platform, extensible delivery:** console first, richer TUI and computer use later. Design the event bus for those consumers now.

## 3. System overview

~~~text
User -> CodeMisterio CLI / Rich live renderer
                 |
                 v
     CodeMisterio Session + Activity Bridge
     (event correlation, journal, safety, display)
                 |
                 v
         LangChain Deep Agents
      create_deep_agent(...) runtime
           /       |        \
    LangChain   LangGraph    Deep Agents
     models     streaming    middleware:
                checkpoint    - filesystem
                interrupts    - planning (as configured)
                              - context
                              - skills/subagents
                 |
           Tool / backend execution
           /        |          \
     Deep Agents   CodeMisterio   MCP client
     built-ins     wrapped tools  (v0.2)
           \        |          /
            Permission/Execution Policy
                      |
       Filesystem + Shell + Git + Tests
       Managed processes (incremental)
       Browser / Desktop (later)
                      |
     Verified ActivityEvent + evidence
                      |
       CLI / JSONL / stored event journal
~~~

**Trust boundary:** even if Deep Agents allows a tool to run, CodeMisterio must enforce approved execution and resource scope at a lower-level backend/executor boundary. LangGraph stream messages inform progress; instrumented file/process tools produce evidence.

## 4. One agent run

~~~text
User request
  -> initialize workspace, provider/model and approved tools
  -> build create_deep_agent(...) with CodeMisterio middleware/backends
  -> subscribe to LangGraph event/stream output
  -> model plans and invokes tools via Deep Agents
  -> permission interrupt/authorization before privileged operations
  -> instrumented tool/backend executes and verifies effects
  -> normalize model/graph/tool updates into ActivityEvent records
  -> persist and stream evidence to CLI continuously
  -> graph loops as required; checkpoints enable recovery
  -> independent final git diff/test/process checks
  -> truthful user-facing task summary
~~~

The actual tool-calling loop, subagent lifecycle and context management belong to **Deep Agents**, not a separate CodeMisterio implementation. Use tested public extension points. Avoid depending on internal LangChain event names without contract tests.

### State and event contracts

Deep Agents/LangGraph owns graph and checkpointed conversation state. CodeMisterio separately owns versioned user-facing **ActivityEvent** records and tool-evidence artifacts, including run/session IDs, tool-call correlation ID, event type, status, timestamp, actor/subagent, workspace-relative path, actual diff hunks, process state, stdout/stderr artifacts, exit code and permission outcome.

See [docs/ACTIVITY_STREAM.md](docs/ACTIVITY_STREAM.md) for the full lifecycle/status model, structured JSON event example and acceptance tests. Actual events must distinguish requested/started/succeeded/failed/denied/unverified.

**Streaming:** prefer the current typed LangGraph event API where supported; compatibility path is `astream(..., stream_mode=["messages","updates","custom"], version="v2")` with an explicit version gate. Model tokens and high-level progress are not proof of filesystem changes. Hide private chain-of-thought and redact secrets.

## 5. Component responsibilities

### CLI and TUI

- **MVP:** a CLI that accepts a prompt, selects a workspace, streams progress, renders tool requests, and requests approvals.
- **Future:** a Textual-based TUI for session history, tool traces, permission prompts, diffs, and cost usage.
- CLI must function without a TUI, to support CI and accessibility.
- Command names are proposals until implemented; avoid publishing installation instructions that do not work.

### Deep Agents runtime and provider integration

- Instantiate the coding agent with `create_deep_agent`, an explicit LangChain chat model, workspace-aware backend, optional planning middleware, and configurable permission/approval policy.
- Prefer Deep Agents' supplied filesystem, shell, subagent, context, skills and checkpoint features over duplicate implementations.
- Deep Agents task planning is configuration-dependent and may be opt-in; enable explicit todo tracking for complex engineering tasks where helpful.
- Use LangChain chat model integrations for OpenAI, Anthropic, Gemini, and compatible/local providers as they are tested. Preserve model-specific capabilities and limitations.
- Stream through LangGraph to the CodeMisterio activity bridge; additional tools should emit structured custom events from trusted execution wrappers.
- **Safety:** Deep Agents' LocalShellBackend executes host shell commands and is **not sandbox isolation**, even when `virtual_mode=True`. Use the correct path/permission guards, approval middleware and eventually isolated containers/VMs; do not imply local host safety is guaranteed.
- Always test the pinned versions of Deep Agents, LangChain and LangGraph together. Project code should use public extension points rather than forked private internals.

### Tool layer

Tools are registered with a canonical name, schema, permissions, execution context, provenance, and bounded result format. A **unified tool registry** is part of v0.1; the MCP client extends it in v0.2. Proposed baseline:

| Tool | Purpose | Risk consideration |
| --- | --- | --- |
| `files.list`, `files.read`, `files.stat` | Inspect repository content | Workspace and symlink boundary |
| `search.glob`, `search.grep` | Search files and content deterministically | Time, ignore rules and output limits |
| `patch.apply`, `files.write` | Apply targeted patches and create/update files | Approval; avoid overwriting user changes |
| `shell.run`, `tests.run` | Build, lint, run tests and inspect processes | Explicit policy; sandbox; timeouts |
| `git.status`, `git.diff`, `git.log` | Inspect changes and history | Preserve unrelated mutations |
| `git.branch`, `git.commit` (v0.2) | Controlled Git mutation | Explicit opt-in |
| `diagnostics.*`, `project.inspect` (v0.2) | Lint, typecheck, inspect manifests | Respect execution policy |
| `mcp.<server-id>.<tool-name>` (v0.2) | External server-provided tools | Server and per-tool approval; untrusted output |
| `browser.*` (later) | Playwright and visual UI testing | Browser profile, network and credentials |
| `desktop.*` (later) | Screenshots, mouse and keyboard | Highly privileged; explicit opt-in |

Use structured patching over whole-file replacement when appropriate. Avoid granting arbitrary shell access to an agent solely because a tool was registered.

For complete built-in tool contracts, see [docs/TOOLS.md](docs/TOOLS.md).

### MCP client (target: v0.2)

CodeMisterio acts as an MCP **client**, connecting to user-approved servers; the MCP server's tool definitions do not bypass the harness's own policy.

- Support local `stdio` and remote **Streamable HTTP** transports with a maintained Python SDK.
- Use namespaced stable IDs (`mcp.<server-id>.<tool-name>`) to prevent collision with built-ins or other servers.
- Support tool discovery and invocation; expose resources and prompts via explicit lower-trust context interfaces.
- Separate MCP configuration, process lifecycle, connection status, authentication, and per-call permission enforcement.
- Do not auto-execute project-supplied server configuration, downloaded packages, or hidden remote endpoints.
- Bound outputs, timeouts and retries; side-effecting calls are not blindly retried on disconnect.
- Respect protocol version negotiation. The MCP 2026-07-28 specification changed behavior relative to earlier deployments; validate compatibility with tests.
- Treat remote HTTP credentials and local child-process environments as sensitive; never print tokens or pass unrestricted host environment variables.

Conceptually:

~~~text
Agent loop
    -> unified registry (built-in + MCP adapters)
    -> argument validation
    -> permission engine
    -> executor / MCP client
    -> normalized ToolResult
    -> model context + CLI event
~~~

See [docs/MCP.md](docs/MCP.md) for server management, transports, authentication, and acceptance tests.

### Context, checkpointing and memory

- Deep Agents supplies context compression, subagent separation, file-backed context and optional persistent memory; configure instead of rebuilding.
- LangGraph checkpointing provides graph thread state. CodeMisterio must still track an independent **activity journal** so a resumed session does not falsely re-report actions as newly executed.
- Persist user-chosen model/config, workspace and permission state where needed. Do not persist raw API keys.
- For resumed tool calls, deduplicate side effects using tool-call IDs and idempotency records, not just conversation history.
- External `AGENTS.md` guidance, skills, files and MCP resources are lower-trust than user instructions and tool security rules.

### Permissions and trust boundaries

Three separate boundaries matter:

1. **Instructions:** user instructions outrank untrusted README files, web content, tool output, and source-code comments. Treat retrieved text as data.
2. **Filesystem/process:** restrict paths to the chosen workspace by default; resolve real paths and symlinks; block traversal escapes; isolate command execution where possible.
3. **Network/desktop:** do not grant arbitrary browser profiles, saved credentials, network destinations, or desktop control by default.

Proposed policy:

| Operation | Proposed default |
| --- | --- |
| Read within workspace, inspect Git diff | Allow |
| Edit files within workspace | Ask until user enables a scoped auto-edit mode |
| Run known, bounded local test/lint commands | Allow only under explicit execution policy |
| Install packages or arbitrary shell commands | Ask |
| Read secrets, private files outside workspace | Deny unless explicitly authorized and safe |
| Network requests, authentication, publishing, pushing Git | Ask |
| MCP server installation/launch and remote connection | Explicitly approve server command/origin and scoped access |
| MCP tool invocation | Evaluate actual effect per call; untrusted server metadata does not grant permission |
| Delete broadly, overwrite unrelated work, elevated privileges | Ask or deny based on policy |
| Browser control | Opt-in, isolated browser session |
| Full desktop control | Off by default; prefer isolated VM |

Build a permission engine independent of model prompts. Approval decisions are scoped (per call, session, workspace) and auditable. “Autonomous mode” must not bypass non-overridable safeguards.

### Tool and command results

Always capture exit status, duration, stdout, stderr, and failures. Cap output size while retaining the relevant tail and an artifact pointer where useful. A tool failing does not mean the entire run failed; a tool reporting success is not proof that the user's requested feature works.

## 6. Computer use (later milestone)

Computer use is an **optional tool execution backend**, not a requirement for CodeMisterio's fundamental agent loop.

Recommended layering:

~~~text
Coding agent -> computer-use tools -> policy gateway
                                 -> environment adapter
                                     -> Playwright browser
                                     -> screenshot-driven browser
                                     -> isolated desktop/VM
~~~

- Start with **Playwright** for deterministic browser tests, DOM inspection, screenshots, console/network errors.
- Add visual coordinate-driven interactions only when necessary; check provider capabilities before enabling native computer-use APIs.
- Add desktop mouse/keyboard control in a dedicated isolated environment before considering host machine access.
- Require affirmative approval for login, account changes, purchases, sending messages, destructive operations and other consequential external actions.
- Record reproducible evidence: URLs, screenshot references, console errors, test assertions and reproduction steps (without secrets).
- Detect when a tool's observed UI differs from expected state. Never blindly replay clicks against a changed screen.

## 7. Proposed repository layout

~~~text
codemisterio/
├── README.md
├── ARCHITECTURE.md
├── PLAN.md
├── AGENTS.md
├── docs/
│   ├── TOOLS.md
│   ├── MCP.md
│   └── ACTIVITY_STREAM.md
├── pyproject.toml                       # future
├── src/codemisterio/                    # future
│   ├── cli/                             # Rich renderer, input, JSONL
│   ├── runtime/                         # Deep Agents factory / LangGraph bridge
│   ├── activity/                        # events, journal, diff, evidence
│   ├── tools/                           # extra tools, wrappers, process manager
│   ├── providers/                       # model selection/config, not replacement agent loop
│   ├── security/                        # permissions/scope/sandbox policy
│   ├── mcp/                             # v0.2
│   └── tui/                             # later
└── tests/                               # future
~~~

Illustrative only; create files when implementing features rather than unused empty stubs.

## 8. Technology choices (committed direction, pending implementation)

| Concern | Direction |
| --- | --- |
| Runtime language | Python 3.12+ and asyncio |
| Agent harness | **LangChain Deep Agents** (`deepagents`) |
| Graph execution / checkpointing | **LangGraph** (as used by Deep Agents) |
| Model abstraction | **LangChain** chat model integrations |
| CLI | Typer + Rich live activity feed |
| Rich TUI | Textual after reliable CLI streaming |
| Activity stream | CodeMisterio event normalizer + file/process evidence |
| Validation and schemas | Pydantic, Git, test runners |
| Session persistence | LangGraph checkpointer; separate CodeMisterio activity journal (SQLite where useful) |
| Shell/filesystem | Deep Agents backends + instrumented policy guards |
| MCP | Client adapters via LangChain/Deep Agents extension points (v0.2) |
| Browser control | Playwright (v0.3) |
| Desktop computer use | Optional LangGraph CUA integration / isolated VM (v0.3+) |
| Sandbox isolation | Explicitly scoped tools; Docker/VM as optional later environments |
| Packaging | uv + pyproject.toml |

**Do not write a second general-purpose agent loop.** Our differentiation is the transparent CLI, coding-oriented tools, verified operation tracking and extensible execution experience.

## 9. Testing and observability strategy

**Release blocker:** live step-by-step CLI activity and evidence-backed diff events are required in v0.1; see [docs/ACTIVITY_STREAM.md](docs/ACTIVITY_STREAM.md).


- Unit tests: LangGraph-to-ActivityEvent normalization, file diff hunks/line numbers, process events, permissions, path containment and redaction.
- Integration tests: Deep Agents with deterministic fake LangChain models, fixture repositories, tool execution streaming, interruption and checkpoint/resume.
- Provider contract tests: opt-in, recorded fixtures where possible; never require paid API access for default CI.
- End-to-end tests: small code-edit tasks with deterministic success criteria.
- Computer-use tests: isolated test websites and VMs; screenshots and safe fake accounts only.
- Metrics: task success with verification, regressions, unauthorized actions prevented, cost/tokens per task, latency, human approvals, interruption/resume correctness.

## 10. Open decisions

These should be resolved by implementation experience, not speculative abstractions:

- Minimum Python version and supported operating systems.
- One provider to integrate first versus a minimal second adapter to validate the abstraction.
- Scope of auto-edit versus approval-per-write.
- How to record context summaries without losing essential debugging evidence.
- Cross-platform shell isolation and process cleanup.
- MCP trust boundaries and third-party skill installation.
- CLI naming and distributable package metadata.
- Open-source license choice (the repository currently has no LICENSE).
- Tested version compatibility and extension points for Deep Agents/LangGraph event streaming.
- Controlled process lifecycle and distinguishing verified restarts from unverified shell claims.

See [PLAN.md](PLAN.md) for milestone gates, [docs/ACTIVITY_STREAM.md](docs/ACTIVITY_STREAM.md) for live CLI events, [docs/TOOLS.md](docs/TOOLS.md) for tool integration, [docs/MCP.md](docs/MCP.md) for server integration, and [AGENTS.md](AGENTS.md) for coding-agent instructions.
