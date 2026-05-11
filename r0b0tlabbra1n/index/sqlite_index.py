"""SQLite FTS5 index for the brain vault — searchable acceleration layer."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path


def _make_fts_query(query: str) -> str:
    """Convert a user query into a safe FTS5 query.

    Wraps each word in double quotes to prevent FTS5 syntax errors
    (e.g., uppercase letters treated as column names, special chars).
    """
    words = [w for w in re.split(r'\s+', query) if w]
    if not words:
        return '""'
    return " OR ".join(f'"{w}"' for w in words)


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
        """Rebuild the FTS5 index from all Markdown files. Returns page count."""
        conn = self._connect()
        try:
            conn.execute("DROP TABLE IF EXISTS pages_fts")

            conn.execute("""
                CREATE VIRTUAL TABLE pages_fts USING fts5(
                    path,
                    title,
                    type,
                    status,
                    tier,
                    body,
                    tokenize='porter unicode61'
                )
            """)

            count = 0
            for md_file in sorted(self.vault_path.rglob("*.md")):
                rel = str(md_file.relative_to(self.vault_path))
                if rel.startswith("_meta") or rel.startswith("raw/"):
                    continue

                content = md_file.read_text(encoding="utf-8")
                title = md_file.stem
                fm_type = ""
                fm_status = ""
                fm_tier = ""
                body = content

                if content.startswith("---\n"):
                    end = content.find("\n---\n", 4)
                    if end != -1:
                        import yaml
                        try:
                            fm = yaml.safe_load(content[4:end])
                            if isinstance(fm, dict):
                                title = fm.get("title", title)
                                fm_type = fm.get("type", "")
                                fm_status = fm.get("status", "")
                                fm_tier = fm.get("tier", "")
                        except yaml.YAMLError:
                            pass
                        body = content[end + 5:]

                conn.execute(
                    "INSERT INTO pages_fts (path, title, type, status, tier, body) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (rel, title, fm_type, fm_status, fm_tier, body),
                )
                count += 1

            conn.commit()
            return count
        finally:
            conn.close()

    def search(self, query: str, limit: int = 10, tier_filter: str | None = None) -> list[dict]:
        """Search the index with FTS5. Returns list of {path, title, snippet, score}."""
        conn = self._connect()
        try:
            fts_query = _make_fts_query(query)

            if tier_filter:
                rows = conn.execute(
                    """SELECT path, title, type, status, tier,
                              snippet(pages_fts, 5, '<mark>', '</mark>', '...', 32) as snippet
                       FROM pages_fts
                       WHERE pages_fts MATCH ? AND tier = ?
                       LIMIT ?""",
                    (fts_query, tier_filter, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT path, title, type, status, tier,
                              snippet(pages_fts, 5, '<mark>', '</mark>', '...', 32) as snippet
                       FROM pages_fts
                       WHERE pages_fts MATCH ?
                       LIMIT ?""",
                    (fts_query, limit),
                ).fetchall()

            return [
                {
                    "path": r[0],
                    "title": r[1],
                    "type": r[2],
                    "status": r[3],
                    "tier": r[4],
                    "snippet": r[5],
                    "score": 0.0,
                }
                for r in rows
            ]
        finally:
            conn.close()

    def search_all_tiers(self, query: str, limit: int = 20) -> dict[str, list[dict]]:
        """Search across all tiers and return grouped results."""
        results: dict[str, list[dict]] = {}
        for tier in ["warm", "cold", "archive"]:
            tier_results = self.search(query, limit=limit, tier_filter=tier)
            if tier_results:
                results[tier] = tier_results
        return results
