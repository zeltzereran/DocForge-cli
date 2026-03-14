"""Generate commands for creating documentation."""

import asyncio
import sys
from pathlib import Path
from typing import Any, List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress

from specwiz.adapters import (
    AnthropicAdapter,
    BlinkerEventBusAdapter,
    LocalStorageAdapter,
)
from specwiz.core import SpecWizPipelineEngine
from specwiz.core.interfaces.engine import ExecutionContext
from specwiz.core.managers import CompositeConfigAdapter

generate_app = typer.Typer(help="Generate documents")
console = Console()

# Context variables injected when --sources is used with generate commands (additional info)
_CONTEXT_INPUT_KEYS = (
    "source_materials",       # knowledge_base_generator
    "supporting_documents",   # product_context_generator
)

# Example variables injected when --sources is used with rulebook generate (style/standards examples)
_EXAMPLE_INPUT_KEYS = (
    "example_requirements",   # engineering_rulebook_generator
    "example_user_guides",    # writing_rulebook_generator
    "example_diagrams",       # architecture_rulebook_generator
    "example_release_notes",  # qa_rulebook_generator
)

_SOURCE_EXTENSIONS = {".md", ".txt", ".yaml", ".yml", ".py"}


def _load_sources(paths: List[str]) -> str:
    """Read files and directories and return their concatenated content."""
    sections: List[str] = []

    for raw_path in paths:
        p = Path(raw_path)
        if not p.exists():
            console.print(f"[yellow]Warning: source path not found, skipping: {raw_path}[/yellow]")
            continue

        if p.is_file():
            files = [p]
        else:
            files = sorted(
                f for f in p.iterdir()
                if f.is_file() and f.suffix in _SOURCE_EXTENSIONS
            )

        for f in files:
            try:
                content = f.read_text(encoding="utf-8")
                sections.append(f"--- {f.name} ---\n{content}")
            except Exception as exc:
                console.print(f"[yellow]Warning: could not read {f}: {exc}[/yellow]")

    return "\n\n".join(sections)


async def _execute_generation(
    doc_type: str,
    project_root: Path,
    config: CompositeConfigAdapter,
    source_paths: Optional[List[str]] = None,
    **options: Any,
) -> bool:
    """Execute document generation pipeline."""

    try:
        # Inject external sources into all relevant stage input variables
        if source_paths:
            sources_content = _load_sources(source_paths)
            if sources_content:
                for key in _CONTEXT_INPUT_KEYS:
                    options.setdefault(key, sources_content)

        # Initialize adapters
        storage = LocalStorageAdapter(
            base_path=project_root / config.get("storage_path", ".specwiz")
        )
        event_bus = BlinkerEventBusAdapter()

        # Get or create LLM adapter
        try:
            llm = AnthropicAdapter()
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            return False

        # Initialize engine
        engine = SpecWizPipelineEngine(
            storage=storage,
            llm=llm,
            event_bus=event_bus,
        )
        await engine.initialize()

        # Create execution context
        context = ExecutionContext(
            project_root=str(project_root),
            project_name=config.get("project_name", "unknown"),
            stage_name="start",
            stage_number=0,
            inputs=options,
        )

        # Show progress
        with Progress() as progress:
            task = progress.add_task(
                f"[cyan]Generating {doc_type}...",
                total=None,
            )

            # Execute pipeline
            result = await engine.execute_pipeline(
                start_stage="knowledge_base_generator",
                context=context,
            )
            progress.update(task, completed=True)

        if result.success:
            console.print(
                Panel(
                    f"[green]✓ {doc_type} generated successfully![/green]\n"
                    f"Artifacts: {len(result.artifacts)}\n"
                    f"Output: {config.get('storage_path')}",
                    title="Generation Complete",
                    expand=False,
                )
            )
            return True
        else:
            console.print(f"[red]Error: {result.error}[/red]")
            return False

    except Exception as e:
        console.print(f"[red]Generation failed: {e}[/red]")
        return False


@generate_app.command()
def prd(
    product: str = typer.Option(..., help="Product name"),
    feature: str = typer.Option(None, help="Feature to document"),
    repo: str = typer.Option(".", help="Repository path"),
    sources: Optional[List[str]] = typer.Option(
        None, "--sources", help="Extra source files or directories to inject (repeatable)"
    ),
) -> None:
    """Generate a Product Requirements Document."""
    project_root = Path(repo).resolve()
    config = CompositeConfigAdapter(project_root=project_root)

    success = asyncio.run(
        _execute_generation(
            "PRD",
            project_root,
            config,
            source_paths=sources or [],
            product_name=product,
            feature_name=feature,
        )
    )

    sys.exit(0 if success else 1)


@generate_app.command()
def user_guide(
    product: str = typer.Option(..., help="Product name"),
    feature: str = typer.Option(None, help="Feature to document"),
    audience: str = typer.Option("general", help="Target audience"),
    repo: str = typer.Option(".", help="Repository path"),
    sources: Optional[List[str]] = typer.Option(
        None, "--sources", help="Extra source files or directories to inject (repeatable)"
    ),
) -> None:
    """Generate a user guide."""
    project_root = Path(repo).resolve()
    config = CompositeConfigAdapter(project_root=project_root)

    success = asyncio.run(
        _execute_generation(
            "User Guide",
            project_root,
            config,
            source_paths=sources or [],
            product_name=product,
            feature_name=feature,
            target_audience=audience,
        )
    )

    sys.exit(0 if success else 1)


@generate_app.command()
def release_notes(
    product: str = typer.Option(..., help="Product name"),
    version: str = typer.Option(..., help="Release version"),
    repo: str = typer.Option(".", help="Repository path"),
    sources: Optional[List[str]] = typer.Option(
        None, "--sources", help="Extra source files or directories to inject (repeatable)"
    ),
) -> None:
    """Generate release notes."""
    project_root = Path(repo).resolve()
    config = CompositeConfigAdapter(project_root=project_root)

    success = asyncio.run(
        _execute_generation(
            "Release Notes",
            project_root,
            config,
            source_paths=sources or [],
            product_name=product,
            version=version,
        )
    )

    sys.exit(0 if success else 1)
