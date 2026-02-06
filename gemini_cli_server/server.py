"""FastAPI server with SSE streaming for Gemini CLI."""
import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from .process import GeminiProcess, GeminiProcessError

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Global process instance

gemini_process: Optional[GeminiProcess] = None
cli_path: Optional[str] = None


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
    title="Gemini CLI Server",
    description="HTTP SSE wrapper for Gemini CLI",
    version="0.1.0",
    lifespan=lifespan,
)


async def startup_event():
    """Validate the Gemini CLI path on server startup."""
    global cli_path

    cli_path = os.getenv("GEMINI_CLI_PATH")

    # Check if CLI exists if path is specified
    if cli_path and not os.path.exists(cli_path):
        raise GeminiProcessError(f"Gemini CLI not found at {cli_path}")

    # Check if default path exists
    if not cli_path:
        default_path = str(Path(__file__).parent.parent / "gemini-cli" / "bundle" / "gemini.js")
        if not os.path.exists(default_path):
            raise GeminiProcessError(
                f"Gemini CLI not found. Please ensure:\n"
                f"  1. The gemini-cli submodule is initialized: git submodule update --init --recursive\n"
                f"  2. The Gemini CLI is built: cd gemini-cli && npm install && npm run build && cd ..\n"
                f"  3. Or set GEMINI_CLI_PATH environment variable to the correct path"
            )
        cli_path = default_path

    logger.info(f"Gemini CLI path validated: {cli_path}")


async def shutdown_event():
    """Stop the Gemini CLI process on server shutdown."""
    global gemini_process
    
    if gemini_process:
        await gemini_process.stop()
        logger.info("Gemini CLI stopped")


def get_gemini_process() -> GeminiProcess:
    """Get the global Gemini process instance."""
    if gemini_process is None:
        logger.error("gemini_process is None")
        raise HTTPException(status_code=503, detail="Gemini CLI is not running")
    
    logger.debug(f"Checking process status: is_running={gemini_process.is_running}, returncode={gemini_process._process.returncode if gemini_process._process else 'N/A'}")
    
    if not gemini_process.is_running:
        logger.error(f"Gemini CLI is not running: is_running={gemini_process.is_running}")
        raise HTTPException(status_code=503, detail="Gemini CLI is not running")
    
    return gemini_process


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    session_id = None
    if gemini_process and gemini_process.is_running:
        session_id = gemini_process.session_id
    
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
    Each event contains a JSON object from Gemini CLI's stream-json output.
    """
    global gemini_process
    
    # Reset if requested
    if request.reset:
        await reset()
    
    proc = GeminiProcess(cli_path=cli_path)

    async def event_generator():
        """Generate SSE events from Gemini CLI output."""
        try:
            async for event in proc.run_prompt_stream(request.prompt):
                yield {
                    "event": event.get("type", "message"),
                    "data": json.dumps(event),
                }

                if event.get("type") == "result":
                    break

        except GeminiProcessError as e:
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
    
    logger.info(f"Starting Gemini CLI Server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
