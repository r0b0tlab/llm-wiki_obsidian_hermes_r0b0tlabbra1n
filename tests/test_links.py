"""Tests for wikilinks extraction and validation."""

import tempfile
from pathlib import Path

from r0b0tlabbra1n.vault.links import (
    extract_wikilinks,
    find_broken_links,
    find_orphans,
    build_link_graph,
    get_backlinks,
)


def test_extract_wikilinks():
    content = """
    See [[project-alpha]] for details.
    Also check [[concepts/memory-systems]] and [[entity-name|display text]].
    An alias: [[path/to/page#heading]].
    """
    links = extract_wikilinks(content)
    assert "project-alpha" in links
    assert "concepts/memory-systems" in links
    assert "entity-name" in links
    assert "path/to/page" in links


def test_extract_wikilinks_empty():
    assert extract_wikilinks("No links here.") == []


def test_find_broken_links():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        # Create one valid target
        (vault / "valid-target.md").write_text("target page")

        content = "See [[valid-target]] and [[missing-target]]."
        broken = find_broken_links(vault, content)
        assert "missing-target" in broken
        assert "valid-target" not in broken


def test_build_link_graph():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "a.md").write_text("References [[b]] and [[c]].")
        (vault / "b.md").write_text("References [[c]].")
        (vault / "c.md").write_text("No outgoing links.")

        graph = build_link_graph(vault)
        assert "a" in graph
        assert "b" in graph["a"]
        assert "c" in graph["a"]
        assert "c" in graph["b"]


def test_get_backlinks():
    graph = {
        "a": ["b", "c"],
        "b": ["c"],
        "c": [],
    }
    backlinks = get_backlinks(graph, "c")
    assert "a" in backlinks
    assert "b" in backlinks
    assert len(backlinks) == 2
