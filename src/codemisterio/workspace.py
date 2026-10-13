"""Bounded, read-only workspace snapshots for honest observed file-change events.

Not a security boundary: side-effecting tools and the OS still need sandboxing.
"""

from __future__ import annotations

import difflib
import os
from dataclasses import dataclass
from pathlib import Path

# Avoid private files and common heavy/generated trees. Snapshot is intentionally partial.
EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", ".next", "dist",
    "build", ".codemisterio", ".tox", ".mypy_cache", ".pytest_cache",
}
EXCLUDED_FILES = {".env", ".npmrc", ".pypirc", "id_rsa", "id_ed25519"}
EXCLUDED_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".sqlite", ".db"}


@dataclass(frozen=True)
class WorkspaceSnapshot:
    files: dict[str, str]
    partial: bool = False


@dataclass(frozen=True)
class FileChange:
    kind: str
    path: str
    added: int
    removed: int
    new_lines: tuple[int, ...]

    def summary(self) -> str:
        if self.kind == "created":
            return f"Created {self.path} (+{self.added} lines)"
        if self.kind == "deleted":
            return f"Deleted {self.path} (-{self.removed} lines)"
        line_text = ", ".join(str(n) for n in self.new_lines[:6])
        extra = f"; new line(s): {line_text}" if line_text else ""
        return f"Modified {self.path} (+{self.added}/-{self.removed}{extra})"


def snapshot_workspace(root: Path, *, max_files: int = 2000, max_bytes: int = 8_000_000,
                       max_file_bytes: int = 512_000) -> WorkspaceSnapshot:
    """Capture bounded UTF-8 text files. External modifications may go undetected."""
    root = root.resolve(strict=True)
    files: dict[str, str] = {}
    total = 0
    partial = False
    for current, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(
            d for d in dirs
            if d not in EXCLUDED_DIRS and not (Path(current) / d).is_symlink()
        )
        for name in sorted(names):
            path = Path(current) / name
            if (name in EXCLUDED_FILES or name.startswith(".env.")
                    or path.suffix.lower() in EXCLUDED_SUFFIXES or path.is_symlink()):
                continue
            if len(files) >= max_files or total >= max_bytes:
                return WorkspaceSnapshot(files, partial=True)
            try:
                st = path.stat()
                if not path.is_file():
                    continue
                if st.st_size > max_file_bytes or st.st_size > max_bytes - total:
                    partial = True
                    continue
                data = path.read_bytes()
                if b"\0" in data:
                    continue
                files[path.relative_to(root).as_posix()] = data.decode("utf-8")
                total += len(data)
            except (OSError, UnicodeError):
                partial = True
    return WorkspaceSnapshot(files, partial)


def compare_snapshots(before: WorkspaceSnapshot, after: WorkspaceSnapshot) -> list[FileChange]:
    """Report only changes observable in both bounded snapshots."""
    # In partial snapshots, missing files might be outside the scan budget.
    deleted = (before.files.keys() - after.files.keys()) if not after.partial else set()
    created = (after.files.keys() - before.files.keys()) if not before.partial else set()
    changed: list[FileChange] = []
    for path in sorted(set(before.files) & set(after.files) | created | deleted):
        old = before.files.get(path, "")
        new = after.files.get(path, "")
        if old == new:
            continue
        if path in created:
            kind = "created"
        elif path in deleted:
            kind = "deleted"
        else:
            kind = "modified"
        opcodes = difflib.SequenceMatcher(
            a=old.splitlines(), b=new.splitlines(), autojunk=False
        ).get_opcodes()
        added = sum(j2 - j1 for tag, _, _, j1, j2 in opcodes if tag != "equal")
        removed = sum(i2 - i1 for tag, i1, i2, _, _ in opcodes if tag != "equal")
        line_starts = tuple(j1 + 1 for tag, _, _, j1, _ in opcodes if tag != "equal")
        changed.append(FileChange(kind, path, added, removed, line_starts))
    return changed
