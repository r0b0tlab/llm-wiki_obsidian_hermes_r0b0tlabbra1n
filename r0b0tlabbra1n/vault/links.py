"""Wikilink extraction and validation for Obsidian/Markdown pages."""

from __future__ import annotations

import re
from pathlib import Path

_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[#|][^\]]+)?\]\]")


def normalize_wikilink_target(link: str) -> str:
    """Normalize an Obsidian wikilink target without resolving it."""
    target = link.split("|", 1)[0].split("#", 1)[0].strip()
    return target.removesuffix(".md")


def extract_wikilinks(content: str) -> list[str]:
    """Extract all wikilinks from markdown content. Returns normalized targets."""
    return [normalize_wikilink_target(m.group(1)) for m in _WIKILINK_RE.finditer(content)]


def _candidate_paths(vault_path: Path, link: str, source_path: Path | None) -> list[Path]:
    link = normalize_wikilink_target(link)
    candidates: list[Path] = []
    if source_path and link.startswith("."):
        candidates.append(source_path.parent / link)
        candidates.append((source_path.parent / link).with_suffix(".md"))
    candidates.append(vault_path / link)
    candidates.append((vault_path / link).with_suffix(".md"))
    if "/" not in link and not link.startswith("."):
        for md in vault_path.rglob(f"{link}.md"):
            candidates.append(md)
    return candidates


def resolve_wikilink(vault_path: Path, link: str, source_path: Path | None = None) -> Path | None:
    """Resolve a wikilink without allowing traversal outside the vault."""
    vault_resolved = Path(vault_path).resolve()
    for candidate in _candidate_paths(vault_resolved, link, source_path):
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if not resolved.is_relative_to(vault_resolved):
            continue
        if resolved.exists() and resolved.is_dir():
            return resolved
        if resolved.exists() and resolved.suffix == ".md":
            return resolved
    return None


def find_broken_links(vault_path: Path, content: str, source_path: Path | None = None) -> list[str]:
    """Find wikilinks in content that don't resolve to existing files."""
    broken = []
    for link in extract_wikilinks(content):
        if resolve_wikilink(vault_path, link, source_path) is None:
            broken.append(link)
    return broken


def find_orphans(vault_path: Path) -> list[Path]:
    """Find .md files in vault that have no incoming wikilinks."""
    md_files: set[Path] = set()
    linked: set[Path] = set()
    for md_file in Path(vault_path).rglob("*.md"):
        rel = md_file.relative_to(vault_path)
        rel_s = str(rel)
        if rel_s.startswith("_meta/") or rel_s.startswith("raw/"):
            continue
        md_files.add(rel)
        try:
            content = md_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for link in extract_wikilinks(content):
            resolved = resolve_wikilink(vault_path, link, md_file)
            if resolved:
                linked.add(resolved.relative_to(vault_path))
    root_names = {"START_HERE.md", "index.md", "SCHEMA.md", "log.md"}
    return [vault_path / f for f in sorted(md_files - linked) if f.name not in root_names]


def build_link_graph(vault_path: Path) -> dict[str, list[str]]:
    """Build a link graph: {source_slug: [target_slug, ...]}."""
    graph: dict[str, list[str]] = {}
    for md_file in Path(vault_path).rglob("*.md"):
        rel = md_file.relative_to(vault_path)
        rel_s = str(rel)
        if rel_s.startswith("_meta/") or rel_s.startswith("raw/"):
            continue
        try:
            links = extract_wikilinks(md_file.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            continue
        graph[rel_s.removesuffix(".md")] = links
    return graph


def get_backlinks(graph: dict[str, list[str]], slug: str) -> list[str]:
    """Get all pages that link to a given slug."""
    slug = normalize_wikilink_target(slug)
    return [source for source, targets in graph.items() if slug in targets]
