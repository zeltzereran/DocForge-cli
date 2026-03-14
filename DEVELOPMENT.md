# DocForge Development Guide

This guide is for developers working on the DocForge CLI codebase.

## Project Structure

```
docforge-cli/
├── docforge/                        # Main package
│   ├── __init__.py
│   ├── exceptions.py                # Custom exceptions
│   ├── core/                        # Core library (no CLI deps)
│   │   ├── interfaces/              # Abstract adapters and engine
│   │   │   ├── adapters.py
│   │   │   └── engine.py
│   │   ├── engine.py                # PipelineEngine implementation
│   │   ├── managers/                # Domain managers
│   │   │   ├── config.py
│   │   │   ├── rulebook.py
│   │   │   └── context.py
│   │   └── prompts/                 # Prompt pipeline
│   │       ├── models.py
│   │       ├── registry.py
│   │       ├── renderer.py
│   │       └── __init__.py
│   ├── adapters/                    # Adapter implementations
│   │   ├── storage.py               # LocalStorageAdapter
│   │   ├── llm.py                   # AnthropicAdapter
│   │   ├── events.py                # BlinkerEventBusAdapter
│   │   └── __init__.py
│   ├── cli/                         # CLI interface (uses core)
│   │   ├── main.py                  # Main Typer app
│   │   ├── commands/
│   │   │   ├── generate.py
│   │   │   └── rulebook.py
│   │   └── __init__.py
│   └── prompts/                     # Prompt definitions
│       ├── knowledge_base_generator/
│       ├── product_context_generator/
│       ├── engineering_rulebook_generator/
│       ├── writing_rulebook_generator/
│       ├── architecture_rulebook_generator/
│       ├── qa_rulebook_generator/
│       ├── prd_generator/
│       ├── user_guide_generator/
│       └── release_notes_generator/
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   └── test_storage_adapter.py
│   └── integration/
│       └── test_full_pipeline.py
├── pyproject.toml
├── README.md
├── QUICKSTART.md
├── Makefile
└── .github/workflows/
    ├── test.yml
    └── lint.yml
```

## Architecture Principles

### 1. Hexagonal Architecture

The core library is surrounded by ports (interfaces) and adapters:

- **Core**: Pure Python business logic (no external dependencies)
- **Ports**: Abstract interfaces defining contracts (adapters.py, engine.py)
- **Adapters**: Concrete implementations (storage, LLM, events)
- **CLI**: Thin wrapper using Typer

This allows:
- Testing the core in isolation with mocks
- Swapping adapters without changing core logic
- Future interfaces (API, GitHub Action, web UI) without refactoring

### 2. Dependency Injection

All adapters are injected into the engine:

```python
engine = DocForgePipelineEngine(
    storage=LocalStorageAdapter(),
    llm=AnthropicAdapter(),
    event_bus=BlinkerEventBusAdapter(),
)
```

Never instantiate adapters inside the engine - always pass them in.

### 3. Event-Driven Extension

The engine publishes lifecycle events that subscribers can attach to:

```python
event_bus.subscribe("pipeline.stage.end", log_handler)
event_bus.subscribe("pipeline.stage.end", metrics_handler)
```

Future integrations (Slack notifier, webhook, metrics collector) just subscribe to events.

### 4. Vertical Slices

Each implementation phase delivers a thin, working slice of the system:

- Phase 1: Interfaces and config
- Phase 2: Adapters
- Phase 3: Pipeline engine
- Phase 4: CLI
- Phase 5: Managers
- Phase 6: Integration tests
- Phase 7: Hardening

At each phase, the system is runnable and testable.

## Development Workflow

### 1. Setup Development Environment

```bash
# Clone and install
git clone <repo>
cd DocForge-cli
pip install -e ".[dev]"

# Verify setup
docforge doctor
```

### 2. Make Changes

```bash
# Edit code
vim docforge/core/engine.py

# Run tests
make test-fast

# Check formatting and types
make lint
make type-check
```

### 3. Testing

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# All tests with coverage
pytest --cov=docforge

# Watch for changes
pytest-watch
```

### 4. Code Quality

```bash
# Format code
black docforge tests

# Lint
ruff check --fix docforge tests

# Type checking
mypy docforge

# All at once
make lint format type-check
```

### 5. Commit and Push

```bash
git add .
git commit -m "feat: add new feature"
git push origin feature-branch
```

## Adding a New Adapter

Example: Add S3 storage adapter.

### 1. Create Adapter Implementation

```python
# docforge/adapters/s3.py
from docforge.core.interfaces.adapters import StorageAdapter

class S3StorageAdapter(StorageAdapter):
    async def save(self, path, content, artifact_type, metadata=None):
        # Implementation
        pass
    
    async def load(self, path):
        # Implementation
        pass
```

### 2. Export from Package

```python
# docforge/adapters/__init__.py
from docforge.adapters.s3 import S3StorageAdapter

__all__ = ["S3StorageAdapter", ...]
```

### 3. Create Unit Tests

```python
# tests/unit/test_s3_adapter.py
@pytest.mark.asyncio
async def test_s3_save(s3_adapter):
    artifact = await s3_adapter.save(...)
    assert artifact.path == "..."
```

### 4. Update CLI if Needed

```python
# docforge/cli/main.py
if config.get("storage_backend") == "s3":
    storage = S3StorageAdapter(bucket=...)
```

## Adding a New Command

Example: Add `docforge analyze` command.

### 1. Create Command Module

```python
# docforge/cli/commands/analyze.py
import typer
from rich.console import Console

analyze_app = typer.Typer(help="Analyze artifacts")
console = Console()

@analyze_app.command()
def diff(file1: str, file2: str):
    """Compare two artifacts."""
    # Implementation
```

### 2. Register with Main App

```python
# docforge/cli/main.py
from docforge.cli.commands.analyze import analyze_app

app.add_typer(analyze_app, name="analyze")
```

### 3. Test the Command

```bash
docforge analyze diff file1.md file2.md
```

## Adding a New Prompt

Example: Add custom diagram generator prompt.

### 1. Create Prompt Directory

```bash
mkdir -p docforge/prompts/diagram_generator
```

### 2. Create Metadata

```yaml
# docforge/prompts/diagram_generator/metadata.yaml
name: diagram_generator
description: Generates draw.io diagrams from descriptions
version: 1.0
category: document
template_path: docforge/prompts/diagram_generator
requires:
  - product_context_generator
```

### 3. Create Template

```markdown
# docforge/prompts/diagram_generator/template.md
Generate a draw.io diagram for: {{ diagram_description }}

Use the provided product context:
{{ product_context }}
```

### 4. Use in Pipeline

The registry will auto-discover and load it. Reference it in code:

```python
prompt = registry.get("diagram_generator")
```

## Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Use Python Debugger

```python
import pdb; pdb.set_trace()
```

### Run with Verbosity

```bash
docforge generate prd --verbose
```

### Check System Health

```bash
docforge doctor
```

## Performance Optimization

### Profiling

```bash
python -m cProfile -s cumulative -m docforge generate prd --product Test
```

### Memory Usage

```bash
pip install memory_profiler
python -m memory_profiler -m docforge generate prd --product Test
```

### Async Optimization

The pipeline engine uses `asyncio` for non-blocking I/O:

```python
# Concurrent execution
result = await asyncio.gather(
    engine.execute_stage("stage1", context),
    engine.execute_stage("stage2", context),
)
```

## Dependencies

### Core Dependencies

- **typer**: CLI framework
- **rich**: Terminal UI
- **pydantic**: Data validation
- **jinja2**: Template rendering
- **anthropic**: LLM API
- **blinker**: Event bus
- **gitpython**: Git operations
- **pyyaml**: Config files

### Dev Dependencies

- **pytest**: Testing framework
- **pytest-asyncio**: Async test support
- **black**: Code formatter
- **ruff**: Linter
- **mypy**: Type checker
- **pre-commit**: Git hooks

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Write or update tests
5. Run `make lint format type-check test`
6. Commit (`git commit -m 'Add amazing feature'`)
7. Push (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Troubleshooting

### Import Errors

```bash
# Reinstall in editable mode
pip install -e ".[dev]"

# Or update path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Test Failures

```bash
# Run with verbose output
pytest -vv tests/unit/test_name.py

# Debug specific test
pytest -vv --pdb tests/unit/test_name.py::test_function
```

### Type Checking Failures

```bash
# Check specific file
mypy docforge/core/engine.py

# Ignore specific errors temporarily (mark as TODO)
# type: ignore
```

## Resources

- [Typer Docs](https://typer.tiangolo.com/)
- [Rich Docs](https://rich.readthedocs.io/)
- [Pydantic Docs](https://docs.pydantic.dev/)
- [Jinja2 Docs](https://jinja.palletsprojects.com/)
- [AsyncIO Docs](https://docs.python.org/3/library/asyncio.html)

## Support

For questions or issues:
- Check the [README](README.md)
- Check the [QuickStart](QUICKSTART.md)
- Review the architecture docs
- Open an issue on GitHub