"""Memory retrieval and ranking — query the brain vault and build context packets."""

from __future__ import annotations

from datetime import datetime, timezone

from r0b0tlabbra1n.index.sqlite_index import BrainIndex
from r0b0tlabbra1n.models import ContextPacket, RetrievalResult

TIER_BOOST = {"hot": 0.35, "warm": 0.25, "cold": 0.05, "archive": -0.25}
CONFIDENCE_BOOST = {"high": 0.15, "medium": 0.05, "low": -0.05}
STATUS_BOOST = {
    "active": 0.05,
    "draft": -0.05,
    "stale": -0.15,
    "archived": -0.25,
    "superseded": -0.25,
}


def _recency_boost(updated: str) -> float:
    if not updated:
        return 0.0
    try:
        dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        days = (datetime.now(timezone.utc) - dt).days
    except ValueError:
        return 0.0
    if days <= 7:
        return 0.10
    if days <= 30:
        return 0.05
    if days > 180:
        return -0.10
    return 0.0


def _weighted_score(result: dict) -> float:
    return (
        float(result.get("score", 0.0))
        + TIER_BOOST.get(result.get("tier", ""), 0.0)
        + CONFIDENCE_BOOST.get(result.get("confidence", ""), 0.0)
        + STATUS_BOOST.get(result.get("status", ""), 0.0)
        + _recency_boost(result.get("updated", ""))
    )


def retrieve(
    index: BrainIndex,
    query: str,
    budget: int = 2000,
    tier_preference: list[str] | None = None,
) -> list[dict]:
    """Retrieve memory matching a query with token-budgeted weighted results."""
    if tier_preference is None:
        tier_preference = ["hot", "warm", "cold"]
    all_results: list[dict] = []
    for tier in tier_preference:
        all_results.extend(index.search(query, limit=20, tier_filter=tier))
    if not all_results:
        all_results = index.search(query, limit=20)
    seen: set[str] = set()
    deduped: list[dict] = []
    for r in all_results:
        if r["path"] in seen:
            continue
        seen.add(r["path"])
        r = dict(r)
        r["weighted_score"] = _weighted_score(r)
        deduped.append(r)
    deduped.sort(key=lambda r: (-r["weighted_score"], r["path"]))
    token_estimate = 0
    budgeted: list[dict] = []
    for r in deduped:
        est = len(r.get("snippet", "")) // 4 + len(r.get("title", "")) // 4 + 24
        if token_estimate + est > budget:
            break
        token_estimate += est
        budgeted.append(r)
    return budgeted


def build_context_packet(results: list[dict], query: str, budget: int) -> ContextPacket:
    retrieval_results = [
        RetrievalResult(
            path=r["path"],
            snippet=r.get("snippet", ""),
            score=r.get("weighted_score", r.get("score", 0.0)),
        )
        for r in results
    ]
    tokens_used = sum(len(r.snippet) // 4 + len(r.path) // 4 + 10 for r in retrieval_results)
    return ContextPacket(
        results=retrieval_results,
        token_budget=budget,
        tokens_used=tokens_used,
        query=query,
    )


def format_context_packet(packet: ContextPacket) -> str:
    lines = [
        "<memory-context>",
        f"<!-- query: {packet.query} -->",
        f"<!-- token_budget: {packet.token_budget}, used: {packet.tokens_used} -->",
        "",
    ]
    for r in packet.results:
        lines.append(f"**{r.path}** (score={r.score:.3f})")
        lines.append(f"  {r.snippet}")
        lines.append("")
    lines.append("</memory-context>")
    return "\n".join(lines)
