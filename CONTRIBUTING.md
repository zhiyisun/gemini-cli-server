# Contributing to gemini-cli-server

Thank you for your interest in contributing! This document provides guidelines for developing and testing this project.

## Development Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd gemini-cli-server
```

### 2. Initialize Git Submodules

The project uses Gemini CLI as a git submodule:

```bash
git submodule update --init --recursive
```

### 3. Set Up Python Environment

We recommend using a virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate  # On Windows

# Install dependencies in editable mode
pip install -e ".[dev]"
```

### 4. Set Up Gemini CLI

Navigate to the submodule and install dependencies:

```bash
cd gemini-cli
npm install
npm run build
cd ..
```

### 5. Configure Authentication

Set environment variables for Gemini API access:

```bash
# Option 1: API Key
export GEMINI_API_KEY="your-api-key"

# Option 2: Vertex AI
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_CLOUD_PROJECT="your-project"
export GOOGLE_CLOUD_LOCATION="us-central1"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/creds.json"
```

## Project Structure

```
gemini-cli-server/
├── gemini_cli_server/      # Main package
│   ├── __init__.py
│   ├── process.py          # Subprocess management
│   ├── server.py           # FastAPI server
│   └── client.py           # Python client
├── tests/                  # Test suite
│   ├── conftest.py         # Pytest configuration
│   ├── test_process.py     # Process tests
│   ├── test_server.py      # Server tests
│   └── test_client.py      # Client tests
├── examples/               # Usage examples
│   ├── simple_chat.py
│   ├── multi_turn_chat.py
│   └── ...
├── gemini-cli/             # Git submodule (Gemini CLI)
├── pyproject.toml          # Project metadata
└── README.md
```

## Development Workflow

### Running Tests

We use pytest for testing. Run the full test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=gemini_cli_server --cov-report=html

# Run specific test file
pytest tests/test_process.py

# Run specific test
pytest tests/test_process.py::TestGeminiProcessStart::test_start_success

# Run with verbose output
pytest -v

# Run with print statements visible
pytest -s
```

### Test Organization

- **Unit tests**: Mock all external dependencies (subprocess, HTTP)
- **Integration tests**: Test actual interaction with Gemini CLI (requires auth)
- **Fixtures**: Define reusable test fixtures in `conftest.py`

### Code Style

We follow PEP 8 with some customizations:

```bash
# Format code (install black first: pip install black)
black gemini_cli_server/ tests/

# Check types (install mypy first: pip install mypy)
mypy gemini_cli_server/

# Lint code (install ruff first: pip install ruff)
ruff check gemini_cli_server/ tests/
```

### Running the Server Locally

```bash
# Development mode with auto-reload
uvicorn gemini_cli_server.server:app --reload

# Or using Python module
python -m gemini_cli_server.server

# Custom port
uvicorn gemini_cli_server.server:app --port 9000
```

### Testing Your Changes

1. **Write tests first** (TDD approach):
   ```python
   # tests/test_new_feature.py
   def test_my_new_feature():
       # Arrange
       client = GeminiClient("http://localhost:8000")
       
       # Act
       result = client.my_new_feature()
       
       # Assert
       assert result == expected_value
   ```

2. **Implement the feature**:
   ```python
   # gemini_cli_server/client.py
   def my_new_feature(self):
       # Implementation
       pass
   ```

3. **Run tests**:
   ```bash
   pytest tests/test_new_feature.py
   ```

4. **Test manually**:
   ```bash
   # Start server
   python -m gemini_cli_server.server
   
   # In another terminal, test with real interaction
   python examples/simple_chat.py
   ```

## Making Changes

### Adding a New Feature

1. Create a new branch:
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. Write tests in `tests/`

3. Implement feature in `gemini_cli_server/`

4. Add example in `examples/` if applicable

5. Update documentation in `README.md`

6. Commit changes:
   ```bash
   git add .
   git commit -m "feat: add my new feature"
   ```

### Commit Message Convention

Follow conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Adding or updating tests
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

Examples:
```
feat: add session timeout configuration
fix: handle connection reset errors gracefully
docs: update README with new examples
test: add integration tests for chat streaming
```

### Fixing a Bug

1. Write a failing test that reproduces the bug

2. Fix the bug

3. Verify the test passes

4. Add regression test if needed

## Testing Guidelines

### Unit Tests

Test individual components in isolation:

```python
import pytest
from unittest.mock import Mock, AsyncMock
from gemini_cli_server.process import GeminiProcess

@pytest.mark.asyncio
async def test_process_start():
    """Test that process starts correctly."""
    # Mock subprocess
    mock_process = AsyncMock()
    mock_process.returncode = None
    
    # Test implementation
    process = GeminiProcess("/path/to/cli")
    # ... test logic
```

### Integration Tests

Test real interactions (requires authentication):

```python
import pytest
from gemini_cli_server.client import GeminiClient

@pytest.mark.integration
async def test_real_chat():
    """Test actual chat with Gemini CLI."""
    client = GeminiClient("http://localhost:8000")
    
    events = list(client.chat("What is 2+2?"))
    
    # Should have init, messages, and result
    assert any(e.get("type") == "init" for e in events)
    assert any(e.get("type") == "message" for e in events)
    assert any(e.get("type") == "result" for e in events)
```

Run integration tests separately:
```bash
pytest -m integration
```

### Test Coverage

Aim for >90% coverage:

```bash
# Generate coverage report
pytest --cov=gemini_cli_server --cov-report=term --cov-report=html

# View HTML report
open htmlcov/index.html  # Mac/Linux
# or
start htmlcov/index.html  # Windows
```

## Debugging

### Debug Server

```bash
# Run with debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
python -m gemini_cli_server.server
```

### Debug Tests

```bash
# Run pytest with pdb on failure
pytest --pdb

# Run specific test with verbose output
pytest -vv -s tests/test_process.py::test_specific_case
```

### Debug Subprocess

Check the actual Gemini CLI process:

```python
# Add to process.py for debugging
print(f"Command: {' '.join(command)}")
print(f"Process PID: {self._process.pid}")
```

## Documentation

### Docstrings

Use Google-style docstrings:

```python
def my_function(param1: str, param2: int) -> bool:
    """Short description of function.
    
    More detailed description if needed.
    
    Args:
        param1: Description of param1.
        param2: Description of param2.
    
    Returns:
        Description of return value.
    
    Raises:
        ValueError: When param1 is empty.
    """
    pass
```

### Update README

When adding features, update relevant sections:
- Architecture diagram (if structure changes)
- API Reference
- Examples section
- Configuration options

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Run full test suite: `pytest`
4. Create git tag: `git tag v0.1.0`
5. Push: `git push --tags`

## Getting Help

- Check existing issues and PRs
- Read the [README.md](README.md)
- Review test files for examples
- Ask questions in issues

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

Thank you for contributing! 🎉
