"""
Unified LLM Integration Layer for MAAPS Nexus
Supports multiple LLM providers with a consistent interface
"""

import os
import logging
from typing import List, Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers"""
    VERTEX_AI = "vertex_ai"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OLLAMA = "ollama"


class LLMClient:
    """
    Unified interface for multiple LLM providers.

    Supports:
    - Vertex AI (Claude + Gemini via Google Cloud)
    - Anthropic (Claude direct API)
    - OpenAI (GPT models)
    - Ollama (local models)
    """

    def __init__(self, provider: str = "vertex_ai", **kwargs):
        """
        Initialize LLM client with specified provider.

        Args:
            provider: LLM provider name (vertex_ai, anthropic, openai, ollama)
            **kwargs: Provider-specific configuration
        """
        self.provider = LLMProvider(provider)
        self._client = None
        self._initialize_client(**kwargs)

    def _initialize_client(self, **kwargs):
        """Initialize the appropriate provider client"""

        if self.provider == LLMProvider.VERTEX_AI:
            from .vertex_ai_integration import VertexAIClient
            self._client = VertexAIClient(**kwargs)
            logger.info("Initialized Vertex AI client")

        elif self.provider == LLMProvider.ANTHROPIC:
            try:
                from anthropic import Anthropic
                api_key = kwargs.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
                self._client = Anthropic(api_key=api_key)
                logger.info("Initialized Anthropic client")
            except ImportError:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")

        elif self.provider == LLMProvider.OPENAI:
            try:
                from openai import OpenAI
                api_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY")
                self._client = OpenAI(api_key=api_key)
                logger.info("Initialized OpenAI client")
            except ImportError:
                raise ImportError("openai package not installed. Run: pip install openai")

        elif self.provider == LLMProvider.OLLAMA:
            try:
                import requests
                self._ollama_base_url = kwargs.get("base_url", "http://localhost:11434")
                # Test connection
                response = requests.get(f"{self._ollama_base_url}/api/tags")
                if response.ok:
                    logger.info("Initialized Ollama client")
                else:
                    raise ConnectionError("Ollama server not responding")
            except ImportError:
                raise ImportError("requests package not installed. Run: pip install requests")

    def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Send a chat completion request.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            model: Optional model override
            **kwargs: Additional model parameters

        Returns:
            Generated text response
        """

        if self.provider == LLMProvider.VERTEX_AI:
            return self._client.chat(
                messages=messages,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

        elif self.provider == LLMProvider.ANTHROPIC:
            model = model or os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
            request_params = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages,
            }
            if system_prompt:
                request_params["system"] = system_prompt

            response = self._client.messages.create(**request_params)
            return response.content[0].text

        elif self.provider == LLMProvider.OPENAI:
            model = model or os.getenv("OPENAI_MODEL", "gpt-4")
            chat_messages = []
            if system_prompt:
                chat_messages.append({"role": "system", "content": system_prompt})
            chat_messages.extend(messages)

            response = self._client.chat.completions.create(
                model=model,
                messages=chat_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response.choices[0].message.content

        elif self.provider == LLMProvider.OLLAMA:
            import requests
            model = model or os.getenv("OLLAMA_MODEL", "llama2")

            # Build prompt from messages
            prompt_parts = []
            if system_prompt:
                prompt_parts.append(f"System: {system_prompt}")
            for msg in messages:
                role = msg["role"].capitalize()
                prompt_parts.append(f"{role}: {msg['content']}")
            prompt_parts.append("Assistant:")
            prompt = "\n\n".join(prompt_parts)

            response = requests.post(
                f"{self._ollama_base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "options": {"num_predict": max_tokens}
                }
            )

            if response.ok:
                # Ollama returns streaming response, combine all chunks
                full_response = ""
                for line in response.text.strip().split("\n"):
                    import json
                    chunk = json.loads(line)
                    full_response += chunk.get("response", "")
                return full_response
            else:
                raise RuntimeError(f"Ollama error: {response.text}")

    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        model: Optional[str] = None,
        **kwargs
    ):
        """
        Stream a chat completion response.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            model: Optional model override
            **kwargs: Additional parameters

        Yields:
            Text chunks as they arrive
        """
        if self.provider == LLMProvider.VERTEX_AI:
            yield from self._client.stream_chat(
                messages=messages,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
        else:
            # Fallback to non-streaming for unsupported providers
            response = self.chat(
                messages=messages,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                model=model,
                **kwargs
            )
            yield response


def create_llm_client(provider: str = "vertex_ai", **kwargs) -> LLMClient:
    """
    Factory function to create an LLM client.

    Args:
        provider: LLM provider name (vertex_ai, anthropic, openai, ollama)
        **kwargs: Provider-specific configuration

    Returns:
        Initialized LLMClient instance

    Example:
        >>> client = create_llm_client("vertex_ai")
        >>> response = client.chat(
        ...     messages=[{"role": "user", "content": "Hello!"}],
        ...     system_prompt="You are a helpful assistant."
        ... )
    """
    return LLMClient(provider=provider, **kwargs)
