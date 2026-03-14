"""Shared engine initialization helper for SpecWiz CLI commands."""

import sys
from pathlib import Path
from typing import Any, Dict

from rich.console import Console

from specwiz.adapters import AnthropicAdapter, BlinkerEventBusAdapter, LocalStorageAdapter
from specwiz.core import SpecWizPipelineEngine
from specwiz.core.interfaces.engine import ExecutionContext


async def run_stage(
    stage_name: str,
    product_path: Path,
    inputs: Dict[str, Any],
    console: Console,
) -> str:
    """Initialize the engine, execute a single named stage, and return the LLM output."""
    storage = LocalStorageAdapter(base_path=product_path / "artifacts")
    event_bus = BlinkerEventBusAdapter()

    try:
        llm = AnthropicAdapter()
    except ValueError as e:
        console.print(f"[red]LLM initialization error: {e}[/red]")
        sys.exit(1)

    engine = SpecWizPipelineEngine(storage=storage, llm=llm, event_bus=event_bus)
    await engine.initialize()

    context = ExecutionContext(
        project_root=str(product_path),
        project_name=product_path.name,
        stage_name=stage_name,
        stage_number=0,
        inputs=inputs,
    )

    result = await engine.execute_stage(stage_name, context)
    return result.content
