"""Persistent wikilink graph and backlinks."""

from __future__ import annotations

import json
from pathlib import Path

from r0b0tlabbra1n.vault.links import extract_wikilinks, normalize_wikilink_target


def build_graph(vault_path: Path) -> dict:
    vault_path = Path(vault_path)
    graph: dict[str, list[str]] = {}
    backlinks: dict[str, list[str]] = {}
    for md_file in sorted(vault_path.rglob("*.md")):
        rel = md_file.relative_to(vault_path)
        rel_s = str(rel)
        if rel_s.startswith("_meta/") or rel_s.startswith("raw/"):
            continue
        try:
            content = md_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        source = rel_s.removesuffix(".md")
        targets = []
        for link in extract_wikilinks(content):
            target = normalize_wikilink_target(link).removesuffix(".md")
            targets.append(target)
            backlinks.setdefault(target, []).append(source)
        graph[source] = sorted(set(targets))
    backlinks = {k: sorted(set(v)) for k, v in backlinks.items()}
    meta = vault_path / "_meta"
    meta.mkdir(parents=True, exist_ok=True)
    (meta / "link-graph.json").write_text(
        json.dumps(graph, indent=2, sort_keys=True), encoding="utf-8"
    )
    (meta / "backlinks.json").write_text(
        json.dumps(backlinks, indent=2, sort_keys=True), encoding="utf-8"
    )
    return {"graph": graph, "backlinks": backlinks}


def load_backlinks(vault_path: Path) -> dict[str, list[str]]:
    path = Path(vault_path) / "_meta" / "backlinks.json"
    if not path.exists():
        return build_graph(vault_path)["backlinks"]
    return json.loads(path.read_text(encoding="utf-8"))
