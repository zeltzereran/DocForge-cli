"""Anthropic Claude LLM adapter."""

import os
from typing import Any, Optional

from anthropic import Anthropic, AsyncAnthropic

from docforge.core.interfaces.adapters import LLMAdapter, LLMResponse


class AnthropicAdapter(LLMAdapter):
    """LLM adapter for Anthropic Claude API.
    
    Supports both sync and async patterns. Credentials loaded from:
    - ANTHROPIC_API_KEY environment variable
    """

    def __init__(self, model: str = "claude-3-opus-20240229"):
        """Initialize Anthropic adapter.
        
        Args:
            model: Claude model to use (default: claude-3-opus)
            
        Raises:
            ValueError: If ANTHROPIC_API_KEY is not set
        """
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable not set. "
                "Please configure your API key."
            )

        self.model = model
        self.sync_client = Anthropic(api_key=api_key)
        self.async_client = AsyncAnthropic(api_key=api_key)

    async def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        """Send prompt to Claude and return response.
        
        Args:
            prompt: User message/prompt
            system: Optional system prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Max tokens in response
            **kwargs: Additional arguments passed to API
            
        Returns:
            LLMResponse with generated content
        """
        messages = [{"role": "user", "content": prompt}]

        response = await self.async_client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system or "",
            messages=messages,
            **kwargs,
        )

        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text

        return LLMResponse(
            content=content,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            model=response.model,
            stop_reason=response.stop_reason,
        )

    async def stream_complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ):
        """Stream response from Claude.
        
        Args:
            prompt: User message/prompt
            system: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Max tokens in response
            **kwargs: Additional arguments passed to API
            
        Yields:
            Text chunks from response
        """
        messages = [{"role": "user", "content": prompt}]

        with self.sync_client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system or "",
            messages=messages,
            **kwargs,
        ) as stream:
            for text in stream.text_stream:
                yield text
