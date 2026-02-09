# Examples

This directory contains example scripts demonstrating how to use the ai-cli-server Python client.

## Quick Start

Before running any example, ensure the server and dependencies are set up. See [../CONTRIBUTING.md](../CONTRIBUTING.md) for environment setup and authentication.

Start the server in one terminal:

```bash
python -m ai_cli_server.server
```

Then run any example in another terminal:

```bash
python examples/simple_chat.py
```

## Examples

1. **simple_chat.py**: Single prompt with streaming response
2. **multi_turn_chat.py**: Multi-turn conversation with history
3. **session_reset.py**: Stateless per-request model demo
4. **error_handling.py**: Connection and server error handling
5. **tool_monitoring.py**: Tool execution monitoring (if backend emits tool events)
6. **multi_backend_demo.py**: Interactive backend comparison (gemini/qwen)

## API Styles

### OpenAI-Compatible API

Drop-in replacement for OpenAI's Python client:

```python
from ai_cli_server.client import OpenAICompatibleClient

client = OpenAICompatibleClient("http://localhost:8000")

stream = client.chat.completions.create(
    messages=[{"role": "user", "content": "Hello"}],
    stream=True,
)
for chunk in stream:
    delta = chunk["choices"][0]["delta"]
    if "content" in delta:
        print(delta["content"], end="")
```

### Native GeminiClient API

Access to the full event stream:

```python
from ai_cli_server.client import GeminiClient

client = GeminiClient("http://localhost:8000")

for event in client.chat("Hello"):
    if event.get("type") == "message":
        print(event.get("content"), end="")
```

## Further Reading

- [Main README](../README.md) for architecture and API details
- [CONTRIBUTING.md](../CONTRIBUTING.md) for development setup
