"""Frontmatter parsing and validation for Obsidian/Markdown pages."""

from __future__ import annotations

from pathlib import Path

import yaml

from r0b0tlabbra1n.models import (
    Confidence,
    MemoryTier,
    MemoryType,
    PageFrontmatter,
    PageStatus,
    PageType,
)

_FRONTMATTER_PATTERN = "---\n"


def parse_frontmatter(content: str) -> tuple[dict | None, str]:
    """Parse YAML frontmatter from markdown content.
    Returns (frontmatter_dict, body) or (None, full_content) if no frontmatter.
    """
    if not content.startswith(_FRONTMATTER_PATTERN):
        return None, content

    # Find closing ---
    end = content.find(_FRONTMATTER_PATTERN, 4)
    if end == -1:
        return None, content

    yaml_str = content[4:end]

    try:
        data = yaml.safe_load(yaml_str)
        return data if isinstance(data, dict) else None, content
    except yaml.YAMLError:
        return None, content


def validate_frontmatter(fm: dict) -> list[str]:
    """Validate frontmatter fields. Returns list of error messages."""
    errors = []

    if "title" not in fm:
        errors.append("Missing required field: title")

    if "type" in fm:
        try:
            PageType(fm["type"])
        except ValueError:
            errors.append(f"Invalid page type: {fm['type']}")

    if "status" in fm:
        try:
            PageStatus(fm["status"])
        except ValueError:
            errors.append(f"Invalid page status: {fm['status']}")

    if "memory_type" in fm:
        try:
            MemoryType(fm["memory_type"])
        except ValueError:
            errors.append(f"Invalid memory type: {fm['memory_type']}")

    if "tier" in fm:
        try:
            MemoryTier(fm["tier"])
        except ValueError:
            errors.append(f"Invalid memory tier: {fm['tier']}")

    if "confidence" in fm:
        try:
            Confidence(fm["confidence"])
        except ValueError:
            errors.append(f"Invalid confidence level: {fm['confidence']}")

    return errors


def load_frontmatter(path: Path) -> PageFrontmatter | None:
    """Load and parse frontmatter from a markdown file."""
    if not path.exists() or path.suffix != ".md":
        return None

    content = path.read_text(encoding="utf-8")
    fm_dict, _ = parse_frontmatter(content)
    if fm_dict is None:
        return None

    title = fm_dict.pop("title", path.stem)
    return PageFrontmatter(title=title, extra=fm_dict)


def write_frontmatter(path: Path, fm: PageFrontmatter, body: str):
    """Write a page with frontmatter atomically."""
    fm_str = yaml.dump(fm.to_dict(), default_flow_style=False, allow_unicode=True, sort_keys=False)
    content = f"---\n{fm_str}---\n\n{body}"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)
