"""Path utilities for r0b0tlabbra1n."""

from pathlib import Path

# Standard vault subdirectories
VAULT_DIRS = [
    "raw/articles",
    "raw/papers",
    "raw/sessions",
    "raw/projects",
    "raw/skills",
    "raw/assets",
    "dashboards",
    "_agent/semantic",
    "_agent/episodic/decisions",
    "_agent/episodic/failures",
    "_agent/episodic/successes",
    "_agent/episodic/incidents",
    "_agent/heartbeat",
    "_agent/audits",
    "projects",
    "sessions/summaries",
    "entities",
    "concepts",
    "comparisons",
    "queries",
    "procedures",
    "skills/catalog",
    "_meta",
    "indexes",
]


def ensure_vault_dirs(vault_path: Path) -> list[Path]:
    """Create all standard vault directories. Returns list of created paths."""
    created = []
    for d in VAULT_DIRS:
        p = vault_path / d
        p.mkdir(parents=True, exist_ok=True)
        created.append(p)
    return created


def resolve_wikilink_path(vault_path: Path, link: str) -> Path | None:
    """Resolve a wikilink like [[project-name]] or [[path/to/page]] to a .md file.
    Supports ../ relative paths."""
    # Strip anchor if present
    if "#" in link:
        link = link.split("#")[0]

    link = link.strip()

    # Resolve .. segments for relative paths
    link_path = Path(link)

    # Try with .md extension (direct)
    candidate = vault_path / f"{link}.md"
    if candidate.exists():
        return candidate

    # Try with .md extension (resolved ..)
    try:
        resolved = (vault_path / link_path).resolve()
        candidate = resolved.with_suffix(".md") if not resolved.suffix else resolved
        if candidate.is_relative_to(vault_path) and candidate.exists():
            return candidate

        candidate = vault_path / f"{link}.md"
        candidate = candidate.resolve()
        if candidate.is_relative_to(vault_path) and candidate.exists():
            return candidate
    except (ValueError, OSError):
        pass

    # Try with explicit extension
    candidate = vault_path / link
    if candidate.exists():
        return candidate

    return None
