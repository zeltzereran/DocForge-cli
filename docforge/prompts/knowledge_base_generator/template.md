You are an expert knowledge engineer. Your task is to analyze a set of source materials and produce a single consolidated knowledge base file that an AI agent can use as foundational organizational context when performing future tasks.

This file is not a summary and not a task output. It is a structured reference artifact — designed to be read by an AI system before it performs work, giving it the domain understanding, terminology, system knowledge, and relational context it needs to reason accurately.

## SOURCE MATERIALS

{{ source_materials }}

## TASK

Perform the following steps and show your work:

### 1. Per-source inventory
For each source provided, write a 3–5 bullet summary identifying: domain area covered, key concepts introduced, systems or components described, and any terminology defined.

### 2. Conflict and ambiguity detection
Identify cases where sources contradict each other or use the same term with different meanings. For each conflict:
- Preserve both interpretations
- Flag with: `[CONFLICT: source A contradicts source B — retaining both]`
- Do not silently resolve conflicts by choosing one version

### 3. Implicit knowledge scan
Identify concepts, abbreviations, or relationships that sources assume the reader already knows. These must be made explicit in the knowledge base — not left implied.

### 4. Structure inference
Based on the sources, determine the most appropriate top-level organization for the knowledge base. Do not impose a fixed template. Derive the structure from what the materials actually contain. State your proposed structure and rationale before proceeding.

### 5. Gap identification
List any areas where the source material is insufficient to produce reliable knowledge base content. Flag each with:
`[MISSING: description of what is needed]`

## OUTPUT

Generate a single Markdown knowledge base document that serves as foundational context for all downstream documentation generation. The knowledge base should be:

- **Well-organized**: Logical structure derived from source materials
- **Cross-referenced**: Concepts linked to their definitions and relationships
- **Explicit**: No assumed knowledge - everything defined
- **Authoritative**: Every fact traceable to source material
- **Machine-readable**: Structured for AI consumption

Include a **## References** section listing every source used, and mark which facts came from which source using inline citations: `[source: filename]`
4. Organizes information for AI consumption
5. Flags gaps or ambiguities

## Output Format

Produce a comprehensive Markdown knowledge base with:
- Clear sections organized by domain
- Definitions and explanations
- Entity relationships and data flows
- Terminology glossary
- Identified gaps or missing information (marked with [MISSING: ...])
- References to source materials

Start your response with the knowledge base content directly.
