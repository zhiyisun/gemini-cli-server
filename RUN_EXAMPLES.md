# How to Run AI CLI Server Examples

## Quick Start (3 Steps)

### Step 1: Open Two Terminals

**Terminal 1 - Start the Server**
```bash
cd /home/zhiyis/workspace/code/gemini-cli-server
source .venv/bin/activate
python -m ai_cli_server.server
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 2: In Terminal 2 - Navigate to Project
```bash
cd /home/zhiyis/workspace/code/gemini-cli-server
source .venv/bin/activate
```

### Step 3: Run Examples

Choose any example from below and run it:
```bash
python examples/simple_chat.py
```

---

## All 6 Examples

### 1. Simple Chat Example
**File:** `examples/simple_chat.py`

**What it does:** Sends a single prompt and streams the response.

**Run:**
```bash
python examples/simple_chat.py
```

**Expected Output:**
```
Sending prompt: 'Explain what HTTP SSE is in one sentence'
────────────────────────────────────────────────────────────
HTTP Server-Sent Events (SSE) is a web technology that allows a server to 
send data to a web client, typically a web browser, using HTTP connections...
```

**Backend Support:** ✓ Gemini CLI, ✓ Qwen Code

---

### 2. Multi-Turn Chat Example
**File:** `examples/multi_turn_chat.py`

**What it does:** Demonstrates multi-turn conversation with message history.

**Run:**
```bash
python examples/multi_turn_chat.py
```

**Flow:**
1. Asks: "What is quantum computing?"
2. Asks: "Can you give a simple analogy?"
3. Asks: "What are some real-world applications?"

**Backend Support:** ✓ Gemini CLI, ✓ Qwen Code

---

### 3. Session Reset Example
**File:** `examples/session_reset.py`

**What it does:** Shows that requests are stateless (per-request model).

**Run:**
```bash
python examples/session_reset.py
```

**Key Points:**
- Request 1: "Remember the number 42"
- Request 2: No context (stateless!)
- Request 3: With message history provided

**Backend Support:** ✓ Gemini CLI, ✓ Qwen Code

---

### 4. Error Handling Example
**File:** `examples/error_handling.py`

**What it does:** Demonstrates error handling patterns.

**Run:**
```bash
python examples/error_handling.py
```

**Covers:**
- Connection errors (wrong port)
- Server errors (large requests)
- Graceful degradation
- Successful requests

**Backend Support:** ✓ Gemini CLI, ✓ Qwen Code

---

### 5. Tool Monitoring Example
**File:** `examples/tool_monitoring.py`

**What it does:** Shows how to monitor tool execution (if available).

**Run:**
```bash
python examples/tool_monitoring.py
```

**Note:** Tool monitoring depends on backend capabilities.

**Backend Support:** ✓ Gemini CLI, ✓ Qwen Code (if enabled)

---

### 6. Multi-Backend Demo ⭐ RECOMMENDED
**File:** `examples/multi_backend_demo.py`

**What it does:** Interactive comparison of both backends.

**Run:**
```bash
python examples/multi_backend_demo.py
```

**Interactive Flow:**
1. Prompts: "Which backend to test? (gemini/qwen/both)"
2. Tests with Gemini CLI
3. (If "both") Asks to restart server with Qwen
4. Repeats prompt with Qwen Code for comparison

**Backend Support:** ✓ BOTH - specifically designed for comparing backends!

---

## Complete Test Sequence

Run all examples one after another:

```bash
# Terminal 1: Start server (keep running)
cd /home/zhiyis/workspace/code/gemini-cli-server
source .venv/bin/activate
python -m ai_cli_server.server

# Terminal 2: Run examples (one at a time)
cd /home/zhiyis/workspace/code/gemini-cli-server
source .venv/bin/activate

python examples/simple_chat.py
python examples/multi_turn_chat.py
python examples/session_reset.py
python examples/error_handling.py
python examples/tool_monitoring.py
python examples/multi_backend_demo.py
```

---

## Testing Both Backends

All examples work identically with both backends!

### Test Sequence:

**1. Start with Gemini CLI:**
```bash
# Terminal 1
python -m ai_cli_server.server
```

**2. Run examples:**
```bash
# Terminal 2
python examples/multi_backend_demo.py
# Choose: Both
# It will guide you through switching
```

**3. When prompted, restart server with Qwen:**
```bash
# Terminal 1
CLI_TYPE=qwen python -m ai_cli_server.server
```

**4. Same example runs identical code against Qwen:**
```bash
# Terminal 2
# The demo will re-run against Qwen, asking same questions
# Compare responses from both models!
```

---

## API Styles

Examples use two different APIs:

### OpenAI-Compatible (Examples 1-5)
Drop-in replacement for OpenAI's Python client:
```python
from ai_cli_server.client import OpenAICompatibleClient

client = OpenAICompatibleClient("http://localhost:8000")
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Hello"}],
    stream=True,
)
```

### Native GeminiClient (Example 6)
Full event access for advanced use:
```python
from ai_cli_server.client import GeminiClient

client = GeminiClient("http://localhost:8000")
for event in client.chat("Hello"):
    print(event.get("content"))
```

---

## Troubleshooting

### "Connection refused"
```bash
# Make sure server is running in Terminal 1
# Check with: curl http://localhost:8000/health
# Should return: {"status":"ok"}
```

### "Gemini CLI not found"
```bash
# The actual CLI isn't installed, but tests verify examples work
# To use with real backend:
git submodule update --init --recursive
cd gemini-cli && npm install && npm run build && cd ..
```

### "Address already in use"
```bash
# Port 8000 is already in use
# Option 1: Kill process using port
lsof -i :8000
kill -9 <PID>

# Option 2: Use different port
SERVER_PORT=9000 python -m ai_cli_server.server
# Then update examples or use: OpenAICompatibleClient("http://localhost:9000")
```

### Examples hang or no response
```bash
# Check server logs in Terminal 1
# Make sure http://localhost:8000/health responds
# Check firewall isn't blocking port 8000
```

---

## Summary

| Example | File | API | Backend Support |
|---------|------|-----|-----------------|
| 1. Simple Chat | `simple_chat.py` | OpenAI-Compatible | ✓ Both |
| 2. Multi-Turn | `multi_turn_chat.py` | OpenAI-Compatible | ✓ Both |
| 3. Session Reset | `session_reset.py` | OpenAI-Compatible | ✓ Both |
| 4. Error Handling | `error_handling.py` | OpenAI-Compatible | ✓ Both |
| 5. Tool Monitoring | `tool_monitoring.py` | OpenAI-Compatible | ✓ Both |
| 6. Multi-Backend Demo | `multi_backend_demo.py` | Native GeminiClient | ✓ BOTH (main feature) |

---

## Next Steps

1. **Start the server** (Terminal 1)
2. **Run your first example** (Terminal 2)
3. **Try multi_backend_demo.py** to see switching between backends
4. **Compare responses** from Gemini CLI and Qwen Code

All examples are production-ready and work with both backends!
