# plumbum

[![CI](https://github.com/habemus-papadum/pdum_plumbum/actions/workflows/ci.yml/badge.svg)](https://github.com/habemus-papadum/pdum_plumbum/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/habemus-papadum-plumbum.svg)](https://pypi.org/project/habemus-papadum-plumbum/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

A plumbing syntax for Python that provides a clear distinction between data and operators, enabling composable function pipelines with explicit control flow.

## Overview

**plumbum** is a library for threading data through function calls using intuitive pipe operators. Inspired by [Pipe](https://github.com/JulienPalard/Pipe), it offers a redesigned approach with clear separation between operator definition and execution.

**This is primarily a syntax library** focused on making data transformations more readable and composable. It is not optimized for performance-critical applications, but rather for clarity and expressiveness in your code.

## Tutorial Notebook

Walk through synchronous and asynchronous pipelines step-by-step in the [Tutorial](https://habemus-papadum.github.io/pdum_plumbum/tutorial/).

### Key Features

- **Clear Operator/Data Distinction**: Define pipelines without executing them
- **Composable Operators**: Combine operators using `|` to build reusable pipelines
- **Threading Syntax**: Use `>>` to thread data through operators
- **Partial Application**: Build up function arguments incrementally
- **First Parameter Threading**: Data is threaded into the first parameter of functions
- **Any Data Type**: No assumptions about data types—works with any Python values, not just iterators
- **Future Async Support**: Planned async/await compatible version

### Why plumbum?

Unlike the original Pipe library, plumbum makes it easy to define operators and compose them **before** execution:

```python
# In plumbum - operators can be defined and composed without data
op = multiply(2) | add(3)  # Just defining the pipeline
result = 5 >> op  # Now execute: (5 * 2) + 3 = 13

# This is not possible in Pipe - execution starts immediately when applying "|'
```

This design enables:
- Defining reusable operator pipelines as values
- Assigning complex operations to variables
- Composing operators before knowing what data they'll process
- Clear distinction between pipeline structure and data flow

## Installation

Install using pip:

```bash
pip install habemus-papadum-plumbum
```

Or using uv:

```bash
uv pip install habemus-papadum-plumbum
```

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
result = 5 >> add(3)
# 8

# Combine operators into pipelines with |
result = 5 >> (add(3) | multiply(2))
# (5 + 3) * 2 = 16

# Define reusable operator pipelines
transform = multiply(2) | add(10) | power(2)
result = 3 >> transform
# ((3 * 2) + 10) ** 2 = 256

# Operators are just values - assign and reuse them
double_and_square = multiply(2) | power(2)
5 >> double_and_square  # (5 * 2) ** 2 = 100
10 >> double_and_square  # (10 * 2) ** 2 = 400
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
5 >> add(10)  # x=5, n=10 -> 15
3.14159 >> format_number(decimals=3)  # value=3.14159 -> "Result: 3.142"
```

#### As a One-Off Wrapper

You can use `pb()` directly to wrap functions inline without decorating them:

```python
# Wrap built-in functions on-the-fly
5 >> pb(print)  # Prints: 5

# Wrap lambdas for one-off operations
"hello" >> pb(lambda s: s.upper()) >> pb(print)  # Prints: HELLO

# Wrap functions with keyword arguments
@pb
def add(x, n):
    return x + n

10 >> add(5) >> pb(print)  # Prints: 15

# Chain multiple one-off wraps
data = [1, 2, 3, 4, 5]
data >> pb(lambda x: [i * 2 for i in x]) >> pb(sum) >> pb(print)  # Prints: 30

# Useful for debugging pipelines
result = (
    10
    >> add(5)
    >> pb(print)  # Debug: prints 15
    >> multiply(2)
    >> pb(print)  # Debug: prints 30
)
```

#### With Keyword Arguments

Keyword arguments work seamlessly with partial application:

```python
@pb
def greet(name, greeting="Hello", punctuation="!"):
    return f"{greeting}, {name}{punctuation}"

# Use with keyword arguments
"Alice" >> greet(greeting="Hi")  # "Hi, Alice!"
"Bob" >> greet(punctuation=".")  # "Hello, Bob."
"Charlie" >> greet(greeting="Hey", punctuation="!!!")  # "Hey, Charlie!!!"

# Mix positional and keyword arguments
"Diana" >> greet("Greetings", punctuation="...")  # "Greetings, Diana..."

# Build incrementally with keywords
formal_greet = greet(greeting="Good day", punctuation=".")
"Elizabeth" >> formal_greet  # "Good day, Elizabeth."
```

### Operators: `|` (Pipe) and `>>` (Thread)

- **`|` (pipe)**: Combines operators into a pipeline without executing
- **`>>` (thread)**: Threads data through an operator or pipeline

```python
# | creates pipelines (no execution yet)
pipeline = add(1) | multiply(2) | add(3)

# >> executes the pipeline with data
result = 5 >> pipeline  # ((5 + 1) * 2) + 3 = 15
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
result = 10 >> op      # 10 + 1 + 2 + 3 = 16
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
5 >> pipeline  # (5 * 2) + 3 = 13

# Combine with functools.partial to supply extra arguments
from functools import partial

pipeline_with_extra = multiply(2) | partial(plain_add, n=3)
5 >> pipeline_with_extra  # (5 * 2) + 3 = 13
```

### Data Type Flexibility

**plumbum makes no assumptions about the data you thread through operators.** Unlike libraries focused on iterators or streams, you can use any Python type:

```python
# Works with numbers
5 >> add(3) >> multiply(2)

# Works with strings
"hello" >> pb(str.upper) >> pb(lambda s: s + "!")

# Works with dictionaries
{"a": 1, "b": 2} >> pb(lambda d: d.copy()) >> pb(lambda d: {**d, "c": 3})

# Works with custom objects
class Point:
    def __init__(self, x, y):
        self.x, self.y = x, y

@pb
def translate(point, dx, dy):
    return Point(point.x + dx, point.y + dy)

Point(1, 2) >> translate(5, 3)  # Point(6, 5)

# Works with lists (but no special iterator handling)
[1, 2, 3] >> pb(lambda lst: [x * 2 for x in lst])  # [2, 4, 6]
```

The data simply flows through your functions—plumbum is purely a **syntax wrapper** around normal function calls.

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
[-2, 3, -1, 4, 5] >> process  # 3² + 4² + 5² = 50
[-10, 2, -5, 6] >> process    # 2² + 6² = 40
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

"  hello world  " >> clean_text  # "HELLO_WORLD"
```

### Chaining with Built-ins

```python
# Wrap built-in functions and compose them
pipeline = pb(str.strip) | pb(str.upper) | pb(print)
"  test  " >> pipeline  # Prints: TEST
```

## Design Philosophy

### Syntax Over Performance

**plumbum prioritizes readability and composability over raw performance.** Each `>>` operation involves some overhead from operator dispatch and wrapper objects. For performance-critical code paths:

- Use traditional function composition
- Consider profiling before adopting plumbum in hot loops
- plumbum shines in data transformation scripts, exploratory code, and ETL pipelines where clarity matters more than microseconds

### General Purpose Data Threading

plumbum is **not** an iterator/stream library. It's a general-purpose syntax for threading **any data** through **any functions**. Whether you're working with:
- Single values (numbers, strings, objects)
- Collections (lists, dicts, sets)
- Custom classes
- Mixed types in a pipeline

The library imposes zero constraints on your data types. It simply provides a cleaner syntax for `f(g(h(x)))` → `x >> h() >> g() >> f()`.


## Roadmap

- ✅ Core pipe operations (`|` and `>>`)
- ✅ Partial application
- ✅ Automatic function wrapping
- ✅ Async/await support
- 🔜 Additional utility operators

## API Reference

### `@pb` Decorator

Converts a function into a `PbFunc` operator.

### `Pb` (Abstract Base Class)

Base class for all pipe operators. Implements `|` and `>>` operators.

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
