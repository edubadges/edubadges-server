# UV Tooling Migration Guide

This document describes the changes made to migrate the Edubadges server from traditional pip to uv tooling.

## What is uv?

[uv](https://github.com/astral-sh/uv) is an extremely fast Python package installer and resolver, designed as a drop-in replacement for pip and pip-tools. It offers:

- **Blazing fast** dependency resolution and installation
- **Deterministic** builds with lock files
- **Better caching** for faster repeated installs
- **Modern** Python packaging experience

## Changes Made

### 1. New Files Added

- **`pyproject.toml`**: Modern Python project configuration file
  - Defines build system, project metadata, and tool configurations
  - Includes configurations for uv, ruff, black, and mypy

- **`uv.lock`**: Lock file generated from requirements.txt
  - Ensures reproducible dependency installation
  - Generated using `uv pip compile requirements.txt --output-file=uv.lock`

- **`.python-version`**: Specifies Python version for tooling
  - Contains `3.9.20` to match the project's Python version

- **`scripts/uv-sync.sh`**: Helper script to sync dependencies
  - Runs `uv pip sync uv.lock` to install exact versions

- **`scripts/update-deps.sh`**: Helper script to update dependencies
  - Regenerates uv.lock from requirements.txt

### 2. Modified Files

- **`Dockerfile`**: Updated to use uv for dependency management
  - Now uses multi-stage builds for better optimization
  - Uses `uv pip sync uv.lock` instead of `pip install -r requirements.txt`
  - Builder stage installs dependencies, final stage copies only what's needed

- **`docker-compose.yml`**: Added uv environment variable
  - Sets `UV_PYTHON=python3.9` to ensure correct Python version

- **`setup.py`**: Improved error handling and git dependency handling
  - Added fallback version if version.py is not found
  - Skips git dependencies for setuptools (handled directly by uv/pip)

- **`README.md`**: Updated installation instructions
  - Added uv as the recommended installation method
  - Kept pip instructions for backward compatibility

## Migration Steps

### For New Developers

1. **Install uv**:
   ```bash
   pip install uv
   ```

2. **Install dependencies**:
   ```bash
   uv pip sync uv.lock
   ```

3. **Run the application**:
   ```bash
   python manage.py runserver
   ```

### For Existing Developers

1. **Install uv**:
   ```bash
   pip install uv
   ```

2. **Sync dependencies**:
   ```bash
   uv pip sync uv.lock
   ```

3. **Update dependencies (when requirements.txt changes)**:
   ```bash
   ./scripts/update-deps.sh
   uv pip sync uv.lock
   ```

## Docker Usage

The Docker setup now uses **official uv Docker base images with Python 3.9** (`ghcr.io/astral-sh/uv:python3.9-trixie-slim`) as recommended in the [uv documentation](https://docs.astral.sh/uv/guides/integration/docker/#available-images).

```bash
# Build and run with Docker
docker compose up

# Or build specifically
docker build -t edubadges-server .
```

### Docker Image Benefits

- **Official support**: Maintained by the uv team
- **Python 3.9 included**: Matches the project's Python version requirement
- **Optimized**: Smaller and more secure base images
- **Consistent**: Same uv version across all environments
- **Up-to-date**: Regular updates from the uv project
- **Multi-stage builds**: Optimal image size with builder pattern

## Benefits

1. **Faster dependency installation**: uv is significantly faster than pip
2. **Reproducible builds**: uv.lock ensures everyone uses exact same versions
3. **Better caching**: Docker builds are more efficient with multi-stage
4. **Modern tooling**: Aligns with current Python packaging best practices

## Backward Compatibility

The setup still supports traditional pip installation:

```bash
pip install -r requirements.txt
```

However, uv is now the recommended approach.

## Troubleshooting

### uv commands not found

Make sure uv is installed and in your PATH:
```bash
pip install --user uv
export PATH=$PATH:~/.local/bin
```

### Dependency conflicts

Regenerate the lock file:
```bash
./scripts/update-deps.sh
uv pip sync uv.lock
```

### Docker build issues

Clean build context and try again:
```bash
docker compose build --no-cache
```

## Future Improvements

Consider these enhancements:

1. **Migrate to PEP 621**: Fully migrate to pyproject.toml-based setup
2. **Add pre-commit hooks**: Use uv with pre-commit for linting/formatting
3. **CI/CD integration**: Update CI pipelines to use uv
4. **Development environment**: Create uv virtual environments for isolation

## References

- [uv GitHub Repository](https://github.com/astral-sh/uv)
- [uv Documentation](https://astral.sh/uv)
- [PEP 621 - Storing project metadata in pyproject.toml](https://peps.python.org/pep-0621/)
