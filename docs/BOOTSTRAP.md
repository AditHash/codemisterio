# Bootstrap and first coding CLI slice

> **Status:** Development preview on the implementation branch, not a stable release. Offline tests passed in a Python 3.13 environment; **Deep Agents/model integration could not be installed or smoke-tested in this environment** because PyPI network access was unavailable. Use this guide to validate with your own API key.

## Install in a fresh checkout

Install Python 3.12+ and [uv](https://docs.astral.sh/uv/), then run from the repository root:

```bash
uv sync --extra openai --extra dev
uv run codemisterio version
uv run pytest -q
```

Alternatively, with pip:

```bash
python -m venv .venv
# activate the virtual environment for your OS
python -m pip install -e '.[openai,dev]'
python -m pytest -q
```

Use a model supported by your installed LangChain provider integration. For an OpenAI API model, configure `OPENAI_API_KEY` in your environment **without committing it**.

## Try a read-only repository task

```bash
uv run codemisterio run "Inspect this project and suggest two improvements" --workspace . --model openai:gpt-5.5
```

The default tool allowlist is `ls`, `read_file`, `glob`, `grep`. The only actual files the agent sees are under virtual `/workspace/`, mapped to your selected directory; Deep Agents' internal virtual files remain in a separate in-memory backend. The agent has **no arbitrary shell execution** in this first slice.

## Enable edits with per-call approval

```bash
uv run codemisterio run "Refactor this Python function" --workspace . --allow-edits --model openai:gpt-5.5
```

This exposes `write_file` and `edit_file`, requiring explicit human approval before each call. In non-interactive modes, edits are disabled. Read-only mode is the default. Note that these controls are **not a sandbox**: do not run CodeMisterio against secrets or untrusted repositories until the security implementation has been independently validated.

## Structured activity events

```bash
uv run codemisterio run "Summarize src/" --jsonl > run.jsonl
```

The CLI consumes LangGraph v3 protocol events. It prints tool-start/tool-finished/tool-error and run lifecycle events, and it observes changed **UTF-8 text files** through bounded before/after workspace scans. Created, deleted and edited files are reported with `observed` status, not falsely attributed to a particular tool. For edits, changed hunk positions come from comparing actual file text.

This first implementation does **not** provide a full diff viewer, live shell output, managed process restarts, test execution, MCP connections or browser/desktop control. Those remain in [PLAN.md](../PLAN.md) and [ACTIVITY_STREAM.md](ACTIVITY_STREAM.md). Workspace snapshots exclude common secret files, binary files, large files, generated folders and anything past the scan budget. They can miss changes, so they are **not** a complete security or audit trail.

## Current verification

The local offline checks covered event conversion, snapshot diffs, secret-file exclusion, CLI arguments, JSONL output and rejection of non-interactive interrupts. Real provider/model integration and host-level permission enforcement still require testing with installed dependencies and a disposable project.

## Next implementation slice

1. Pin known-compatible Deep Agents/LangChain/LangGraph versions after a real-provider smoke test.
2. Add a sandboxed and approved shell/test runner; stream stdout, stderr, exit status and process events.
3. Instrument backend mutations directly so events have reliable tool correlation and atomic before/after evidence.
4. Add checkpoint persistence, session resume and a rich interactive CLI.
5. Implement MCP clients over stdio/Streamable HTTP using the same permission/event pipeline.
