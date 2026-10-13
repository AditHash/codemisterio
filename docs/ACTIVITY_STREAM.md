# CodeMisterio Activity Stream and CLI Observability

> **Status:** Design specification, not an implemented CLI. **Core requirement from v0.1:** show ordered, real-time, evidence-backed activity. CodeMisterio must never be a black box.

## 1. Product requirement

Users must be able to answer: **What is the agent doing now? Which exact files changed? Which commands ran? Which processes started, stopped, or restarted? What passed, failed, was denied, or remains unverified?**

CodeMisterio uses **LangChain Deep Agents** for agent runtime and **LangGraph** for streaming/checkpointed execution. CodeMisterio owns the activity event schema, tool/backend instrumentation, evidence collectors, event persistence, and CLI renderer. Model-generated narration is not evidence of an action.

## 2. Example terminal transcript (concept only)

~~~text
$ codemisterio
  Workspace: ~/src/store-api | Model: provider/model

> Fix JWT expiration and test the API

◌ Task started (run: 7f3...)
✓ Read src/auth/tokens.py (lines 1–109)
✓ Read tests/test_tokens.py (lines 1–82)
→ Edit proposed: src/auth/tokens.py
  - 42 | if token:
  + 42 | if token and not is_expired(token):
? Approve this write? [once / session / deny]
✓ Edited src/auth/tokens.py (+1 −1; hunk 42–42)
✓ Added tests/test_expired_token.py (+28 lines)
→ Running pytest -q
✓ Command exited 0 (2.4s)
✓ Tests: 27 passed, 0 failed
→ Restart requested: dev-api (managed process #2)
✓ Stopped previous dev-api process (pid 1124)
✓ Started dev-api (pid 1198)
✓ Health check: GET http://127.0.0.1:8000/health -> 200
✓ Final check: git diff --stat
  Changed: 1 | Added: 1 | Deleted: 0 | Tests: passed
✓ Task complete

> Show the diff for src/auth/tokens.py
~~~

**All paths, line numbers, PIDs, test counts and health status above are imaginary examples.** In production, the renderer must use real evidence, not a generated story.

For failures, be equally explicit:

~~~text
✗ Attempted patch src/auth/tokens.py: context mismatch (no file change)
✗ pytest exited 1; 2 failures (tests/test_tokens.py)
! Server restart NOT verified: process was launched but health probe timed out
⊘ delete .env denied by workspace policy
~~~

## 3. Event architecture

~~~text
Deep Agents graph (LangGraph streaming)
      |
      +--> agent/model/plan updates
      |
      +--> tool calls + lifecycle interception
      |       |
      |       +--> filesystem backend / patch diff collector
      |       +--> shell command runner / stdout+stderr+exit code
      |       +--> managed process registry / health probes
      |       +--> git snapshot/diff collector
      |       +--> MCP tool adapter / approved server events
      |       +--> browser/desktop adapter (later)
      |
      v
CodeMisterio ActivityEvent normalizer
      |
      +--> permission + secret redaction
      +--> event order / correlation IDs / deduplication
      +--> session event journal
      |
      v
CLI renderer (Rich; advanced TUI later)
      |
      +--> compact live feed (default)
      +--> expandable diffs and tool details
      +--> verbose JSONL / machine-readable output
~~~

### LangGraph stream inputs

LangGraph supports streamed graph updates, model output and custom runtime updates. **Preferred implementation:** the current LangGraph typed event streaming API (`astream_events(..., version="v3")`, with a tested compatible LangGraph release). It exposes `tools` events including `tool-started`, `tool-output-delta`, `tool-finished` and `tool-error`, alongside `lifecycle`, `messages`, `custom`, and subgraph state. Protocol event sequence numbers and tool-call IDs allow ordering and correlation. For older version compatibility, use `astream(..., stream_mode=["updates","messages","custom"], version="v2")` and instrument tool starts/completions directly.

Conceptual stream bridge (verify with pinned dependencies before implementation):

~~~python
from deepagents import create_deep_agent

agent = create_deep_agent(model=model, backend=instrumented_backend)

stream = await agent.astream_events(
    {"messages": [{"role": "user", "content": task}]},
    version="v3",
)
async for event in stream:
    if event["method"] == "tools":
        await activity_bridge.on_tool_event(event)  # statuses, stdout deltas
    elif event["method"] in {"lifecycle", "custom"}:
        await activity_bridge.on_runtime_event(event)

# Real file hunks and process/restart evidence come from
# instrumented_backend/process_manager, not the LLM stream.
~~~

The above is an **integration sketch**, not yet executable CodeMisterio source. Inspect supported subgraph namespaces and actual event structures in tests.

- `messages`: stream model output or user-facing progress, **not hidden chain-of-thought**.
- `updates` / `tasks`: graph-node transitions, todo updates, subagent activity and execution status where available.
- `custom`: structured application-generated milestones and tool-specific events.
- **Direct tool instrumentation:** trusted source for actual filesystem/process effects, not merely graph state.
- **Interrupts/approvals:** show approval requested/granted/denied and resume status.

Do not dump raw LangGraph state, tokens, or proprietary/private model reasoning to the terminal. Rendering should be filtered and safely summarized.

## 4. Proposed event contract

Version the schema and avoid tying it to one model/provider/runtime representation. Conceptual fields:

~~~json
{
  "schema_version": 1,
  "event_id": "evt_000042",
  "sequence": 42,
  "timestamp": "2026-01-01T00:00:00Z",
  "run_id": "run_...",
  "session_id": "session_...",
  "agent_id": "primary",
  "parent_span_id": null,
  "tool_call_id": "call_...",
  "source": "builtin:patch.apply",
  "type": "file.modified",
  "status": "succeeded",
  "summary": "Edited src/auth/tokens.py",
  "evidence": {
    "path": "src/auth/tokens.py",
    "change_kind": "modified",
    "before_hash": "...",
    "after_hash": "...",
    "diff_artifact_id": "artifact_...",
    "hunks": [{"old_start": 42, "old_count": 1, "new_start": 42, "new_count": 1}],
    "added_lines": 1,
    "removed_lines": 1
  },
  "redacted": false
}
~~~

Example event families (extensible):

| Family | Event types / evidence |
| --- | --- |
| Run | `run.started`, `run.completed`, `run.failed`, `run.cancelled` |
| Agent | `agent.started`, `agent.progress`, `agent.subtask.started/completed` |
| Tool | `tool.requested`, `tool.started`, `tool.succeeded/failed` |
| Policy | `permission.requested`, `permission.granted/denied` |
| File | `file.created`, `file.modified`, `file.deleted`, `file.renamed`, `file.operation_failed` |
| Shell | `command.started`, `command.output`, `command.exited`, `command.timed_out` |
| Processes | `process.started`, `process.stopped`, `process.restart_requested`, `process.restarted`, `process.health_checked` |
| Tests | `tests.started`, `tests.summary`, `tests.failed`, `tests.skipped` |
| Git | `git.status`, `git.diff_ready` |
| MCP | `mcp.server.connected/disconnected`, `mcp.tool.started/completed/failed` |
| UI later | `browser.navigated`, `browser.screenshot`, `desktop.action` |

Every event must distinguish `requested`, `started`, `succeeded`, `failed`, `denied`, and `unverified` where relevant. Do not use “success” for a request that was merely issued.

## 5. File-change evidence

Line-level reporting **cannot** be obtained reliably from text generated by the LLM or from generic tool-stream messages alone.

For tool-originated edits:

1. Resolve the workspace-relative real path and authorization.
2. Record pre-image content/hash or a bounded snapshot before mutation.
3. Perform the write/edit/patch through an instrumented Deep Agents filesystem backend or approved wrapped tool.
4. Read the post-image and calculate a unified diff; emit added/removed counts and actual hunk line ranges.
5. Classify creations, deletions, renames and modified files from observed before/after state. Rename detection may require explicit operation metadata or Git heuristics; do not assert a rename when ambiguous.
6. Emit an event only after confirming the mutation; on error emit an explicit failed event without inventing a successful change.

When commands or external tools (e.g., `python scripts/migrate.py`, formatters, npm generators, MCP servers) can modify files **outside direct filesystem wrappers**, track the effect using a scoped before/after workspace snapshot and Git porcelain/diff, with performance/size caps. Detect only observed changes; if external side effects cannot be inspected, mark them **unverified**. Do not attribute every change to the last command if other processes may have written concurrently.

Protect binary files, large files, permission bits, symlinks, CRLF/encoding and ignored/untracked files. Avoid recording secret file contents in diffs/logs. Line numbers refer to actual diff hunks, not guessed source locations.

## 6. Shell and process lifecycle evidence

### Foreground command

Record exact command/argv (safely redacted), cwd, start time, timeout, streamed stdout/stderr, exit code, duration and cancellation/termination status. A command returning exit 0 does not prove that a service was restarted.

### Managed/background process

Build a **process manager** for long-running development commands; a plain one-shot shell tool is insufficient. Track process ID/handle, command, cwd, environment policy, ports when known, output streams and lifecycle events. Keep process groups/child processes manageable across cancellation.

Only emit `process.restarted` when the old managed process has actually terminated and the new process has started. Report separately whether readiness/health was confirmed. An unmanaged process restarted by third-party scripts should be labeled `restart_unverified` unless operating-system/process-specific proof exists.

Sample verification:

~~~text
→ Restart requested: api
✓ Old managed process terminated
✓ New process running: pid 1198
! Readiness check pending...
✓ HTTP /health responded 200
~~~

## 7. Presentation policy

- **Default:** compact chronological events, one line per significant action.
- **Verbose:** full tool arguments where safe, bounded command output, diffs, subagent namespaces, timings and token/cost estimates.
- **Quiet:** important permissions, failures and final summary only.
- **JSONL:** stable machine-readable events (do not mix free-form escape sequences into stdout).
- Group repetitive read/search operations without hiding available details.
- Show file changes after observed success with `+`, `-`, paths and hunk ranges; allow expansion for complete diff.
- Update running command output without freezing input; controls for cancel/approve and inspect.
- TTY uses Rich/optional Textual; non-TTY falls back to plain text and JSONL.
- Event journaling preserves order per run with correlation IDs; across parallel subagents use timestamps and parent IDs rather than pretending a total causal order.
- Never show secret-bearing environment variables, token-bearing HTTP headers or private chain-of-thought content.

## 8. Implementation placement

Proposed modules (adjust names after initial code exists):

~~~text
src/codemisterio/
  runtime/             # Deep Agents construction; LangGraph checkpoint/stream adapter
  activity/
    events.py          # versioned ActivityEvent types
    bridge.py          # graph/tool streams -> activity events
    journal.py         # bounded persisted event feed
    evidence.py        # snapshot, diff and test evidence
  tools/
    instrumented.py    # wrapper/adapter for built-in tool effects
    processes.py       # managed process and readiness tracking
  cli/
    renderer.py        # live Rich timeline
    output.py          # --verbose, --quiet, --format jsonl
~~~

Observability is a **cross-cutting requirement**, not an agent prompt. Add instrumentation at the backend/executor boundary instead of forking the Deep Agents runtime without necessity.

## 9. v0.1 acceptance tests (release blockers)

- [ ] Emit tool requested/started/completed/failed with accurate IDs.
- [ ] File create/edit/delete classification uses real before/after evidence; line ranges match the resulting unified diff.
- [ ] Denied, failed and cancelled mutations never appear as completed edits.
- [ ] Shell streaming shows output before command exits, then actual exit status and duration.
- [ ] Managed process start/stop/restart events are accurate; health/readiness is a separate verified state.
- [ ] Streaming works with Deep Agents' supported version; multi-mode and subagent events do not double-print.
- [ ] CLI remains responsive during a running command and during approval interrupts.
- [ ] Events redact secrets and never display hidden reasoning or entire private environment.
- [ ] `--format jsonl` output is parseable; versioned schema can be replayed.
- [ ] Final summary is derived from events plus independently checked Git status/test results, not LLM claims.

**v0.1 scope:** managed process start/stop/restart tracking and honest health reporting are required for the core CLI; support for arbitrary unmanaged processes can arrive later. Always label untracked background process changes as unverified.

## 10. Reference projects

- [LangGraph typed event streaming](https://docs.langchain.com/oss/python/langgraph/event-streaming) — recommended v3 API, including tools/lifecycle events.


- [Deep Agents](https://github.com/langchain-ai/deepagents) — create_deep_agent, backends, tool middleware, subagents.
- [LangGraph streaming](https://docs.langchain.com/oss/python/langgraph/streaming) — updates/messages/custom and typed event streaming.
- [Open SWE](https://github.com/langchain-ai/open-swe) — Deep Agents-backed engineering product, workflows and integrations.
- [LangGraph CUA](https://github.com/langchain-ai/langgraph-cua-py) — separate optional VM/browser computer-use backend.

Related docs: [../ARCHITECTURE.md](../ARCHITECTURE.md), [../PLAN.md](../PLAN.md), [TOOLS.md](TOOLS.md), [MCP.md](MCP.md).
