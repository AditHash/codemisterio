# CodeMisterio

**An open-source-intended, model-agnostic agentic coding CLI and harness.**

> **Project status: early implementation preview (v0.1 alpha).** A CLI entry point and offline-tested activity/file-snapshot components are present. Actual Deep Agents/provider calls have not been smoke-tested in this environment because PyPI installation was unavailable. There is no production-ready shell runner, MCP client or computer use yet. An OSI license still needs to be selected.

CodeMisterio aims to bring a capable software engineering agent to the terminal. It is inspired by the workflow of tools such as Claude Code, Codex and OpenCode, while aiming to give developers control over the model, execution tools, permissions and environment.

**Deep Agents is the chosen agent harness.** CodeMisterio is built on [LangChain Deep Agents](https://github.com/langchain-ai/deepagents) and its LangGraph runtime. Deep Agents owns the agent loop, planning and context; CodeMisterio owns the developer-facing CLI, verified step-by-step activity tracking, coding tool integrations, permissions, MCP configuration and user experience. Language models remain selectable through LangChain integrations.

## Try the first development preview

Install Python 3.12+ and uv, then in a fresh checkout:

~~~bash
uv sync --extra openai --extra dev
uv run codemisterio version
uv run pytest -q
~~~

For an actual model task, configure your API credentials in your shell (for example, `OPENAI_API_KEY`), then run:

~~~bash
uv run codemisterio run "Inspect the repository and suggest improvements" --workspace . --model openai:gpt-5.5
~~~

The CLI is **read-only by default**, with Deep Agents `ls`, `read_file`, `glob`, `grep` tools. Add `--allow-edits` for per-call approvals before `write_file` and `edit_file`. `--jsonl` emits machine-readable tool/activity events but is read-only. Arbitrary shell execution, restarting services, browser/desktop automation and MCP are **not yet implemented**. Repository snapshots can miss changes in large, binary, generated or ignored files.

See [docs/BOOTSTRAP.md](docs/BOOTSTRAP.md) for installation and limitations. The CLI currently has 12 passing offline tests; real model integration is unverified until its dependencies and credentials are exercised.

## Vision

A developer should be able to give CodeMisterio a repository and a task, then inspect how the agent explores code, proposes edits, runs development commands, tests its changes, and reports verifiable results.

Example *future* workflow (illustration, not a command that works today):

~~~text
$ codemisterio
> Find why authentication tests fail, fix the code and verify the change.

✓ Read src/auth/token.py:1–120
→ Proposed edit src/auth/token.py:42–42
  - if token:
  + if token and not is_expired(token):
? Approve file edit? [once / session / deny]
✓ Edited src/auth/token.py (+1 −1)
✓ Created tests/test_expired_token.py (+28 lines)
→ Running pytest -q
✓ pytest exited 0 — 27 tests passed
→ Restart requested: dev-api (managed service)
✓ Restarted dev-api (PID change confirmed)
✓ /health returned HTTP 200
✓ Finished — 1 modified, 1 added, 0 deleted
~~~

The goal is not to generate code blindly. It is to close the loop between **understanding, changing, executing and validating** software. **Every operation shown above is illustrative; the actual CLI must derive events from real tool execution and verified diffs/process status, not model narration.**

## Intended capabilities

| Area | Direction | Status |
| --- | --- | --- |
| Terminal coding agent | Deep Agents-backed CLI command, activity events and per-write approvals | Early implementation; real-provider test pending |
| Live step-by-step activity | Tool lifecycle and observed text-file creates/edits/deletes exist; streaming shell/process/test output remains planned | Partial v0.1 |
| Built-in coding tools | Deep Agents filesystem read/search and opt-in writes included; terminal, Git and tests still planned | Partial v0.1 |
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
- **Verified live execution:** show every meaningful operation in a chronological terminal feed—actual file paths and edited lines, added/deleted files, shell output, running processes, restarts, tests, failures and approvals. Commands and diffs are checked independently of model narration.
- **Explicit permission boundaries:** a model's tool call does not itself authorize filesystem, terminal, network or desktop access.
- **Extensible tool layer:** robust built-in tools first; a shared tool registry supports external MCP servers starting in v0.2 and computer-use backends later.
- **Local-first workflow:** work in the chosen repository while preserving unrelated files and uncommitted changes.

These are design goals, not a claim that CodeMisterio currently outperforms other agents.

## Proposed architecture

~~~text
                  CodeMisterio CLI / TUI
                 Live Activity Stream
                           |
                   LangChain Deep Agents
                     (LangGraph runtime)
              +------------+-----------+
              |            |           |
         LangChain     Tool/Backend   Policy +
          Models       Middleware     Approvals
                           |
                 Files/Git/Shell/Tests
                    MCP (v0.2)
                 Browser/desktop (later)
                           |
                Evidence collectors
                (diffs, output, PIDs)
                           |
                   Live CLI + Journal
~~~

The initial architecture uses **LangChain Deep Agents** with its underlying **LangGraph** state and streaming APIs; CodeMisterio adds an activity/event bridge and coding-specific execution tooling. See [ARCHITECTURE.md](ARCHITECTURE.md) for integration details and [docs/ACTIVITY_STREAM.md](docs/ACTIVITY_STREAM.md) for event contracts.

## Implementation direction

Proposed stack, subject to implementation validation:

- **Runtime:** Python 3.12+ and asyncio.
- **CLI:** Typer and Rich; Textual can power a richer TUI later.
- **Schemas:** Pydantic.
- **Agent framework:** LangChain Deep Agents (`deepagents`), powered by LangGraph.
- **Model layer:** LangChain chat model integrations, initially one tested provider.
- **Execution:** built-in filesystem/search/patch, Git, bounded shell and tests; project-specific diagnostics as integrations.
- **Persistence:** LangGraph checkpointing plus a separate CodeMisterio event journal (SQLite if needed).
- **UI automation (later):** Playwright for browsers; optional isolated desktop adapters.
- **Integration (v0.2):** MCP client with local stdio and remote Streamable HTTP server support, plus explicit project-level instructions and skills.
- **Packaging:** pyproject.toml with uv for development.

A development package and CLI entry point are present, but end-to-end Deep Agents/model integration is not yet verified.

## Development roadmap

**Milestone 0 — Foundations:** project documentation, license selection, packaging, offline CI and contributor instructions.

**v0.1 — Deep Agents coding CLI + live activity:** one tested model, Deep Agents-backed tool execution, streamed file-change evidence (including diff hunk lines), command output, managed process lifecycle, test results, approvals, cancellation and a truthful final report.

**v0.2 — MCP and extensible harness:** more model adapters, local and remote MCP servers, MCP tools/resources/prompts, additional built-in tools, session persistence, context management and project instructions.

**v0.3 — Browser and computer use:** Playwright-based browser tests, screenshots and optional sandboxed desktop interactions.

**v0.4 — Advanced engineering:** richer TUI, subagents, isolated worktrees, parallel workflows and deeper software validation.

**v1.0 — Stable open-source release:** an OSI-approved license, security review, cross-platform verification, packaging, documented compatibility and stable interfaces.

Detailed tasks, acceptance criteria and release gates are in [PLAN.md](PLAN.md).

## Repository documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) — architecture, trust boundaries, tool interfaces and design decisions.
- [PLAN.md](PLAN.md) — phased milestones, tasks and acceptance tests.
- [AGENTS.md](AGENTS.md) — guidance for coding agents and contributors working on this repository.
- [docs/TOOLS.md](docs/TOOLS.md) — Deep Agents-compatible tool catalog and uniform execution contracts.
- [docs/ACTIVITY_STREAM.md](docs/ACTIVITY_STREAM.md) — required step-by-step CLI events, actual diff/process evidence and rendering modes.
- [docs/BOOTSTRAP.md](docs/BOOTSTRAP.md) — initial Python setup, preview commands, limitations and next steps.
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

**Success means a reproducible, validated engineering task with a live, inspectable execution timeline — not merely plausible generated code.**
