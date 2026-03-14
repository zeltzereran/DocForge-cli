# SpecWiz CLI - Quick Start Guide

Welcome to SpecWiz! This guide will get you up and running in minutes.

## Installation

### Prerequisites

- Python 3.10 or higher
- `pip` or `pipenv`
- Anthropic API key (for LLM-based generation)

### Install from Source

```bash
git clone https://github.com/your-org/SpecWiz-cli.git
cd SpecWiz-cli
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
SPECWIZ_PROJECT_NAME=MyProduct
SPECWIZ_STORAGE_PATH=.specwiz
```

## Initialize a Project

```bash
specwiz init --product MyProduct --repo /path/to/repo
```

This creates:
- `specwiz.yaml` - Project configuration
- `.specwiz/` - Output directory for generated artifacts

## Generate Documentation

### Generate a Product Requirements Document (PRD)

```bash
specwiz generate prd \
  --product MyProduct \
  --feature "New Dashboard" \
  --repo /path/to/repo
```

Optionally inject extra source documents (PRDs, architecture docs, design files) to give the pipeline richer context:

```bash
specwiz generate prd \
  --product MyProduct \
  --feature "New Dashboard" \
  --repo /path/to/repo \
  --sources docs/prd.md \
  --sources docs/sad.md
```

You can also pass a directory — all `.md`, `.txt`, `.yaml`, and `.py` files inside it are loaded:

```bash
specwiz generate prd --product MyProduct --repo /path/to/repo --sources ./docs/
```

### Generate a User Guide

```bash
specwiz generate user-guide \
  --product MyProduct \
  --feature "Dashboard" \
  --audience "end-users" \
  --repo /path/to/repo \
  --sources docs/
```

### Generate Release Notes

```bash
specwiz generate release-notes \
  --product MyProduct \
  --version 1.0.0 \
  --repo /path/to/repo \
  --sources docs/
```

## Manage Rulebooks

Rulebooks are the heart of SpecWiz - they codify your organization's documentation standards.

### Initialize Rulebooks

```bash
# Create an engineering standards rulebook
specwiz rulebook create \
  --name engineering_standards \
  --category engineering

# Create a writing guide
specwiz rulebook create \
  --name style_guide \
  --category writing
```

### List and Validate Rulebooks

```bash
# List all rulebooks
specwiz rulebook list

# Validate all rulebooks
specwiz rulebook validate
```

## Check System Health

```bash
specwiz doctor
```

This checks:
- Python version and packages
- Configuration validity
- API connectivity
- Adapter readiness

## Understanding the Generation Pipeline

SpecWiz uses a 9-stage pipeline to generate documentation:

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
├── specwiz.yaml                 # Project config
├── .specwiz/                    # Generated artifacts
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
specwiz init --product Acme --repo ~/projects/acme
cd ~/projects/acme
```

### 2. Create Rulebooks

Create your organization's documentation standards:

```bash
specwiz rulebook create --name engineering-standards --category engineering
specwiz rulebook create --name documentation-style --category writing
```

Edit the created rulebooks to match your standards.

### 3. Generate Documents

```bash
# Generate PRD for a new feature
specwiz generate prd --product Acme --feature "User Analytics" --sources docs/

# Generate user guide
specwiz generate user-guide --product Acme --feature "User Analytics" --audience developers --sources docs/

# Generate release notes (after release)
specwiz generate release-notes --product Acme --version 2.0.0 --sources docs/
```

### 4. Review and Edit

The generated documents are in `.specwiz/generated/`. Review them, make any necessary adjustments, and commit to your repository.

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | Required |
| `SPECWIZ_PROJECT_NAME` | Project name | "" |
| `SPECWIZ_PROJECT_ROOT` | Project root directory | Current dir |
| `SPECWIZ_STORAGE_PATH` | Artifact storage path | `.specwiz` |
| `SPECWIZ_LLM_MODEL` | Claude model to use | `claude-3-opus-20240229` |
| `SPECWIZ_TEMPERATURE` | LLM temperature (0-1) | `0.7` |
| `SPECWIZ_MAX_TOKENS` | Max tokens per response | `4096` |

## Troubleshooting

### "ANTHROPIC_API_KEY not set"

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### "Generation failed"

Run health check:

```bash
specwiz doctor
```

This shows configuration issues and adapter status.

### "No project context found"

Ensure your repository has:
- `README.md` - Product overview
- `pyproject.toml` or `package.json` - Project metadata
- Documentation files or comments explaining the system

## Next Steps

- Read the [Architecture Guide](SpecWiz_SAD.md) for system design
- Review the [Product Specification](SpecWiz_CLI_PRD.md) for feature details
- Check the [Execution Plan](SpecWiz_Execution_Plan.md) for implementation roadmap

## Support

For issues or questions:
- Check the [README](README.md)
- Run `specwiz doctor` to diagnose problems
- Review generated artifacts in `.specwiz/`

## License

Apache 2.0