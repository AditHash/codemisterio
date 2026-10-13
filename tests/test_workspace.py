from pathlib import Path

from codemisterio.workspace import compare_snapshots, snapshot_workspace


def test_observed_file_edits_and_creates(tmp_path: Path) -> None:
    file = tmp_path / "app.py"
    file.write_text("def run():\n    return False\n")
    before = snapshot_workspace(tmp_path)
    file.write_text("def run():\n    return True\n")
    (tmp_path / "tests.py").write_text("assert True\n")
    after = snapshot_workspace(tmp_path)
    changed = {x.path: x for x in compare_snapshots(before, after)}
    assert changed["app.py"].kind == "modified"
    assert changed["app.py"].new_lines == (2,)
    assert changed["app.py"].added == 1
    assert changed["app.py"].removed == 1
    assert changed["tests.py"].kind == "created"


def test_deleted_file(tmp_path: Path) -> None:
    target = tmp_path / "gone.py"
    target.write_text("bye\n")
    first = snapshot_workspace(tmp_path)
    target.unlink()
    assert compare_snapshots(first, snapshot_workspace(tmp_path))[0].kind == "deleted"


def test_ignores_secrets_symlinks_and_large_directories(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("API_KEY=SECRET")
    (tmp_path / "one.py").write_text("ok")
    (tmp_path / "linked.py").symlink_to(tmp_path / ".env")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "a.js").write_text("code")
    assert snapshot_workspace(tmp_path).files == {"one.py": "ok"}


def test_partial_scan_does_not_falsely_claim_deletions(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("a")
    before = snapshot_workspace(tmp_path)
    after = snapshot_workspace(tmp_path, max_files=0)
    assert after.partial
    assert compare_snapshots(before, after) == []
