"""Abstract interfaces for DocForge adapters.

These interfaces define the contracts that all adapters must implement.
Adapters are injected dependencies - the engine never instantiates them directly.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel


class StorageArtifact(BaseModel):
    """Metadata about a stored artifact."""

    path: str
    artifact_type: str  # "rulebook", "context", "document", etc.
    created_at: str
    modified_at: str
    version: str
    metadata: Dict[str, Any]


class StorageAdapter(ABC):
    """Interface for persisting artifacts.
    
    Implementations: LocalStorageAdapter, S3StorageAdapter (future).
    """

    @abstractmethod
    async def save(
        self,
        path: str,
        content: Union[str, bytes],
        artifact_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StorageArtifact:
        """Save artifact and return metadata."""
        pass

    @abstractmethod
    async def load(self, path: str) -> Union[str, bytes]:
        """Load artifact content by path."""
        pass

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """Check if artifact exists."""
        pass

    @abstractmethod
    async def list_artifacts(
        self, artifact_type: Optional[str] = None, prefix: Optional[str] = None
    ) -> List[StorageArtifact]:
        """List artifacts optionally filtered by type or path prefix."""
        pass

    @abstractmethod
    async def delete(self, path: str) -> None:
        """Delete artifact."""
        pass


class LLMResponse(BaseModel):
    """Response from LLM provider."""

    content: str
    usage: Dict[str, int]  # tokens used
    model: str
    stop_reason: Optional[str] = None


class LLMAdapter(ABC):
    """Interface for LLM providers.
    
    Implementations: AnthropicAdapter, OllamaAdapter (future), AzureOpenAIAdapter (future).
    """

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        """Send prompt to LLM and return response."""
        pass

    @abstractmethod
    async def stream_complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ):
        """Stream response from LLM."""
        pass


class ConfigSource(BaseModel):
    """Configuration source (env var, file, etc.)."""

    key: str
    value: Any
    source: str  # "env", "file", "cli", "default"


class ConfigAdapter(ABC):
    """Interface for configuration management.
    
    Implementations: EnvConfigAdapter, FileConfigAdapter, CompositeConfigAdapter.
    """

    @abstractmethod
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get config value by key."""
        pass

    @abstractmethod
    def get_source(self, key: str) -> Optional[ConfigSource]:
        """Get config value with source metadata."""
        pass

    @abstractmethod
    def all_config(self) -> Dict[str, Any]:
        """Get all configuration as dictionary."""
        pass

    @abstractmethod
    def validate(self) -> List[str]:
        """Validate required config. Return list of errors if invalid."""
        pass


class EventBusAdapter(ABC):
    """Interface for event publishing/subscription.
    
    Implementations: BlinkerEventBusAdapter, AsyncIOEventBusAdapter (future).
    """

    @abstractmethod
    def subscribe(self, event_type: str, handler: callable) -> None:
        """Subscribe to event type."""
        pass

    @abstractmethod
    def unsubscribe(self, event_type: str, handler: callable) -> None:
        """Unsubscribe from event type."""
        pass

    @abstractmethod
    def publish(
        self, event_type: str, **data: Any
    ) -> None:
        """Publish event."""
        pass
