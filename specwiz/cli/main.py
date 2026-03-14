"""SpecWiz CLI application."""

import sys
from pathlib import Path

import typer
from rich.console import Console

from specwiz.cli.commands.create import create_app
from specwiz.cli.commands.generate import generate_app
from specwiz.cli.commands.rulebook import rulebook_app

# Create CLI app
app = typer.Typer(
    name="specwiz",
    help="Documentation generation platform with versioned rulebooks",
    no_args_is_help=True,
)

# Create console for output
console = Console()

# Add command groups
app.add_typer(
    create_app, name="create", help="Create knowledge base, product context, and rulebooks"
)
app.add_typer(
    generate_app, name="generate", help="Generate documents (PRD, user guide, release notes)"
)
app.add_typer(rulebook_app, name="rulebook", help="Manage documentation rulebooks")


@app.command()
def init(
    product: str = typer.Option(..., "--product", help="Product name"),
    base_path: str = typer.Option(
        ".specwiz", "--base-path", help="Base directory for product storage"
    ),
) -> None:
    """Initialize a new SpecWiz product directory."""
    from rich.panel import Panel

    try:
        cwd = Path.cwd()
        product_path = cwd / base_path / product

        if product_path.exists():
            console.print(
                f"[yellow]Product '[bold]{product}[/bold]' already exists at "
                f"{product_path.relative_to(cwd)}.[/yellow]\n"
                f"Nothing was changed."
            )
            return

        # Create only product-specific directories
        # (knowledge-base/ and rulebooks/ are global and auto-created on first use)
        dirs = [
            product_path / "product-context",
            product_path / "generated" / "prd",
            product_path / "generated" / "user-guide",
            product_path / "generated" / "release-notes",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

        # Write top-level config file (only if it doesn't already exist)
        config_file = cwd / "specwiz.yaml"
        if not config_file.exists():
            config_file.write_text(
                f"# SpecWiz Configuration\n"
                f"base_path: {base_path}\n"
                f"llm_provider: anthropic\n"
                f"llm_model: claude-3-5-sonnet-20241022\n",
                encoding="utf-8",
            )

        console.print(
            Panel(
                f"[green]✓ Product initialized![/green]\n"
                f"Product: [bold]{product}[/bold]\n"
                f"Directory: {product_path.relative_to(cwd)}\n\n"
                f"[dim]Next steps:[/dim]\n"
                f"  1. [cyan]specwiz create knowledge-base --sources ./docs[/cyan]\n"
                f"  2. [cyan]specwiz create product-context --product {product} --git .[/cyan]\n"
                f"  3. [cyan]specwiz create rulebook prd --resources ./examples[/cyan]",
                title="SpecWiz Init",
                expand=False,
            )
        )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@app.command()
def doctor() -> None:
    """Check SpecWiz setup: API keys, adapters, and product readiness."""
    import os

    from rich.table import Table

    from specwiz.adapters import BlinkerEventBusAdapter, LocalStorageAdapter
    from specwiz.cli._paths import get_base_path

    table = Table(title="SpecWiz System Health")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Details", style="green")

    # Python version
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    table.add_row("Python", "✓", f"v{py_version}")

    # API key
    if os.getenv("ANTHROPIC_API_KEY"):
        table.add_row("Anthropic API Key", "✓", "ANTHROPIC_API_KEY is set")
    else:
        table.add_row("Anthropic API Key", "⚠", "ANTHROPIC_API_KEY not set — LLM calls will fail")

    # Adapters
    try:
        LocalStorageAdapter()
        table.add_row("Storage Adapter", "✓", "OK")
    except Exception as e:
        table.add_row("Storage Adapter", "✗", str(e))

    try:
        BlinkerEventBusAdapter()
        table.add_row("Event Bus", "✓", "OK")
    except Exception as e:
        table.add_row("Event Bus", "✗", str(e))

    cwd = Path.cwd()
    base = get_base_path(cwd)

    # Global: knowledge base
    kb_file = base / "knowledge-base" / "knowledge-base.md"
    if kb_file.exists():
        table.add_row("Knowledge Base", "✓", str(kb_file.relative_to(cwd)))
    else:
        table.add_row(
            "Knowledge Base", "⚠", "Not found — run: specwiz create knowledge-base --sources <path>"
        )

    # Global: rulebooks
    rulebooks_dir = base / "rulebooks"
    _RULEBOOK_TYPES = ["prd", "user-guide", "release-note", "diagram"]
    if rulebooks_dir.exists():
        created = [t for t in _RULEBOOK_TYPES if (rulebooks_dir / f"{t}-rulebook.md").exists()]
        missing = [t for t in _RULEBOOK_TYPES if t not in created]
        rb_detail = f"created: {', '.join(created) or 'none'}" + (
            f"  missing: {', '.join(missing)}" if missing else ""
        )
        table.add_row("Rulebooks", "✓" if created else "⚠", rb_detail)
    else:
        table.add_row(
            "Rulebooks", "⚠", "No rulebooks — run: specwiz create rulebook prd --resources <path>"
        )

    # Products
    _add_product_rows(table, base, cwd)

    console.print(table)


def _add_product_rows(table, base: Path, cwd: Path) -> None:
    """Add per-product health rows to the doctor table."""
    from specwiz.cli._paths import DEFAULT_BASE

    if not base.exists():
        table.add_row(
            "Products", "⚠", f"No {DEFAULT_BASE}/ directory — run: specwiz init --product <name>"
        )
        return

    products = sorted(
        d for d in base.iterdir() if d.is_dir() and d.name not in ("knowledge-base", "rulebooks")
    )
    try:
        base_rel = base.relative_to(cwd)
    except ValueError:
        base_rel = base

    if not products:
        table.add_row("Products", "⚠", f"No products found in {base_rel}")
        return

    table.add_row("Products", "✓", f"{len(products)} found in {base_rel}")
    for p in products:
        ctx = (
            any((p / "product-context").glob("*.md")) if (p / "product-context").exists() else False
        )
        status = "✓" if ctx else "⚠"
        ctx_hint = (
            "✓" if ctx else f"✗ (run: specwiz create product-context --product {p.name} --git .)"
        )
        detail = f"product-context: {ctx_hint}"
        table.add_row(f"  └ {p.name}", status, detail)


@app.callback(invoke_without_command=True)
def version_callback(
    version: bool = typer.Option(
        None,
        "--version",
        help="Show version information",
    ),
) -> None:
    """Display version information."""
    if version:
        from specwiz import __version__

        console.print(f"SpecWiz v{__version__}")
        raise typer.Exit(code=0)


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
