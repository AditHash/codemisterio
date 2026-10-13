# CodeMisterio Architecture

> **Status:** Proposed architecture, not a description of a working implementation. Changes to these choices should be recorded as short design decisions in this document or linked issues.

## 1. Product boundary

CodeMisterio is a local-first, extensible **agentic coding CLI and harness**. It is not limited to code review: it should be able to understand repositories, plan changes, edit code, execute development tools, observe results, debug failures, and explain its work.

The harness owns the agent loop, permissions, tool execution, context management, sessions, and user experience. Models supply reasoning and tool-call decisions through provider adapters. No individual model vendor or agent framework should be required by the core.

Primary interface: terminal CLI; optional rich TUI. Headless automation, IDE integration, remote execution, and multi-agent orchestration are future capabilities, not MVP requirements.

## 2. Core principles

1. **Harness-first:** control the agent lifecycle in CodeMisterio's own Python code.
2. **Provider independence, not lowest-common-denominator behavior:** normalize common events and tools; keep optional provider-native features behind capability checks.
3. **Deterministic before probabilistic:** use Git, language servers, parsers, linters, test runners, and Playwright when they are more precise than visual reasoning.
4. **Safe by default:** a model's request is never authorization to execute a dangerous action.
5. **Local-first and inspectable:** users can see proposed edits, tool calls, approvals, and session state.
6. **Evidence over confidence:** test results, diffs, logs, and reproducible steps support claims.
7. **Incremental delivery:** one reliable agent loop precedes subagents, remote sandboxes, and desktop control.

## 3. System overview

~~~text
User / CLI / TUI
        |
        v
CLI command + session controller
        |
        v
+---------------- CodeMisterio Harness ----------------+
| Agent loop / run state / cancellation                 |
| Prompt + context assembler / compaction               |
| Provider router + feature negotiation                 |
| Tool registry / execution scheduler                   |
| Permissions / user approval / audit trail             |
| Session persistence / event streaming                 |
+-------------+------------------+---------------------+
              |                  |
      Model adapters       Tool execution
      - OpenAI             - repo files/search/patch
      - Anthropic          - shell/Git/build/tests
      - Gemini (later)     - MCP (later)
      - Ollama (later)     - browser (later)
                           - desktop (later)
              |                  |
              +--------+---------+
                       v
            Results + validation evidence
                       |
                       v
              User-visible summary
~~~

The model sees tools exposed by the harness. The harness validates requested arguments, checks the permission policy, executes the operation, captures bounded results, and returns observations to the model.

## 4. One agent run

A coding task is a sequence of **model turns** and **tool results** controlled by the harness.

~~~text
Receive task
  -> resolve workspace and permissions
  -> load session/context
  -> select compatible provider and tools
  -> request model response (stream events to UI)
  -> if tool calls:
       validate arguments
       evaluate risk and request approval if needed
       execute with timeouts and resource bounds
       redact/truncate observations where appropriate
       append results to session
       compact context if necessary
       continue loop
  -> else:
       verify claims against available evidence
       present changes, tests, warnings and final answer
~~~

Hard stops: user cancellation, maximum turns, token/cost budget, execution timeout, repeated tool failure, or unrecoverable provider error. Stop states must be distinguishable from successful completion.

The agent may propose a plan, but a separate planner or mandatory plan phase is **not** required for simple tasks.

### Minimal state contracts (conceptual)

- **Run:** ID, workspace, user request, selected provider/model, operating mode, budgets, status.
- **Message:** role, text and/or multimodal parts, optional reasoning/metadata as supported.
- **ToolCall:** ID, canonical tool name, validated arguments, requested scope.
- **ToolResult:** call ID, status, bounded stdout/stderr or structured data, duration, artifacts.
- **Event:** session/run IDs, event type, timestamp, payload for CLI/TUI streaming.
- **Approval:** call/operation ID, risk category, decision, scope and provenance.
- **ModelCapabilities:** tool calls, streaming, vision, structured outputs, native computer use, context limit (if known).

Define these contracts explicitly and version persisted representations before adding multiple providers.

## 5. Component responsibilities

### CLI and TUI

- **MVP:** a CLI that accepts a prompt, selects a workspace, streams progress, renders tool requests, and requests approvals.
- **Future:** a Textual-based TUI for session history, tool traces, permission prompts, diffs, and cost usage.
- CLI must function without a TUI, to support CI and accessibility.
- Command names are proposals until implemented; avoid publishing installation instructions that do not work.

### Agent loop

- CodeMisterio owns tool-call iteration, budgets, retries, interrupts, and completion criteria.
- Agent run state must be independent of any provider SDK response object.
- Initial execution is sequential and predictable. Parallel reads and subagents arrive only after permissions and cancellation are reliable.

### Provider layer

Implement a small adapter protocol such as:

~~~python
class ModelAdapter(Protocol):
    async def generate(self, request: ModelRequest) -> AsyncIterator[ModelEvent]:
        ...
    def capabilities(self, model: str) -> ModelCapabilities:
        ...
~~~

The exact types are to be finalized during implementation. Provider adapters translate request/response formats, authentication, tool definitions and results, token usage, and provider-specific errors. The core should not import provider SDKs directly.

Treat *native computer-use APIs*, reasoning traces, prompt caching, and model-specific modalities as optional extensions. Never silently claim equivalent behavior across providers.

### Tool layer

Tools are registered with a canonical name, schema, permissions, execution context, and bounded result format. Proposed baseline:

| Tool | Purpose | Risk consideration |
| --- | --- | --- |
| `files.list`, `files.read` | Inspect repository content | Workspace and symlink boundary |
| `search.code` | Search repository using available local tooling | Time and output limits |
| `files.patch` | Apply targeted patches | Review diffs; limit writable paths |
| `shell.run` | Build, lint, run tests and inspect processes | Explicit policy; sandbox; timeouts |
| `git.status`, `git.diff` | Inspect changes | Avoid unintended mutations |
| `git.commit` | Commit approved changes | Explicit opt-in |
| `browser.*` (later) | Playwright and visual UI testing | Browser profile, network and credentials |
| `desktop.*` (later) | Screenshots, mouse and keyboard | Highly privileged; explicit opt-in |

Use structured patching over whole-file replacement when appropriate. Avoid granting arbitrary shell access to an agent solely because a tool was registered.

### Context and memory

- Read only the files needed for the task; don't inject an entire repository blindly.
- Track a bounded working set of relevant files, current plan, tool summaries, errors, and important user constraints.
- Separate transient run context from persistent user-approved project knowledge.
- When compaction is needed, preserve unfinished work, file paths, decisions, pending approvals, and error evidence.
- Repository instructions in `AGENTS.md` are **project data**, not an override of safety policy or user authorization.

### Session persistence

SQLite is a suitable first implementation for runs, messages, tool events, approvals and usage. Store schema versions and support migrations. Never store raw API keys; redact secrets in logs. Persist enough metadata to resume safely, but do not automatically repeat a previously approved destructive action.

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
├── pyproject.toml                 # future
├── src/codemisterio/              # future
│   ├── cli/
│   ├── core/                      # loop, run state, context, sessions
│   ├── providers/                 # model SDK adapters
│   ├── tools/                     # registry + built-in tools
│   │   └── computer/              # later
│   ├── security/                  # permissions, scope, auditing
│   ├── mcp/                       # later
│   └── tui/                       # later
└── tests/                         # future
~~~

Directories marked `future` are illustrative: do not create empty scaffolding purely to match the diagram.

## 8. Technology choices (tentative)

| Concern | Initial direction |
| --- | --- |
| Runtime | Python 3.12+ with asyncio |
| Project management | uv, pyproject.toml |
| Basic CLI | Typer |
| Terminal formatting | Rich |
| Advanced TUI | Textual (later) |
| Data contracts | Pydantic |
| Agent loop | Custom, with optional future LangGraph integration |
| Model integration | Provider-specific adapters behind a common protocol |
| Persistence | SQLite |
| Browser control | Playwright (later) |
| Desktop control | Optional isolated computer-use adapters (later) |
| Remote/sandbox execution | Local permissions first; Docker/VM later |
| Extensibility | MCP, skills and repository instructions (after MVP) |

No framework should be adopted merely to claim feature parity. Evaluate dependencies for maintenance burden, license compatibility, portability and security before merging.

## 9. Testing and observability strategy

- Unit tests: event normalization, permission decisions, path containment, patch application, session serialization, context budgets.
- Integration tests: local fixture repositories; fake model adapters; tool execution and interruption.
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

See [PLAN.md](PLAN.md) for milestone gates and [AGENTS.md](AGENTS.md) for instructions to coding agents working in this repository.
