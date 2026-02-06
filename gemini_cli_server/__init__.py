"""Gemini CLI Server - HTTP SSE wrapper for Gemini CLI."""

__version__ = "0.1.0"

from .process import GeminiProcess, GeminiProcessError
from .client import GeminiClient, OpenAICompatibleClient, GeminiClientError

__all__ = [
    "GeminiProcess",
    "GeminiProcessError",
    "GeminiClient",
    "OpenAICompatibleClient",
    "GeminiClientError",
]
