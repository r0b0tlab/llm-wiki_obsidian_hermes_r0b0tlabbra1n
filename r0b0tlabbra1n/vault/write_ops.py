"""Write operations for the brain vault — safe, atomic, provenance-tracked."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from r0b0tlabbra1n.models import PageFrontmatter
from r0b0tlabbra1n.security.secret_scan import scan_for_secrets
from r0b0tlabbra1n.vault.frontmatter import write_frontmatter


def safe_write_page(
    path: Path,
    fm: PageFrontmatter,
    body: str,
    provenance: str = "agent",
    secret_scan: bool = True,
) -> Path:
    """Write a page to the vault with safety checks."""
    fm.provenance = provenance
    fm.updated = datetime.now().isoformat()
    if not fm.created:
        fm.created = fm.updated
    if secret_scan:
        secrets = scan_for_secrets(body, str(path))
        if secrets:
            raise ValueError(f"Secrets detected in page {path}: {'; '.join(secrets)}")
    write_frontmatter(path, fm, body)
    _log_write(path, provenance)
    return path


def append_to_page(
    path: Path,
    section: str,
    provenance: str = "agent",
    secret_scan: bool = True,
) -> Path:
    """Append a section to a page, scanning the final content before writing."""
    old = path.read_text(encoding="utf-8") if path.exists() else ""
    new = old if section in old else old.rstrip() + ("\n\n" if old.strip() else "") + section
    if secret_scan:
        secrets = scan_for_secrets(new, str(path))
        if secrets:
            raise ValueError(f"Secrets detected in page {path}: {'; '.join(secrets)}")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(new, encoding="utf-8")
    tmp.replace(path)
    _log_write(path, provenance)
    return path


def _log_write(path: Path, provenance: str):
    """Log a write operation to the vault log."""
    vault = _find_vault_root(path)
    if vault is None:
        return
    log_path = vault / "log.md"
    now = datetime.now().isoformat()
    rel = path.relative_to(vault)
    entry = f"| {now} | page_updated | [[{str(rel).replace('.md', '')}]] | {provenance} |\n"
    if log_path.exists():
        content = log_path.read_text(encoding="utf-8")
        lines = content.split("\n")
        insert_at = len(lines)
        for i, line in enumerate(lines):
            if line.startswith("| init "):
                insert_at = i + 1
                break
        lines.insert(insert_at, entry.rstrip())
        tmp = log_path.with_name(f".{log_path.name}.tmp")
        tmp.write_text("\n".join(lines), encoding="utf-8")
        tmp.replace(log_path)
    else:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(
            "# Vault Log\n\n"
            "| Timestamp | Action | Page | Provenance |\n"
            "|-----------|--------|------|------------|\n"
            f"{entry}",
            encoding="utf-8",
        )


def _find_vault_root(path: Path) -> Path | None:
    current = path.parent
    while current != current.parent:
        if (current / "START_HERE.md").exists() or (current / "SCHEMA.md").exists():
            return current
        current = current.parent
    return None
