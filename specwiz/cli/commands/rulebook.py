"""Rulebook management commands."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from specwiz.cli._paths import get_rulebooks_dir

rulebook_app = typer.Typer(help="Manage documentation rulebooks")
console = Console()

_RULEBOOK_TYPES = ["prd", "user-guide", "release-note", "diagram"]


@rulebook_app.command()
def list() -> None:
    """List all global rulebooks."""
    cwd = Path.cwd()
    rulebooks_dir = get_rulebooks_dir(cwd)

    if not rulebooks_dir.exists():
        console.print("[yellow]No rulebooks found.[/yellow]")
        console.print("Run: [cyan]specwiz create rulebook prd --resources ./examples[/cyan]")
        return

    table = Table(title="Global Rulebooks")
    table.add_column("Type", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Path", style="green")

    for rb_type in _RULEBOOK_TYPES:
        rb_file = rulebooks_dir / f"{rb_type}-rulebook.md"
        if rb_file.exists():
            try:
                rel = str(rb_file.relative_to(cwd))
            except ValueError:
                rel = str(rb_file)
            table.add_row(rb_type, "✓", rel)
        else:
            table.add_row(rb_type, "✗ missing", "—")

    console.print(table)
