"""Core pipeline engine orchestration."""

import json
from typing import Any, Dict, List, Optional

from docforge.core.interfaces.adapters import (
    EventBusAdapter,
    LLMAdapter,
    StorageAdapter,
)
from docforge.core.interfaces.engine import (
    ArtifactResult,
    ExecutionContext,
    PipelineEngine,
    PipelineResult,
    PipelineStage,
)
from docforge.core.prompts.models import PromptDefinition
from docforge.core.prompts.registry import PromptRegistry
from docforge.core.prompts.renderer import PromptRenderer


class DocForgePipelineEngine(PipelineEngine):
    """Complete documentation generation pipeline orchestrator.
    
    Responsibilities:
    - Load and validate prompt templates
    - Execute prompts with injected dependencies  
    - Manage context flow through pipeline stages
    - Validate outputs against schemas
    - Emit lifecycle events
    - Persist artifacts
    """

    def __init__(
        self,
        storage: StorageAdapter,
        llm: LLMAdapter,
        event_bus: EventBusAdapter,
        prompt_registry: Optional[PromptRegistry] = None,
    ) -> None:
        """Initialize the pipeline engine.
        
        Args:
            storage: Storage adapter for artifacts
            llm: LLM adapter for prompt completion
            event_bus: Event bus for lifecycle signals
            prompt_registry: Prompt registry (default: creates new)
        """
        self.storage = storage
        self.llm = llm
        self.event_bus = event_bus
        self.prompt_registry = prompt_registry or PromptRegistry()
        self.renderer = PromptRenderer()
        
        self._context: Optional[ExecutionContext] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize engine (load prompts, setup adapters).
        
        Called before executing any pipeline stages.
        """
        # Validate LLM adapter
        # Validate storage adapter
        # Load all prompts into registry
        
        self._initialized = True
        self.event_bus.publish("pipeline.initialized")

    async def get_stages(self) -> List[PipelineStage]:
        """Get all available pipeline stages.
        
        Returns:
            List of all pipeline stages with metadata
        """
        stages: List[PipelineStage] = []

        prompts = self.prompt_registry.all_prompts()
        for name, prompt_def in prompts.items():
            stage = PipelineStage(
                name=prompt_def.metadata.name,
                description=prompt_def.metadata.description,
                input_schema=prompt_def.metadata.input_schema.model_dump(),
                output_schema=prompt_def.metadata.output_schema.model_dump(),
                template_path=prompt_def.metadata.template_path,
                requires=prompt_def.metadata.requires,
            )
            stages.append(stage)

        return stages

    async def execute_stage(
        self,
        stage_name: str,
        context: ExecutionContext,
    ) -> ArtifactResult:
        """Execute single pipeline stage.
        
        Args:
            stage_name: Name of stage to execute
            context: Execution context with inputs
            
        Returns:
            ArtifactResult with generated content
            
        Raises:
            ValueError: If stage not found
            RuntimeError: If stage execution fails
        """
        self._context = context

        prompt_def = self.prompt_registry.get(stage_name)
        if not prompt_def:
            raise ValueError(f"Stage not found: {stage_name}")

        # Emit stage start event
        self.event_bus.publish(
            "pipeline.stage.begin",
            stage_name=stage_name,
            stage_number=context.stage_number,
        )

        try:
            # Render prompt template with context
            rendered_prompt = self.renderer.render(
                prompt_def,
                context.inputs,
                strict=False,
            )

            # Submit to LLM
            llm_response = await self.llm.complete(
                prompt=rendered_prompt,
                temperature=context.inputs.get("temperature", 0.7),
                max_tokens=context.inputs.get("max_tokens", 4096),
            )

            # Store output
            context.outputs[stage_name] = llm_response.content

            # Emit stage end event
            self.event_bus.publish(
                "pipeline.stage.end",
                stage_name=stage_name,
                output_length=len(llm_response.content),
            )

            return ArtifactResult(
                artifact_type=prompt_def.category,
                path=f"artifacts/{stage_name}.txt",
                content=llm_response.content,
                metadata={
                    "stage": stage_name,
                    "model": llm_response.model,
                    "tokens_used": llm_response.usage,
                },
            )

        except Exception as e:
            # Emit error event
            self.event_bus.publish(
                "pipeline.stage.error",
                stage_name=stage_name,
                error=str(e),
            )
            raise RuntimeError(f"Stage {stage_name} failed: {e}")

    async def execute_pipeline(
        self,
        start_stage: str,
        context: ExecutionContext,
    ) -> PipelineResult:
        """Execute pipeline from specified stage onward.
        
        Executes stages in order, passing outputs as inputs to next stage.
        
        Args:
            start_stage: Name of first stage to execute
            context: Initial execution context
            
        Returns:
            PipelineResult with all artifacts and status
        """
        self._context = context

        # Emit pipeline start
        self.event_bus.publish(
            "pipeline.start",
            project_name=context.project_name,
            start_stage=start_stage,
        )

        result = PipelineResult(success=True)
        stages = await self.get_stages()

        try:
            # Find starting index
            stage_names = [s.name for s in stages]
            if start_stage not in stage_names:
                result.success = False
                result.error = f"Start stage not found: {start_stage}"
                return result

            start_idx = stage_names.index(start_stage)

            # Execute stages in order
            for stage_num, stage in enumerate(stages[start_idx:], start=start_idx):
                context.stage_number = stage_num
                context.stage_name = stage.name

                try:
                    artifact = await self.execute_stage(stage.name, context)
                    result.stage_results[stage.name] = artifact
                    result.artifacts.append(artifact)

                    # Persist artifact
                    await self.storage.save(
                        path=artifact.path,
                        content=artifact.content,
                        artifact_type=artifact.artifact_type,
                        metadata=artifact.metadata,
                    )

                except Exception as e:
                    context.errors.append(f"Stage {stage.name}: {e}")
                    result.errors.append(str(e))
                    # Continue to next stage on error (configurable)
                    # For now, stop on first error
                    result.success = False
                    result.error = str(e)
                    break

            # Emit pipeline complete
            self.event_bus.publish(
                "pipeline.complete",
                success=result.success,
                artifacts_generated=len(result.artifacts),
            )

        except Exception as e:
            result.success = False
            result.error = str(e)

        return result

    def get_context(self) -> ExecutionContext:
        """Get current execution context.
        
        Returns:
            Current ExecutionContext or raises if not set
        """
        if self._context is None:
            raise RuntimeError("No execution context set")
        return self._context