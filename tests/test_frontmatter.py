"""Tests for frontmatter parsing and validation."""

from r0b0tlabbra1n.models import PageFrontmatter
from r0b0tlabbra1n.vault.frontmatter import (
    parse_frontmatter,
    validate_frontmatter,
    write_frontmatter,
)


def test_parse_valid_frontmatter():
    content = """---
title: Test Page
type: concept
status: active
---

Body content here.
"""
    fm, body = parse_frontmatter(content)
    assert fm is not None
    assert fm["title"] == "Test Page"
    assert fm["type"] == "concept"
    assert "Body content here." in body


def test_parse_no_frontmatter():
    content = "Just plain markdown."
    fm, body = parse_frontmatter(content)
    assert fm is None
    assert body == content


def test_parse_unclosed_frontmatter():
    content = """---
title: Test
Body after unclosed.
"""
    fm, body = parse_frontmatter(content)
    assert fm is None


def test_validate_valid_frontmatter():
    fm = {"title": "Test", "type": "concept", "status": "active"}
    errors = validate_frontmatter(fm)
    assert errors == []


def test_validate_missing_title():
    fm = {"type": "concept"}
    errors = validate_frontmatter(fm)
    assert len(errors) >= 1
    assert any("title" in e.lower() for e in errors)


def test_validate_invalid_type():
    fm = {"title": "Test", "type": "bogus"}
    errors = validate_frontmatter(fm)
    assert len(errors) >= 1
    assert any("type" in e.lower() for e in errors)


def test_write_and_roundtrip():
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "test.md"
        fm = PageFrontmatter(title="Roundtrip Test")
        write_frontmatter(path, fm, "Body content.")

        content = path.read_text()
        parsed_fm, body = parse_frontmatter(content)
        assert parsed_fm is not None
        assert parsed_fm["title"] == "Roundtrip Test"
        assert "Body content." in body
