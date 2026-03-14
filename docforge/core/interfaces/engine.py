"""Abstract interface for the PipelineEngine.

The PipelineEngine is the core orchestrator of the DocForge system.
It coordinates the prompt pipeline, manages artifacts, and emits events.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel


class PipelineStage(BaseModel):
    """Description of a stage in the prompt pipeline."""

    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    template_path: str
    requires: List[str] = []  # prior stage names required


class ExecutionContext(BaseModel):
    """Context passed through the pipeline."""

    project_root: str
    project_name: str
    stage_name: str
    stage_number: int
    inputs: Dict[str, Any]
    outputs: Dict[str, Any] = {}
    artifacts: Dict[str, str] = {}  # path -> content
    errors: List[str] = []

    class Config:
        """Allow arbitrary types."""

        arbitrary_types_allowed = True


class ArtifactResult(BaseModel):
    """Result of artifact generation."""

    artifact_type: str
    path: str
    content: Union[str, bytes]
    metadata: Dict[str, Any] = {}


class PipelineResult(BaseModel):
    """Result of full pipeline execution."""

    success: bool
    stage_results: Dict[str, ArtifactResult] = {}
    error: Optional[str] = None
    errors: List[str] = []
    artifacts: List[ArtifactResult] = []


class PipelineEngine(ABC):
    """Core orchestration engine for the DocForge documentation generation pipeline.
    
    Responsibilities:
    - Load and validate prompt templates
    - Execute prompts with injected dependencies
    - Manage context flow through pipeline stages
    - Validate outputs against schemas
    - Emit lifecycle events
    - Persist artifacts
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize engine (load prompts, setup adapters)."""
        pass

    @abstractmethod
    async def get_stages(self) -> List[PipelineStage]:
        """Get all available pipeline stages."""
        pass

    @abstractmethod
    async def execute_stage(
        self,
        stage_name: str,
        context: ExecutionContext,
    ) -> ArtifactResult:
        """Execute single pipeline stage."""
        pass

    @abstractmethod
    async def execute_pipeline(
        self,
        start_stage: str,
        context: ExecutionContext,
    ) -> PipelineResult:
        """Execute pipeline from specified stage onward."""
        pass

    @abstractmethod
    def get_context(self) -> ExecutionContext:
        """Get current execution context."""
        pass
