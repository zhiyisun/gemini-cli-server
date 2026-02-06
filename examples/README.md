# Examples

This directory contains example scripts demonstrating how to use the gemini-cli-server Python client.

## Quick Start

Before running any example, ensure the server and dependencies are set up. See [../CONTRIBUTING.md](../CONTRIBUTING.md) for:
- Development setup instructions
- Git submodule initialization
- Python environment configuration  
- Authentication setup

Then start the server in one terminal:

```bash
python -m gemini_cli_server.server
```

## Running Examples

### 1. Simple Chat (`simple_chat.py`)

Basic single-prompt interaction showing event streaming.

```bash
python examples/simple_chat.py
```

**What it demonstrates:**
- Connecting to the server
- Sending a prompt with OpenAI-compatible API
- Streaming response chunks
- Extracting content from delta objects

### 2. Multi-Turn Conversation (`multi_turn_chat.py`)

Multiple sequential prompts in the same session.

```bash
python examples/multi_turn_chat.py
```

**What it demonstrates:**
- Maintaining conversation history by passing message list
- Multiple prompts with context
- Building coherent conversations
- Response streaming and accumulation

### 3. Session Reset (`session_reset.py`)

Demonstrating stateless per-request behavior with manual history management.

```bash
python examples/session_reset.py
```

**What it demonstrates:**
- Per-request stateless architecture
- Manual conversation history management  
- Including history in requests to maintain context
- Verifying context is not persisted server-side

### 4. Tool Monitoring (`tool_monitoring.py`)

Real-time monitoring of tool execution (if Gemini CLI uses tools).

```bash
python examples/tool_monitoring.py
```

**What it demonstrates:**
- Detecting tool_use events
- Capturing tool arguments
- Processing tool_result events
- Collecting execution statistics
- Displaying tool call summaries

### 5. Error Handling (`error_handling.py`)

Comprehensive error handling strategies.

```bash
python examples/error_handling.py
```

**What it demonstrates:**
- Connection error handling
- Server error recovery
- Graceful degradation on malformed responses
- Using context managers for cleanup
- Retry strategies
- Session reset on errors

## Example Patterns
API Styles

### OpenAI-Compatible API (Standard)

Drop-in replacement for OpenAI's Python client:

```python
from gemini_cli_server.client import OpenAICompatibleClient

client = OpenAICompatibleClient("http://localhost:8000")

# Streaming
stream = client.chat.completions.create(
    messages=[{"role": "user", "content": "Hello"}],
    stream=True,
)
for chunk in stream:
    if "content" in chunk["choices"][0]["delta"]:
        print(chunk["choices"][0]["delta"]["content"], end="")

# Non-streaming
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Hello"}]
)
print(response["choices"][0]["message"]["content"])
```

### Native GeminiClient API

Access to full event stream (tool calls, etc.):

```python
from gemini_cli_server.client import GeminiClient

client = GeminiClient("http://localhost:8000")

for event in client.chat("Hello"):
    if event.get("type") == "message":
        print(event.get("content"), end="")
    elif event.get("type") == "tool_use":
        print(f"Using tool: {event.get('name')}")

## Event Types

The client yields different event types from the SSE stream:

| Type | Description | Key Fields |
|------|-------------|------------|
| `init` | Session initialized | `session_id` |
| `message` | Response text chunk | `content` |
| `tool_use` | Tool being executed | `name`, `args` |
| `tool_result` | Tool execution result | `output`, `error` |
| `result` | Final response | `stats` (tokens, timing) |
| `error` | Error occurred | `error` (message) |

## Customization

### Custom Base URL
```python
client = Gemin (GeminiClient)

The native GeminiClient yields different event types from the SSE stream:

| Type | Description | Key Fields |
|------|-------------|------------|
| `init` | Stream initialized | `session_id` |
| `message` | Response text chunk | `role`, `content` |
| `tool_use` | Tool being executed | `name`, `args` |
| `tool_result` | Tool execution result | `output`, `error` |
| `result` | Final response metadata | `stats` (tokens, timing) |
| `error` | Error occurred | `message`
        elif event_type == "tool_use":
            # Log tool usage
            print(f"Using tool: {event.get('name')}")
Server URL
```python
from gemini_cli_server.client import OpenAICompatibleClient

client = OpenAICompatibleClient("http://your-server:9000")
```

### Per-Request vs. Persistent Context
Server not responding
- Ensure server is running: `python -m gemini_cli_server.server`
- Check the port (default: 8000)
- Verify no firewall is blocking

### Authentication errors
- Check environment variables are set
- See setup guide in [../CONTRIBUTING.md](../CONTRIBUTING.md)

### No response
- Check server logs for errors
- Verify Gemini CLI is installed in submodule

### Slow first response
- First prompt initializes the session (slower)
- Subsequent prompts are faster

## Further Reading

- [Main README](../README.md) - Architecture and API overview
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Development setup and guidelines  
- [Test files](../tests/) - More usage examples and pattern
- Monitor server resource usage

## Next Steps

- Read the [main README](../README.md) for architecture details
- Check the [API documentation](../README.md#api-reference) for all methods
- Review test files in `tests/` for more usage examples
- Explore Gemini CLI documentation for available capabilities
