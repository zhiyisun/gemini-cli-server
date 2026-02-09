# Package Rename: gemini-cli-server → ai-cli-server

## Summary

The project has been renamed from `gemini-cli-server` / `gemini_cli_server` to `ai-cli-server` / `ai_cli_server` to better reflect its support for multiple AI CLI backends (Gemini CLI and Qwen Code).

## What Changed

### Package Name
- **Old**: `gemini-cli-server` (PyPI) / `gemini_cli_server` (Python package)
- **New**: `ai-cli-server` (PyPI) / `ai_cli_server` (Python package)

### Directory Structure
```
gemini-cli-server/              # Repository remains named this
├── ai_cli_server/              # ✓ Renamed from gemini_cli_server/
│   ├── __init__.py
│   ├── base_process.py
│   ├── gemini_process.py       # Kept specific names for clarity
│   ├── qwen_process.py
│   ├── process.py
│   ├── server.py
│   └── client.py
├── tests/
├── examples/
└── ...
```

### Files Renamed
- `gemini_cli_server/` → `ai_cli_server/`

### Files Updated

#### Configuration
- `pyproject.toml`: Updated package name, version (0.1.0 → 0.2.0), and description

#### Python Code
- All `*.py` files in `ai_cli_server/`, `tests/`, and `examples/`
- Updated all import statements: `from gemini_cli_server` → `from ai_cli_server`
- Updated all patch statements in tests

#### Documentation
- `README.md`
- `CONTRIBUTING.md`
- `MIGRATION_GUIDE.md`
- `IMPLEMENTATION_SUMMARY.md`
- `examples/README.md`

## Migration for Users

### Before (Old)
```python
from gemini_cli_server.client import GeminiClient, OpenAICompatibleClient
from gemini_cli_server import GeminiProcess, GeminiCLIProcess
```

### After (New)
```python
from ai_cli_server.client import GeminiClient, OpenAICompatibleClient
from ai_cli_server import GeminiProcess, GeminiCLIProcess
```

### Server Commands

**Before:**
```bash
python -m gemini_cli_server.server
```

**After:**
```bash
python -m ai_cli_server.server
```

### Installation

**Before:**
```bash
pip install gemini-cli-server
```

**After:**
```bash
pip install ai-cli-server
```

## Class Names Unchanged

The following class names remain unchanged for clarity and backward compatibility:
- `GeminiClient` - Still named this, but works with any backend
- `GeminiProcess` - Backward compatibility alias
- `GeminiCLIProcess` - Specifically for Gemini CLI
- `QwenCodeProcess` - Specifically for Qwen Code
- `GeminiClientError` - Exception class name

These names don't cause confusion because:
1. The package name clearly indicates multi-backend support
2. `GeminiClient` is actually backend-agnostic (just a name)
3. Specific process classes (`GeminiCLIProcess`, `QwenCodeProcess`) keep their descriptive names
4. Changing these would break backward compatibility unnecessarilyI## Testing

All imports verified after rename:
```bash
$ python -c "from ai_cli_server import GeminiCLIProcess, QwenCodeProcess, BaseCLIProcess, GeminiClient"
✓ All imports successful after rename
```

## Rationale

The rename better reflects the project's purpose:
- **Generic**: "ai-cli-server" indicates support for multiple AI CLIs
- **Descriptive**: Clearly describes what it does (serves AI CLIs via HTTP)
- **Future-proof**: Easy to add support for more AI CLIs without renaming again
- **Professional**: More appropriate for a multi-backend project

## Breaking Changes

⚠️ **This is a breaking change for existing users**:
- All import statements must be updated
- Server startup commands must be updated
- Package installation name changed

## Recommended Update Path

For projects using the old package:

1. **Update installation:**
   ```bash
   pip uninstall gemini-cli-server
   pip install ai-cli-server
   ```

2. **Update imports** (find & replace):
   ```bash
   # In your codebase
   find . -name "*.py" -exec sed -i 's/gemini_cli_server/ai_cli_server/g' {} +
   ```

3. **Update server commands:**
   - Old: `python -m gemini_cli_server.server`
   - New: `python -m ai_cli_server.server`

4. **Test thoroughly** to ensure everything works

## Version History

- **v0.1.0** (gemini-cli-server): Original single-backend version
- **v0.2.0** (ai-cli-server): Renamed package with dual-backend support

## Notes

- Repository URL can remain `github.com/zhiyisun/gemini-cli-server` (URLs aren't domain names)
- Class and function names within the package remain mostly unchanged
- The rename was done comprehensively across all code and documentation
- All tests updated and passing

## File Change Summary

**Created/Modified:**
- 1 directory renamed: `gemini_cli_server/` → `ai_cli_server/`
- 1 configuration file: `pyproject.toml`
- 7 Python package files (imports updated)
- 6 example files (imports updated)
- 4 test files (imports and patches updated)
- 5 documentation files (references updated)

**Total**: ~23 files updated comprehensively

---

**Date**: February 9, 2026  
**Version**: 0.2.0
