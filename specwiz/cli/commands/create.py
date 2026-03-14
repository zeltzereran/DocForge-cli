"""Create commands: knowledge-base, product-context, and rulebooks."""

import asyncio
import sys
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress

from specwiz.cli._engine import run_stage
from specwiz.cli._paths import (
    _is_remote_url,
    get_base_path,
    get_knowledge_base_path,
    get_product_context_dir,
    get_rulebook_path,
    load_git_repo,
    load_git_repo_from_url,
    load_knowledge_base,
    load_sources,
    validate_product,
)

create_app = typer.Typer(help="Create knowledge base, product context, and rulebooks")
create_rulebook_app = typer.Typer(help="Create documentation rulebooks from example resources")
create_app.add_typer(create_rulebook_app, name="rulebook")

console = Console()


# ──────────────────────────────────────────────
# knowledge-base
# ──────────────────────────────────────────────


@create_app.command("knowledge-base")
def knowledge_base(
    sources: Optional[List[str]] = typer.Option(
        None,
        "--sources",
        help="File or directory with source materials (repeatable, at least one required)",
    ),
) -> None:
    """Build the global knowledge base from source documents."""
    if not sources:
        console.print("[red]Error: at least one --sources path is required.[/red]")
        console.print("Example: [cyan]specwiz create knowledge-base --sources ./docs[/cyan]")
        sys.exit(1)

    cwd = Path.cwd()
    base_path = get_base_path(cwd)

    sources_content = load_sources(sources, console)
    if not sources_content.strip():
        console.print(
            "[red]Error: no readable content found in the provided --sources paths.[/red]"
        )
        sys.exit(1)

    out_path = get_knowledge_base_path(cwd)

    with Progress() as progress:
        task = progress.add_task("[cyan]Building knowledge base...", total=None)
        content = asyncio.run(
            run_stage(
                "knowledge_base_generator",
                base_path,
                {
                    "source_materials": sources_content,
                    "project_context": "",
                },
                console,
            )
        )
        progress.update(task, completed=True)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")

    console.print(
        Panel(
            f"[green]✓ Knowledge base created![/green]\n" f"Output: {out_path.relative_to(cwd)}",
            title="Knowledge Base",
            expand=False,
        )
    )


# ──────────────────────────────────────────────
# product-context
# ──────────────────────────────────────────────


@create_app.command("product-context")
def product_context(
    product: str = typer.Option(..., "--product", help="Product name (must be initialized)"),
    git: Optional[str] = typer.Option(
        None,
        "--git",
        help="Path to a local git repository, or a remote URL (https/git@) to shallow-clone",
    ),
    sources: Optional[List[str]] = typer.Option(
        None,
        "--sources",
        help="Additional source files or directories (repeatable)",
    ),
) -> None:
    """Build the product context from a git repo and/or source documents."""
    if not git and not sources:
        console.print("[red]Error: at least one of --git or --sources is required.[/red]")
        console.print(
            "Example: [cyan]specwiz create product-context --product myapp --git .[/cyan]"
        )
        sys.exit(1)

    cwd = Path.cwd()
    product_path = validate_product(product, cwd)

    repository_content = ""
    if git:
        if _is_remote_url(git):
            repository_content = load_git_repo_from_url(git, console)
        else:
            repo_path = Path(git).resolve()
            if not repo_path.exists():
                console.print(f"[red]Error: git path not found: {repo_path}[/red]")
                sys.exit(1)
            console.print(f"[dim]Scanning repository: {repo_path}[/dim]")
            repository_content = load_git_repo(repo_path, console)

    supporting_documents = load_sources(sources, console) if sources else ""

    if not repository_content and not supporting_documents:
        console.print("[red]Error: no readable content found in the provided paths.[/red]")
        sys.exit(1)

    # If only --sources provided (no --git), treat them as the primary repository content
    if not repository_content:
        repository_content = supporting_documents
        supporting_documents = ""

    # Inject existing knowledge base if present (optional enrichment)
    knowledge_base = load_knowledge_base(cwd)

    out_dir = get_product_context_dir(product, cwd)

    with Progress() as progress:
        task = progress.add_task("[cyan]Building product context...", total=None)
        content = asyncio.run(
            run_stage(
                "product_context_generator",
                product_path,
                {
                    "product_name": product,
                    "repository_content": repository_content,
                    "knowledge_base": knowledge_base,
                    "supporting_documents": supporting_documents,
                },
                console,
            )
        )
        progress.update(task, completed=True)

    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "product-context.md"
    out_file.write_text(content, encoding="utf-8")

    console.print(
        Panel(
            f"[green]✓ Product context created![/green]\n"
            f"Product: [bold]{product}[/bold]\n"
            f"Output: {out_file.relative_to(cwd)}",
            title="Product Context",
            expand=False,
        )
    )


# ──────────────────────────────────────────────
# rulebook (shared logic)
# ──────────────────────────────────────────────


def _build_rulebook(
    rulebook_type: str,
    stage_name: str,
    example_key: str,
    resources: Optional[List[str]],
) -> None:
    """Shared implementation for all rulebook creation sub-commands."""
    if not resources:
        console.print("[red]Error: at least one --resources path is required.[/red]")
        console.print(
            f"Example: [cyan]specwiz create rulebook {rulebook_type} --resources ./examples[/cyan]"
        )
        sys.exit(1)

    cwd = Path.cwd()
    base_path = get_base_path(cwd)

    resources_content = load_sources(resources, console)
    out_path = get_rulebook_path(rulebook_type, cwd)

    with Progress() as progress:
        task = progress.add_task(f"[cyan]Building {rulebook_type} rulebook...", total=None)
        content = asyncio.run(
            run_stage(
                stage_name,
                base_path,
                {
                    "product_context": "",
                    example_key: resources_content,
                },
                console,
            )
        )
        progress.update(task, completed=True)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")

    console.print(
        Panel(
            f"[green]✓ Rulebook created![/green]\n"
            f"Type: {rulebook_type}\n"
            f"Output: {out_path.relative_to(cwd)}",
            title="Rulebook",
            expand=False,
        )
    )


# ──────────────────────────────────────────────
# rulebook sub-commands
# ──────────────────────────────────────────────


@create_rulebook_app.command("prd")
def rulebook_prd(
    resources: Optional[List[str]] = typer.Option(
        None,
        "--resources",
        help="Example PRD/requirement files (repeatable, at least one required)",
    ),
) -> None:
    """Create the global PRD rulebook from example requirement documents."""
    _build_rulebook("prd", "engineering_rulebook_generator", "example_requirements", resources)


@create_rulebook_app.command("user-guide")
def rulebook_user_guide(
    resources: Optional[List[str]] = typer.Option(
        None,
        "--resources",
        help="Example user guide files (repeatable, at least one required)",
    ),
) -> None:
    """Create the global user-guide rulebook from example user guide documents."""
    _build_rulebook("user-guide", "writing_rulebook_generator", "example_user_guides", resources)


@create_rulebook_app.command("release-note")
def rulebook_release_note(
    resources: Optional[List[str]] = typer.Option(
        None,
        "--resources",
        help="Example release notes files (repeatable, at least one required)",
    ),
) -> None:
    """Create the global release-note rulebook from example release notes."""
    _build_rulebook("release-note", "qa_rulebook_generator", "example_release_notes", resources)


@create_rulebook_app.command("diagram")
def rulebook_diagram(
    resources: Optional[List[str]] = typer.Option(
        None,
        "--resources",
        help="Example diagram files (repeatable, at least one required)",
    ),
) -> None:
    """Create the global diagram rulebook from example diagram files."""
    _build_rulebook("diagram", "architecture_rulebook_generator", "example_diagrams", resources)
