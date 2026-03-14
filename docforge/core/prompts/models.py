"""Prompt models and metadata structures."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PromptSchema(BaseModel):
    """Input/output schema for a prompt."""

    type: str = "object"
    properties: Dict[str, Any] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)
    description: Optional[str] = None


class PromptMetadata(BaseModel):
    """Complete metadata block for a prompt definition."""

    name: str
    description: str
    version: str
    category: str  # "knowledge_base", "context", "rulebook", "document"
    template_path: str
    input_schema: PromptSchema
    output_schema: PromptSchema
    tags: List[str] = Field(default_factory=list)
    requires: List[str] = Field(default_factory=list)  # prior prompt names
    configurable_params: Dict[str, Any] = Field(default_factory=dict)


class PromptDefinition(BaseModel):
    """A complete prompt definition: metadata + template content."""

    metadata: PromptMetadata
    template: str
    
    @property
    def name(self) -> str:
        return self.metadata.name
    
    @property
    def description(self) -> str:
        return self.metadata.description
    
    @property
    def category(self) -> str:
        return self.metadata.category