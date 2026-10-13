"""Construct a Deep Agents runtime with workspace-scoped filesystem tools.

The first slice deliberately has NO arbitrary shell/execute tool. File edits require
interactive LangGraph approval. This is not an OS-level sandbox.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


SYSTEM_PROMPT = """You are CodeMisterio, a careful software-engineering assistant.
The project is mounted in the virtual filesystem at /workspace/.
Use ls, read_file, glob and grep to inspect the repository before proposing edits.
Never claim a file was edited, a command ran, or tests passed unless tool evidence confirms it.
You currently have NO shell/test runner. Say explicitly when you cannot run tests.
Do not attempt to read secrets or files outside /workspace/.
Keep changes targeted and explain how the user can validate them.
"""


def build_agent(workspace: Path, model: str, *, allow_edits: bool = False) -> Any:
    """Build a runnable Deep Agent; heavy imports are delayed for fast CLI startup."""
    from deepagents import FilesystemPermission, create_deep_agent
    from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend
    from deepagents.middleware import FilesystemMiddleware
    from langgraph.checkpoint.memory import MemorySaver

    workspace = workspace.resolve(strict=True)
    if not workspace.is_dir():
        raise ValueError(f"Workspace must be a directory: {workspace}")

    backend = CompositeBackend(
        default=StateBackend(),
        routes={"/workspace/": FilesystemBackend(root_dir=str(workspace), virtual_mode=True)},
    )
    visible_tools = ["ls", "read_file", "glob", "grep"]
    interrupts: dict[str, Any] = {}
    if allow_edits:
        visible_tools.extend(["write_file", "edit_file"])
        interrupts = {
            "write_file": {"allowed_decisions": ["approve", "reject"]},
            "edit_file": {"allowed_decisions": ["approve", "reject"]},
        }

    sensitive = [
        "/workspace/.env", "/workspace/.env.*", "/workspace/**/.env",
        "/workspace/**/.env.*", "/workspace/**/.ssh/**", "/workspace/**/*.pem",
        "/workspace/**/*.key",
    ]
    permissions = [FilesystemPermission(
        operations=["read", "write"], paths=sensitive, mode="deny",
    )]
    if not allow_edits:
        permissions.append(FilesystemPermission(
            operations=["write"], paths=["/workspace/**"], mode="deny",
        ))

    return create_deep_agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        backend=backend,
        middleware=[FilesystemMiddleware(backend=backend, tools=visible_tools)],
        interrupt_on=interrupts,
        checkpointer=MemorySaver(),
        permissions=permissions,
    )
