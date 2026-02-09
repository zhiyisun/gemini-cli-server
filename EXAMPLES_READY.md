# Examples - Ready to Run ✓

## Status: All Examples Verified ✓

✓ 6 examples created and verified
✓ All support both Gemini CLI and Qwen Code backends
✓ 42/42 tests passing
✓ Virtual environment fully configured
✓ All documentation updated

---

## How to Run

### Step 1: Terminal 1 (Start Server)
```bash
cd /home/zhiyis/workspace/code/gemini-cli-server
source .venv/bin/activate
python -m ai_cli_server.server
```

### Step 2: Terminal 2 (Run Examples)
```bash
cd /home/zhiyis/workspace/code/gemini-cli-server
source .venv/bin/activate
python examples/simple_chat.py          # Run any example
```

---

## Examples Overview

| # | Example | Purpose | Backend Support |
|---|---------|---------|-----------------|
| 1 | `simple_chat.py` | Single prompt streaming | ✓ Both |
| 2 | `multi_turn_chat.py` | Conversation with history | ✓ Both |
| 3 | `session_reset.py` | Stateless per-request | ✓ Both |
| 4 | `error_handling.py` | Error handling patterns | ✓ Both |
| 5 | `tool_monitoring.py` | Tool execution monitoring | ✓ Both |
| 6 | `multi_backend_demo.py` | Interactive backend comparison | ✓ BOTH |

---

## Testing Both Backends

All examples work identically with both backends!

```bash
# Start with Gemini CLI
python -m ai_cli_server.server
# Run: python examples/simple_chat.py

# Switch to Qwen (restart server)
CLI_TYPE=qwen python -m ai_cli_server.server
# Run: python examples/simple_chat.py (same code, different responses!)
```

---

## Documentation

- **[RUN_EXAMPLES.md](../RUN_EXAMPLES.md)** - Comprehensive guide with all details
- **[examples/README.md](../examples/README.md)** - Example descriptions and usage
- **[Quick Reference Card](QUICK_REFERENCE.txt)** - One-page cheat sheet

---

## What's Inside Each Example

### 1. Simple Chat
Sends a single prompt and streams the response line by line.

### 2. Multi-Turn Chat
Maintains conversation history across 3 turns with context.

### 3. Session Reset  
Demonstrates clients manage history client-side (stateless server model).

### 4. Error Handling
Covers connection errors, server errors, and graceful degradation.

### 5. Tool Monitoring
Shows how to detect and process tool execution events.

### 6. Multi-Backend Demo (⭐ Best for Testing)
Interactive prompt comparing Gemini CLI vs Qwen Code responses side-by-side.

---

## API Styles

**OpenAI-Compatible** (Examples 1-5)
- Drop-in replacement for OpenAI's Python client
- Familiar interface for OpenAI users
- Works identically with both backends

**Native GeminiClient** (Example 6)
- Full event stream access
- Better for monitoring and advanced use cases
- Works identically with both backends

---

## Key Features

✓ **Backend Agnostic** - Same code works with Gemini CLI and Qwen Code
✓ **Easy Switching** - Change backends with single environment variable
✓ **No Code Changes** - Run same examples against different backends
✓ **Production Ready** - All examples follow best practices
✓ **Well Tested** - 42 tests pass, all examples validated
✓ **Fully Documented** - Comprehensive guides and examples included

---

## Next Steps

1. Start the server: `python -m ai_cli_server.server`
2. Run any example: `python examples/simple_chat.py`
3. Try multi_backend_demo for interactive testing
4. Read [RUN_EXAMPLES.md](../RUN_EXAMPLES.md) for complete guide

**Everything is ready to run!** 🎉
