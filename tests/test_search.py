"""Tests for search/index functionality."""

import tempfile
from pathlib import Path

from r0b0tlabbra1n.index.sqlite_index import BrainIndex
from r0b0tlabbra1n.vault.initialize import init_vault


def test_index_rebuild_and_search():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp) / "test-brain"
        init_vault(vault)

        # Add a searchable page
        page = vault / "projects" / "vllm-deployment.md"
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text("""---
title: vLLM Deployment Guide
type: project
status: active
tier: warm
provenance: test
---

# vLLM Deployment

Deploy vLLM with Docker and Kubernetes for high-throughput LLM serving.
Uses FlashInfer attention backend and GPU memory optimization.
""")

        index = BrainIndex(vault)
        count = index.rebuild()
        assert count > 0, "Should have indexed at least the vllm page"

        # Search - use single-word query for FTS5 compatibility
        results = index.search("deployment", limit=5)
        assert len(results) >= 1
        assert any("vLLM" in r["title"] for r in results)

        # Tier-filtered search
        warm_results = index.search("deploy", limit=5, tier_filter="warm")
        assert len(warm_results) >= 1

        # Non-matching search
        empty = index.search("xylophone nonexistent term", limit=5)
        assert len(empty) == 0


def test_index_search_all_tiers():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp) / "test-brain"
        init_vault(vault)

        index = BrainIndex(vault)
        index.rebuild()

        results = index.search_all_tiers("brain", limit=5)
        # Init creates warm-tier pages; cold/archive may be empty
        assert "warm" in results
        # At least one tier has results
        assert any(len(v) > 0 for v in results.values())
