# DocForge Prompt Definitions

This directory contains the prompt pipeline that drives DocForge documentation generation.

## Structure

Each prompt is a directory containing:
- `metadata.yaml` - Prompt metadata (name, description, schemas, etc.)
- `template.md` (or .txt, .jinja2) - The actual prompt template using Jinja2

## Pipeline Stages

The DocForge generation pipeline consists of 9 stages:

### Stage 1: Knowledge Base Generator
Extracts domain knowledge from provided source materials.

### Stage 2: Product Context Generator  
Analyzes repository and creates structured product context files.

### Stages 3-6: Rulebook Generators
Generates 4 types of rulebooks:
- Engineering rulebook
- Writing/documentation rulebook
- Architecture rulebook
- QA rulebook

### Stages 7-9: Document Generators
Generates 3 types of documents:
- PRD (Product Requirements Document)
- User Guide
- Release Notes

## Adding a New Prompt

1. Create a directory: `prompts/my_prompt/`
2. Create `metadata.yaml` with prompt definition
3. Create `template.md` with Jinja2 template
4. The registry will auto-discover and load it

## Example Metadata

```yaml
name: my_prompt
description: What this prompt does
version: 1.0
category: document  # or: knowledge_base, context, rulebook
template_path: docforge/prompts/my_prompt
input_schema:
  properties:
    project_name:
      type: string
      description: Product name
  required:
    - project_name
output_schema:
  properties:
    document:
      type: string
      description: Generated document
  required:
    - document
tags:
  - generation
  - documentation
requires:
  - prior_prompt_name  # if this depends on another prompt
```