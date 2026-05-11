"""Memory retrieval and ranking — query the brain vault and build context packets."""

from __future__ import annotations

from r0b0tlabbra1n.index.sqlite_index import BrainIndex
from r0b0tlabbra1n.models import ContextPacket, RetrievalResult


def retrieve(
    index: BrainIndex,
    query: str,
    budget: int = 2000,
    tier_preference: list[str] | None = None,
) -> list[dict]:
    """Retrieve memory matching a query with token-budgeted results.

    Args:
        index: The brain index to search
        query: Search query
        budget: Max estimated tokens for context packet
        tier_preference: Preferred tiers in order (default: warm first, then cold)

    Returns:
        List of result dicts with path, title, snippet, score, tier
    """
    if tier_preference is None:
        tier_preference = ["warm", "cold"]

    all_results: list[dict] = []
    for tier in tier_preference:
        tier_results = index.search(query, limit=10, tier_filter=tier)
        all_results.extend(tier_results)

    # Deduplicate by path
    seen: set[str] = set()
    deduped: list[dict] = []
    for r in all_results:
        if r["path"] not in seen:
            seen.add(r["path"])
            deduped.append(r)

    # Budget-aware truncation (rough estimate: 4 chars ≈ 1 token for English)
    token_estimate = 0
    budgeted: list[dict] = []
    for r in deduped:
        snippet_tokens = len(r.get("snippet", "")) // 4
        title_tokens = len(r.get("title", "")) // 4
        est = snippet_tokens + title_tokens + 20  # overhead per result
        if token_estimate + est > budget:
            break
        token_estimate += est
        budgeted.append(r)

    return budgeted


def build_context_packet(results: list[dict], query: str, budget: int) -> ContextPacket:
    """Build a ContextPacket from retrieval results."""
    retrieval_results = [
        RetrievalResult(
            path=r["path"],
            snippet=r.get("snippet", ""),
            score=r.get("score", 0.0),
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
    """Format a ContextPacket as text for injection into an agent prompt."""
    lines = [
        "<memory-context>",
        f"<!-- query: {packet.query} -->",
        f"<!-- token_budget: {packet.token_budget}, used: {packet.tokens_used} -->",
        "",
    ]
    for r in packet.results:
        lines.append(f"**{r.path}** (score={r.score:.2f})")
        lines.append(f"  {r.snippet}")
        lines.append("")

    lines.append("</memory-context>")
    return "\n".join(lines)
