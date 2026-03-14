"""Adapters for DocForge.

Implementations of the adapter interfaces for concrete services:
- StorageAdapter: local file system
- LLMAdapter: Anthropic Claude
- ConfigAdapter: environment variables + config files
- EventBusAdapter: blinker-based event bus
"""

from docforge.adapters.events import BlinkerEventBusAdapter
from docforge.adapters.llm import AnthropicAdapter
from docforge.adapters.storage import LocalStorageAdapter

__all__ = [
    "LocalStorageAdapter",
    "AnthropicAdapter",
    "BlinkerEventBusAdapter",
]