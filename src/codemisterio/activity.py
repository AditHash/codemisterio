"""Normalize LangGraph v3 protocol events into verifiable terminal activity.

Tool lifecycle events prove that calls ran; only workspace snapshots prove file
mutations. Snapshot attribution is deliberately conservative ("observed").
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from codemisterio.workspace import compare_snapshots, snapshot_workspace


@dataclass(frozen=True)
class ActivityEvent:
    kind: str
    summary: str
    status: str = "info"
    source: str = "codemisterio"
    seq: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _payload(raw: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    params = raw.get("params") or {}
    data = params.get("data") or {}
    return str(raw.get("method") or ""), data if isinstance(data, dict) else {}


def _tool_name(payload: dict[str, Any]) -> str:
    # Protocol details differ by LangGraph version; never invent a specific name.
    return str(payload.get("tool_name") or payload.get("name") or "tool")


class ActivityBridge:
    """Consume ordered v3 raw protocol events; capture observed file effects."""

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace.resolve(strict=True)
        self.snapshot = snapshot_workspace(self.workspace)
        self._message_fragments: list[str] = []

    def consume(self, raw: dict[str, Any]) -> list[ActivityEvent]:
        method, payload = _payload(raw)
        seq = raw.get("seq") if isinstance(raw.get("seq"), int) else None
        events: list[ActivityEvent] = []
        if method == "tools":
            name = _tool_name(payload)
            event_type = payload.get("event")
            if event_type == "tool-started":
                events.append(ActivityEvent("tool.started", f"Started {name}", "running", name, seq))
            elif event_type in {"tool-finished", "tool-error"}:
                status = "completed" if event_type == "tool-finished" else "failed"
                events.append(ActivityEvent("tool." + status, f"{name}: {status}", status,
                                            name, seq))
                events.extend(self.poll_file_changes(seq=seq))
            elif event_type == "tool-output-delta":
                # Tool streaming output may contain secrets. Do not dump arbitrary chunks.
                pass
        elif method == "messages":
            blocks = raw.get("params", {}).get("data", [])
            if isinstance(blocks, list):
                for block in blocks:
                    if not isinstance(block, dict):
                        continue
                    if block.get("event") == "content-block-delta":
                        delta = block.get("delta") or {}
                        if delta.get("type") == "text-delta":
                            self._message_fragments.append(str(delta.get("text") or ""))
                    elif block.get("event") == "message-finish":
                        text = "".join(self._message_fragments).strip()
                        self._message_fragments.clear()
                        if text:
                            # This is assistant speech, not evidence of tool execution.
                            events.append(ActivityEvent("assistant.message", text, seq=seq,
                                                        source="model"))
        elif method == "lifecycle":
            # Root only; nested scopes may generate duplicates.
            namespace = (raw.get("params") or {}).get("namespace") or []
            if not namespace and payload.get("event") in {"started", "completed", "failed", "interrupted"}:
                status = str(payload["event"])
                events.append(ActivityEvent("run." + status, "Agent run " + status,
                                            status, "langgraph", seq))
        return events

    def poll_file_changes(self, *, seq: int | None = None) -> list[ActivityEvent]:
        new = snapshot_workspace(self.workspace)
        changes = compare_snapshots(self.snapshot, new)
        self.snapshot = new
        return [ActivityEvent("file." + item.kind, "Observed: " + item.summary(),
                              "observed", "workspace-snapshot", seq) for item in changes]
