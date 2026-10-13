# CodeMisterio Development Plan

> **Status:** Project planning. Checkboxes are not claims of implementation. Do not mark tasks complete until corresponding code, documentation and tests are merged.

## Goal

Build a trustworthy, local-first, open-source-intended **agentic coding CLI powered by LangChain Deep Agents**. CodeMisterio owns the user experience, live evidence-based activity journal, tool/backend policies and extra coding tools; **Deep Agents owns the agent loop, planning, context, subagents and graph state**. The first test of success is whether it can take a small repository task, inspect and modify relevant files, execute verification, and accurately report what happened.

**Real-time, verifiable step-by-step CLI output is a v0.1 requirement**, not a future UI enhancement. A useful built-in coding toolset ships in v0.1; MCP server integration remains a committed v0.2 milestone. All tools pass one permission and activity-reporting pipeline.

## Implementation checkpoint — initial CLI branch

The first v0.1 foundation is available on `feat/initial-deepagents-cli`, but **v0.1 is not complete**.

- [x] Python package metadata, CLI entry point, `version` and `run` commands.
- [x] Deep Agents `create_deep_agent` construction with composite workspace backend and read/search tool surface (not yet verified against installed dependencies).
- [x] Optional write/edit tools with human-in-the-loop approval flow (offline tests cover rejection; real model test pending).
- [x] LangGraph v3 event normalizer for tool lifecycle and assistant text output.
- [x] Bounded observed UTF-8 workspace snapshots for created/modified/deleted files and actual changed-line positions.
- [x] JSONL output and Rich event renderer.
- [x] Offline unit tests (12 passed locally on Python 3.13).
- [x] Python 3.12/3.13 GitHub Actions workflow committed (workflow result pending).
- [ ] Install/test Deep Agents + LangChain dependencies and complete a real provider smoke test.
- [ ] Add instrumented filesystem backend writes with true tool attribution and stronger secret protection.
- [ ] Add sandboxed/approved shell, test execution and verified managed process lifecycle.
- [ ] Add persistent sessions, cancellation handling and robust stream retry behavior.
- [ ] Build MCP client/server management in v0.2.

See [docs/BOOTSTRAP.md](docs/BOOTSTRAP.md) for preview limitations.

## Guiding release rules

- Every milestone must be independently useful and demoable.
- Keep Deep Agents as the single primary agent runtime; extend it via documented middleware/backends/tools.
- Every meaningful tool action must emit truthful activity events in the CLI; never replace operational evidence with generated narrative.
- New provider integrations must pass the same tool-calling contract tests.
- Avoid claims of “autonomous” success without actual verification evidence.
- Paid API tests must be optional; default CI runs offline with fakes.
- Do not release under an “open source” label until a suitable LICENSE is added.

## Milestone 0 — Documentation and repository foundations

**Outcome:** consistent vision, contribution rules and minimal project metadata.

- [x] Establish product direction: agentic coding CLI, not only code scanner/reviewer.
- [x] Draft architecture, roadmap and `AGENTS.md`.
- [ ] Select an OSI-approved license and add `LICENSE`.
- [ ] Add `CONTRIBUTING.md` and a code of conduct when external contributions begin.
- [ ] Choose supported Python version and initial Windows/macOS/Linux targets.
- [ ] Add `pyproject.toml`, `src/`, `tests/` and packaging metadata once implementation begins.
- [ ] Add formatting, linting, type checking and test commands.
- [ ] Add offline CI for tests and basic package build.
- [ ] Pin/test compatible LangChain, Deep Agents and LangGraph versions with a minimal streaming smoke test.
- [ ] Document security reporting and credential-handling expectations.

**Gate:** a fresh contributor can install the package in development mode, run offline checks and understand the roadmap. Documentation alone does not satisfy the gate.

## Milestone 1 — v0.1: A real coding CLI

**Scope:** a working Deep Agents coding CLI with one tested model, one workspace, sequential tool execution and a live, evidence-backed activity timeline.

### CLI and Deep Agents runtime

- [ ] Implement `codemisterio` executable with help, version and interactive prompt mode.
- [ ] Integrate `create_deep_agent` with one real LangChain chat model, explicit workspace/backend and coding-specific system prompt.
- [ ] Use tested Deep Agents middleware for filesystem, context management, approvals and optional todo planning. Avoid writing a second tool-call loop.
- [ ] Consume LangGraph streaming events for model text, tool status and graph/todo updates; support cancellation.
- [ ] Add tool/backend instrumentation to emit requested, started, completed, failed and denied states.
- [ ] Build a **Rich real-time activity feed** showing every meaningful read/search/command/edit/test event with actual tool status.
- [ ] Implement **before/after verified file-change events**: created, edited with real hunk line numbers, deleted and renamed when provable.
- [ ] Implement an approval UI that remains responsive while streaming and clearly shows exact target paths/commands.
- [ ] Support structured JSONL activity output and plain-text non-TTY fallback.
- [ ] Stream foreground process output, exit code, elapsed time and tool errors without hiding failures.
- [ ] Introduce a minimal **managed development-process lifecycle** (start, stop, restart) with actual PID/process state and separate health-check result.
- [ ] Bound agent execution: time/cost where available, max steps, failure/cancellation handling and useful completion status.

### Tools and safe editing

- [ ] Resolve a repository root and configure a Deep Agents filesystem/shell backend with explicit workspace and trusted execution policy.
- [ ] Implement built-ins: `files.list`, `files.read`, `files.stat`, `search.glob`, `search.grep`, `patch.apply`, `files.write`.
- [ ] Implement bounded `shell.run` and `tests.run` with stdout/stderr, timeout, cancellation and exit status.
- [ ] Implement read-only `git.status`, `git.diff` and `git.log`; preserve unrelated user edits.
- [ ] Implement a **Deep Agents-compatible** unified tool adapter/registry now: canonical names, JSON Schema validation, approval requirements, bounded structured results, and event hooks for Deep Agents built-ins plus CodeMisterio tools.
- [ ] Instrument all enabled file-writing backends and tool side effects; file changes from shell commands also require scoped Git/filesystem diff inspection.
- [ ] Publish basic tool help/listing; MCP tools use the same policy/event architecture in v0.2.
- [ ] Add an approval gate for writes, risky commands and network side effects.
- [ ] Block unauthorized access outside workspace, including symlink/path traversal.
- [ ] Present an accurate final summary: files changed, commands run, tests passed/failed/not run.

### Tests and demo

- [ ] Add offline integration/unit tests using Deep Agents and deterministic fake LangChain models and tool stubs.
- [ ] Test tools on temporary Git repositories, including malformed requests.
- [ ] Test streaming order/deduplication, event accuracy, cancellation, tool timeouts, denied permissions, dirty worktrees and secret redaction.
- [ ] Test real diff line ranges, new/deleted-file classification, and no false positive after failed edit.
- [ ] Test foreground command output plus managed start/stop/restart with health result distinguished from process state.
- [ ] Create a demonstration fixture with a small Python bug and pytest regression.
- [ ] Document supported commands, actual configuration and known limitations.

**v0.1 acceptance test:**

1. Launch CodeMisterio from a terminal in a small test repository.
2. Ask it to identify and fix a failing Python test, watching a **live activity timeline** rather than a spinner.
3. Observe real file reads, an approval prompt and tool start/finish states.
4. Verify actual edit/file creation/deletion events and exact diff hunk lines match the changed worktree.
5. Verify pytest output streams live and the final exit code/test summary matches reality.
6. Start/restart a managed fixture development service; show PID/lifecycle and independently checked readiness.
7. Confirm the final report contains actual git diff and names any tests it could not run.
8. Ensure denial/cancellation leaves the repository in a predictable state and never reports unperformed changes.

The milestone is complete only when this workflow passes repeatably in automated integration tests and a real-provider smoke test.

## Milestone 2 — v0.2: Extensible harness

**Scope:** make the core useful beyond a single model and session.

- [ ] Add a second model adapter to validate provider independence.
- [ ] Provide configurable model and API credential selection.
- [ ] Normalize stream, tool-calling, usage and error events while preserving optional provider features.
- [ ] Add SQLite-backed session history with versioned migrations.
- [ ] Implement context selection, budgets, compaction and recovery of interrupted sessions.
- [ ] Add `AGENTS.md` repository instruction loading with explicit untrusted-content handling.
- [ ] Extend the existing tool registry with useful built-ins: safe file move/delete, controlled Git branch/stage/commit, project inspection, diagnostics (lint/typecheck), and bounded HTTP fetch.
- [ ] Build MCP server management: configure, list, inspect, enable/disable and remove servers.
- [ ] Support local MCP servers over **stdio** and remote servers over **Streamable HTTP** using a maintained Python MCP SDK.
- [ ] Discover/invoke MCP tools through the same validation, permissions, budgets and audit pipeline as built-in tools; namespace IDs by server.
- [ ] Support MCP resources and prompts as lower-trust content with explicit loading and context limits.
- [ ] Handle MCP credentials safely, connection failures, timeouts, protocol-version negotiation and server process cleanup.
- [ ] Add fake MCP server tests plus opt-in real-server compatibility checks; isolate untrusted servers.
- [ ] Keep OAuth UX and additional MCP extension features incremental where the core SDK/transport makes full support complex.
- [ ] Add reusable skills or task templates without silently executing downloaded instructions.
- [ ] Add token/cost tracking when providers expose reliable usage information.

**Gate:** the same coding task works on at least two providers; resume does not duplicate non-idempotent operations; an explicitly approved local MCP server and a remote MCP server can expose tools through the shared registry, while unauthorized actions are rejected. A disconnecting server does not break core coding tasks.

## Milestone 3 — v0.3: Browser and computer use

**Scope:** add evidence-driven validation of running applications.

- [ ] Integrate Playwright as a separately enabled browser tool backend.
- [ ] Support navigation, DOM inspection, clicks, forms, screenshots, console logs and test assertions.
- [ ] Capture frontend and backend errors from a locally running application.
- [ ] Tie browser observations back to source edits and automated verification.
- [ ] Add screenshot-based fallback only for supported provider/environment combinations.
- [ ] Add optional isolated VM/desktop backend for keyboard, mouse and window control.
- [ ] Require explicit approvals for credentials, external writes and consequential UI actions.
- [ ] Prevent arbitrary host-desktop control by default; provide isolation guidance.
- [ ] Record UI evidence with secret redaction and bounded retention.

**Gate:** in an isolated fixture app, CodeMisterio can reproduce a UI defect, identify its cause, apply a patch and demonstrate a passing browser test. No real personal accounts are involved.

## Milestone 4 — v0.4: Advanced engineering agent

**Scope:** deeper workflows after baseline reliability is established.

- [ ] Add a richer terminal UI with diffs, session navigation and approval views.
- [ ] Add specialized workflows for review, test generation, debugging and security analysis.
- [ ] Add subagents with bounded context, tools, cost and cancellation.
- [ ] Support parallel independent reads; serialize conflicting writes.
- [ ] Add isolated worktrees/branches for long-running tasks.
- [ ] Introduce safe checkpoints and recoverable change sets.
- [ ] Evaluate optional remote sandboxes and durable workflow runtimes.
- [ ] Publish reproducible benchmark tasks and failure analysis.

**Gate:** improve task completion on a fixed benchmark without increasing unauthorized operations or hidden regressions.

## Milestone 5 — v1.0: Stable, distributable CLI

**Scope:** harden and publish the capabilities proved in earlier milestones rather than expanding scope indefinitely.

- [ ] Select and publish a compatible OSI-approved license before marketing the software as open source.
- [ ] Run repeatable cross-platform CI on supported Windows, macOS and Linux versions.
- [ ] Stabilize provider and tool interfaces, documented config migrations, and session format.
- [ ] Security review of shell tools, path containment, MCP server trust and credential handling.
- [ ] Publish honest install/upgrade guidance, docs, compatibility matrix, examples and troubleshooting.
- [ ] Add releases/packages with signed or verifiable distribution where practical.
- [ ] Maintain an end-to-end coding benchmark and release-blocking regression tests.
- [ ] Document extension APIs and supported MCP transport versions.

**Gate:** clean install, reliable core editing/testing and supported MCP workflows on advertised platforms; no known critical sandbox/permission escapes; public release documentation matches actual behavior.

## Backlog (not commitments)

- Local model support via Ollama or OpenAI-compatible inference endpoints.
- Optional LangGraph/DeepAgents interoperability where it adds value.
- LSP integration, semantic repository indexing and dependency graphs.
- IDE/editor integration and headless CI automation.
- Community plugin and skill registry with provenance checks.
- Reproducible cross-platform binaries and install scripts.
- Remote execution environments and delegated tasks.

## What not to build in v0.1

- A React dashboard or hosted service.
- Ten “specialized agents” before one agent works.
- Full desktop control against the user's host OS.
- Distributed queues, Kubernetes or enterprise SSO.
- Persistent vector storage without a demonstrated need.
- A provider abstraction so broad that the first working tool call is delayed.

## Suggested first implementation issues

1. **Bootstrap package and offline CI** — Typer/Rich, formatting, linting, tests, pin Deep Agents/LangGraph versions.
2. **Deep Agents smoke test** — `create_deep_agent`, fake model, one real model, streaming and interrupt demonstration.
3. **Activity event schema + renderer** — versioned events, live CLI, JSONL, cancellation and durable journal.
4. **Instrument filesystem backend** — before/after snapshots, diff hunks, creates/deletes, failed operations and redaction.
5. **Shell and managed process instrumentation** — streamed output, exit status, start/stop/restart and readiness probe.
6. **Permissions + workspace** — approval interrupts, path safety and scoped execution policy.
7. **Baseline coding tools** — files, search, patch, Git inspection and test runner integrated into Deep Agents.
8. **v0.1 fixture/demo** — fix a pytest bug with full live evidence and a process restart fixture.
9. **v0.2 MCP compatibility suite** — fake stdio + HTTP servers, tools/resources/prompts, malformed responses and denials.
10. **v0.2 tool expansion** — diagnostics, project inspection, controlled Git mutation.

## Definition of done for any feature

- Implementation and tests exist, with at least one failure-path test.
- The CLI behavior and permissions are documented.
- Every actual mutation/command outcome has a verified activity event; wrong line numbers or fabricated process restarts block release.
- Existing tests pass, or failures are called out explicitly.
- User-visible outputs do not claim unperformed actions.
- Changes respect the workspace boundary and preserve unrelated edits.
- New dependencies have a clear reason and compatible licensing.

See [ARCHITECTURE.md](ARCHITECTURE.md) for Deep Agents integration, [docs/ACTIVITY_STREAM.md](docs/ACTIVITY_STREAM.md) for required CLI events, [docs/TOOLS.md](docs/TOOLS.md) for tools, [docs/MCP.md](docs/MCP.md) for MCP, and [AGENTS.md](AGENTS.md) for contributor-agent guidance.
