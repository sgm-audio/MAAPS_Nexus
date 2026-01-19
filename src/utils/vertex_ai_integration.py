"""
Vertex AI Integration for MAAPS Nexus
Provides access to Claude and Gemini models via Google Cloud Vertex AI
"""

import os
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class VertexAIConfig:
    """Configuration for Vertex AI"""
    project_id: str
    location: str = "us-central1"
    model: str = "claude-3-5-sonnet@20241022"


class VertexAIClient:
    """
    Client for interacting with Claude and Gemini models via Google Cloud Vertex AI.

    Supports:
    - Claude 3.5 Sonnet, Opus, Haiku
    - Gemini 1.5 Pro, Flash

    Authentication:
    - Option 1: Application Default Credentials (gcloud auth application-default login)
    - Option 2: Service Account Key (GOOGLE_APPLICATION_CREDENTIALS env var)
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        Initialize Vertex AI client.

        Args:
            project_id: GCP project ID (defaults to VERTEX_PROJECT_ID env var)
            location: GCP region (defaults to VERTEX_LOCATION or us-central1)
            model: Model name (defaults to VERTEX_MODEL or claude-3-5-sonnet@20241022)
        """
        self.project_id = project_id or os.getenv("VERTEX_PROJECT_ID")
        self.location = location or os.getenv("VERTEX_LOCATION", "us-central1")
        self.model = model or os.getenv("VERTEX_MODEL", "claude-3-5-sonnet@20241022")

        if not self.project_id:
            raise ValueError(
                "project_id is required. Set VERTEX_PROJECT_ID env var or pass as parameter."
            )

        self._client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the Anthropic Vertex AI client"""
        try:
            from anthropic import AnthropicVertex

            self._client = AnthropicVertex(
                project_id=self.project_id,
                region=self.location
            )
            logger.info(f"Vertex AI client initialized: {self.model} in {self.location}")

        except ImportError:
            raise ImportError(
                "anthropic[vertex] package not installed. "
                "Run: pip install 'anthropic[vertex]'"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Vertex AI client: {e}")

    def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> str:
        """
        Send a chat completion request to Vertex AI.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional model parameters

        Returns:
            Generated text response
        """
        if not self._client:
            raise RuntimeError("Client not initialized")

        # Use Claude models via Vertex AI
        if "claude" in self.model.lower():
            try:
                request_params = {
                    "model": self.model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": messages,
                }

                if system_prompt:
                    request_params["system"] = system_prompt

                request_params.update(kwargs)

                response = self._client.messages.create(**request_params)

                return response.content[0].text

            except Exception as e:
                logger.error(f"Vertex AI chat error: {e}")
                raise

        # Use Gemini models via Vertex AI
        elif "gemini" in self.model.lower():
            try:
                from vertexai.generative_models import GenerativeModel
                import vertexai

                vertexai.init(project=self.project_id, location=self.location)

                model = GenerativeModel(self.model)

                # Convert messages to Gemini format
                prompt_parts = []
                if system_prompt:
                    prompt_parts.append(system_prompt)

                for msg in messages:
                    role_prefix = "User: " if msg["role"] == "user" else "Assistant: "
                    prompt_parts.append(f"{role_prefix}{msg['content']}")

                full_prompt = "\n\n".join(prompt_parts)

                response = model.generate_content(
                    full_prompt,
                    generation_config={
                        "temperature": temperature,
                        "max_output_tokens": max_tokens,
                    }
                )

                return response.text

            except ImportError:
                raise ImportError(
                    "google-cloud-aiplatform package not installed. "
                    "Run: pip install google-cloud-aiplatform"
                )
            except Exception as e:
                logger.error(f"Vertex AI Gemini error: {e}")
                raise

        else:
            raise ValueError(f"Unsupported model: {self.model}")

    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ):
        """
        Stream a chat completion response from Vertex AI.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional model parameters

        Yields:
            Text chunks as they arrive
        """
        if not self._client:
            raise RuntimeError("Client not initialized")

        if "claude" in self.model.lower():
            try:
                request_params = {
                    "model": self.model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": messages,
                }

                if system_prompt:
                    request_params["system"] = system_prompt

                request_params.update(kwargs)

                with self._client.messages.stream(**request_params) as stream:
                    for text in stream.text_stream:
                        yield text

            except Exception as e:
                logger.error(f"Vertex AI stream error: {e}")
                raise
        else:
            # Fallback to non-streaming for unsupported models
            response = self.chat(
                messages=messages,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            yield response

    def test_connection(self) -> Dict[str, Any]:
        """
        Test the Vertex AI connection.

        Returns:
            Dict with status and details
        """
        try:
            response = self.chat(
                messages=[{"role": "user", "content": "Say 'connected' only."}],
                max_tokens=10
            )

            return {
                "status": "success",
                "model": self.model,
                "location": self.location,
                "project_id": self.project_id,
                "response": response.strip()
            }

        except Exception as e:
            return {
                "status": "error",
                "model": self.model,
                "location": self.location,
                "project_id": self.project_id,
                "error": str(e)
            }


# Available models
CLAUDE_MODELS = {
    "sonnet": "claude-3-5-sonnet@20241022",
    "opus": "claude-3-opus@20240229",
    "haiku": "claude-3-haiku@20240307",
}

GEMINI_MODELS = {
    "pro": "gemini-1.5-pro",
    "flash": "gemini-1.5-flash",
}
