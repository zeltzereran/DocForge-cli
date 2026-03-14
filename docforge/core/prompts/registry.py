"""Prompt registry for discovery and loading."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Union

import yaml

from docforge.core.prompts.models import PromptDefinition, PromptMetadata, PromptSchema


class PromptRegistry:
    """Central registry for prompt discovery and loading.
    
    Prompts are loaded from a structured directory tree with
    metadata files and template files.
    """

    def __init__(self, prompts_dir: Optional[Union[str, Path]] = None) -> None:
        """Initialize registry.
        
        Args:
            prompts_dir: Directory containing prompt definitions
                        (default: docforge/prompts/)
        """
        if prompts_dir is None:
            # Default: look for prompts relative to this module
            prompts_dir = Path(__file__).parent.parent.parent / "prompts"
        
        self.prompts_dir = Path(prompts_dir).resolve()
        self._registry: Dict[str, PromptDefinition] = {}
        self._discover()

    def _discover(self) -> None:
        """Discover all prompts in the prompts directory."""
        if not self.prompts_dir.exists():
            # Create empty registry if prompts directory doesn't exist yet
            return

        for metadata_file in self.prompts_dir.rglob("metadata.yaml"):
            try:
                self._load_prompt(metadata_file.parent)
            except Exception:
                # Skip invalid prompts
                pass

    def _load_prompt(self, prompt_dir: Path) -> None:
        """Load a single prompt from its directory.
        
        Directory structure:
            prompt_name/
            ├── metadata.yaml
            └── template.md (or .txt, .jinja2)
        
        Args:
            prompt_dir: Directory containing the prompt
        """
        metadata_file = prompt_dir / "metadata.yaml"
        if not metadata_file.exists():
            return

        # Load metadata
        metadata_data = yaml.safe_load(metadata_file.read_text())
        
        # Load template (look for .md, .txt, .jinja2)
        template_content = ""
        for ext in [".md", ".txt", ".jinja2"]:
            template_file = prompt_dir / f"template{ext}"
            if template_file.exists():
                template_content = template_file.read_text()
                break

        # Create input/output schemas
        input_schema = PromptSchema(
            properties=metadata_data.get("input_schema", {}).get("properties", {}),
            required=metadata_data.get("input_schema", {}).get("required", []),
        )
        output_schema = PromptSchema(
            properties=metadata_data.get("output_schema", {}).get("properties", {}),
            required=metadata_data.get("output_schema", {}).get("required", []),
        )

        # Create prompt definition
        metadata = PromptMetadata(
            name=metadata_data["name"],
            description=metadata_data.get("description", ""),
            version=metadata_data.get("version", "1.0"),
            category=metadata_data.get("category", "misc"),
            template_path=str(prompt_dir),
            input_schema=input_schema,
            output_schema=output_schema,
            tags=metadata_data.get("tags", []),
            requires=metadata_data.get("requires", []),
        )

        prompt_def = PromptDefinition(
            metadata=metadata,
            template=template_content,
        )

        self._registry[prompt_def.name] = prompt_def

    def get(self, name: str) -> Optional[PromptDefinition]:
        """Get a prompt by name.
        
        Args:
            name: Prompt name
            
        Returns:
            PromptDefinition or None if not found
        """
        return self._registry.get(name)

    def list_by_category(self, category: str) -> List[PromptDefinition]:
        """List all prompts in a category.
        
        Args:
            category: Category name
            
        Returns:
            List of prompts in the category
        """
        return [
            p for p in self._registry.values()
            if p.category == category
        ]

    def all_prompts(self) -> Dict[str, PromptDefinition]:
        """Get all registered prompts.
        
        Returns:
            Dictionary of all prompts by name
        """
        return self._registry.copy()