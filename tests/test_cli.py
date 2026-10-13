import json
from pathlib import Path

from typer.testing import CliRunner

from codemisterio.cli import ActivityPrinter, _approval_decisions, app
from codemisterio.activity import ActivityEvent

runner = CliRunner()


def test_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "codemisterio 0.1.0a1" in result.output


def test_invalid_workspace(tmp_path: Path) -> None:
    result = runner.invoke(app, ["run", "inspect", "--workspace", str(tmp_path / "none")])
    assert result.exit_code == 2


def test_activity_printer_jsonl(capsys) -> None:
    ActivityPrinter(jsonl=True).emit(ActivityEvent("tool.started", "Started ls", "running"))
    parsed = json.loads(capsys.readouterr().out)
    assert parsed["kind"] == "tool.started"


def test_noninteractive_approval_rejects() -> None:
    interrupt = {"value": {"action_requests": [{"name": "edit_file", "args": {"file_path": "/workspace/a.py"}}]}}
    decisions = _approval_decisions([interrupt], interactive=False, jsonl=True)
    assert decisions[0]["type"] == "reject"


def test_full_session_stream_and_rejects_interrupted_edits(tmp_path: Path, monkeypatch, capsys) -> None:
    import sys
    import types
    from codemisterio.cli import run_session

    class Command:
        def __init__(self, *, resume):
            self.resume = resume

    fake_langgraph = types.ModuleType("langgraph")
    fake_types = types.ModuleType("langgraph.types")
    fake_types.Command = Command
    monkeypatch.setitem(sys.modules, "langgraph", fake_langgraph)
    monkeypatch.setitem(sys.modules, "langgraph.types", fake_types)

    class FakeStream:
        def __init__(self, events, *, interrupted=False, interrupts=()):
            self.events = events
            self.interrupted = interrupted
            self.interrupts = interrupts

        def __iter__(self):
            return iter(self.events)

    class FakeAgent:
        def __init__(self):
            self.calls = []

        def stream_events(self, data, *, config, version):
            self.calls.append(data)
            assert version == "v3" and config["configurable"]["thread_id"]
            if len(self.calls) == 1:
                return FakeStream([
                    {"method": "tools", "seq": 1,
                     "params": {"namespace": [], "data": {"event": "tool-started", "tool_name": "edit_file"}}},
                ], interrupted=True, interrupts=[{"value": {"action_requests": [
                    {"name": "edit_file", "args": {"file_path": "/workspace/example.py"}}
                ]}}])
            return FakeStream([
                {"method": "lifecycle", "seq": 2,
                 "params": {"namespace": [], "data": {"event": "completed"}}},
            ])

    agent = FakeAgent()
    run_session("Fix bug", workspace=tmp_path, model="irrelevant", allow_edits=True,
                jsonl=True, interactive=False, agent=agent)
    assert len(agent.calls) == 2
    assert agent.calls[1].resume["decisions"][0]["type"] == "reject"
    events = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert "tool.started" in [e["kind"] for e in events]
    assert "permission.requested" in [e["kind"] for e in events]
    assert "run.completed" in [e["kind"] for e in events]
