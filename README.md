# plumbum

[![CI](https://github.com/habemus-papadum/pdum_plumbum/actions/workflows/ci.yml/badge.svg)](https://github.com/habemus-papadum/pdum_plumbum/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/habemus-papadum-plumbum.svg)](https://pypi.org/project/habemus-papadum-plumbum/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Coverage](https://raw.githubusercontent.com/habemus-papadum/pdum_plumbum/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/habemus-papadum/pdum_plumbum/blob/python-coverage-comment-action-data/htmlcov/index.html)

A plumbing syntax for Python that provides a clear distinction between data and operators, enabling composable function pipelines.

## Overview

**plumbum** is a library for threading data through function calls using intuitive pipe operators. Inspired by [Pipe](https://github.com/JulienPalard/Pipe), it offers a redesigned approach with a separation between operator construction and execution.

**This is primarily a syntax library** focused on making data transformations more readable and composable. It is not optimized for performance-critical applications, but rather caters to the aesthetics of @habemus-papadum -- so, your mileage may vary...

## Installation
```bash
pip install habemus-papadum-plumbum
```

## Usage

```python
# Basics
5 > add(1) | mul(2)  # 12

# Iterators
[1, 2, 3] > select(mul(3) | add(1)) | where(even) | list # [4, 10]

# Async
await (5 > async_add(1) | async_mul(2))  # 12
await ([1, 2, 3] > aiter | aselect(async_add(1)) | alist) # [2, 3, 4]

# Pipelines are reusable values
op = add(1) | multiply(2)
op2 = add(3) | multiply(12)
6 > op | op2  # 204
```

## Mental Model

- Compose first, execute later. The `|` operator chains together `@pb`/`@apb` operators (and plain callables) without running them. The pipeline becomes a first-class value that you can store, combine, or pass around.
- Thread data explicitly. The `>` operator injects the left-hand value into the pipeline’s first argument. That works for numbers, strings, dicts, iterables, custom classes—any Python object.
- Async is contagious by design. Introducing an async operator (created with `@apb`, an async iterator helper, or any awaitable) upgrades the whole pipeline so `value > pipeline` returns a coroutine. Call it with `await`.
- Iterables stay lazy. Synchronous helpers like `select`, `where`, `take`, or `chain` return iterators; async counterparts (`aselect`, `awhere`, `aiter`, …) yield async iterators. Add a materializer (`list`, `tuple`, `alist`) when you actually need the concrete collection.

## Features

- Compatible with arbitrary data types; the library focuses on syntax and composability rather than constraining what flows through the pipes.
- Seamless sync/async mixing: pipelines promote themselves to async when an async stage is present, including adapters for awaitables returned by sync operators.
- Rich iterable toolkits for sync (`pdum.plumbum.iterops`) and async (`pdum.plumbum.aiterops`) flows, covering batching, zipping, traversal, networking, and more.(Modelled after the operators from[Pipe](https://github.com/JulienPalard/Pipe))
- jq-inspired JSON utilities (`pdum.plumbum.jq`) for parsing dotted paths, querying nested data, and performing immutable transformations—plus async counterparts.

## Style Guide

- **Favor `|` for composition.** Build operators with `|` so you can refactor pipelines into reusable pieces. Use `>` sparingly—ideally once—when you finally thread data through the pipeline. Remember that `|` binds more tightly than `>`, so `value > a | b` means `value > (a | b)`; add parentheses only when you truly need different grouping.
- **Iterators remain lazy by default.** Iterator pipelines usually yield another iterator. In tests or scripts, append a materializer such as `| list` when you need concrete values. Plain callables are auto-wrapped; no need for `pb(list)`.
- **Sync to async promotion is automatic.** Pipelines built from `@pb` operators seamlessly adopt async semantics when an `@apb` stage (or any awaitable) appears. Keep composing with `|`; the result becomes awaitable.
- **Await async chains.** Any pipeline that includes async operators returns a coroutine. Execute it with `await (value > pipeline)` (or equivalently `await pipeline(value)`).
- **Collect async results with `alist` / `acollect`.** Finish async iterator pipelines with `| alist` (alias `| acollect`) when you need a list in memory.
- **Avoid chained `>` comparisons.** Python treats `x > a > b` as a chained comparison, which is incompatible with plumbum operators. Prefer `x > a | b`; only use `(x > a) > b` when you intentionally need two separate execution steps.

## Tutorial Notebook

Learn the details of synchronous and asynchronous pipelines by following along step-by-step in the [Tutorial](https://habemus-papadum.github.io/pdum_plumbum/tutorial/), which hosts the full quick-start tour covering core operators, partial application, iterable helpers, and async variants.


## Acknowledgements

- plumbum draws direct inspiration from Julien Palard’s [Pipe](https://github.com/JulienPalard/Pipe); several iterable operators (for example `select`, `where`, and `dedup`) started life there before being reworked for plumbum’s APIs.
- Key differences from Pipe:
    - Operators are inert values: `|` builds pipelines while `>` triggers execution, making composition and reuse explicit.
    - Async is a core capability: sync and async operators coexist in the same pipeline, and iterator helpers come in both synchronous and asynchronous flavors.
    - The bundled `pdum.plumbum.jq` module adds a jq-inspired path/query layer, expanding the original operator toolbox into structured-data transformations.
- The codebase was authored primarily with AI assistance—roughly 95% by OpenAI Codex and 5% by Claude Code—with artistic direction and stewardship by @habemus-papadum.

## Development

This project uses [UV](https://docs.astral.sh/uv/) for dependency management.

### Setup

```bash
# Install UV if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/habemus-papadum/pdum_plumbum.git
cd pdum_plumbum

# Provision the entire toolchain (uv sync, pnpm install, widget build, pre-commit hooks)
./scripts/setup.sh
```

**Important for Development**:
- `./scripts/setup.sh` is idempotent—rerun it after pulling dependency changes
- Use `uv sync --frozen` to ensure the lockfile is respected when installing Python deps

### Running Tests

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

### Building

```bash
# Build Python
./scripts/build.sh

# Or build just the Python distribution artifacts
uv build
```

### Publishing

```bash
# Build and publish to PyPI (requires credentials)
./scripts/publish.sh
```

### Automation scripts

- `./scripts/setup.sh` – bootstrap uv, pnpm, widget bundle, and pre-commit hooks
- `./scripts/build.sh` – reproduce the release build locally
- `./scripts/pre-release.sh` – run the full battery of quality checks
- `./scripts/release.sh` – orchestrate the release (creates tags, publishes to PyPI/GitHub)
- `./scripts/test_notebooks.sh` – execute demo notebooks (uses `./scripts/nb.sh` under the hood)
- `./scripts/setup-visual-tests.sh` – install Playwright browsers for visual tests

## License

MIT License - see LICENSE file for details.
