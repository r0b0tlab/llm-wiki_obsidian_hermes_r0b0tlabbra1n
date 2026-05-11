"""Adversarial and quality-gate tests for memory system hardening."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from click.testing import CliRunner

from r0b0tlabbra1n.cli import main
from r0b0tlabbra1n.index.sqlite_index import BrainIndex
from r0b0tlabbra1n.models import MemoryTier, PageFrontmatter, PageStatus, PageType
from r0b0tlabbra1n.vault.hashes import check_drift
from r0b0tlabbra1n.vault.initialize import init_vault
from r0b0tlabbra1n.vault.write_ops import append_to_page, safe_write_page


def test_fts_handles_adversarial_queries(tmp_path: Path):
    vault = tmp_path / "brain"
    init_vault(vault)
    page = vault / "concepts" / "hermes-memory.md"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(
        "---\ntitle: Hermes Memory\ntype: concept\nstatus: active\ntier: warm\n---\n"
        "Hermes memory handles unicode 秘密 and query syntax safely.",
        encoding="utf-8",
    )
    index = BrainIndex(vault)
    index.rebuild()
    for query in ["", '"unterminated', "foo:bar", "Hermes AND memory", "秘密 Hermes"]:
        results = index.search(query)
        assert isinstance(results, list)
    scored = index.search("Hermes memory")
    assert scored
    assert any(r["score"] != 0.0 for r in scored)


def test_append_to_page_blocks_secrets_without_modifying_file(tmp_path: Path):
    vault = tmp_path / "brain"
    init_vault(vault)
    page = vault / "notes.md"
    safe_write_page(
        page,
        PageFrontmatter(
            title="Notes",
            type=PageType.CONCEPT,
            status=PageStatus.ACTIVE,
            tier=MemoryTier.L3_COLD,
        ),
        "clean body",
    )
    before = page.read_text(encoding="utf-8")
    with pytest.raises(ValueError):
        append_to_page(page, 'token="ghp_aaaaaaaaaaaaaaaaaaaaaaaa"')
    assert page.read_text(encoding="utf-8") == before


def test_lint_info_only_exits_zero_and_strict_warning_fails(tmp_path: Path):
    vault = tmp_path / "brain"
    runner = CliRunner()
    result = runner.invoke(main, ["init", "--vault", str(vault)])
    assert result.exit_code == 0
    result = runner.invoke(main, ["lint", "--vault", str(vault)])
    assert result.exit_code == 0
    bad = vault / "broken.md"
    bad.write_text(
        "---\ntitle: Broken\ntype: concept\nstatus: active\n---\n[[missing-target]]",
        encoding="utf-8",
    )
    result = runner.invoke(main, ["lint", "--vault", str(vault), "--strict"])
    assert result.exit_code == 1


def test_graph_drift_eval_and_context_cli(tmp_path: Path):
    vault = tmp_path / "brain"
    init_vault(vault)
    runner = CliRunner()
    build = runner.invoke(main, ["build-index", "--vault", str(vault)])
    assert build.exit_code == 0
    graph = runner.invoke(main, ["graph", "--vault", str(vault), "--json"])
    assert graph.exit_code == 0
    assert "graph" in json.loads(graph.output)
    context = runner.invoke(
        main, ["search", "brain", "--vault", str(vault), "--context", "--budget", "500"]
    )
    assert context.exit_code == 0
    assert "<memory-context>" in context.output
    assert check_drift(vault)["clean"]
    (vault / "START_HERE.md").write_text("changed brain", encoding="utf-8")
    assert not check_drift(vault)["clean"]


def test_ingest_is_schema_tolerant_and_writes_structured_summary(tmp_path: Path):
    db = tmp_path / "state.db"
    conn = sqlite3.connect(db)
    conn.execute(
        "CREATE TABLE sessions (id TEXT PRIMARY KEY, created_at TEXT, parent_session_id TEXT, "
        "model_name TEXT, provider_name TEXT)"
    )
    conn.execute(
        "CREATE TABLE messages (id INTEGER PRIMARY KEY, session_id TEXT, role TEXT, content TEXT)"
    )
    conn.execute(
        "INSERT INTO sessions VALUES ('sid-1', '2026-05-11T00:00:00', '', 'model', 'provider')"
    )
    conn.execute(
        "INSERT INTO messages (session_id, role, content) VALUES ('sid-1', 'user', 'Do X')"
    )
    conn.execute(
        "INSERT INTO messages (session_id, role, content) VALUES "
        "('sid-1', 'assistant', 'Decision: use Markdown source of truth')"
    )
    conn.commit()
    conn.close()
    vault = tmp_path / "brain"
    init_vault(vault)
    result = CliRunner().invoke(
        main,
        ["ingest-sessions", "--hermes-home", str(tmp_path), "--vault", str(vault)],
    )
    assert result.exit_code == 0
    summary = next((vault / "sessions" / "summaries").glob("*.md")).read_text(encoding="utf-8")
    assert "## User Requests" in summary
    assert "## Decisions" in summary
