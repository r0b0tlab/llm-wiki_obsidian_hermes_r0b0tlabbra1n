"""Vault linting — validate frontmatter, wikilinks, secrets, and orphans."""

from __future__ import annotations

from pathlib import Path

from r0b0tlabbra1n.security.secret_scan import scan_for_secrets
from r0b0tlabbra1n.vault.frontmatter import parse_frontmatter, validate_frontmatter
from r0b0tlabbra1n.vault.links import find_broken_links, find_orphans


def lint_vault(vault_path: Path) -> list[dict]:
    """Lint all markdown files in a vault. Returns list of issues found."""
    issues = []

    for md_file in sorted(vault_path.rglob("*.md")):
        # Skip meta and raw directories
        if "_meta" in md_file.parts:
            continue

        rel = md_file.relative_to(vault_path)
        content = md_file.read_text(encoding="utf-8")

        # Check frontmatter
        fm_dict, body = parse_frontmatter(content)
        if fm_dict is None:
            issues.append({
                "level": "WARNING",
                "path": str(rel),
                "message": "Missing or invalid frontmatter",
            })
        else:
            fm_errors = validate_frontmatter(fm_dict)
            for err in fm_errors:
                issues.append({
                    "level": "ERROR",
                    "path": str(rel),
                    "message": err,
                })

        # Check wikilinks
        broken = find_broken_links(vault_path, content, source_path=md_file)
        for link in broken:
            issues.append({
                "level": "WARNING",
                "path": str(rel),
                "message": f"Broken wikilink: [[{link}]]",
            })

        # Check secrets
        secret_issues = scan_for_secrets(content, str(rel))
        for si in secret_issues:
            issues.append({
                "level": "ERROR",
                "path": str(rel),
                "message": si,
            })

    # Check orphans (skip raw dir)
    for orphan in find_orphans(vault_path):
        rel = orphan.relative_to(vault_path)
        if "raw" not in orphan.parts:
            issues.append({
                "level": "INFO",
                "path": str(rel),
                "message": "Orphan page (no incoming links)",
            })

    return issues
