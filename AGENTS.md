# AGENTS.md

This file provides guidance to AI agents when working with code in this repository.

## Project Overview

This is a Python library called `plumbum` (package name: `plumbum`, module name: `pdum.plumbum`). A plumbing syntax for Python

The project uses a modern Python toolchain with UV for dependency management.

## Important Rules

### Versions and releases
`ship` (habemus-papadum-ship) releases this package. The manifest carries
`<last release>+dev` between releases; never edit a version field by hand.
`__version__` reads the installed metadata.

To release, ask the operator. When they agree, run the release workflow:
`gh workflow run release.yml -f bump=minor -f dry_run=false` (run with
`dry_run=true` first to see the plan). Do not publish from this machine.
Do not update repositories that consume this package; their scheduled refresh
does that. If your change needs a newer release of another of our packages,
raise that package's floor here.

Do not commit a `path` or `editable` entry in `[tool.uv.sources]`. Do not pin
another `habemus-papadum-*` package to an exact version without a reason on the
same line or in `[tool.ship.pins]`. Run `uv run ship deps check` before you
finish.

## Development Commands

### Environment Setup
```bash
# Bootstrap the full toolchain (uv sync, pnpm install, widget build, hooks)
./scripts/setup.sh
```

**Important for Development**:
- Use `uv sync --frozen` to ensure the lockfile is used without modification, maintaining reproducible builds
- Re-run `./scripts/setup.sh` whenever dependencies change

### Testing
```bash
# Run all tests
uv run pytest

# Run a specific test file
uv run pytest tests/test_example.py

# Run a specific test function
uv run pytest tests/test_example.py::test_version

# Run tests with coverage
uv run pytest --cov=src/pdum/plumbum --cov-report=xml --cov-report=term
```

### Code Quality
```bash
# Check code with ruff
uv run ruff check .

# Format code with ruff
uv run ruff format .

# Fix auto-fixable issues
uv run ruff check --fix .
```

## Architecture

### Project Structure
- **src/pdum/plumbum/**: Main package source code (src-layout)
  - `__init__.py`: Package initialization and version
- **tests/**: Test suite using pytest
  - `test_example.py`: Example tests

### Key Constraints
- **Python Version**: Requires Python 3.12+
- **Dependency Management**: Uses UV exclusively; uv.lock is committed
- **Build System**: Uses Hatchling for building distributions

### Code Standards
- **Ruff Configuration**:
  - Target: Python 3.12
  - Line length: 120 characters
  - Linting rules: E (pycodestyle errors), F (pyflakes), W (warnings), I (isort)
- **Type Hints**: Use type hints where appropriate
- **Docstrings**: NumPy style, include Parameters, Returns, Raises sections

### Testing Strategy
- Test files must start with `test_` prefix
- Test classes must start with `Test` prefix
- Test functions must start with `test_` prefix
- Tests run with `-s` flag (no capture) by default
- Coverage reporting: use `--cov=src/pdum/plumbum --cov-report=xml --cov-report=term`

### Testing Configuration
The pytest configuration is in `pyproject.toml`:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-s"
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

Coverage configuration is also in `pyproject.toml`:
```toml
[tool.coverage.run]
source = ["src/pdum/plumbum"]
relative_files = true
omit = [
    "*/tests/*",
    "*/testing.py",
]
```

## CI/CD

### Continuous Integration
The project uses GitHub Actions for CI (`.github/workflows/ci.yml`):
- Runs on every push to main and pull requests
- Executes linting with ruff
- Runs unit tests with coverage reporting
- Posts coverage report as a PR comment

### Release Process
Releases run from the `release` workflow (`.github/workflows/release.yml`),
which calls the reusable workflow in
[ship](https://github.com/habemus-papadum/pdum_ship). It waits for CI on the
commit, then sets the release version, builds, tests, publishes to PyPI, tags
`habemus-papadum-plumbum-v<version>`, creates the GitHub release and restores
the `+dev` marker. Documentation deploys on every push to `main`.
