"""Promotion candidate generation from session and memory pages."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from r0b0tlabbra1n.memory.extract import extract_facts


def promotion_candidates(vault_path: Path, min_occurrences: int = 2) -> list[dict]:
    counter: Counter[str] = Counter()
    sources: dict[str, list[str]] = {}
    for md in sorted(Path(vault_path).glob("sessions/**/*.md")):
        try:
            text = md.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for item in extract_facts(text, source=str(md.relative_to(vault_path))):
            key = item.content.strip()
            counter[key] += 1
            sources.setdefault(key, []).append(str(md.relative_to(vault_path)))
    return [
        {"content": k, "occurrences": v, "sources": sources[k]}
        for k, v in counter.most_common()
        if v >= min_occurrences
    ]
