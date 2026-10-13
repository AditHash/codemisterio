# CodeMisterio Development Plan

> **Status:** Project planning. Checkboxes are not claims of implementation. Do not mark tasks complete until corresponding code, documentation and tests are merged.

## Goal

Build a trustworthy, local-first, open-source-intended **agentic coding CLI** with a replaceable model layer and a CodeMisterio-owned harness. The first test of success is whether it can take a small repository task, inspect and modify relevant files, execute verification, and accurately report what happened.

The core loop and permission model take priority over elaborate TUI, subagents and desktop automation. **A useful built-in toolset ships in v0.1; MCP server integration is a committed v0.2 milestone.** Both share one tool registry and permission pipeline.

## Guiding release rules

- Every milestone must be independently useful and demoable.
- Maintain a working CLI before adding optional abstractions.
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
- [ ] Document security reporting and credential-handling expectations.

**Gate:** a fresh contributor can install the package in development mode, run offline checks and understand the roadmap. Documentation alone does not satisfy the gate.

## Milestone 1 — v0.1: A real coding CLI

**Scope:** one reliable agent, one provider, one workspace, sequential execution.

### CLI and agent runtime

- [ ] Implement `codemisterio` executable with help, version and a prompt command.
- [ ] Implement an interactive text session (rich TUI not required).
- [ ] Build the core model -> tool call -> result -> model loop with a maximum step count.
- [ ] Stream assistant/tool status and support Ctrl-C cancellation.
- [ ] Add tool call and tool result schemas, typed errors, timeouts and output truncation.
- [ ] Add one supported model provider with real API tool calling.
- [ ] Separate provider SDK types from core state.
- [ ] Handle provider errors, rate limits and malformed tool calls without losing the session.

### Tools and safe editing

- [ ] Resolve a repository root and operate within an explicit workspace.
- [ ] Implement built-ins: `files.list`, `files.read`, `files.stat`, `search.glob`, `search.grep`, `patch.apply`, `files.write`.
- [ ] Implement bounded `shell.run` and `tests.run` with stdout/stderr, timeout, cancellation and exit status.
- [ ] Implement read-only `git.status`, `git.diff` and `git.log`; preserve unrelated user edits.
- [ ] Implement the unified tool registry **now**: canonical tool names, JSON Schema validation, permission classifications and structured results.
- [ ] Publish basic tool help/listing; external MCP tools use the same registry in v0.2.
- [ ] Add an approval gate for writes, risky commands and network side effects.
- [ ] Block unauthorized access outside workspace, including symlink/path traversal.
- [ ] Present an accurate final summary: files changed, commands run, tests passed/failed/not run.

### Tests and demo

- [ ] Add unit tests with a deterministic fake model adapter.
- [ ] Test tools on temporary Git repositories, including malformed requests.
- [ ] Test cancellation, tool timeouts, rejected permissions and dirty-worktree handling.
- [ ] Create a demonstration fixture with a small Python bug and pytest regression.
- [ ] Document supported commands, actual configuration and known limitations.

**v0.1 acceptance test:**

1. Launch CodeMisterio from a terminal in a small test repository.
2. Ask it to identify and fix a failing Python test.
3. Observe file reads, a proposed change and a scoped approval prompt.
4. Verify CodeMisterio applies a correct patch, reruns pytest and surfaces the exit code.
5. Confirm the report contains the diff and names any tests it could not run.
6. Ensure denial/cancellation leaves the repository in a predictable state.

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

1. **Bootstrap Python package and offline CI** — executable, type checking, formatting and tests.
2. **Define model/tool event contracts** — typed schemas and fake adapter.
3. **Implement agent loop** — streaming, budgets, cancellation and tool result feedback.
4. **Implement workspace tools** — read/search/patch with containment tests.
5. **Implement shell runner and permission decisions** — timeouts, stdout/stderr, reject/approve flows.
6. **Implement first provider adapter** — tool calling plus a real smoke-test script.
7. **Create bug-fixing benchmark fixture** — Python + pytest, clean and dirty worktree cases.
8. **Document reproducible v0.1 demo** — accurate flags, limitations and results.
9. **Design v0.2 MCP compatibility suite** — fake stdio + HTTP servers, tools/resources/prompts, malformed responses and approval denials.
10. **Plan v0.2 tool expansion** — diagnostics, project inspection and controlled Git mutation.

## Definition of done for any feature

- Implementation and tests exist, with at least one failure-path test.
- The CLI behavior and permissions are documented.
- Existing tests pass, or failures are called out explicitly.
- User-visible outputs do not claim unperformed actions.
- Changes respect the workspace boundary and preserve unrelated edits.
- New dependencies have a clear reason and compatible licensing.

See [ARCHITECTURE.md](ARCHITECTURE.md) for system boundaries, [docs/TOOLS.md](docs/TOOLS.md) for the built-in tool catalog, [docs/MCP.md](docs/MCP.md) for the MCP client contract, and [AGENTS.md](AGENTS.md) for contributor-agent guidance.
