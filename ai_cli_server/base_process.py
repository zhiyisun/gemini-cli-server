"""Base CLI process manager for SSE server."""
import asyncio
import json
import logging
import os
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import AsyncIterator, Optional, List

# Setup logging
logger = logging.getLogger(__name__)


class CLIProcessError(Exception):
    """Exception raised for CLI process errors."""
    pass


class BaseCLIProcess(ABC):
    """Base class for managing CLI processes with stdin/stdout communication."""

    def __init__(self, cli_path: Optional[str] = None):
        """
        Initialize the CLI process manager.

        Args:
            cli_path: Path to the CLI executable. Defaults to bundled version.
        """
        if cli_path is None:
            cli_path = self._get_default_cli_path()
        
        self.cli_path = cli_path
        self._process: Optional[asyncio.subprocess.Process] = None
        self._session_id: Optional[str] = None
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._reader_task: Optional[asyncio.Task] = None

    @abstractmethod
    def _get_default_cli_path(self) -> str:
        """Get the default CLI path for this implementation."""
        pass

    @abstractmethod
    def _get_cli_executable_args(self) -> List[str]:
        """Get the executable and base arguments to start the CLI."""
        pass

    @abstractmethod
    def _get_stream_args(self) -> List[str]:
        """Get arguments for stream-json output mode."""
        pass

    @abstractmethod
    def _get_auto_approve_args(self) -> List[str]:
        """Get arguments for auto-approval mode."""
        pass

    @abstractmethod
    def _get_prompt_args(self, prompt: str) -> List[str]:
        """Get arguments for running a single prompt."""
        pass

    @property
    def is_running(self) -> bool:
        """Check if the process is currently running."""
        if self._process is None:
            return False
        return self._process.returncode is None

    @property
    def session_id(self) -> Optional[str]:
        """Get the current session ID from the init event."""
        return self._session_id

    async def _background_reader(self) -> None:
        """
        Background task to read events from the CLI process.
        This keeps the process alive by continuously reading from stdout.
        """
        logger.info("Background reader started")
        try:
            while self._process and self.is_running:
                line = await self._process.stdout.readline()
                if not line:
                    # Process closed stdout, it's probably exiting
                    logger.warning("Process closed stdout, exiting reader")
                    break
                
                try:
                    event = json.loads(line.decode("utf-8").strip())
                    await self._event_queue.put(event)
                    logger.debug(f"Queued event: {event.get('type')}")
                    
                    # Extract session_id from init event
                    if event.get("type") == "init" and self._session_id is None:
                        self._session_id = event.get("session_id")
                        logger.info(f"Session ID set to: {self._session_id}")
                except json.JSONDecodeError as e:
                    # Skip invalid JSON lines
                    logger.debug(f"Skipped invalid JSON line")
                    pass
        except asyncio.CancelledError:
            logger.info("Background reader cancelled")
            pass
        except Exception as e:
            # Log error but don't crash
            logger.error(f"Error in background reader: {e}")
            pass
        finally:
            logger.info("Background reader stopped")

    async def start(self) -> None:
        """
        Start the CLI process.

        Raises:
            CLIProcessError: If process is already running or cannot be started.
        """
        if self.is_running:
            raise CLIProcessError("Process is already running")

        try:
            logger.info(f"Starting CLI from {self.cli_path}")
            
            # Build command arguments
            cmd_args = self._get_cli_executable_args()
            cmd_args.extend(self._get_stream_args())
            cmd_args.extend(self._get_auto_approve_args())
            
            # Start CLI process
            self._process = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ.copy(),  # Pass through environment for auth
            )
            logger.info(f"Process created with PID {self._process.pid}")

            # Start the background reader task
            self._reader_task = asyncio.create_task(self._background_reader())
            logger.info("Background reader task started")
            logger.info(f"Process running: {self.is_running}")

        except FileNotFoundError:
            logger.error(f"CLI not found at {self.cli_path}")
            raise CLIProcessError(f"CLI not found at {self.cli_path}")
        except CLIProcessError:
            # Re-raise our custom errors
            raise
        except Exception as e:
            logger.error(f"Failed to start process: {e}")
            raise CLIProcessError(f"Failed to start process: {e}")

    async def stop(self, timeout: float = 5.0) -> None:
        """
        Stop the CLI process.

        Args:
            timeout: Maximum time to wait for process termination.
        """
        if not self.is_running:
            return

        # Cancel background reader task
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass

        try:
            self._process.terminate()
            await asyncio.wait_for(self._process.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            # Force kill if terminate doesn't work
            self._process.kill()
            await self._process.wait()
        finally:
            self._process = None
            self._session_id = None
            self._reader_task = None

    async def _read_init_event(self) -> None:
        """
        Read events until we get the init event with session ID.

        Raises:
            CLIProcessError: If we can't read the init event.
        """
        try:
            async for event in self.read_events():
                if event.get("type") == "init":
                    self._session_id = event.get("session_id")
                    return
                # Also check for error events
                if event.get("type") == "error":
                    raise CLIProcessError(f"Init error: {event.get('error')}")
        except CLIProcessError:
            raise
        except Exception as e:
            raise CLIProcessError(f"Failed to read init event: {e}")

    async def send_prompt(self, prompt: str) -> None:
        """
        Send a prompt to the CLI process.

        Args:
            prompt: The prompt text to send.

        Raises:
            CLIProcessError: If process is not running.
        """
        if not self.is_running:
            logger.warning(
                "Process not running. is_running=%s, returncode=%s",
                self.is_running,
                self._process.returncode if self._process else "N/A",
            )
            raise CLIProcessError("Process is not running")

        # Write prompt followed by newline
        logger.info(f"Sending prompt: {prompt[:50]}...")
        self._process.stdin.write((prompt + "\n").encode("utf-8"))
        await self._process.stdin.drain()
        logger.debug("Prompt written to stdin")

    async def run_prompt_stream(self, prompt: str) -> AsyncIterator[dict]:
        """
        Run a single non-interactive prompt and stream JSON events.

        Args:
            prompt: The prompt text to send.

        Yields:
            Parsed JSON events as dictionaries.
        """
        start_time = time.monotonic()

        try:
            async for event in self._run_stream_json_prompt(prompt):
                yield event
            return
        except CLIProcessError as e:
            if not self._is_stream_args_error(str(e)):
                raise

        async for event in self._run_plain_prompt(prompt, start_time):
            yield event

    def _is_stream_args_error(self, message: str) -> bool:
        """Check if error indicates unsupported stream-json arguments."""
        lower_msg = message.lower()
        if "output-format" in lower_msg or "outputformat" in lower_msg:
            if "unknown" in lower_msg or "unrecognized" in lower_msg:
                return True
        return False

    async def _run_stream_json_prompt(self, prompt: str) -> AsyncIterator[dict]:
        """Run prompt using stream-json output and yield parsed events."""
        try:
            cmd_args = self._get_cli_executable_args()
            cmd_args.extend(self._get_prompt_args(prompt))
            cmd_args.extend(self._get_stream_args())
            cmd_args.extend(self._get_auto_approve_args())

            process = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ.copy(),
            )
        except FileNotFoundError:
            raise CLIProcessError(f"CLI not found at {self.cli_path}")
        except Exception as e:
            raise CLIProcessError(f"Failed to start process: {e}")

        try:
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                try:
                    event = json.loads(line.decode("utf-8").strip())
                except json.JSONDecodeError:
                    logger.debug("Skipped invalid JSON line")
                    continue
                yield event

            await process.wait()
            if process.returncode and process.returncode != 0:
                stderr_data = await process.stderr.read()
                stderr_text = stderr_data.decode("utf-8", errors="replace").strip()
                raise CLIProcessError(
                    f"CLI exited with code {process.returncode}: {stderr_text}"
                )
        finally:
            if process.returncode is None:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()

    async def _run_plain_prompt(self, prompt: str, start_time: float) -> AsyncIterator[dict]:
        """Run prompt without stream-json and yield synthesized events."""
        try:
            cmd_args = self._get_cli_executable_args()
            cmd_args.extend(self._get_prompt_args(prompt))
            cmd_args.extend(self._get_auto_approve_args())

            process = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ.copy(),
            )
        except FileNotFoundError:
            raise CLIProcessError(f"CLI not found at {self.cli_path}")
        except Exception as e:
            raise CLIProcessError(f"Failed to start process: {e}")

        try:
            output_chunks: List[str] = []
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                text = line.decode("utf-8", errors="replace")
                if not text:
                    continue
                output_chunks.append(text)
                yield {
                    "type": "message",
                    "role": "assistant",
                    "content": text,
                }

            await process.wait()
            if process.returncode and process.returncode != 0:
                stderr_data = await process.stderr.read()
                stderr_text = stderr_data.decode("utf-8", errors="replace").strip()
                raise CLIProcessError(
                    f"CLI exited with code {process.returncode}: {stderr_text}"
                )

            duration_ms = int((time.monotonic() - start_time) * 1000)
            yield {
                "type": "result",
                "duration_ms": duration_ms,
                "stats": {
                    "input_tokens": 0,
                    "output_tokens": 0,
                },
                "result": "".join(output_chunks).strip(),
            }
        finally:
            if process.returncode is None:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()

    async def read_events(self) -> AsyncIterator[dict]:
        """
        Read and parse JSONL events from the CLI process stdout.

        Yields:
            Parsed JSON events as dictionaries.

        Raises:
            CLIProcessError: If process is not running.
        """
        if not self.is_running:
            raise CLIProcessError("Process is not running")

        while self.is_running:
            try:
                # Wait for events from the background reader
                event = await asyncio.wait_for(self._event_queue.get(), timeout=30.0)
                yield event
            except asyncio.TimeoutError:
                # No events for 30 seconds, assume process is idle
                continue
            except asyncio.CancelledError:
                break

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
