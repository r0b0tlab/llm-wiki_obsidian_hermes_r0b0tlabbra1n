"""Hermes session ingestion — read state.db and convert to vault pages."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from r0b0tlabbra1n.security.raw_policy import raw_metadata
from r0b0tlabbra1n.security.secret_scan import scan_for_secrets


def ingest(
    state_db_path: Path,
    vault_path: Path,
    since_cursor: str | None = None,
    include_transcripts: bool = False,
) -> int:
    """Ingest Hermes sessions from state.db into the brain vault."""
    vault_path = Path(vault_path)
    manifest_path = vault_path / "_meta" / "ingestion-manifest.jsonl"
    ingested_ids = _load_ingested(manifest_path)
    uri = f"file:{state_db_path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        _validate_schema(conn)
        query = "SELECT id, created_at, parent_session_id, model_name, provider_name FROM sessions"
        params: list[str] = []
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
            page = _create_session_page(conn, session, vault_path)
            if page and include_transcripts:
                _write_transcript(conn, session, state_db_path, vault_path)
            if page:
                _record_ingested(manifest_path, sid)
                count += 1
    finally:
        conn.close()
    return count


def _validate_schema(conn: sqlite3.Connection) -> None:
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    missing = {"sessions", "messages"} - tables
    if missing:
        raise ValueError(f"Unsupported Hermes state.db schema; missing tables: {sorted(missing)}")
    cols = {r[1] for r in conn.execute("PRAGMA table_info(sessions)")}
    required = {"id", "created_at"}
    if not required.issubset(cols):
        raise ValueError(f"Unsupported sessions schema; missing columns: {sorted(required - cols)}")


def _load_ingested(manifest_path: Path) -> set[str]:
    ingested = set()
    if manifest_path.exists():
        for line in manifest_path.read_text(encoding="utf-8").splitlines():
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("session_id"):
                ingested.add(entry["session_id"])
    return ingested


def _record_ingested(manifest_path: Path, session_id: str):
    entry = json.dumps({"session_id": session_id, "ingested_at": datetime.now().isoformat()})
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("a", encoding="utf-8") as f:
        f.write(entry + "\n")


def _messages(conn: sqlite3.Connection, sid: str) -> list[sqlite3.Row]:
    cols = {r[1] for r in conn.execute("PRAGMA table_info(messages)")}
    if {"session_id", "role", "content"}.issubset(cols):
        return conn.execute(
            "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id ASC", (sid,)
        ).fetchall()
    return []


def _summarize_messages(messages: list[sqlite3.Row]) -> dict[str, list[str]]:
    summary = {
        "requests": [],
        "actions": [],
        "decisions": [],
        "failures": [],
        "commands": [],
        "followups": [],
    }
    for m in messages:
        role = m["role"]
        content = (m["content"] or "").strip()
        if not content:
            continue
        low = content.lower()
        first = " ".join(content.split())[:180]
        if role == "user":
            summary["requests"].append(first)
        elif "error" in low or "traceback" in low or "failed" in low:
            summary["failures"].append(first)
        elif "decision" in low or "decided" in low:
            summary["decisions"].append(first)
        elif "```" in content or content.startswith("$"):
            summary["commands"].append(first)
        else:
            summary["actions"].append(first)
    return {k: v[:8] for k, v in summary.items()}


def _section(title: str, items: list[str]) -> str:
    if not items:
        return f"## {title}\n\nNone detected.\n"
    lines = "\n".join(f"- {item}" for item in items)
    return f"## {title}\n\n{lines}\n"


def _create_session_page(
    conn: sqlite3.Connection, session: sqlite3.Row, vault_path: Path
) -> Path | None:
    sid = session["id"]
    created = session["created_at"] or datetime.now().isoformat()
    model = session["model_name"] if "model_name" in session.keys() else "unknown"
    provider = session["provider_name"] if "provider_name" in session.keys() else "unknown"
    parent_id = session["parent_session_id"] if "parent_session_id" in session.keys() else ""
    messages = _messages(conn, sid)
    summary = _summarize_messages(messages)
    try:
        date_prefix = datetime.fromisoformat(created).strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        date_prefix = "unknown"
    page_dir = vault_path / "sessions" / "summaries"
    page_dir.mkdir(parents=True, exist_ok=True)
    page_path = page_dir / f"{date_prefix}-{sid[:8]}.md"
    parent_ref = f"\n- Parent session: `{parent_id}`" if parent_id else ""
    content = f"""---
title: Session {sid[:12]}
created: {created}
type: session
status: active
memory_type: episodic
tier: cold
model: {model or "unknown"}
provider: {provider or "unknown"}
session_id: "{sid}"
parent_session_id: "{parent_id or ""}"
msg_count: {len(messages)}
provenance: ingest
---

# Session {sid[:12]}

- **Date:** {created}
- **Model:** {model or "unknown"}
- **Provider:** {provider or "unknown"}
- **Messages:** {len(messages)}{parent_ref}

{_section("User Requests", summary["requests"])}
{_section("Actions Taken", summary["actions"])}
{_section("Decisions", summary["decisions"])}
{_section("Failures", summary["failures"])}
{_section("Commands", summary["commands"])}
{_section("Follow-ups", summary["followups"])}
## Provenance

- Source: Hermes state.db read-only ingest
- Session ID: `{sid}`
- Review status: generated summary, needs human review

[[../transcripts-index]]
"""
    secrets = scan_for_secrets(content, str(page_path))
    if secrets:
        raise ValueError(f"Secrets detected while ingesting session {sid}: {'; '.join(secrets)}")
    page_path.write_text(content, encoding="utf-8")
    return page_path


def _write_transcript(
    conn: sqlite3.Connection, session: sqlite3.Row, state_db_path: Path, vault_path: Path
) -> Path:
    sid = session["id"]
    messages = [{"role": m["role"], "content": m["content"]} for m in _messages(conn, sid)]
    payload = {
        "metadata": raw_metadata(str(state_db_path)),
        "session_id": sid,
        "messages": messages,
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    secrets = scan_for_secrets(text, f"raw transcript {sid}")
    if secrets:
        raise ValueError(f"Secrets detected in raw transcript {sid}: {'; '.join(secrets)}")
    raw_dir = vault_path / "raw" / "hermes-sessions"
    raw_dir.mkdir(parents=True, exist_ok=True)
    out = raw_dir / f"{sid}.json"
    out.write_text(text, encoding="utf-8")
    return out
