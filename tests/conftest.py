"""Pytest configuration and fixtures."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from docforge.core.interfaces import (
    ConfigAdapter,
    EventBusAdapter,
    LLMAdapter,
    PipelineEngine,
    StorageAdapter,
)


@pytest.fixture
def mock_storage_adapter() -> StorageAdapter:
    """Create mock StorageAdapter."""
    adapter = AsyncMock(spec=StorageAdapter)
    return adapter


@pytest.fixture
def mock_llm_adapter() -> LLMAdapter:
    """Create mock LLMAdapter."""
    adapter = AsyncMock(spec=LLMAdapter)
    return adapter


@pytest.fixture
def mock_config_adapter() -> ConfigAdapter:
    """Create mock ConfigAdapter."""
    adapter = MagicMock(spec=ConfigAdapter)
    adapter.get.return_value = None
    adapter.all_config.return_value = {}
    adapter.validate.return_value = []
    return adapter


@pytest.fixture
def mock_event_bus() -> EventBusAdapter:
    """Create mock EventBusAdapter."""
    adapter = MagicMock(spec=EventBusAdapter)
    return adapter
