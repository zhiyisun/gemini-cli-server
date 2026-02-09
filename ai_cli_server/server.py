"""FastAPI server with SSE streaming for multiple AI CLI backends."""
import json
import logging
import os
import sys
import shutil
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from .base_process import BaseCLIProcess, CLIProcessError
from .gemini_process import GeminiCLIProcess
from .qwen_process import QwenCodeProcess

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Global process instance and configuration
cli_process: Optional[BaseCLIProcess] = None
cli_path: Optional[str] = None
cli_type: str = "gemini"  # Default to gemini for backward compatibility


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    prompt: str
    reset: bool = False


class ResetResponse(BaseModel):
    """Response model for reset endpoint."""
    status: str
    message: str


class HealthResponse(BaseModel):
    """Response model for health endpoint."""
    status: str
    session_id: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan (startup/shutdown)."""
    # Startup
    await startup_event()
    yield
    # Shutdown
    await shutdown_event()


app = FastAPI(
    title="AI CLI Server",
    description="HTTP SSE wrapper for Gemini CLI and Qwen Code",
    version="0.2.0",
    lifespan=lifespan,
)


async def startup_event():
    """Validate the CLI path and initialize the appropriate CLI backend on server startup."""
    global cli_path, cli_type, cli_process

    # Determine CLI type (default to gemini for backward compatibility)
    cli_type = os.getenv("CLI_TYPE", "gemini").lower()
    
    if cli_type not in ["gemini", "qwen"]:
        raise CLIProcessError(f"Invalid CLI_TYPE: {cli_type}. Must be 'gemini' or 'qwen'")

    # Get CLI path from environment or resolve from PATH/bundled defaults
    cli_path = os.getenv("CLI_PATH")

    def resolve_cli_path(path_hint: Optional[str]) -> Optional[str]:
        if not path_hint:
            return None
        if os.path.exists(path_hint):
            return path_hint
        resolved = shutil.which(path_hint)
        return resolved

    if cli_path:
        resolved_path = resolve_cli_path(cli_path)
        if not resolved_path:
            raise CLIProcessError(f"{cli_type.title()} CLI not found at {cli_path} or in PATH")
        cli_path = resolved_path
    else:
        if cli_type == "gemini":
            resolved_path = resolve_cli_path("gemini")
            if resolved_path:
                cli_path = resolved_path
            else:
                default_path = str(Path(__file__).parent.parent / "gemini-cli" / "bundle" / "gemini.js")
                if not os.path.exists(default_path):
                    raise CLIProcessError(
                        f"Gemini CLI not found. Please ensure:\n"
                        f"  1. The gemini CLI is available in PATH (gemini)\n"
                        f"  2. Or the gemini-cli submodule is initialized and built\n"
                        f"     - git submodule update --init --recursive\n"
                        f"     - cd gemini-cli && npm install && npm run build && cd ..\n"
                        f"  3. Or set CLI_PATH environment variable to the correct path"
                    )
                cli_path = default_path
        elif cli_type == "qwen":
            resolved_path = resolve_cli_path("qwen") or resolve_cli_path("qwen-code")
            if resolved_path:
                cli_path = resolved_path
            else:
                default_path = str(Path(__file__).parent.parent / "qwen-code" / "dist" / "cli.js")
                if not os.path.exists(default_path):
                    raise CLIProcessError(
                        f"Qwen Code CLI not found. Please ensure:\n"
                        f"  1. The Qwen CLI is available in PATH (qwen)\n"
                        f"  2. Or the qwen-code directory is present and built\n"
                        f"     - cd qwen-code && npm install && npm run build && cd ..\n"
                        f"  3. Or set CLI_PATH environment variable to the correct path"
                    )
                cli_path = default_path

    logger.info(f"{cli_type.title()} CLI path validated: {cli_path}")


async def shutdown_event():
    """Stop the CLI process on server shutdown."""
    global cli_process
    
    if cli_process:
        await cli_process.stop()
        logger.info(f"{cli_type.title()} CLI stopped")


def get_cli_process() -> BaseCLIProcess:
    """Get the global CLI process instance."""
    if cli_process is None:
        logger.error("cli_process is None")
        raise HTTPException(status_code=503, detail=f"{cli_type.title()} CLI is not running")
    
    logger.debug(f"Checking process status: is_running={cli_process.is_running}, returncode={cli_process._process.returncode if cli_process._process else 'N/A'}")
    
    if not cli_process.is_running:
        logger.error(f"{cli_type.title()} CLI is not running: is_running={cli_process.is_running}")
        raise HTTPException(status_code=503, detail=f"{cli_type.title()} CLI is not running")
    
    return cli_process


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    session_id = None
    if cli_process and cli_process.is_running:
        session_id = cli_process.session_id
    
    return HealthResponse(status="ok", session_id=session_id)


@app.post("/reset", response_model=ResetResponse)
async def reset():
    """Reset the session (no-op for per-request processes)."""
    return ResetResponse(
        status="reset",
        message="No persistent session. A new process is created per request.",
    )


@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Send a prompt and receive streaming SSE response.
    
    The response is a stream of Server-Sent Events with JSONL data.
    Each event contains a JSON object from the CLI's stream-json output.
    """
    global cli_process
    
    # Reset if requested
    if request.reset:
        await reset()
    
    # Instantiate the appropriate CLI process
    if cli_type == "gemini":
        proc = GeminiCLIProcess(cli_path=cli_path)
    elif cli_type == "qwen":
        proc = QwenCodeProcess(cli_path=cli_path)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown CLI type: {cli_type}")

    async def event_generator():
        """Generate SSE events from CLI output."""
        try:
            async for event in proc.run_prompt_stream(request.prompt):
                yield {
                    "event": event.get("type", "message"),
                    "data": json.dumps(event),
                }

                if event.get("type") == "result":
                    break

        except CLIProcessError as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)}),
            }

    return EventSourceResponse(event_generator())


def main():
    """Run the server."""
    import uvicorn
    
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "8000"))
    
    logger.info(f"Starting AI CLI Server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
