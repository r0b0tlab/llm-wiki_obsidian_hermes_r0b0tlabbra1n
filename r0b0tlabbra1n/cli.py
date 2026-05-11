"""CLI entry point for r0b0tlabbra1n — the brain command."""

import sys
from pathlib import Path

import click

from r0b0tlabbra1n import __version__


@click.group()
@click.version_option(__version__, prog_name="brain")
def main():
    """r0b0tlabbra1n — Filesystem-first LLM-Wiki + Obsidian + Hermes memory system."""
    pass


@main.command()
@click.option("--vault", "-v", type=click.Path(path_type=Path), required=True,
              help="Path to the brain vault directory")
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
@click.option("--vault", "-v", type=click.Path(exists=True, path_type=Path), required=True,
              help="Path to the brain vault directory")
def lint(vault: Path):
    """Lint a brain vault for broken links, invalid frontmatter, and secrets."""
    from r0b0tlabbra1n.vault.lint import lint_vault
    issues = lint_vault(vault)
    if issues:
        for issue in issues:
            click.echo(f"{issue['level']}: {issue['path']}: {issue['message']}", err=True)
        sys.exit(1)
    else:
        click.echo("Vault is clean.")


@main.command()
@click.argument("query")
@click.option("--vault", "-v", type=click.Path(exists=True, path_type=Path), required=True,
              help="Path to the brain vault directory")
@click.option("--budget", "-b", type=int, default=2000,
              help="Token budget for context packet (default: 2000)")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def search(vault: Path, query: str, budget: int, json_output: bool):
    """Search the brain vault."""
    from r0b0tlabbra1n.index.sqlite_index import BrainIndex
    from r0b0tlabbra1n.memory.retrieve import retrieve
    index = BrainIndex(vault)
    results = retrieve(index, query, budget=budget)
    if json_output:
        import json
        click.echo(json.dumps(results, indent=2))
    else:
        for r in results:
            click.echo(f"  {r['path']} (score={r.get('score', 'N/A')})")


@main.command()
@click.option("--vault", "-v", type=click.Path(exists=True, path_type=Path), required=True,
              help="Path to the brain vault directory")
def build_index(vault: Path):
    """Build or rebuild the FTS5 search index."""
    from r0b0tlabbra1n.index.sqlite_index import BrainIndex
    index = BrainIndex(vault)
    count = index.rebuild()
    click.echo(f"Index rebuilt: {count} pages indexed.")


@main.command()
@click.option("--hermes-home", type=click.Path(exists=True, path_type=Path),
              default=Path.home() / ".hermes",
              help="Path to Hermes home directory (default: ~/.hermes)")
@click.option("--vault", "-v", type=click.Path(path_type=Path), required=True,
              help="Path to the brain vault for output")
@click.option("--since", type=str, default=None,
              help="Only ingest sessions since this cursor (ISO timestamp or session ID)")
def ingest_sessions(hermes_home: Path, vault: Path, since: str | None):
    """Ingest Hermes sessions from state.db into the brain vault."""
    from r0b0tlabbra1n.ingest.hermes_sessions import ingest
    state_db = hermes_home / "state.db"
    if not state_db.exists():
        click.echo(f"Error: {state_db} not found", err=True)
        sys.exit(1)
    count = ingest(state_db, vault, since_cursor=since)
    click.echo(f"Ingested {count} sessions.")


if __name__ == "__main__":
    main()
