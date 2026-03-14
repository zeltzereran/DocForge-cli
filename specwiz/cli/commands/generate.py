"""Generate commands: prd, user-guide, release-notes."""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress

from specwiz.cli._engine import run_stage
from specwiz.cli._paths import (
    get_generated_dir,
    load_knowledge_base,
    load_sources,
    validate_product,
    validate_product_context,
    validate_rulebook,
)

generate_app = typer.Typer(help="Generate documents")
console = Console()


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


# ──────────────────────────────────────────────
# generate prd
# ──────────────────────────────────────────────


@generate_app.command("prd")
def prd(
    product: str = typer.Option(..., "--product", help="Initialized product name"),
    feature: str = typer.Option(..., "--feature", help="Feature to document"),
    resources: Optional[List[str]] = typer.Option(
        None,
        "--resources",
        help="Additional context files (feature specs, research, etc.) — repeatable",
    ),
) -> None:
    """Generate a Product Requirements Document for a feature."""
    cwd = Path.cwd()
    product_path = validate_product(product, cwd)
    product_context = validate_product_context(product, cwd)
    requirement_rulebook = validate_rulebook("prd", cwd)
    knowledge_base = load_knowledge_base(cwd)

    resources_content = load_sources(resources, console) if resources else ""

    out_dir = get_generated_dir(product, "prd", cwd)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{_timestamp()}-prd.md"

    with Progress() as progress:
        task = progress.add_task("[cyan]Generating PRD...", total=None)
        content = asyncio.run(
            run_stage(
                "prd_generator",
                product_path,
                {
                    "product_name": product,
                    "feature_name": feature,
                    "feature_goal": resources_content,
                    "product_context": product_context,
                    "knowledge_base": knowledge_base,
                    "requirement_rulebook": requirement_rulebook,
                },
                console,
            )
        )
        progress.update(task, completed=True)

    out_file.write_text(content, encoding="utf-8")
    console.print(
        Panel(
            f"[green]✓ PRD generated![/green]\n"
            f"Product: [bold]{product}[/bold]\n"
            f"Feature: {feature}\n"
            f"Output: {out_file.relative_to(cwd)}",
            title="PRD Generated",
            expand=False,
        )
    )


# ──────────────────────────────────────────────
# generate user-guide
# ──────────────────────────────────────────────


@generate_app.command("user-guide")
def user_guide(
    product: str = typer.Option(..., "--product", help="Initialized product name"),
    feature: Optional[str] = typer.Option(
        None,
        "--feature",
        help="Specific feature or workflow to document (omit to document the whole product)",
    ),
    audience: str = typer.Option("end-user", "--audience", help="Target audience"),
    resources: Optional[List[str]] = typer.Option(
        None,
        "--resources",
        help="Additional context files (API specs, mockups, etc.) — repeatable",
    ),
) -> None:
    """Generate a user guide for a product or specific feature."""
    cwd = Path.cwd()
    product_path = validate_product(product, cwd)
    product_context = validate_product_context(product, cwd)
    user_guide_rulebook = validate_rulebook("user-guide", cwd)
    knowledge_base = load_knowledge_base(cwd)

    resources_content = load_sources(resources, console) if resources else ""
    feature_or_workflow = feature or f"{product} — complete product guide"

    out_dir = get_generated_dir(product, "user-guide", cwd)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{_timestamp()}-user-guide.md"

    with Progress() as progress:
        task = progress.add_task("[cyan]Generating user guide...", total=None)
        content = asyncio.run(
            run_stage(
                "user_guide_generator",
                product_path,
                {
                    "product_name": product,
                    "feature_or_workflow": feature_or_workflow,
                    "target_audience": audience,
                    "product_context": product_context,
                    "knowledge_base": knowledge_base,
                    "user_guide_rulebook": user_guide_rulebook,
                    "api_specs": resources_content,
                },
                console,
            )
        )
        progress.update(task, completed=True)

    out_file.write_text(content, encoding="utf-8")
    console.print(
        Panel(
            f"[green]✓ User guide generated![/green]\n"
            f"Product: [bold]{product}[/bold]\n"
            f"Scope: {feature_or_workflow}\n"
            f"Audience: {audience}\n"
            f"Output: {out_file.relative_to(cwd)}",
            title="User Guide Generated",
            expand=False,
        )
    )


# ──────────────────────────────────────────────
# generate release-notes
# ──────────────────────────────────────────────


@generate_app.command("release-notes")
def release_notes(
    product: str = typer.Option(..., "--product", help="Initialized product name"),
    release_version: str = typer.Option(
        "", "--release-version", help="Release version string (e.g. v2.1.0)"
    ),
    resources: Optional[List[str]] = typer.Option(
        None,
        "--resources",
        help="Development artifacts: commits, PRs, tickets, changelogs (repeatable, at least one required)",
    ),
) -> None:
    """Generate release notes from development artifacts."""
    if not resources:
        console.print("[red]Error: at least one --resources path is required.[/red]")
        console.print(
            "Example: [cyan]specwiz generate release-notes "
            "--product myapp --resources ./changelog.txt[/cyan]"
        )
        sys.exit(1)

    cwd = Path.cwd()
    product_path = validate_product(product, cwd)
    product_context = validate_product_context(product, cwd)
    release_notes_rulebook = validate_rulebook("release-note", cwd)
    knowledge_base = load_knowledge_base(cwd)

    resources_content = load_sources(resources, console)
    release_date = datetime.now().strftime("%B %d, %Y")

    out_dir = get_generated_dir(product, "release-notes", cwd)
    out_dir.mkdir(parents=True, exist_ok=True)
    label = release_version.lstrip("v") if release_version else _timestamp()
    out_file = out_dir / f"{label}-release-notes.md"

    with Progress() as progress:
        task = progress.add_task("[cyan]Generating release notes...", total=None)
        content = asyncio.run(
            run_stage(
                "release_notes_generator",
                product_path,
                {
                    "product_name": product,
                    "release_version": release_version,
                    "release_date": release_date,
                    "product_context": product_context,
                    "knowledge_base": knowledge_base,
                    "release_notes_rulebook": release_notes_rulebook,
                    "commit_messages": resources_content,
                    "feature_specs": resources_content,
                },
                console,
            )
        )
        progress.update(task, completed=True)

    out_file.write_text(content, encoding="utf-8")
    console.print(
        Panel(
            f"[green]✓ Release notes generated![/green]\n"
            f"Product: [bold]{product}[/bold]\n"
            f"Version: {release_version or 'unversioned'}\n"
            f"Output: {out_file.relative_to(cwd)}",
            title="Release Notes Generated",
            expand=False,
        )
    )
