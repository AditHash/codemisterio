from pathlib import Path

from codemisterio.activity import ActivityBridge


def raw(method: str, data, seq: int = 1):
    return {"seq": seq, "method": method, "params": {"namespace": [], "data": data}}


def test_streamed_tool_and_observed_effects(tmp_path: Path) -> None:
    bridge = ActivityBridge(tmp_path)
    events = bridge.consume(raw("tools", {"event": "tool-started", "tool_name": "write_file"}))
    assert [e.kind for e in events] == ["tool.started"]
    (tmp_path / "new.txt").write_text("hello\n")
    events = bridge.consume(raw("tools", {"event": "tool-finished", "tool_name": "write_file"}, 2))
    assert [e.kind for e in events] == ["tool.completed", "file.created"]
    assert "Observed: Created new.txt" in events[1].summary


def test_failure_never_fabricates_a_successful_tool(tmp_path: Path) -> None:
    bridge = ActivityBridge(tmp_path)
    events = bridge.consume(raw("tools", {"event": "tool-error", "tool_name": "edit_file"}))
    assert events[0].kind == "tool.failed"
    assert not any(e.kind.startswith("file.") for e in events)


def test_only_plain_model_text_is_rendered(tmp_path: Path) -> None:
    bridge = ActivityBridge(tmp_path)
    assert not bridge.consume(raw("messages", [{"event": "content-block-delta", "delta": {"type": "reasoning-delta", "reasoning": "PRIVATE"}}]))
    assert not bridge.consume(raw("messages", [{"event": "content-block-delta", "delta": {"type": "text-delta", "text": "Hello"}}]))
    events = bridge.consume(raw("messages", [{"event": "message-finish"}]))
    assert len(events) == 1 and events[0].summary == "Hello"
