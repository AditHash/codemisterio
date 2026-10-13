# CodeMisterio

**An open-source-intended, model-agnostic agentic coding CLI and harness.**

> **Project status: design and planning.** This repository currently contains specifications, not a runnable coding agent. Installation instructions and executable CLI examples will be added after the first working release. A license has not yet been selected, so the repository should not be described as licensed open source yet.

CodeMisterio aims to bring a capable software engineering agent to the terminal. It is inspired by the workflow of tools such as Claude Code, Codex and OpenCode, while aiming to give developers control over the model, execution tools, permissions and environment.

**The harness is the product.** CodeMisterio should own the agent loop, context, tool registry, approvals, session state and user experience. Language models are interchangeable reasoning backends, not owners of the workflow.

## Vision

A developer should be able to give CodeMisterio a repository and a task, then inspect how the agent explores code, proposes edits, runs development commands, tests its changes, and reports verifiable results.

Example *future* workflow (illustration, not a command that works today):

~~~text
$ codemisterio
> Find why authentication tests fail, fix the code and verify the change.

Reading project files...
Running pytest...
Investigating traceback...
Proposing patch to auth/token.py...
Approval requested for file edit...
Running tests after patch...
Reporting diff and test results.
~~~

The goal is not to generate code blindly. It is to close the loop between **understanding, changing, executing and validating** software.

## Intended capabilities

| Area | Direction | Status |
| --- | --- | --- |
| Terminal coding agent | Interactive sessions, streaming tool events, plans and explanations | Planned |
| Built-in coding tools | Files, glob/grep search, patch editing, terminal commands, Git and tests | v0.1 planned |
| Development execution | Bounded shell commands, linting, builds and test runs | Planned |
| Debugging and code quality | Identify bugs, write regression tests, review changes | Planned |
| Provider independence | Model adapters for OpenAI, Anthropic and potentially Gemini/local models | Planned |
| Policy and permissions | Workspace boundaries, approvals and auditable actions | Planned |
| Sessions and context | Persistence, context budgeting and controlled resumption | Planned |
| MCP server integration | Local stdio and remote Streamable HTTP servers; tools, resources, prompts and server management | v0.2 planned |
| Extended tool catalog | Project discovery, diagnostics, controlled Git operations and HTTP fetch | v0.2 planned |
| Repository instructions and skills | Explicitly loaded guidance and reusable skills under safety policy | v0.2 planned |
| Browser validation | Playwright, screenshots, console errors, UI testing | Later milestone |
| Desktop computer use | Optional, sandboxed mouse/keyboard/window control | Later milestone |
| Advanced agents | Bounded subagents and parallel work | Later milestone |

These are **goals**, not shipped features. Provider availability and feature parity must be verified during implementation.

## What makes CodeMisterio different?

Rather than centering the product on a single model or narrow code-review workflow, CodeMisterio is intended as a **developer-controlled coding harness**:

- **Model replaceability:** start with one real provider, then validate the interface with others. Provider-native capabilities remain optional rather than artificially flattened.
- **Visible tool execution:** show operations, diffs, failures and verification evidence instead of only claiming success.
- **Explicit permission boundaries:** a model's tool call does not itself authorize filesystem, terminal, network or desktop access.
- **Extensible tool layer:** robust built-in tools first; a shared tool registry supports external MCP servers starting in v0.2 and computer-use backends later.
- **Local-first workflow:** work in the chosen repository while preserving unrelated files and uncommitted changes.

These are design goals, not a claim that CodeMisterio currently outperforms other agents.

## Proposed architecture

~~~text
                  CodeMisterio CLI / TUI
                           |
                    Core Agent Harness
               +-----------+-----------+
               |           |           |
          Model Router  Tool Registry  Policy Engine
               |           |           |
         Model adapters    |       Approvals
               |           |
         OpenAI / ...   Files / Git / Shell / Tests
                           |
                 MCP servers (v0.2)
                           |
                 Browser / Desktop (later)
                           |
                 Workspace or Sandbox
                           |
                Evidence + Final Report
~~~

The initial architecture uses a **custom Python agent loop**, with optional integration of orchestration libraries later if they provide a clear benefit. See [ARCHITECTURE.md](ARCHITECTURE.md) for component boundaries, contracts, and security rules.

## Implementation direction

Proposed stack, subject to implementation validation:

- **Runtime:** Python 3.12+ and asyncio.
- **CLI:** Typer and Rich; Textual can power a richer TUI later.
- **Schemas:** Pydantic.
- **Model layer:** small provider adapters, initially one provider.
- **Execution:** built-in filesystem/search/patch, Git, bounded shell and tests; project-specific diagnostics as integrations.
- **Persistence:** SQLite.
- **UI automation (later):** Playwright for browsers; optional isolated desktop adapters.
- **Integration (v0.2):** MCP client with local stdio and remote Streamable HTTP server support, plus explicit project-level instructions and skills.
- **Packaging:** pyproject.toml with uv for development.

No executable package or supported installation flow exists yet.

## Development roadmap

**Milestone 0 — Foundations:** project documentation, license selection, packaging, offline CI and contributor instructions.

**v0.1 — Working coding CLI and built-in tools:** one real model provider, shared tool registry, file and search tools, patching, controlled shell execution, Git inspection, test validation, permissions and truthful reports.

**v0.2 — MCP and extensible harness:** more model adapters, local and remote MCP servers, MCP tools/resources/prompts, additional built-in tools, session persistence, context management and project instructions.

**v0.3 — Browser and computer use:** Playwright-based browser tests, screenshots and optional sandboxed desktop interactions.

**v0.4 — Advanced engineering:** richer TUI, subagents, isolated worktrees, parallel workflows and deeper software validation.

**v1.0 — Stable open-source release:** an OSI-approved license, security review, cross-platform verification, packaging, documented compatibility and stable interfaces.

Detailed tasks, acceptance criteria and release gates are in [PLAN.md](PLAN.md).

## Repository documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) — architecture, trust boundaries, tool interfaces and design decisions.
- [PLAN.md](PLAN.md) — phased milestones, tasks and acceptance tests.
- [AGENTS.md](AGENTS.md) — guidance for coding agents and contributors working on this repository.
- [docs/TOOLS.md](docs/TOOLS.md) — built-in tool catalog and uniform execution contracts.
- [docs/MCP.md](docs/MCP.md) — MCP client design, server configuration, transports and security.

## Safety model

CodeMisterio will execute code and, eventually, interact with user interfaces. Its core must therefore distinguish **model intent** from **user authorization**.

By default, proposed tools should be limited to an explicit workspace. Risky commands, external side effects, credential use and host desktop access require carefully scoped authorization. Browser or desktop control should use isolated environments when possible. No autonomy setting should bypass hard safety boundaries.

Actual controls and tests will be implemented incrementally; documentation is not a security guarantee.

## Contributing

The project is at an early design stage. Discussions, issues and focused implementation proposals are welcome. Read [AGENTS.md](AGENTS.md) and [PLAN.md](PLAN.md) before submitting changes.

**License:** not yet selected. Until a license is published, public visibility alone does not authorize reuse or redistribution as an open-source project.

## Current focus

The immediate target is a minimal coding CLI that can:

1. Inspect a small Python repository.
2. Use built-in file, search, Git and terminal tools to find a failing pytest test.
3. Explain and propose a targeted fix.
4. Request approval before changing files.
5. Apply a patch and rerun verification.
6. Report the actual results and Git diff.

**Success means a reproducible, validated engineering task — not merely plausible generated code.**
