"""Tests for LLM adapter."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from docforge.adapters.llm import AnthropicAdapter
from docforge.core.interfaces.adapters import LLMResponse


@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic client."""
    client = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_anthropic_adapter_initialization():
    """Test AnthropicAdapter initialization."""
    # Set API key for test
    import os
    os.environ["ANTHROPIC_API_KEY"] = "test-key"
    
    try:
        adapter = AnthropicAdapter(model="claude-3-opus-20240229")
        assert adapter.model == "claude-3-opus-20240229"
    finally:
        os.environ.pop("ANTHROPIC_API_KEY", None)


@pytest.mark.asyncio
async def test_anthropic_adapter_complete():
    """Test that complete method is async and callable."""
    import os
    import asyncio
    os.environ["ANTHROPIC_API_KEY"] = "test-key"
    
    try:
        adapter = AnthropicAdapter(model="claude-3-opus-20240229")
        
        # Verify the method exists and is awaitable
        assert hasattr(adapter, 'complete')
        assert asyncio.iscoroutinefunction(adapter.complete)
        
        # Mock the entire async_client at the instance level
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Test response")]
        mock_response.model = "claude-3-opus-20240229"
        mock_response.usage = MagicMock(input_tokens=10, output_tokens=5)
        mock_response.stop_reason = "end_turn"
        
        # Create a coroutine that returns our mock response
        async def mock_create(*args, **kwargs):
            return mock_response
        
        # Replace the async_client's messages.create method
        adapter.async_client.messages.create = mock_create
        
        response = await adapter.complete(
            prompt="Test prompt",
            temperature=0.7,
            max_tokens=1000,
        )
        
        assert isinstance(response, LLMResponse)
        assert response.content == "Test response"
        assert response.model == "claude-3-opus-20240229"
    finally:
        os.environ.pop("ANTHROPIC_API_KEY", None)


@pytest.mark.asyncio
async def test_anthropic_adapter_complete_async():
    """Test asynchronous completion."""
    import os
    os.environ["ANTHROPIC_API_KEY"] = "test-key"
    
    try:
        adapter = AnthropicAdapter(model="claude-3-opus-20240229")
        
        with patch.object(adapter, 'async_client') as mock_client:
            # Mock the response
            mock_message = MagicMock()
            mock_message.content = [MagicMock(text="Generated async response")]
            mock_message.model = "claude-3-opus-20240229"
            mock_message.usage = MagicMock(input_tokens=200, output_tokens=75)
            mock_message.stop_reason = "end_turn"
            
            async def async_create(*args, **kwargs):
                return mock_message
            
            mock_client.messages.create = async_create
            
            response = await adapter.complete(
                prompt="Test async prompt",
                temperature=0.5,
                max_tokens=2000,
            )
            
            assert isinstance(response, LLMResponse)
            assert response.content == "Generated async response"
            assert response.usage["input_tokens"] == 200
    finally:
        os.environ.pop("ANTHROPIC_API_KEY", None)


@pytest.mark.asyncio
async def test_anthropic_adapter_stream():
    """Test streaming completion."""
    import os
    os.environ["ANTHROPIC_API_KEY"] = "test-key"
    
    try:
        adapter = AnthropicAdapter(model="claude-3-opus-20240229")
        
        # stream_complete is an async generator
        # For testing, just verify it can be called
        gen = adapter.stream_complete(
            prompt="Streaming test",
            temperature=0.7,
        )
        
        # Verify we get an async generator
        assert hasattr(gen, '__aiter__') or hasattr(gen, '__iter__')
    finally:
        os.environ.pop("ANTHROPIC_API_KEY", None)


@pytest.mark.asyncio
async def test_anthropic_adapter_with_custom_model():
    """Test adapter with different model."""
    import os
    os.environ["ANTHROPIC_API_KEY"] = "test-key"
    
    try:
        adapter = AnthropicAdapter(
            model="claude-3-sonnet-20240229"
        )
        assert adapter.model == "claude-3-sonnet-20240229"
    finally:
        os.environ.pop("ANTHROPIC_API_KEY", None)


@pytest.mark.asyncio
async def test_llm_response_creation():
    """Test LLMResponse model creation."""
    response = LLMResponse(
        content="Test response",
        model="claude-3-opus-20240229",
        usage={"input_tokens": 100, "output_tokens": 50},
        stop_reason="end_turn",
    )
    
    assert response.content == "Test response"
    assert response.model == "claude-3-opus-20240229"
    assert response.usage["input_tokens"] == 100
    assert response.stop_reason == "end_turn"
