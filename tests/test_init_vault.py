"""Tests for vault initialization."""

import tempfile
from pathlib import Path

import pytest

from r0b0tlabbra1n.vault.initialize import init_vault


def test_init_vault_creates_structure():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp) / "test-brain"
        result = init_vault(vault)

        assert result == vault
        assert vault.exists()
        assert (vault / "START_HERE.md").exists()
        assert (vault / "SCHEMA.md").exists()
        assert (vault / "index.md").exists()
        assert (vault / "log.md").exists()
        assert (vault / "_agent" / "START_HERE.md").exists()
        assert (vault / "_agent" / "operating-rules.md").exists()
        assert (vault / "_agent" / "semantic" / "project-status.md").exists()
        assert (vault / "dashboards" / "agent-dashboard.md").exists()
        assert (vault / "_meta" / "vault-state.json").exists()


def test_init_vault_fileexists_error():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp) / "test-brain"
        vault.mkdir()
        (vault / "existing.txt").write_text("hello")

        with pytest.raises(FileExistsError):
            init_vault(vault, force=False)


def test_init_vault_force_overwrites():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp) / "test-brain"
        vault.mkdir()
        (vault / "existing.txt").write_text("hello")

        result = init_vault(vault, force=True)
        assert result == vault
        # Should have overwritten/created new files
        assert (vault / "START_HERE.md").exists()
