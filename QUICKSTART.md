# DocForge CLI - Quick Start Guide

Welcome to DocForge! This guide will get you up and running in minutes.

## Installation

### Prerequisites

- Python 3.10 or higher
- `pip` or `pipenv`
- Anthropic API key (for LLM-based generation)

### Install from Source

```bash
git clone https://github.com/your-org/DocForge-cli.git
cd DocForge-cli
pip install -e .
```

### Install with Development Tools

```bash
pip install -e ".[dev]"
```

## Configuration

### Set up Anthropic API Key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Or create a `.env` file in your project:

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
DOCFORGE_PROJECT_NAME=MyProduct
DOCFORGE_STORAGE_PATH=.docforge
```

## Initialize a Project

```bash
docforge init --product MyProduct --repo /path/to/repo
```

This creates:
- `docforge.yaml` - Project configuration
- `.docforge/` - Output directory for generated artifacts

## Generate Documentation

### Generate a Product Requirements Document (PRD)

```bash
docforge generate prd \
  --product MyProduct \
  --feature "New Dashboard" \
  --repo /path/to/repo
```

### Generate a User Guide

```bash
docforge generate user-guide \
  --product MyProduct \
  --feature "Dashboard" \
  --audience "end-users" \
  --repo /path/to/repo
```

### Generate Release Notes

```bash
docforge generate release-notes \
  --product MyProduct \
  --version 1.0.0 \
  --repo /path/to/repo
```

## Manage Rulebooks

Rulebooks are the heart of DocForge - they codify your organization's documentation standards.

### Initialize Rulebooks

```bash
# Create an engineering standards rulebook
docforge rulebook create \
  --name engineering_standards \
  --category engineering

# Create a writing guide
docforge rulebook create \
  --name style_guide \
  --category writing
```

### List and Validate Rulebooks

```bash
# List all rulebooks
docforge rulebook list

# Validate all rulebooks
docforge rulebook validate
```

## Check System Health

```bash
docforge doctor
```

This checks:
- Python version and packages
- Configuration validity
- API connectivity
- Adapter readiness

## Understanding the Generation Pipeline

DocForge uses a 9-stage pipeline to generate documentation:

**Stage 1:** Knowledge Base Generator
- Analyzes source materials and creates a consolidated knowledge base

**Stage 2:** Product Context Generator
- Extracts repository structure, architecture, and data model

**Stages 3-6:** Rulebook Generators
- Engineering rulebook - coding standards, architecture patterns
- Writing rulebook - documentation tone, style, structure
- Architecture rulebook - system design principles
- QA rulebook - testing strategies and standards

**Stages 7-9:** Document Generators
- PRD generator - product requirements
- User guide generator - step-by-step instructions
- Release notes generator - versioned change documentation

Each stage uses the output of previous stages as input.

## Project Structure

```
project_root/
├── docforge.yaml                 # Project config
├── .docforge/                    # Generated artifacts
│   ├── knowledge_base.json
│   ├── context/
│   │   ├── overview.md
│   │   ├── architecture.md
│   │   └── glossary.md
│   ├── rulebooks/
│   │   ├── engineering/
│   │   ├── writing/
│   │   └── architecture/
│   └── generated/
│       ├── prd.md
│       ├── user_guide.md
│       └── release_notes.md
├── rulebooks/                    # Organization rulebooks (git tracked)
│   ├── engineering/
│   │   └── engineering-rulebook.md
│   ├── writing/
│   │   └── writing-rulebook.md
│   └── architecture/
│       └── architecture-rulebook.md
└── examples/                      # Example documents
    └── release-notes/
```

## Workflow Example

### 1. Initialize Project

```bash
docforge init --product Acme --repo ~/projects/acme
cd ~/projects/acme
```

### 2. Create Rulebooks

Create your organization's documentation standards:

```bash
docforge rulebook create --name engineering-standards --category engineering
docforge rulebook create --name documentation-style --category writing
```

Edit the created rulebooks to match your standards.

### 3. Generate Documents

```bash
# Generate PRD for a new feature
docforge generate prd --product Acme --feature "User Analytics"

# Generate user guide
docforge generate user-guide --product Acme --feature "User Analytics" --audience developers

# Generate release notes (after release)
docforge generate release-notes --product Acme --version 2.0.0
```

### 4. Review and Edit

The generated documents are in `.docforge/generated/`. Review them, make any necessary adjustments, and commit to your repository.

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | Required |
| `DOCFORGE_PROJECT_NAME` | Project name | "" |
| `DOCFORGE_PROJECT_ROOT` | Project root directory | Current dir |
| `DOCFORGE_STORAGE_PATH` | Artifact storage path | `.docforge` |
| `DOCFORGE_LLM_MODEL` | Claude model to use | `claude-3-opus-20240229` |
| `DOCFORGE_TEMPERATURE` | LLM temperature (0-1) | `0.7` |
| `DOCFORGE_MAX_TOKENS` | Max tokens per response | `4096` |

## Troubleshooting

### "ANTHROPIC_API_KEY not set"

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### "Generation failed"

Run health check:

```bash
docforge doctor
```

This shows configuration issues and adapter status.

### "No project context found"

Ensure your repository has:
- `README.md` - Product overview
- `pyproject.toml` or `package.json` - Project metadata
- Documentation files or comments explaining the system

## Next Steps

- Read the [Architecture Guide](DocForge_SAD.md) for system design
- Review the [Product Specification](DocForge_CLI_PRD.md) for feature details
- Check the [Execution Plan](DocForge_Execution_Plan.md) for implementation roadmap

## Support

For issues or questions:
- Check the [README](README.md)
- Run `docforge doctor` to diagnose problems
- Review generated artifacts in `.docforge/`

## License

MIT
