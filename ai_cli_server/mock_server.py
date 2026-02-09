#!/usr/bin/env python3
"""
Mock AI CLI Server for testing examples without real CLI backends.
This server responds to all endpoints and simulates AI responses.
Useful for testing examples and demonstrating functionality.
"""

import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


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


# Mock responses for different prompts
MOCK_RESPONSES = {
    "http sse": "HTTP Server-Sent Events (SSE) is a web technology that allows servers to push real-time data to web browsers without requiring reconnection. It provides a simple, standardized way to stream events from server to client over HTTP.",
    "quantum computing": "Quantum computing is a type of computing that uses quantum bits (qubits) instead of classical bits (0 and 1). Qubits can exist in superposition, allowing quantum computers to process multiple possibilities simultaneously, making them potentially much faster for certain problem types.",
    "simple analogy": "Sure! Think of quantum computers like exploring a maze: a classical computer checks one path at a time methodically, while a quantum computer can explore all possible paths simultaneously. Once it finds the solution, the quantum computer collapses to show the correct path.",
    "real-world applications": "Real-world applications of quantum computing include: drug discovery and molecular simulation, optimization problems in logistics and finance, cryptography and security, machine learning and AI, weather prediction and climate modeling, and materials science research.",
    "files": "The current directory contains several important files and folders: the 'ai_cli_server' package with server and client modules, 'examples' directory with 6 different usage examples, 'tests' directory with comprehensive test suite, configuration files like pyproject.toml and setup.py, and documentation files.",
    "remember the number 42": "I've noted the number 42. However, please remember that each request in this server is stateless - I won't remember this in future requests unless you include it in the message history.",
    "number did i": "I don't have any memory of previous requests. This is a stateless per-request model - each request is independent. To maintain context, you need to include the full conversation history in the messages array.",
    "haiku": "Bits dance in patterns,\nLogic flows through quantum gates,\nFuture fast emerges.",
}


def get_mock_response(prompt: str) -> str:
    """Get a mock response based on the prompt."""
    prompt_lower = prompt.lower()
    
    # Check for keyword matches
    for keyword, response in MOCK_RESPONSES.items():
        if keyword in prompt_lower:
            return response
    
    # Default response
    return f"This is a mock response to your prompt: '{prompt}'. In a real scenario, I would provide a detailed response from the AI model. This mock server is useful for testing the client examples without requiring the actual Gemini CLI or Qwen Code backends."


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan (startup/shutdown)."""
    logger.info("Mock server starting up")
    yield
    logger.info("Mock server shutting down")


app = FastAPI(
    title="AI CLI Server (Mock Mode)",
    description="Mock server for testing examples without real CLI backends",
    version="0.2.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        session_id="mock-session-123"
    )


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
    Send a prompt and receive streaming SSE response (mock).
    
    The response is a stream of Server-Sent Events with JSONL data.
    Each event contains a JSON object from the CLI's stream-json output.
    """
    response_text = get_mock_response(request.prompt)
    
    async def event_generator():
        """Generate SSE events from mock response."""
        # Send message chunks
        words = response_text.split()
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            yield {
                "event": "message",
                "data": json.dumps({
                    "type": "message",
                    "role": "assistant",
                    "content": chunk
                }),
            }
        
        # Send final result event
        yield {
            "event": "result",
            "data": json.dumps({
                "type": "result",
                "duration_ms": 1234,
                "stats": {
                    "input_tokens": 10,
                    "output_tokens": len(response_text.split())
                }
            }),
        }
    
    return EventSourceResponse(event_generator())


def main():
    """Run the mock server."""
    import uvicorn
    
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "8000"))
    
    logger.info(f"Starting Mock AI CLI Server on {host}:{port}")
    logger.info("This mock server simulates Gemini CLI and Qwen Code for testing")
    logger.info("Use examples/ to test the client implementations")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
