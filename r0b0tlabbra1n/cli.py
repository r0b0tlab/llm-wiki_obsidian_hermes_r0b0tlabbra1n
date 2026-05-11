"""CLI entry point for r0b0tlabbra1n — the brain command."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from r0b0tlabbra1n import __version__


@click.group()
@click.version_option(__version__, prog_name="brain")
def main():
    """r0b0tlabbra1n — Filesystem-first LLM-Wiki + Obsidian + Hermes memory system."""


@main.command()
@click.option("--vault", "-v", type=click.Path(path_type=Path), required=True, help="Path to vault")
@click.option("--force", is_flag=True, help="Overwrite existing files")
def init(vault: Path, force: bool):
    """Initialize a new brain vault with templates and structure."""
    from r0b0tlabbra1n.vault.initialize import init_vault

    try:
        init_vault(vault, force=force)
        click.echo(f"Brain vault initialized at {vault}")
    except FileExistsError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo("Use --force to overwrite existing files.", err=True)
        sys.exit(1)


@main.command()
@click.option("--vault", "-v", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--strict", is_flag=True, help="Fail on WARNING as well as ERROR")
def lint(vault: Path, strict: bool):
    """Lint a brain vault for broken links, invalid frontmatter, and secrets."""
    from r0b0tlabbra1n.vault.lint import lint_vault

    issues = lint_vault(vault)
    for issue in issues:
        stream = sys.stderr if issue["level"] in {"ERROR", "WARNING"} else sys.stdout
        click.echo(f"{issue['level']}: {issue['path']}: {issue['message']}", file=stream)
    fatal_levels = {"ERROR", "WARNING"} if strict else {"ERROR"}
    if any(i["level"] in fatal_levels for i in issues):
        sys.exit(1)
    if not issues:
        click.echo("Vault is clean.")


@main.command()
@click.argument("query")
@click.option("--vault", "-v", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--budget", "-b", type=int, default=2000, help="Token budget for context packet")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.option("--context", "context_output", is_flag=True, help="Output agent context packet")
def search(vault: Path, query: str, budget: int, json_output: bool, context_output: bool):
    """Search the brain vault."""
    from r0b0tlabbra1n.index.sqlite_index import BrainIndex
    from r0b0tlabbra1n.memory.retrieve import build_context_packet, format_context_packet, retrieve

    index = BrainIndex(vault)
    results = retrieve(index, query, budget=budget)
    if context_output:
        click.echo(format_context_packet(build_context_packet(results, query, budget)))
    elif json_output:
        click.echo(json.dumps(results, indent=2, sort_keys=True))
    else:
        for r in results:
            click.echo(f"  {r['path']} (score={r.get('weighted_score', r.get('score', 0.0)):.3f})")


@main.command(name="build-index")
@click.option("--vault", "-v", type=click.Path(exists=True, path_type=Path), required=True)
def build_index(vault: Path):
    """Build or rebuild the FTS5 search index."""
    from r0b0tlabbra1n.index.graph_index import build_graph
    from r0b0tlabbra1n.index.sqlite_index import BrainIndex

    index = BrainIndex(vault)
    count = index.rebuild()
    build_graph(vault)
    click.echo(f"Index rebuilt: {count} pages indexed.")


@main.command(name="ingest-sessions")
@click.option(
    "--hermes-home", type=click.Path(exists=True, path_type=Path), default=Path.home() / ".hermes"
)
@click.option("--vault", "-v", type=click.Path(path_type=Path), required=True)
@click.option("--since", type=str, default=None, help="Only ingest sessions since this cursor")
@click.option("--include-transcripts", is_flag=True, help="Write raw JSON transcripts under raw/")
def ingest_sessions(hermes_home: Path, vault: Path, since: str | None, include_transcripts: bool):
    """Ingest Hermes sessions from state.db into the brain vault."""
    from r0b0tlabbra1n.ingest.hermes_sessions import ingest

    state_db = hermes_home / "state.db"
    if not state_db.exists():
        click.echo(f"Error: {state_db} not found", err=True)
        sys.exit(1)
    count = ingest(state_db, vault, since_cursor=since, include_transcripts=include_transcripts)
    click.echo(f"Ingested {count} sessions.")


@main.command(name="drift-check")
@click.option("--vault", "-v", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--json", "json_output", is_flag=True)
def drift_check(vault: Path, json_output: bool):
    """Detect pages changed since the last index/hash manifest."""
    from r0b0tlabbra1n.vault.hashes import check_drift

    report = check_drift(vault)
    if json_output:
        click.echo(json.dumps(report, indent=2, sort_keys=True))
    elif report["clean"]:
        click.echo("No drift detected.")
    else:
        click.echo("Drift detected:")
        for key in ("added", "removed", "changed"):
            for path in report[key]:
                click.echo(f"  {key}: {path}")
    if not report["clean"]:
        sys.exit(1)


@main.command(name="graph")
@click.option("--vault", "-v", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--json", "json_output", is_flag=True)
def graph(vault: Path, json_output: bool):
    """Build/export link graph and backlinks."""
    from r0b0tlabbra1n.index.graph_index import build_graph

    data = build_graph(vault)
    if json_output:
        click.echo(json.dumps(data, indent=2, sort_keys=True))
    else:
        click.echo(f"Graph: {len(data['graph'])} pages, {len(data['backlinks'])} backlink targets")


@main.command(name="backlinks")
@click.argument("slug")
@click.option("--vault", "-v", type=click.Path(exists=True, path_type=Path), required=True)
def backlinks(slug: str, vault: Path):
    """Show backlinks for a slug."""
    from r0b0tlabbra1n.index.graph_index import load_backlinks

    for source in load_backlinks(vault).get(slug.removesuffix(".md"), []):
        click.echo(source)


@main.command(name="eval")
@click.option("--vault", "-v", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--gold", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--json", "json_output", is_flag=True)
def eval_cmd(vault: Path, gold: Path, json_output: bool):
    """Run retrieval evals against a gold query file."""
    from r0b0tlabbra1n.evals.retrieval_eval import evaluate, format_report

    report = evaluate(vault, gold)
    click.echo(format_report(report, as_json=json_output))
    if report["failures"]:
        sys.exit(1)


@main.command(name="promote-candidates")
@click.option("--vault", "-v", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--json", "json_output", is_flag=True)
def promote_candidates(vault: Path, json_output: bool):
    """List repeated session facts that may deserve promotion."""
    from r0b0tlabbra1n.memory.promote import promotion_candidates

    candidates = promotion_candidates(vault)
    if json_output:
        click.echo(json.dumps(candidates, indent=2, sort_keys=True))
    else:
        for c in candidates:
            click.echo(f"{c['occurrences']}x {c['content']}")


if __name__ == "__main__":
    main()
