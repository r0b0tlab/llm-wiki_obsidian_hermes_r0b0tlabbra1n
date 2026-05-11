"""Retrieval evaluation harness for brain vaults."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from r0b0tlabbra1n.index.sqlite_index import BrainIndex
from r0b0tlabbra1n.memory.retrieve import retrieve


def load_gold(path: Path) -> list[dict]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or []
    if not isinstance(data, list):
        raise ValueError("Gold file must contain a list of query specs")
    return data


def evaluate(vault: Path, gold: Path, top_k: int = 5, budget: int = 2000) -> dict:
    index = BrainIndex(vault)
    index.rebuild()
    cases = load_gold(gold)
    failures = []
    reciprocal_sum = 0.0
    top1 = 0
    top3 = 0
    total = len(cases)
    for case in cases:
        results = retrieve(index, case["query"], budget=budget)[:top_k]
        paths = [r["path"] for r in results]
        expected = case.get("expected_paths", [])
        hit_ranks = [paths.index(p) + 1 for p in expected if p in paths]
        if hit_ranks:
            best = min(hit_ranks)
            reciprocal_sum += 1.0 / best
            top1 += int(best == 1)
            top3 += int(best <= 3)
        else:
            failures.append(
                {"id": case.get("id"), "query": case["query"], "expected": expected, "got": paths}
            )
    return {
        "total": total,
        "top1_accuracy": top1 / total if total else 0.0,
        "top3_accuracy": top3 / total if total else 0.0,
        "mrr": reciprocal_sum / total if total else 0.0,
        "failures": failures,
        "passed": not failures,
    }


def format_report(report: dict, as_json: bool = False) -> str:
    if as_json:
        return json.dumps(report, indent=2, sort_keys=True)
    return (
        f"Retrieval eval: {report['total']} cases\n"
        f"top1={report['top1_accuracy']:.2%} top3={report['top3_accuracy']:.2%} "
        f"mrr={report['mrr']:.3f} failures={len(report['failures'])}"
    )
