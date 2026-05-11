"""SQLite FTS5 index for the brain vault — searchable acceleration layer."""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import yaml

from r0b0tlabbra1n.vault.hashes import build_hash_manifest


def _make_fts_query(query: str) -> str:
    """Convert a user query into a safe FTS5 query.

    FTS5 has surprising syntax: bare uppercase terms can be parsed as operators,
    punctuation can create column filters, and embedded quotes can break parsing.
    We strip to word-ish chunks, escape embedded quotes, and OR the tokens so a
    broad memory search doesn't miss useful partial matches.
    """
    words = re.findall(r"[\w\-]+", query or "", flags=re.UNICODE)
    if not words:
        return '""'
    quoted = []
    for word in words:
        escaped = word.replace('"', '""')
        quoted.append(f'"{escaped}"')
    return " OR ".join(quoted)


class BrainIndex:
    """Full-text search index over a brain vault's Markdown pages."""

    def __init__(self, vault_path: Path):
        self.vault_path = Path(vault_path)
        self._index_dir = self.vault_path / "_meta"
        self._index_dir.mkdir(parents=True, exist_ok=True)
        self._db_path = self._index_dir / "retrieval-index.sqlite"

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def rebuild(self) -> int:
        """Rebuild the FTS5 index from Markdown files. Returns page count."""
        conn = self._connect()
        try:
            conn.execute("DROP TABLE IF EXISTS pages_fts")
            conn.execute("DROP TABLE IF EXISTS pages_meta")
            conn.execute(
                """
                CREATE VIRTUAL TABLE pages_fts USING fts5(
                    path, title, type, status, tier, memory_type,
                    confidence, created, updated, source_hash, body,
                    tokenize='porter unicode61'
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE pages_meta (
                    path TEXT PRIMARY KEY,
                    title TEXT,
                    type TEXT,
                    status TEXT,
                    tier TEXT,
                    memory_type TEXT,
                    confidence TEXT,
                    created TEXT,
                    updated TEXT,
                    source_hash TEXT,
                    bytes INTEGER
                )
                """
            )

            count = 0
            hashes = {}
            for md_file in sorted(self.vault_path.rglob("*.md")):
                rel = str(md_file.relative_to(self.vault_path))
                if rel.startswith("_meta/") or rel.startswith("raw/"):
                    continue
                try:
                    content = md_file.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue

                fm, body = self._split_frontmatter(content)
                digest = build_hash_manifest.hash_file(md_file)
                hashes[rel] = digest
                title = str(fm.get("title") or md_file.stem)
                row = {
                    "path": rel,
                    "title": title,
                    "type": str(fm.get("type") or ""),
                    "status": str(fm.get("status") or ""),
                    "tier": str(fm.get("tier") or ""),
                    "memory_type": str(fm.get("memory_type") or ""),
                    "confidence": str(fm.get("confidence") or ""),
                    "created": str(fm.get("created") or ""),
                    "updated": str(fm.get("updated") or ""),
                    "source_hash": str(fm.get("source_hash") or digest),
                    "body": body,
                }
                values = tuple(
                    row[k]
                    for k in (
                        "path",
                        "title",
                        "type",
                        "status",
                        "tier",
                        "memory_type",
                        "confidence",
                        "created",
                        "updated",
                        "source_hash",
                        "body",
                    )
                )
                conn.execute(
                    "INSERT INTO pages_fts (path, title, type, status, tier, memory_type, "
                    "confidence, created, updated, source_hash, body) VALUES "
                    "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    values,
                )
                conn.execute(
                    "INSERT INTO pages_meta VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    values[:-1] + (md_file.stat().st_size,),
                )
                count += 1

            manifest = {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "page_count": count,
                "hashes": hashes,
            }
            (self._index_dir / "source-hashes.json").write_text(
                json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
            )
            conn.commit()
            return count
        finally:
            conn.close()

    @staticmethod
    def _split_frontmatter(content: str) -> tuple[dict, str]:
        if not content.startswith("---\n"):
            return {}, content
        end = content.find("\n---\n", 4)
        if end == -1:
            return {}, content
        body = content[end + 5 :]
        try:
            fm = yaml.safe_load(content[4:end])
        except yaml.YAMLError:
            fm = None
        return (fm if isinstance(fm, dict) else {}), body

    def search(self, query: str, limit: int = 10, tier_filter: str | None = None) -> list[dict]:
        """Search the index. Returns path/title/snippet/score metadata dictionaries."""
        if limit <= 0:
            return []
        fts_query = _make_fts_query(query)
        if fts_query == '""':
            return []
        conn = self._connect()
        try:
            where = "pages_fts MATCH ?"
            params: list[object] = [fts_query]
            if tier_filter:
                where += " AND tier = ?"
                params.append(tier_filter)
            params.append(limit)
            rows = conn.execute(
                f"""SELECT path, title, type, status, tier, memory_type, confidence,
                           created, updated, source_hash,
                           snippet(pages_fts, 10, '<mark>', '</mark>', '...', 32) AS snippet,
                           bm25(pages_fts) AS rank
                    FROM pages_fts
                    WHERE {where}
                    ORDER BY rank ASC, tier ASC, updated DESC, path ASC
                    LIMIT ?""",
                params,
            ).fetchall()
            results = []
            for r in rows:
                rank = float(r[11])
                results.append(
                    {
                        "path": r[0],
                        "title": r[1],
                        "type": r[2],
                        "status": r[3],
                        "tier": r[4],
                        "memory_type": r[5],
                        "confidence": r[6],
                        "created": r[7],
                        "updated": r[8],
                        "source_hash": r[9],
                        "snippet": r[10],
                        "rank": rank,
                        "score": -rank,
                    }
                )
            return results
        finally:
            conn.close()

    def search_all_tiers(self, query: str, limit: int = 20) -> dict[str, list[dict]]:
        """Search across all tiers and return grouped results."""
        results: dict[str, list[dict]] = {}
        for tier in ["hot", "warm", "cold", "archive"]:
            tier_results = self.search(query, limit=limit, tier_filter=tier)
            if tier_results:
                results[tier] = tier_results
        return results
