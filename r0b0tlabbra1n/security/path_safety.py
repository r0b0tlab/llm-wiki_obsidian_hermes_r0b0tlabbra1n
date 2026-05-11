"""Filesystem safety helpers."""

from __future__ import annotations

from pathlib import Path


def require_within_vault(vault: Path, target: Path) -> Path:
    vault_r = Path(vault).resolve()
    target_r = Path(target).resolve()
    if not target_r.is_relative_to(vault_r):
        raise ValueError(f"Path escapes vault: {target}")
    return target_r
