"""Source hash manifest and drift detection for vault pages."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def hash_file(path: Path) -> str:
    """Return a SHA256 digest for a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_indexable_markdown(vault_path: Path):
    """Yield markdown files that are source pages, excluding metadata/raw."""
    for md_file in sorted(Path(vault_path).rglob("*.md")):
        rel = md_file.relative_to(vault_path)
        rel_s = str(rel)
        if rel_s.startswith("_meta/") or rel_s.startswith("raw/"):
            continue
        yield md_file


def build_hash_manifest(vault_path: Path) -> dict:
    """Build and persist source-hashes.json."""
    vault_path = Path(vault_path)
    hashes = {
        str(p.relative_to(vault_path)): hash_file(p)
        for p in iter_indexable_markdown(vault_path)
    }
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "page_count": len(hashes),
        "hashes": hashes,
    }
    meta = vault_path / "_meta"
    meta.mkdir(parents=True, exist_ok=True)
    (meta / "source-hashes.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return manifest

# Backward-compatible attribute used by sqlite_index import style.
build_hash_manifest.hash_file = hash_file  # type: ignore[attr-defined]


def load_hash_manifest(vault_path: Path) -> dict:
    path = Path(vault_path) / "_meta" / "source-hashes.json"
    if not path.exists():
        return {"hashes": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"hashes": {}, "error": "corrupt manifest"}


def check_drift(vault_path: Path) -> dict:
    """Compare current markdown hashes with the last persisted manifest."""
    vault_path = Path(vault_path)
    old = load_hash_manifest(vault_path).get("hashes", {})
    current = {
        str(p.relative_to(vault_path)): hash_file(p)
        for p in iter_indexable_markdown(vault_path)
    }
    added = sorted(set(current) - set(old))
    removed = sorted(set(old) - set(current))
    changed = sorted(p for p in set(current) & set(old) if current[p] != old[p])
    return {
        "clean": not (added or removed or changed),
        "added": added,
        "removed": removed,
        "changed": changed,
        "current": current,
    }
