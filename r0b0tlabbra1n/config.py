"""Configuration for r0b0tlabbra1n."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class BrainConfig:
    """Configuration for a brain instance."""

    # Paths
    vault_path: Path = Path("vault")
    raw_path: Path = Path("raw")
    index_path: Path = Path("_meta")

    # Memory policy
    hot_memory_max_chars: int = 2200  # Hermes MEMORY.md limit
    user_profile_max_chars: int = 1375  # Hermes USER.md limit
    context_packet_token_budget: int = 2000

    # Retrieval
    fts_weight: float = 1.0
    boost_compiled_truth: float = 1.5
    boost_backlinks: float = 1.2

    # Ingestion
    session_ingest_batch_size: int = 50

    # Security
    secret_scan_enabled: bool = True
    prompt_injection_scan_enabled: bool = True

    # Optional features
    embeddings_enabled: bool = False
    graph_enabled: bool = False

    def with_vault(self, vault_path: Path) -> BrainConfig:
        """Return a copy scoped to a specific vault."""
        return BrainConfig(
            vault_path=vault_path,
            raw_path=vault_path / "raw",
            index_path=vault_path / "_meta",
            hot_memory_max_chars=self.hot_memory_max_chars,
            user_profile_max_chars=self.user_profile_max_chars,
            context_packet_token_budget=self.context_packet_token_budget,
            fts_weight=self.fts_weight,
            boost_compiled_truth=self.boost_compiled_truth,
            boost_backlinks=self.boost_backlinks,
            session_ingest_batch_size=self.session_ingest_batch_size,
            secret_scan_enabled=self.secret_scan_enabled,
            prompt_injection_scan_enabled=self.prompt_injection_scan_enabled,
            embeddings_enabled=self.embeddings_enabled,
            graph_enabled=self.graph_enabled,
        )


def load_config(path: Path | None = None) -> BrainConfig:
    """Load configuration from a brain vault's _meta/config.yaml or defaults."""
    if path is None:
        return BrainConfig()

    config_path = path / "_meta" / "config.yaml"
    if config_path.exists():
        import yaml
        data = yaml.safe_load(config_path.read_text()) or {}
        return BrainConfig(**{k: v for k, v in data.items() if hasattr(BrainConfig, k)})

    return BrainConfig()
