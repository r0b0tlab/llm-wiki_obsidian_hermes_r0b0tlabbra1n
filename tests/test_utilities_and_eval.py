"""Coverage tests for public utility modules and eval/promote commands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from r0b0tlabbra1n.cli import main
from r0b0tlabbra1n.config import BrainConfig, load_config
from r0b0tlabbra1n.evals.retrieval_eval import evaluate, format_report, load_gold
from r0b0tlabbra1n.memory.promote import promotion_candidates
from r0b0tlabbra1n.paths import ensure_vault_dirs, resolve_wikilink_path
from r0b0tlabbra1n.security.path_safety import require_within_vault
from r0b0tlabbra1n.security.raw_policy import raw_metadata
from r0b0tlabbra1n.vault.hashes import build_hash_manifest, load_hash_manifest
from r0b0tlabbra1n.vault.initialize import init_vault


def test_config_and_paths(tmp_path: Path):
    cfg = BrainConfig().with_vault(tmp_path / "brain")
    assert cfg.raw_path == tmp_path / "brain" / "raw"
    assert load_config().vault_path == Path("vault")
    vault = tmp_path / "brain"
    created = ensure_vault_dirs(vault)
    assert created
    page = vault / "concepts" / "thing.md"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text("ok", encoding="utf-8")
    assert resolve_wikilink_path(vault, "concepts/thing") == page
    assert resolve_wikilink_path(vault, "missing") is None


def test_config_file_load(tmp_path: Path):
    meta = tmp_path / "_meta"
    meta.mkdir()
    (meta / "config.yaml").write_text("context_packet_token_budget: 123\nunknown: ignored\n")
    assert load_config(tmp_path).context_packet_token_budget == 123


def test_path_safety_and_raw_metadata(tmp_path: Path):
    inside = tmp_path / "x.md"
    inside.write_text("x", encoding="utf-8")
    assert require_within_vault(tmp_path, inside) == inside.resolve()
    with pytest.raises(ValueError):
        require_within_vault(tmp_path, tmp_path.parent / "evil.md")
    md = raw_metadata("state.db")
    assert md["trusted"] is False
    assert "untrusted" in md["warning"].lower()


def test_eval_harness_and_cli(tmp_path: Path):
    vault = tmp_path / "brain"
    init_vault(vault)
    gold = tmp_path / "gold.yaml"
    gold.write_text(
        "- id: q\n  query: brain\n  expected_paths:\n    - START_HERE.md\n",
        encoding="utf-8",
    )
    cases = load_gold(gold)
    assert cases[0]["id"] == "q"
    report = evaluate(vault, gold)
    assert report["total"] == 1
    assert "Retrieval eval" in format_report(report)
    assert "top1_accuracy" in format_report(report, as_json=True)
    cli = CliRunner().invoke(main, ["eval", "--vault", str(vault), "--gold", str(gold), "--json"])
    assert cli.exit_code == 0
    assert json.loads(cli.output)["total"] == 1


def test_promotion_candidates_and_cli(tmp_path: Path):
    vault = tmp_path / "brain"
    init_vault(vault)
    session_dir = vault / "sessions" / "summaries"
    session_dir.mkdir(parents=True, exist_ok=True)
    for idx in range(2):
        (session_dir / f"s{idx}.md").write_text(
            "Decision: use Markdown source of truth\nFix: rebuild the FTS index\n",
            encoding="utf-8",
        )
    candidates = promotion_candidates(vault)
    assert any("Markdown source" in c["content"] for c in candidates)
    cli = CliRunner().invoke(main, ["promote-candidates", "--vault", str(vault), "--json"])
    assert cli.exit_code == 0
    assert json.loads(cli.output)


def test_hash_manifest_load(tmp_path: Path):
    vault = tmp_path / "brain"
    init_vault(vault)
    manifest = build_hash_manifest(vault)
    loaded = load_hash_manifest(vault)
    assert manifest["page_count"] == loaded["page_count"]
