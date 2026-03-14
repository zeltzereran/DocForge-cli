# SpecWiz CLI

A documentation generation platform that treats organizational documentation standards as first-class, versioned artifacts.

## Vision

Make documentation generation as repeatable and trustworthy as running a test suite. Instead of manually copying prompts into an LLM, teams codify their documentation standards as versioned rulebooks and run SpecWiz CLI to generate PRDs, user guides, and release notes automatically.

## Quick Start

```bash
# Install
pip install -e .

# Initialize a new project
specwiz init --product MyProduct --repo /path/to/repo

# Generate a PRD
specwiz generate prd --product MyProduct --feature "New Dashboard"

# Generate a user guide
specwiz generate user-guide --product MyProduct --feature "Dashboard"

# Generate release notes
specwiz generate release-notes --product MyProduct --version 1.0.0
```

## Architecture

SpecWiz follows a **hexagonal architecture**:

```
┌─────────────────────────────────────────────┐
│ CLI Interface (Typer + Rich)                │
│ (thin delivery layer)                       │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│ specwiz-core Library (Pure Python)         │
│ ├─ PipelineEngine (orchestrator)            │
│ ├─ PromptTemplateLayer (Jinja2)             │
│ ├─ RulebookManager (load/validate)          │
│ ├─ ContextManager (extract from repo)       │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
    ┌───▼──┐  ┌───▼──┐  ┌───▼────┐
    │Store │  │ LLM  │  │ Events │
    │      │  │Adptr │  │        │
    └──────┘  └──────┘  └────────┘
```

## Project Phases

- **Phase 1**: Core foundation (interfaces, config)
- **Phase 2**: Adapters (storage, LLM, events)
- **Phase 3**: Pipeline engine (orchestration, templating)
- **Phase 4**: CLI commands (Typer interface)
- **Phase 5**: Domain managers (rulebooks, context)
- **Phase 6**: Document generators (PRD, user-guide, release-notes)
- **Phase 7**: Hardening and production readiness

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check specwiz tests
black --check specwiz tests

# Fix linting
black specwiz tests
ruff check --fix specwiz tests

# Type checking
mypy specwiz
```

## License

Apache 2.0