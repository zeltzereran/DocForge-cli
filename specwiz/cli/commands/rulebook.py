"""Rulebook management commands."""

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.table import Table

from specwiz.adapters import (
    AnthropicAdapter,
    BlinkerEventBusAdapter,
    LocalStorageAdapter,
)
from specwiz.cli.commands.generate import _EXAMPLE_INPUT_KEYS, _load_sources
from specwiz.core import SpecWizPipelineEngine
from specwiz.core.interfaces.engine import ExecutionContext
from specwiz.core.managers import CompositeConfigAdapter

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
    category: str = typer.Option(
        ..., help="Rulebook category (engineering, writing, architecture, qa)"
    ),
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

    console.print(
        Panel(
            f"[green]✓ Rulebook created![/green]\n"
            f"Name: [bold]{name}[/bold]\n"
            f"Category: {category}\n"
            f"Path: {rulebook_file.relative_to(project_root)}",
            title="Rulebook Created",
            expand=False,
        )
    )


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

async def _execute_rulebook_generation(
    project_root: Path,
    config: CompositeConfigAdapter,
    product_name: str,
    source_paths: List[str],
) -> bool:
    """Execute rulebook generation pipeline."""
    try:
        storage = LocalStorageAdapter(
            base_path=project_root / config.get("storage_path", ".specwiz")
        )
        event_bus = BlinkerEventBusAdapter()

        try:
            llm = AnthropicAdapter()
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            return False

        engine = SpecWizPipelineEngine(
            storage=storage,
            llm=llm,
            event_bus=event_bus,
        )
        await engine.initialize()

        inputs: Dict[str, Any] = {"product_name": product_name}

        # Sources are examples — inject into example vars and source_materials
        if source_paths:
            sources_content = _load_sources(source_paths)
            if sources_content:
                for key in _EXAMPLE_INPUT_KEYS:
                    inputs.setdefault(key, sources_content)
                inputs.setdefault("source_materials", sources_content)

        context = ExecutionContext(
            project_root=str(project_root),
            project_name=config.get("project_name", product_name),
            stage_name="start",
            stage_number=0,
            inputs=inputs,
        )

        with Progress() as progress:
            task = progress.add_task("[cyan]Generating rulebooks...", total=None)
            result = await engine.execute_pipeline(
                start_stage="knowledge_base_generator",
                context=context,
            )
            progress.update(task, completed=True)

        if result.success:
            console.print(
                Panel(
                    f"[green]\u2713 Rulebooks generated successfully![/green]\n"
                    f"Artifacts: {len(result.artifacts)}\n"
                    f"Output: {config.get('storage_path')}",
                    title="Rulebook Generation Complete",
                    expand=False,
                )
            )
            return True
        else:
            console.print(f"[red]Error: {result.error}[/red]")
            return False

    except Exception as e:
        console.print(f"[red]Rulebook generation failed: {e}[/red]")
        return False


@rulebook_app.command()
def generate(
    product: str = typer.Option(..., help="Product name"),
    repo: str = typer.Option(".", help="Repository path"),
    sources: Optional[List[str]] = typer.Option(
        None, "--sources", help="Example documents to derive standards from (repeatable)"
    ),
) -> None:
    """Generate rulebooks using AI from example documents."""
    project_root = Path(repo).resolve()
    config = CompositeConfigAdapter(project_root=project_root)

    success = asyncio.run(
        _execute_rulebook_generation(
            project_root,
            config,
            product,
            sources or [],
        )
    )

    sys.exit(0 if success else 1)
