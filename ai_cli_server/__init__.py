"""AI CLI Server - HTTP SSE wrapper for Gemini CLI and Qwen Code."""

__version__ = "0.2.0"

from .process import GeminiProcess, GeminiProcessError
from .base_process import BaseCLIProcess, CLIProcessError
from .gemini_process import GeminiCLIProcess
from .qwen_process import QwenCodeProcess
from .client import GeminiClient, OpenAICompatibleClient, GeminiClientError

__all__ = [
    "GeminiProcess",
    "GeminiProcessError",
    "BaseCLIProcess",
    "CLIProcessError",
    "GeminiCLIProcess",
    "QwenCodeProcess",
    "GeminiClient",
    "OpenAICompatibleClient",
    "GeminiClientError",
]

