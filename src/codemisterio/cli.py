"""CodeMisterio CLI: Deep Agents v3 streaming and interactive edit approvals."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

import typer
from rich.console import Console

from codemisterio import __version__
from codemisterio.activity import ActivityBridge, ActivityEvent

app = typer.Typer(help="CodeMisterio — observable agentic coding CLI", no_args_is_help=True)


class ActivityPrinter:
    def __init__(self, *, jsonl: bool = False) -> None:
        self.jsonl = jsonl
        self.console = Console(stderr=not jsonl, highlight=False)

    def emit(self, event: ActivityEvent) -> None:
        if self.jsonl:
            print(json.dumps(event.as_dict(), ensure_ascii=False), flush=True)
            return
        styles = {
            "running": "cyan", "completed": "green", "failed": "red",
            "observed": "yellow", "interrupted": "yellow",
        }
        style = styles.get(event.status, "dim")
        marker = {"running": "→", "completed": "✓", "failed": "✗",
                  "observed": "~", "interrupted": "!"}.get(event.status, "·")
        self.console.print(f"[{style}]{marker}[/{style}] {event.summary}")


def _approval_decisions(interrupts: Any, *, interactive: bool, jsonl: bool) -> list[dict[str, str]]:
    """Never auto-approve. JSONL and non-interactive runs always reject."""
    decisions: list[dict[str, str]] = []
    console = Console(stderr=True)
    for interrupt in interrupts:
        details = getattr(interrupt, "value", None)
        if details is None and isinstance(interrupt, dict):
            details = interrupt.get("value", interrupt)
        actions = (details or {}).get("action_requests", []) if isinstance(details, dict) else []
        for action in actions:
            name = action.get("name", "unknown")
            args = action.get("args", {})
            target = args.get("file_path", args.get("path", "<unspecified>")) if isinstance(args, dict) else "<unspecified>"
            console.print(f"[yellow]Approval required:[/] {name} → {target}")
            approve = False
            if interactive and not jsonl:
                answer = typer.prompt("Approve once? [y/N]", default="N")
                approve = answer.strip().lower() in {"y", "yes"}
            decisions.append({"type": "approve"} if approve else {
                "type": "reject", "message": "User declined this operation; do not retry it."
            })
    return decisions


def run_session(prompt: str, *, workspace: Path, model: str, allow_edits: bool,
                jsonl: bool, interactive: bool = True, agent: Any | None = None) -> None:
    """Stream agent events and handle approval interrupts. Accepts fake agents for offline tests."""
    from langgraph.types import Command

    if agent is None:
        from codemisterio.runtime import build_agent
        agent = build_agent(workspace, model, allow_edits=allow_edits)
    bridge = ActivityBridge(workspace)
    printer = ActivityPrinter(jsonl=jsonl)
    config = {"configurable": {"thread_id": uuid4().hex}}
    data: Any = {"messages": [{"role": "user", "content": prompt}]}
    while True:
        stream = agent.stream_events(data, config=config, version="v3")
        for raw in stream:
            for event in bridge.consume(raw):
                printer.emit(event)
        for event in bridge.poll_file_changes():
            printer.emit(event)
        if not stream.interrupted:
            break
        printer.emit(ActivityEvent("permission.requested", "User approval required", "interrupted"))
        decisions = _approval_decisions(stream.interrupts, interactive=interactive, jsonl=jsonl)
        if not decisions:
            raise RuntimeError("Agent requested an interrupt with no reviewable actions")
        data = Command(resume={"decisions": decisions})


@app.command()
def version() -> None:
    """Print the installed version."""
    typer.echo(f"codemisterio {__version__}")


@app.command()
def run(
    prompt: str = typer.Argument(..., help="Software engineering task to perform"),
    workspace: Path = typer.Option(Path("."), "--workspace", "-w", help="Project directory"),
    model: str = typer.Option("openai:gpt-5.5", "--model", "-m", help="LangChain model ID"),
    allow_edits: bool = typer.Option(False, "--allow-edits", help="Enable edits with approval before each tool call"),
    jsonl: bool = typer.Option(False, "--jsonl", help="Machine-readable JSONL activity"),
) -> None:
    """Run a Deep Agent in a workspace (read-only by default, no shell access)."""
    if not workspace.exists() or not workspace.is_dir():
        typer.echo(f"Invalid workspace: {workspace}", err=True)
        raise typer.Exit(code=2)
    if not sys.stdin.isatty() and allow_edits:
        typer.echo("Non-interactive edits are disabled. Remove --allow-edits.", err=True)
        raise typer.Exit(code=2)
    if allow_edits and jsonl:
        typer.echo("--jsonl is read-only in this release; do not combine with --allow-edits.", err=True)
        raise typer.Exit(code=2)
    try:
        run_session(prompt, workspace=workspace.resolve(), model=model,
                    allow_edits=allow_edits, jsonl=jsonl)
    except (KeyboardInterrupt, EOFError):
        typer.echo("Cancelled by user.", err=True)
        raise typer.Exit(code=130) from None
    except Exception as exc:
        typer.echo(f"Agent failed: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=1) from None
