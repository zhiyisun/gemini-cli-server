# AI CLI Server

A Python HTTP Server/Client wrapper for AI-powered CLIs ([Google Gemini CLI](https://github.com/google-gemini/gemini-cli) and [Qwen Code](https://github.com/QwenLM/qwen-code)), enabling programmatic access via REST API with Server-Sent Events (SSE) streaming.

## Features

- 🚀 **HTTP SSE Streaming**: Real-time streaming of AI responses, tool calls, and events
- 💬 **Session Management**: Persistent conversation sessions with automatic lifecycle management
- 🔧 **Simple Python Client**: Ergonomic Python library for consuming the API
- 🔐 **Secure Auth**: Uses existing CLI authentication (env vars or OAuth)
- 📦 **Dual CLI Support**: Works with both Gemini CLI and Qwen Code
- 🔄 **Flexible**: Easy switching between CLIs via environment variable

## Architecture

```
┌─────────────────┐     HTTP POST      ┌──────────────────┐
│  Python Client  │ ───────────────────>│  FastAPI Server  │
│                 │ <─────────────────  │                  │
└─────────────────┘   SSE Stream        └──────────────────┘
                                               │
                                               ▼
                                        ┌──────────────────┐
                                        │  Gemini CLI or   │
                                        │  Qwen Code CLI   │
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

### 2. Install a CLI Backend

Choose one or both:

#### Option A: Install Gemini CLI (submodule)

```bash
# Initialize submodule
git submodule update --init --recursive

# Build Gemini CLI
cd gemini-cli
git fetch --tags
git checkout $(git describe --tags $(git rev-list --tags --max-count=1))
npm install
npm run build
cd ..
```

#### Option B: Install Qwen Code (already cloned)

The qwen-code directory is already present in the repository. Build it:

```bash
cd qwen-code
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
#### Using Gemini CLI (default)

```bash
# Activate virtual environment (if not already activated)
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Set authentication
export GEMINI_API_KEY="your-api-key"
# OR for Vertex AI
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_CLOUD_PROJECT="your-project"
export GOOGLE_CLOUD_LOCATION="us-central1"

# Start server
python -m ai_cli_server.server
```

#### Using Qwen Code

```bash
# Activate virtual environment (if not already activated)
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Set Qwen authentication (see Qwen Code docs for auth options)
# For example, using OpenAI-compatible API:
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://api.your-provider.com/v1"

# Start server with Qwen Code
CLI_TYPE=qwen python -m ai_cli_server.server
```

### Environment Variables

- `CLI_TYPE`: Choose CLI backend (`gemini` or `qwen`). Default: `gemini`
- `CLI_PATH`: Custom path to CLI executable (optional)
- `SERVER_HOST`: Server host. Default: `0.0.0.0`
- `SERVER_PORT`: Server port. Default: `8000OR
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_CLOUD_PROJECT="your-project"
export GOOGLE_CLOUD_LOCATION="us-central1"

# Start server
python -m ai_cli_server.server
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
from ai_cli_server.client import GeminiClient

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

**Response:**
```json
{
  "status": "ok",
  "session_id": "abc123"
}
```

## Switching Between CLIs

You can easily switch between Gemini CLI and Qwen Code:

```bash
# Use Gemini CLI (default)
python -m ai_cli_server.server

# Use Qwen Code
CLI_TYPE=qwen python -m ai_cli_server.server

# Use custom CLI path
CLI_PATH=/path/to/custom/cli.js python -m ai_cli_server.server
```

Both CLIs support the same API and event formats, making them interchangeable for most use cases.

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
- `CLI_TYPE`: Choose CLI backend (`gemini` or `qwen`). Default: `gemini`
- `CLI_PATH`: Path to CLI executable (optional, auto-detected based on CLI_TYPE)
- `SERVER_HOST`: Server host (default: `0.0.0.0`)
- `SERVER_PORT`: Server port (default: `8000`)

### Gemini CLI Authentication:
- `GEMINI_API_KEY`: Gemini API key
- `GOOGLE_GENAI_USE_VERTEXAI`: Use Vertex AI mode
- `GOOGLE_CLOUD_PROJECT`: GCP project ID
- `GOOGLE_CLOUD_LOCATION`: GCP location

### Qwen Code Authentication:
- See [Qwen Code documentation](https://qwenlm.github.io/qwen-code-docs/users/overview) for authentication options
- Supports OpenAI-compatible APIs, OAuth, and more

## License

MIT License

## Contributing

Contributions welcome! Please open an issue or PR.
