"""Generate commands for creating documentation."""

import asyncio
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress

from docforge.adapters import (
    AnthropicAdapter,
    BlinkerEventBusAdapter,
    LocalStorageAdapter,
)
from docforge.core import DocForgePipelineEngine
from docforge.core.interfaces.engine import ExecutionContext
from docforge.core.managers import CompositeConfigAdapter
from docforge.core.prompts import PromptRegistry

generate_app = typer.Typer(help="Generate documents")
console = Console()


async def _execute_generation(
    doc_type: str,
    project_root: Path,
    config: CompositeConfigAdapter,
    **options,
) -> bool:
    """Execute document generation pipeline."""
    
    try:
        # Initialize adapters
        storage = LocalStorageAdapter(
            base_path=project_root / config.get("storage_path", ".docforge")
        )
        event_bus = BlinkerEventBusAdapter()
        
        # Get or create LLM adapter
        try:
            llm = AnthropicAdapter()
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            return False
        
        # Initialize engine
        engine = DocForgePipelineEngine(
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
            console.print(Panel(
                f"[green]✓ {doc_type} generated successfully![/green]\n"
                f"Artifacts: {len(result.artifacts)}\n"
                f"Output: {config.get('storage_path')}",
                title="Generation Complete",
                expand=False,
            ))
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
) -> None:
    """Generate a Product Requirements Document."""
    project_root = Path(repo).resolve()
    config = CompositeConfigAdapter(project_root=project_root)
    
    success = asyncio.run(_execute_generation(
        "PRD",
        project_root,
        config,
        product_name=product,
        feature_name=feature,
    ))
    
    sys.exit(0 if success else 1)


@generate_app.command()
def user_guide(
    product: str = typer.Option(..., help="Product name"),
    feature: str = typer.Option(None, help="Feature to document"),
    audience: str = typer.Option("general", help="Target audience"),
    repo: str = typer.Option(".", help="Repository path"),
) -> None:
    """Generate a user guide."""
    project_root = Path(repo).resolve()
    config = CompositeConfigAdapter(project_root=project_root)
    
    success = asyncio.run(_execute_generation(
        "User Guide",
        project_root,
        config,
        product_name=product,
        feature_name=feature,
        target_audience=audience,
    ))
    
    sys.exit(0 if success else 1)


@generate_app.command()
def release_notes(
    product: str = typer.Option(..., help="Product name"),
    version: str = typer.Option(..., help="Release version"),
    repo: str = typer.Option(".", help="Repository path"),
) -> None:
    """Generate release notes."""
    project_root = Path(repo).resolve()
    config = CompositeConfigAdapter(project_root=project_root)
    
    success = asyncio.run(_execute_generation(
        "Release Notes",
        project_root,
        config,
        product_name=product,
        version=version,
    ))
    
    sys.exit(0 if success else 1)