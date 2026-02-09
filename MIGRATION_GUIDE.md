# Migration Guide: Supporting Both Gemini CLI and Qwen Code

## Overview

The gemini-cli-server package has been enhanced to support both **Gemini CLI** and **Qwen Code** as backend AI engines. This provides flexibility to choose between different AI models while keeping the same API interface.

## What Changed

### Architecture Updates

1. **Base Abstraction Layer** (`base_process.py`)
   - Created `BaseCLIProcess` abstract class
   - Common functionality for all CLI backends
   - Handles process lifecycle, JSONL streaming, and event management

2. **Backend Implementations**
   - `gemini_process.py`: Gemini CLI-specific implementation
   - `qwen_process.py`: Qwen Code-specific implementation
   - Both inherit from `BaseCLIProcess`

3. **Server Updates** (`server.py`)
   - Now supports `CLI_TYPE` environment variable (`gemini` or `qwen`)
   - Auto-detects appropriate CLI based on configuration
   - Backward compatible with existing `GEMINI_CLI_PATH` usage

4. **Backward Compatibility** (`process.py`)
   - Original `GeminiProcess` class now aliases `GeminiCLIProcess`
   - Existing code continues to work without changes

## New Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CLI_TYPE` | Choose backend (`gemini` or `qwen`) | `gemini` |
| `CLI_PATH` | Custom path to CLI executable | Auto-detected |

### Legacy Variables (Still Supported)
- `GEMINI_CLI_PATH`: Equivalent to `CLI_PATH` when using Gemini

## Usage Examples

### Starting Server with Gemini CLI

```bash
# Default behavior (backward compatible)
python -m ai_cli_server.server

# Explicit
CLI_TYPE=gemini python -m ai_cli_server.server
```

### Starting Server with Qwen Code

```bash
CLI_TYPE=qwen python -m ai_cli_server.server
```

### Using Custom CLI Path

```bash
CLI_PATH=/custom/path/to/cli.js python -m ai_cli_server.server
```

## Python API

### Using Specific CLI Implementations

```python
from ai_cli_server import GeminiCLIProcess, QwenCodeProcess

# Use Gemini CLI
async with GeminiCLIProcess() as gemini:
    async for event in gemini.run_prompt_stream("Hello"):
        print(event)

# Use Qwen Code
async with QwenCodeProcess() as qwen:
    async for event in qwen.run_prompt_stream("Hello"):
        print(event)
```

### Backward Compatible Usage

```python
from ai_cli_server import GeminiProcess

# Still works - aliases GeminiCLIProcess
async with GeminiProcess() as process:
    async for event in process.run_prompt_stream("Hello"):
        print(event)
```

### Using Base Class

```python
from ai_cli_server import BaseCLIProcess, GeminiCLIProcess, QwenCodeProcess

def use_ai_cli(cli: BaseCLIProcess):
    """Works with any CLI implementation"""
    # Your code here
    pass

# Use with either backend
use_ai_cli(GeminiCLIProcess())
use_ai_cli(QwenCodeProcess())
```

## Client Code

**No changes required!** The client API remains identical:

```python
from ai_cli_server.client import GeminiClient

client = GeminiClient("http://localhost:8000")

# Works with both Gemini CLI and Qwen Code backends
for event in client.chat("Your prompt"):
    if event["type"] == "message":
        print(event["content"])
```

## Setup Requirements

### For Gemini CLI

```bash
# Initialize and build submodule
git submodule update --init --recursive
cd gemini-cli
npm install && npm run build
cd ..

# Set authentication
export GEMINI_API_KEY="your-key"
```

### For Qwen Code  

```bash
# Build Qwen Code (already cloned)
cd qwen-code
npm install && npm run build
cd ..

# Set authentication (varies by provider)
export OPENAI_API_KEY="your-key"
```

## Benefits

1. **Flexibility**: Choose the AI model that best fits your needs
2. **Comparison**: Easily compare outputs from different models
3. **Future-Proof**: Easy to add support for additional CLIs
4. **Backward Compatible**: Existing code continues to work
5. **Same API**: Client code doesn't need to know which backend is used

## Migration Checklist

- [ ] Update environment variables if using custom paths
- [ ] Install and build desired CLI backend(s)
- [ ] Set appropriate authentication for chosen backend
- [ ] Test server startup with `CLI_TYPE` variable
- [ ] Verify client code works with new backend
- [ ] Update deployment scripts if needed

## Testing

Run the multi-backend demo to verify both CLIs work:

```bash
# Terminal 1: Start with Gemini
python -m ai_cli_server.server

# Terminal 2: Test
python examples/multi_backend_demo.py

# Terminal 1: Restart with Qwen
CLI_TYPE=qwen python -m ai_cli_server.server

# Terminal 2: Test again
python examples/multi_backend_demo.py
```

## Troubleshooting

### "CLI not found" Error

**For Gemini:**
```bash
cd gemini-cli && npm install && npm run build && cd ..
```

**For Qwen:**
```bash
cd qwen-code && npm install && npm run build && cd ..
```

### Custom Path Not Working

Make sure `CLI_PATH` points to the actual CLI file:
- Gemini: `path/to/gemini-cli/bundle/gemini.js`
- Qwen: `path/to/qwen-code/dist/cli.js`

### Authentication Issues

Check the respective CLI documentation:
- [Gemini CLI Authentication](https://github.com/google-gemini/gemini-cli)
- [Qwen Code Authentication](https://qwenlm.github.io/qwen-code-docs/users/overview)

## Future Enhancements

Potential future additions:
- Support for additional CLI backends
- Auto-detection of installed CLIs
- Multi-model routing in a single server
- Benchmark tools for comparing backends

## Questions?

See the main [README.md](../README.md) for more information or open an issue on GitHub.
