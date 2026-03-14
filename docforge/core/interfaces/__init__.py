"""Interfaces package for DocForge core.

This package defines the abstract contracts that all adapters and 
the engine must implement.
"""

from docforge.core.interfaces.adapters import (
    ConfigAdapter,
    ConfigSource,
    EventBusAdapter,
    LLMAdapter,
    LLMResponse,
    StorageAdapter,
    StorageArtifact,
)
from docforge.core.interfaces.engine import (
    ArtifactResult,
    ExecutionContext,
    PipelineEngine,
    PipelineResult,
    PipelineStage,
)

__all__ = [
    # Adapters
    "StorageAdapter",
    "StorageArtifact",
    "LLMAdapter",
    "LLMResponse",
    "ConfigAdapter",
    "ConfigSource",
    "EventBusAdapter",
    # Engine
    "PipelineEngine",
    "ExecutionContext",
    "PipelineStage",
    "ArtifactResult",
    "PipelineResult",
]