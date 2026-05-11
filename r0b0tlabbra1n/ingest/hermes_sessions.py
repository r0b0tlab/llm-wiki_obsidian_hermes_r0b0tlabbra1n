"""Hermes session ingestion — read state.db and convert to vault pages."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path


def ingest(state_db_path: Path, vault_path: Path, since_cursor: str | None = None) -> int:
    """Ingest Hermes sessions from state.db into the brain vault.

    Args:
        state_db_path: Path to Hermes state.db
        vault_path: Path to the brain vault
        since_cursor: ISO timestamp or session ID to start from

    Returns:
        Number of sessions ingested
    """
    manifest_path = vault_path / "_meta" / "ingestion-manifest.jsonl"
    ingested_ids = _load_ingested(manifest_path)

    # Read-only connection
    uri = f"file:{state_db_path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row

    try:
        # Find sessions to ingest
        query = """
            SELECT id, created_at, parent_session_id, model_name, provider_name
            FROM sessions
        """
        params: list = []

        if since_cursor:
            query += " WHERE created_at > ?"
            params.append(since_cursor)

        query += " ORDER BY created_at ASC"

        sessions = conn.execute(query, params).fetchall()

        count = 0
        for session in sessions:
            sid = session["id"]
            if sid in ingested_ids:
                continue

            # Create session summary page
            summary = _create_session_page(conn, session, vault_path)
            if summary:
                _record_ingested(manifest_path, sid)
                count += 1

    finally:
        conn.close()

    return count


def _load_ingested(manifest_path: Path) -> set[str]:
    """Load previously ingested session IDs."""
    ingested = set()
    if manifest_path.exists():
        for line in manifest_path.read_text(encoding="utf-8").strip().split("\n"):
            if line:
                try:
                    entry = json.loads(line)
                    ingested.add(entry.get("session_id", ""))
                except json.JSONDecodeError:
                    continue
    return ingested


def _record_ingested(manifest_path: Path, session_id: str):
    """Record a session as ingested."""
    entry = json.dumps({
        "session_id": session_id,
        "ingested_at": datetime.now().isoformat(),
    })
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "a") as f:
        f.write(entry + "\n")


def _create_session_page(
    conn: sqlite3.Connection,
    session: sqlite3.Row,
    vault_path: Path,
) -> Path | None:
    """Create a session summary page in the vault. Returns the path or None."""
    sid = session["id"]
    created = session["created_at"] or datetime.now().isoformat()
    model = session["model_name"] or "unknown"
    parent_id = session["parent_session_id"]

    # Get message count
    msg_count = conn.execute(
        "SELECT COUNT(*) as cnt FROM messages WHERE session_id = ?", (sid,)
    ).fetchone()["cnt"]

    # Get a sample of messages for summary (first 5 user messages)
    user_msgs = conn.execute(
        "SELECT content FROM messages WHERE session_id = ? AND role = 'user' LIMIT 5",
        (sid,),
    ).fetchall()

    topics = ", ".join(m["content"][:80] for m in user_msgs[:3])

    # Create date-based path
    try:
        dt = datetime.fromisoformat(created)
        date_prefix = dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        date_prefix = "unknown"

    page_dir = vault_path / "sessions" / "summaries"
    page_dir.mkdir(parents=True, exist_ok=True)

    slug = f"{date_prefix}-{sid[:8]}"
    page_path = page_dir / f"{slug}.md"

    parent_ref = f"\n- Parent session: `{parent_id}`" if parent_id else ""

    content = f"""---
title: Session {sid[:12]}
created: {created}
type: session
status: active
memory_type: episodic
tier: cold
model: {model}
session_id: "{sid}"
parent_session_id: "{parent_id or ''}"
msg_count: {msg_count}
provenance: ingest
---

# Session {sid[:12]}

- **Date:** {created}
- **Model:** {model}
- **Messages:** {msg_count}{parent_ref}

## Topics

{topics or 'No user messages found.'}

## Notes

Auto-generated from Hermes session ingest. Review and add human notes.

[[../transcripts-index]]

---
*Ingested by brain ingest-sessions*
"""
    page_path.write_text(content, encoding="utf-8")
    return page_path
