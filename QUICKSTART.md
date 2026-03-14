# SpecWiz CLI - Quick Start Guide

Welcome to SpecWiz! This guide walks you through the complete workflow, from installation to generating your first document.

## Installation

### Prerequisites

- Python 3.10 or higher
- Anthropic API key

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

A `specwiz.yaml` file is created automatically when you run `specwiz init`. You can edit it to change the storage path or LLM model:

```yaml
# specwiz.yaml
base_path: .specwiz
llm_provider: anthropic
llm_model: claude-3-5-sonnet-20241022
```

---

## Concepts: Global vs Product-Specific Artifacts

SpecWiz has two tiers of artifacts:

| Artifact | Scope | Command |
|---|---|---|
| Knowledge Base | **Global** (whole workspace) | `create knowledge-base` |
| Rulebooks | **Global** (whole workspace) | `create rulebook <type>` |
| Product Context | **Per product** | `create product-context --product <name>` |
| Generated docs | **Per product** | `generate prd/user-guide/release-notes --product <name>` |

The global knowledge base and rulebooks reflect your organization's standards and example documents � they are created **once** and shared across all products in the workspace.

---

## Directory Layout

After initialization and creating all artifacts, your workspace will look like:

```
project_root/
├── specwiz.yaml
└── .specwiz/
    ├── knowledge-base/
    │   └── knowledge-base.md        <- global, created by `create knowledge-base`
    ├── rulebooks/
    │   ├── prd-rulebook.md          <- global, created by `create rulebook prd`
    │   ├── user-guide-rulebook.md   <- global, created by `create rulebook user-guide`
    │   ├── release-note-rulebook.md <- global, created by `create rulebook release-note`
    │   └── diagram-rulebook.md      <- global, created by `create rulebook diagram`
    └── <product>/
        ├── product-context/
        │   └── product-context.md   <- per-product, created by `create product-context`
        └── generated/
            ├── prd/
            ├── user-guide/
            └── release-notes/
```

---

## Step-by-Step Workflow

### Step 1 - Initialize a product

```bash
specwiz init --product MyProduct
```

Creates the per-product directory structure under `.specwiz/MyProduct/`.

### Step 2 - Build the global knowledge base

```bash
specwiz create knowledge-base --sources ./docs
```

Reads all `.md`, `.txt`, `.yaml`, and `.py` files from the provided paths and summarises them into a global knowledge base. Run this once per workspace (or re-run to refresh).

You can pass multiple paths:

```bash
specwiz create knowledge-base --sources ./docs --sources ./architecture/README.md
```

### Step 3 - Create product context

```bash
specwiz create product-context --product MyProduct --git .
```

You can also pass a remote URL — SpecWiz will shallow-clone it automatically (requires `git` on `PATH`):

```bash
specwiz create product-context --product MyProduct --git https://github.com/org/repo.git
specwiz create product-context --product MyProduct --git git@github.com:org/repo.git
```

```bash
# Or use source documents instead of (or in addition to) the git repo
specwiz create product-context --product MyProduct --git . --sources ./design-docs
```

### Step 4 - Create global rulebooks

Rulebooks encode your organization's documentation standards, derived from real example documents.

```bash
specwiz create rulebook prd --resources ./examples/prd
specwiz create rulebook user-guide --resources ./examples/user-guide
specwiz create rulebook release-note --resources ./examples/release-notes
specwiz create rulebook diagram --resources ./examples/diagrams
```

Each `--resources` path can be a file or a directory (scanned recursively).

### Step 5 - Generate documents

```bash
# Generate a PRD
specwiz generate prd --product MyProduct --feature "New Dashboard"

# Generate a PRD with extra context
specwiz generate prd --product MyProduct --feature "New Dashboard" --resources ./design-spec.md

# Generate a user guide
specwiz generate user-guide --product MyProduct --feature "Dashboard" --audience "end-users"

# Generate release notes (--resources provides commits/changelog/PR list)
specwiz generate release-notes --product MyProduct --release-version v1.2.0 --resources ./changelog.txt
```

---

## Utility Commands

```bash
# List all global rulebooks and their status
specwiz rulebook list

# Check system health: API key, adapters, global artifacts, per-product contexts
specwiz doctor
```

---

## Common Workflows

### Working with Multiple Products

```bash
# Each product has its own context and generated docs
specwiz init --product ProductA
specwiz init --product ProductB

# Shared global artifacts (KB + rulebooks) are created once
specwiz create knowledge-base --sources ./shared-docs

# Per-product context
specwiz create product-context --product ProductA --git ./productA
specwiz create product-context --product ProductB --git ./productB

# Generate independently
specwiz generate prd --product ProductA --feature "Onboarding Flow"
specwiz generate prd --product ProductB --feature "API Gateway"
```

### Refreshing Rulebooks

Simply re-run the `create rulebook` command with updated example resources:

```bash
specwiz create rulebook prd --resources ./examples/prd-v2
```

---

## Troubleshooting

### `ANTHROPIC_API_KEY not set`

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Rulebook not found

Run `specwiz rulebook list` to see which rulebooks exist, then create any missing ones:

```bash
specwiz create rulebook prd --resources ./examples/prd
```

### Product not found

Ensure you initialized the product first:

```bash
specwiz init --product MyProduct
```

### Check overall health

```bash
specwiz doctor
```
