# plumbum

[![CI](https://github.com/habemus-papadum/pdum_plumbum/actions/workflows/ci.yml/badge.svg)](https://github.com/habemus-papadum/pdum_plumbum/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/habemus-papadum-plumbum.svg)](https://pypi.org/project/habemus-papadum-plumbum/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Coverage](https://raw.githubusercontent.com/habemus-papadum/pdum_plumbum/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/habemus-papadum/pdum_plumbum/blob/python-coverage-comment-action-data/htmlcov/index.html)

A plumbing syntax for Python that provides a clear distinction between data and operators, enabling composable function pipelines with explicit control flow.

## Overview

**plumbum** is a library for threading data through function calls using intuitive pipe operators. Inspired by [Pipe](https://github.com/JulienPalard/Pipe), it offers a redesigned approach with a separation between operator construction and execution.

**This is primarily a syntax library** focused on making data transformations more readable and composable. It is not optimized for performance-critical applications, but rather for clarity and expressiveness in your code.

## Installation
```bash
pip install habemus-papadum-plumbum
```

## Usage

```python
# Basics
5 > add(1) | multiply(2)  # 12

# Iterators
[1, 2, 3, 4] > select(add(1) | multiply(2)) | where(lambda x: x < 8) # [4, 6]
 
# Async
await (5 > async_add(1) | async_multiply(2))  # 12
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
- **Avoid chained `>` comparisons.** Python treats `x > a > b` as a chained comparison, which is incompatible with plumbum operators. Prefer `x > (a | b)`; only use `(x > a) > b` when you intentionally need two separate execution steps.

## Tutorial Notebook

Walk through synchronous and asynchronous pipelines step-by-step in the [Tutorial](https://habemus-papadum.github.io/pdum_plumbum/tutorial/).

## Quick Start

```python
from pdum.plumbum import pb

# Define operators using the @pb decorator
@pb
def add(x, n):
    return x + n

@pb
def multiply(x, n):
    return x * n

@pb
def power(x, n):
    return x ** n

# Thread data through a single operator
result = 5 > add(3)
# 8

# Combine operators into pipelines with |
result = 5 > (add(3) | multiply(2))
# (5 + 3) * 2 = 16

# Define reusable operator pipelines
transform = multiply(2) | add(10) | power(2)
result = 3 > transform
# ((3 * 2) + 10) ** 2 = 256

# Operators are just values - assign and reuse them
double_and_square = multiply(2) | power(2)
5 > double_and_square  # (5 * 2) ** 2 = 100
10 > double_and_square  # (10 * 2) ** 2 = 400
```

## Core Concepts

### The `@pb` Decorator

The `@pb` decorator converts functions into pipe-compatible operators. The **first parameter** of the function is where threaded data will be inserted.

#### As a Function Decorator

```python
@pb
def add(x, n):  # x receives the threaded data
    return x + n

@pb
def format_number(value, prefix="Result:", decimals=2):
    return f"{prefix} {value:.{decimals}f}"

# Threading data
5 > add(10)  # x=5, n=10 -> 15
3.14159 > format_number(decimals=3)  # value=3.14159 -> "Result: 3.142"
```

#### As a One-Off Wrapper

You can use `pb()` directly to wrap functions inline without decorating them:

```python
# Wrap built-in functions on-the-fly
5 > pb(print)  # Prints: 5

# Wrap lambdas for one-off operations
"hello" > (pb(lambda s: s.upper()) | pb(print))  # Prints: HELLO

# Wrap functions with keyword arguments
@pb
def add(x, n):
    return x + n

10 > (add(5) | pb(print))  # Prints: 15

# Chain multiple one-off wraps
data = [1, 2, 3, 4, 5]
data > (pb(lambda x: [i * 2 for i in x]) | pb(sum) | pb(print))  # Prints: 30

# Useful for debugging pipelines
debug_pipeline = add(5) | pb(print) | multiply(2) | pb(print)
result = 10 > debug_pipeline  # Debug prints fire at each stage
```

#### With Keyword Arguments

Keyword arguments work seamlessly with partial application:

```python
@pb
def greet(name, greeting="Hello", punctuation="!"):
    return f"{greeting}, {name}{punctuation}"

# Use with keyword arguments
"Alice" > greet(greeting="Hi")  # "Hi, Alice!"
"Bob" > greet(punctuation=".")  # "Hello, Bob."
"Charlie" > greet(greeting="Hey", punctuation="!!!")  # "Hey, Charlie!!!"

# Mix positional and keyword arguments
"Diana" > greet("Greetings", punctuation="...")  # "Greetings, Diana..."

# Build incrementally with keywords
formal_greet = greet(greeting="Good day", punctuation=".")
"Elizabeth" > formal_greet  # "Good day, Elizabeth."
```

### Operators: `|` (Pipe) and `>` (Thread)

- **`|` (pipe)**: Combines operators into a pipeline without executing
- **`>` (thread)**: Threads data through an operator or pipeline

```python
# | creates pipelines (no execution yet)
pipeline = add(1) | multiply(2) | add(3)

# > executes the pipeline with data
result = 5 > pipeline  # ((5 + 1) * 2) + 3 = 15
```

### Partial Application

Call operators with arguments to partially apply them:

```python
@pb
def add_three(x, a, b, c):
    return x + a + b + c

# Build up arguments incrementally
op = add_three(1)      # x will be threaded, a=1
op = op(2)             # Add b=2
op = op(3)             # Add c=3
result = 10 > op      # 10 + 1 + 2 + 3 = 16
```

### Iterable Helpers (`select` and `where`)

Use the built-in iterable operators to transform and filter collections without
dropping out of pipeline composition:

```python
from pdum.plumbum import pb, select, where

# Transform every item in an iterable
double_values = select(lambda value: value * 2)
list([1, 2, 3] > double_values)
# [2, 4, 6]

# Keep only values that satisfy a predicate
only_evens = where(lambda value: value % 2 == 0)
list([1, 2, 3, 4, 5] > only_evens)
# [2, 4]

# Compose transformations and filters
normalize = select(lambda value: value + 1) | where(lambda value: value % 2 == 0)
list([1, 2, 3, 4] > normalize)
# [2, 4]

# Embed a pipeline as a function using to_function()
@pb
def add_one(value: int) -> int:
    return value + 1

@pb
def mul_two(value: int) -> int:
    return value * 2

combine = select(add_one | mul_two) | where(lambda value: value % 2 == 0)
list([1, 2, 3, 4] > combine)
# [4, 6, 8, 10]
```

### Async Iterable Helpers (`aiter`, `aselect`, and `awhere`)

The async counterparts mirror the synchronous helpers and work with both sync and async callables:

```python
import asyncio

from pdum.plumbum import apb, pb
from pdum.plumbum.aiterops import aiter, aselect, awhere

@pb
def inc(value: int) -> int:
    return value + 1

@apb
async def async_double(value: int) -> int:
    await asyncio.sleep(0)
    return value * 2

async def main() -> list[int]:
    pipeline = (
        aiter
        | aselect(inc)  # sync mapper
        | awhere(lambda value: value % 2 == 0)  # sync predicate
        | aselect(async_double)  # async mapper
    )
    iterator = await ([1, 2, 3, 4] > pipeline)
    return [item async for item in iterator]

asyncio.run(main())
# [4, 6]
```

### Plain Functions as Operators

Functions are automatically wrapped when used in pipelines:

```python
def plain_increment(x):
    return x + 3

def plain_add(x, n):
    return x + n

# Automatically wrapped in PbFunc when used with |
pipeline = multiply(2) | plain_increment  # plain_increment gets wrapped
5 > pipeline  # (5 * 2) + 3 = 13

# Combine with functools.partial to supply extra arguments
from functools import partial

pipeline_with_extra = multiply(2) | partial(plain_add, n=3)
5 > pipeline_with_extra  # (5 * 2) + 3 = 13
```

### Data Type Flexibility

**plumbum makes no assumptions about the data you thread through operators.** Unlike libraries focused on iterators or streams, you can use any Python type:

```python
# Works with numbers
5 > (add(3) | multiply(2))

# Works with strings
"hello" > (pb(str.upper) | pb(lambda s: s + "!"))

# Works with dictionaries
{"a": 1, "b": 2} > (pb(lambda d: d.copy()) | pb(lambda d: {**d, "c": 3}))

# Works with custom objects
class Point:
    def __init__(self, x, y):
        self.x, self.y = x, y

@pb
def translate(point, dx, dy):
    return Point(point.x + dx, point.y + dy)

Point(1, 2) > translate(5, 3)  # Point(6, 5)

# Works with lists (but no special iterator handling)
[1, 2, 3] > pb(lambda lst: [x * 2 for x in lst])  # [2, 4, 6]
```

The data simply flows through your functions—plumbum is purely a **syntax wrapper** around normal function calls.

## jq-like Operators

The `pdum.plumbum.jq` module layers a minimal jq-style path syntax on top of plumbum's pipelines. Use it to navigate and transform JSON-like data structures without leaving Python:

```python
from pdum.plumbum import pb
from pdum.plumbum.jq import field, transform, group_by
from pdum.plumbum.iterops import select, where

records = [
    {"user": {"id": 1, "name": "Ada"}, "scores": [10, 15]},
    {"user": {"id": 2, "name": "Linus"}, "scores": [20]},
]

# Extract nested fields via dotted expressions
names = records > (select(field("user.name")) | pb(list))
# ['Ada', 'Linus']

# Transform values in-place while keeping the original structure immutable
curved = records > transform("scores[]", lambda score: score * 1.1)

# Combine with iterops helpers for more complex pipelines
high_scorers = (
    records
    > (
        where(lambda row: max(row["scores"]) >= 15)
        | group_by("user.id")
    )
)
```

Async counterparts (prefixed with `a`, e.g. `aexplode`, `agroup_by`) are available for working with `async` iterators.

## Advanced Examples

### Data Processing Pipeline

```python
from pdum.plumbum import pb

@pb
def filter_positive(numbers):
    """Generator that yields only positive numbers"""
    for n in numbers:
        if n > 0:
            yield n

@pb
def square_all(numbers):
    """Generator that yields squared values"""
    for n in numbers:
        yield n ** 2

# Define a reusable data processing pipeline
# Note: Decorated functions can be used directly (no parentheses needed)
# sum is a plain function, automatically wrapped by PbPair
process = filter_positive | square_all | sum

# Apply to different datasets
[-2, 3, -1, 4, 5] > process  # 3² + 4² + 5² = 50
[-10, 2, -5, 6] > process    # 2² + 6² = 40
```

### String Processing

```python
@pb
def strip(s):
    return s.strip()

@pb
def uppercase(s):
    return s.upper()

@pb
def replace(s, old, new):
    return s.replace(old, new)

# Build text transformation pipeline
clean_text = strip() | replace(" ", "_") | uppercase()

"  hello world  " > clean_text  # "HELLO_WORLD"
```

### Chaining with Built-ins

```python
# Wrap built-in functions and compose them
pipeline = pb(str.strip) | pb(str.upper) | pb(print)
"  test  " > pipeline  # Prints: TEST
```

## Design Philosophy

### Syntax Over Performance

**plumbum prioritizes readability and composability over raw performance.** Each pipeline execution involves some overhead from operator dispatch and wrapper objects. For performance-critical code paths:

- Use traditional function composition
- Consider profiling before adopting plumbum in hot loops
- plumbum shines in data transformation scripts, exploratory code, and ETL pipelines where clarity matters more than microseconds

### General Purpose Data Threading

plumbum is **not** an iterator/stream library. It's a general-purpose syntax for threading **any data** through **any functions**. Whether you're working with:
- Single values (numbers, strings, objects)
- Collections (lists, dicts, sets)
- Custom classes
- Mixed types in a pipeline

The library imposes zero constraints on your data types. It simply provides a cleaner syntax for `f(g(h(x)))` → `x > (h() | g() | f())`.


## Roadmap

- ✅ Core pipe operations (`|` and `>`)
- ✅ Partial application
- ✅ Automatic function wrapping
- ✅ Async/await support
- ✅ Additional utility operators

## Acknowledgements

- plumbum draws direct inspiration from Julien Palard’s [Pipe](https://github.com/JulienPalard/Pipe); several iterable operators (for example `select`, `where`, and `dedup`) started life there before being reworked for plumbum’s APIs.
- Key differences from Pipe:
  - Operators are inert values: `|` builds pipelines while `>` triggers execution, making composition and reuse explicit.
  - Async is a core capability: sync and async operators coexist in the same pipeline, and iterator helpers come in both synchronous and asynchronous flavors.
  - The bundled `pdum.plumbum.jq` module adds a jq-inspired path/query layer, expanding the original operator toolbox into structured-data transformations.
- The codebase was authored primarily with AI assistance—roughly 95% by OpenAI Codex and 5% by Claude Code—with artistic direction and stewardship by @habemus-papadum.

## API Reference

### `@pb` Decorator

Converts a function into a `PbFunc` operator.

### `Pb` (Abstract Base Class)

Base class for all pipe operators. Implements `|` and `>` operators.

### `PbFunc`

Wraps a function for use in pipelines. Supports partial application and threading.

### `PbPair`

Represents two operators combined with `|`. Threads data sequentially through both.

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
# Build Python + TypeScript artifacts
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
