# Gemini CLI Server

A Python HTTP Server/Client wrapper for [Google Gemini CLI](https://github.com/google-gemini/gemini-cli), enabling programmatic access via REST API with Server-Sent Events (SSE) streaming.

## Features

- 🚀 **HTTP SSE Streaming**: Real-time streaming of Gemini responses, tool calls, and events
- 💬 **Session Management**: Persistent conversation sessions with automatic lifecycle management
- 🔧 **Simple Python Client**: Ergonomic Python library for consuming the API
- 🔐 **Secure Auth**: Uses existing Gemini CLI authentication (env vars)
- 📦 **Standalone**: Separate project using Gemini CLI as a Git submodule

## Architecture

```
┌─────────────────┐     HTTP POST      ┌──────────────────┐
│  Python Client  │ ───────────────────>│  FastAPI Server  │
│                 │ <─────────────────  │                  │
└─────────────────┘   SSE Stream        └──────────────────┘
                                               │
                                               ▼
                                        ┌──────────────────┐
                                        │  Gemini CLI      │
                                        │  (Node.js)       │
                                        └──────────────────┘
                                          stdin/stdout JSONL
```

## Installation

### 1. Clone the repository

If you haven't cloned yet:
```bash
git clone https://github.com/zhiyisun/gemini-cli-server.git
cd gemini-cli-server
```

Or with submodule included:
```bash
git clone --recurse-submodules https://github.com/zhiyisun/gemini-cli-server.git
cd gemini-cli-server
```

If the repo is already cloned but the submodule is missing:
```bash
git submodule update --init --recursive
```

### 2. Install Gemini CLI (submodule)

```bash
cd gemini-cli
# Checkout the latest release version
git fetch --tags
git checkout $(git describe --tags $(git rev-list --tags --max-count=1))
npm install
npm run build
cd ..
```

### 3. Set up Python environment

```bash
# Create virtual environment using uv
uv venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package
uv pip install -e .
```

## Quick Start

### Server

```bash
# Activate virtual environment (if not already activated)
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Set authentication (choose one)
export GEMINI_API_KEY="your-api-key"
# OR
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_CLOUD_PROJECT="your-project"
export GOOGLE_CLOUD_LOCATION="us-central1"

# Start server
python -m gemini_cli_server.server
```

### Client

See the [examples/](examples/) directory for sample code:

- **[simple_chat.py](examples/simple_chat.py)**: Basic single-prompt chat example with event handling
- **[multi_turn_chat.py](examples/multi_turn_chat.py)**: Multi-turn conversation example
- **[error_handling.py](examples/error_handling.py)**: Error handling and recovery patterns
- **[tool_monitoring.py](examples/tool_monitoring.py)**: Monitoring tool executions
- **[session_reset.py](examples/session_reset.py)**: Session management examples

Quick usage:
```python
from gemini_cli_server.client import GeminiClient

client = GeminiClient("http://localhost:8000")
for event in client.chat("Your prompt here"):
    if event["type"] == "message":
        print(event["content"], end="", flush=True)
```

## API Reference

### Server Endpoints

#### `POST /chat`

Send a prompt and receive streaming SSE response.

**Request:**
```json
{
  "prompt": "Your prompt here",
  "reset": false
}
```

**Response:** SSE stream with events:
- `init`: Session started
- `message`: Text response chunk
- `tool_use`: Tool execution started
- `tool_result`: Tool execution completed
- `result`: Final response with stats
- `error`: Error occurred

#### `POST /reset`

Reset the session (restart Gemini CLI process).

**Response:**
```json
{
  "status": "reset",
  "message": "Session restarted"
}
```

#### `GET /health`

Health check endpoint.

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Test-Driven Development

This project follows TDD principles. Tests are in `tests/` directory:
- `test_process.py`: Process manager tests
- `test_server.py`: Server endpoint tests
- `test_client.py`: Client library tests

## Configuration

Environment variables:
- `GEMINI_CLI_PATH`: Path to gemini CLI executable (default: `./gemini-cli/bundle/gemini.js`)
- `SERVER_HOST`: Server host (default: `0.0.0.0`)
- `SERVER_PORT`: Server port (default: `8000`)
- `GEMINI_API_KEY`: Gemini API key
- `GOOGLE_GENAI_USE_VERTEXAI`: Use Vertex AI mode
- `GOOGLE_CLOUD_PROJECT`: GCP project ID
- `GOOGLE_CLOUD_LOCATION`: GCP location

## License

MIT License

## Contributing

Contributions welcome! Please open an issue or PR.
