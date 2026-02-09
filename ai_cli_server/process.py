"""Gemini CLI process manager for SSE server.

This module provides backward compatibility by re-exporting from gemini_process.
For new code, import from gemini_process or qwen_process directly.
"""
from .base_process import BaseCLIProcess, CLIProcessError
from .gemini_process import GeminiCLIProcess

# Backward compatibility
GeminiProcess = GeminiCLIProcess
GeminiProcessError = CLIProcessError

__all__ = ["GeminiProcess", "GeminiProcessError", "BaseCLIProcess", "CLIProcessError"]
