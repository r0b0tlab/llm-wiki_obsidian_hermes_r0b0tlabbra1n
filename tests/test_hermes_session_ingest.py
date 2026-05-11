"""Tests for Hermes session ingestion."""

import json
import sqlite3
import tempfile
from pathlib import Path

from r0b0tlabbra1n.ingest.hermes_sessions import ingest
from r0b0tlabbra1n.vault.initialize import init_vault


def _create_test_state_db(db_path: Path, num_sessions: int = 3) -> list[str]:
    """Create a synthetic Hermes state.db for testing."""
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")

    # Create Hermes-like schema
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            created_at TEXT,
            parent_session_id TEXT,
            model_name TEXT,
            provider_name TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT
        )
    """)

    session_ids = []
    for i in range(num_sessions):
        sid = f"test-session-{i:04d}"
        session_ids.append(sid)
        conn.execute(
            "INSERT INTO sessions (id, created_at, model_name, provider_name) "
            "VALUES (?, ?, ?, ?)",
            (sid, f"2026-05-{10+i:02d}T12:00:00", "test-model", "test-provider"),
        )
        for j in range(3):
            conn.execute(
                "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
                (sid, "user", f"Test question {j} from session {i}"),
            )
            conn.execute(
                "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
                (sid, "assistant", f"Test answer {j} from session {i}"),
            )

    conn.commit()
    conn.close()
    return session_ids


def test_ingest_sessions():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # Create test state.db
        db_path = tmp_path / "state.db"
        session_ids = _create_test_state_db(db_path, num_sessions=3)

        # Create vault
        vault = tmp_path / "test-brain"
        init_vault(vault)

        # Ingest
        count = ingest(db_path, vault)
        assert count == 3

        # Check session pages were created
        summaries = list((vault / "sessions" / "summaries").glob("*.md"))
        assert len(summaries) == 3

        # Check manifest
        manifest = vault / "_meta" / "ingestion-manifest.jsonl"
        assert manifest.exists()
        lines = manifest.read_text().strip().split("\n")
        assert len(lines) == 3

        # Verify idempotence
        count2 = ingest(db_path, vault)
        assert count2 == 0  # Already ingested


def test_ingest_sessions_since_cursor():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        db_path = tmp_path / "state.db"
        _create_test_state_db(db_path, num_sessions=5)

        vault = tmp_path / "test-brain"
        init_vault(vault)

        # Only ingest sessions after 2026-05-13
        count = ingest(db_path, vault, since_cursor="2026-05-13T00:00:00")
        assert count >= 1  # Sessions on 05-13 and 05-14
