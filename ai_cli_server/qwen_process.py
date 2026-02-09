"""Qwen Code CLI process manager."""
from pathlib import Path
from typing import List

from .base_process import BaseCLIProcess


class QwenCodeProcess(BaseCLIProcess):
    """Manages a Qwen Code CLI process with stdin/stdout communication."""

    def _get_default_cli_path(self) -> str:
        """Get the default Qwen Code CLI path."""
        base_dir = Path(__file__).parent.parent
        return str(base_dir / "qwen-code" / "dist" / "cli.js")

    def _get_cli_executable_args(self) -> List[str]:
        """Get the executable and base arguments to start Qwen Code CLI."""
        cli_path = Path(self.cli_path)
        if cli_path.suffix in {".js", ".mjs", ".cjs"}:
            return ["node", str(cli_path)]
        return [str(cli_path)]

    def _get_stream_args(self) -> List[str]:
        """Get arguments for stream-json output mode."""
        return ["--output-format", "stream-json"]

    def _get_auto_approve_args(self) -> List[str]:
        """Get arguments for auto-approval mode."""
        return ["--yolo"]

    def _get_prompt_args(self, prompt: str) -> List[str]:
        """Get arguments for running a single prompt."""
        return ["-p", prompt]
