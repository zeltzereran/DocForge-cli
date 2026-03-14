"""Rulebook management commands."""

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

rulebook_app = typer.Typer(help="Manage documentation rulebooks")
console = Console()


@rulebook_app.command()
def list(
    repo: str = typer.Option(".", help="Repository path"),
) -> None:
    """List all available rulebooks."""
    project_root = Path(repo).resolve()
    rulebooks_dir = project_root / "rulebooks"
    
    if not rulebooks_dir.exists():
        console.print("[yellow]No rulebooks directory found[/yellow]")
        return
    
    table = Table(title="Available Rulebooks")
    table.add_column("Type", style="cyan")
    table.add_column("Version", style="magenta")
    table.add_column("Path", style="green")
    
    for rulebook_dir in rulebooks_dir.iterdir():
        if rulebook_dir.is_dir():
            rulebook_path = rulebook_dir / f"{rulebook_dir.name}-rulebook.md"
            if rulebook_path.exists():
                # Try to extract version from file
                version = "1.0"
                table.add_row(
                    rulebook_dir.name,
                    version,
                    str(rulebook_path.relative_to(project_root)),
                )
    
    console.print(table)


@rulebook_app.command()
def create(
    name: str = typer.Option(..., help="Rulebook name"),
    category: str = typer.Option(..., help="Rulebook category (engineering, writing, architecture, qa)"),
    repo: str = typer.Option(".", help="Repository path"),
) -> None:
    """Create a new rulebook."""
    project_root = Path(repo).resolve()
    rulebooks_dir = project_root / "rulebooks" / category
    rulebooks_dir.mkdir(parents=True, exist_ok=True)
    
    rulebook_file = rulebooks_dir / f"{name}-rulebook.md"
    
    # Template content
    template = f"""# {name.replace('_', ' ').title()} Rulebook

## Purpose

This rulebook defines the organizational standards for {name.replace('_', ' ')}.

## Table of Contents

1. [Principles](#principles)
2. [Standards](#standards)
3. [Best Practices](#best-practices)
4. [References](#references)

## Principles

Define core principles that guide {name.replace('_', ' ')}.

## Standards

Define specific standards and requirements.

## Best Practices

Document proven practices and patterns.

## References

- Source documents
- External references
- Related rulebooks
"""
    
    rulebook_file.write_text(template)
    
    console.print(Panel(
        f"[green]✓ Rulebook created![/green]\n"
        f"Name: [bold]{name}[/bold]\n"
        f"Category: {category}\n"
        f"Path: {rulebook_file.relative_to(project_root)}",
        title="Rulebook Created",
        expand=False,
    ))


@rulebook_app.command()
def validate(
    repo: str = typer.Option(".", help="Repository path"),
) -> None:
    """Validate all rulebooks."""
    project_root = Path(repo).resolve()
    rulebooks_dir = project_root / "rulebooks"
    
    if not rulebooks_dir.exists():
        console.print("[yellow]No rulebooks directory found[/yellow]")
        return
    
    console.print("[cyan]Validating rulebooks...[/cyan]")
    
    errors = []
    count = 0
    
    for rulebook_file in rulebooks_dir.rglob("*-rulebook.md"):
        count += 1
        content = rulebook_file.read_text()
        
        # Basic validation
        if not content.strip().startswith("#"):
            errors.append(f"{rulebook_file}: Missing title")
        
        if "## Purpose" not in content:
            errors.append(f"{rulebook_file}: Missing Purpose section")
    
    if errors:
        console.print(f"[red]Found {len(errors)} issues:[/red]")
        for error in errors:
            console.print(f"  • {error}")
        sys.exit(1)
    else:
        console.print(f"[green]✓ All {count} rulebooks are valid![/green]")