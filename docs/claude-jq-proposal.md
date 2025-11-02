# JQ-like Module for plumbum: Design and Implementation Plan

## Executive Summary

This proposal outlines the design and implementation of a jq-like module for the plumbum library that enables powerful JSON/dict transformation pipelines. The module, tentatively named `jqops`, will provide composable operators that leverage plumbum's existing pipeline infrastructure while introducing jq-specific functionality through a balanced mix of programmatic operators and string-based selectors.

## Design Philosophy

### Core Principles

1. **Composability First**: Every operator must work seamlessly with plumbum's `|` and `>>` operators
2. **Leverage Existing Infrastructure**: Reuse `iterops` operators where appropriate (select, where, chain, etc.)
3. **Progressive Complexity**: Simple operations should be simple, complex operations should be possible
4. **Type Flexibility**: Support both streaming (iterator) and batch (list/dict) operations
5. **Pythonic API**: Feel natural to Python developers while providing jq's power

### Key Design Decisions

1. **Dual Interface Approach**:
   - Programmatic operators for complex logic (lambdas, functions)
   - String-based selectors for common path operations (dot notation)

2. **Streaming by Default**: Most operators yield results to support large datasets

3. **Explicit vs Implicit**: Make data flow explicit rather than relying on jq's implicit context

## Module Architecture

### Core Components

```
src/pdum/plumbum/jqops/
├── __init__.py          # Public API exports
├── core.py              # Core jq-like operators
├── selectors.py         # String-based path selectors
├── transformers.py      # Data transformation operators
├── aggregators.py       # Aggregation and reduction operators
├── validators.py        # Data validation operators
└── utils.py            # Helper functions and utilities
```

## Operator Categories

### 1. Path Selection Operators

These operators handle navigation through JSON-like structures using both programmatic and string-based approaches.

#### `jq()` - String-based path selector
```python
@pb
def jq(data, path: str):
    """
    Parse and apply jq-like path expressions.
    Supports:
    - Simple paths: "name", "user.email"
    - Array indexing: "items[0]", "users[-1]"
    - Array slicing: "items[1:3]", "items[:2]"
    - Wildcards: "users[*].name", "*.id"
    - Optional chaining: "user?.email", "meta?.tags?"
    - Multi-select: "{name,email}", "{id,user.name}"
    """
```

#### `path()` - Programmatic path selector
```python
@pb
def path(data, *keys):
    """Navigate through nested structures programmatically."""
    # Example: data >> path("users", 0, "email")
```

#### `paths()` - Extract all paths
```python
@pb
def paths(data, predicate=None):
    """
    Yield all paths to leaf values.
    Optional predicate filters which paths to include.
    """
```

### 2. Object/Dict Operators

#### `pick()` - Select specific fields
```python
@pb
def pick(data, *keys, **renames):
    """
    Select and optionally rename fields.
    Examples:
    - pick("id", "name")
    - pick("id", username="user.name")
    """
```

#### `omit()` - Remove specific fields
```python
@pb
def omit(data, *keys, recursive=False):
    """Remove specified keys from objects."""
```

#### `merge()` - Deep merge objects
```python
@pb
def merge(data, *others, strategy="deep"):
    """Merge objects with configurable strategy."""
```

#### `flatten_obj()` - Flatten nested objects
```python
@pb
def flatten_obj(data, separator="."):
    """
    Flatten nested objects to single-level with compound keys.
    {"a": {"b": 1}} -> {"a.b": 1}
    """
```

#### `unflatten_obj()` - Unflatten to nested
```python
@pb
def unflatten_obj(data, separator="."):
    """
    Unflatten compound keys back to nested structure.
    {"a.b": 1} -> {"a": {"b": 1}}
    """
```

### 3. Array/List Operators

#### `explode()` - Expand arrays into stream
```python
@pb
def explode(data, path=None, preserve_parent=False):
    """
    Explode array at path into individual items.
    If preserve_parent=True, add parent context to each item.
    """
```

#### `implode()` - Collect stream into array
```python
@pb
def implode(items):
    """Collect items from iterator into list."""
```

#### `index_by()` - Index array by field
```python
@pb
def index_by(data, key):
    """
    Convert array to dict indexed by field.
    [{"id": 1, "name": "a"}] -> {1: {"id": 1, "name": "a"}}
    """
```

#### `unique_by()` - Unique by field
```python
@pb
def unique_by(data, key):
    """Remove duplicates based on field value."""
```

### 4. Transformation Operators

#### `map_values()` - Transform all values
```python
@pb
def map_values(data, mapper):
    """Apply transformation to all values in dict/list."""
```

#### `map_keys()` - Transform all keys
```python
@pb
def map_keys(data, mapper):
    """Apply transformation to all keys in dict."""
```

#### `with_entries()` - Transform key-value pairs
```python
@pb
def with_entries(data, transformer):
    """
    Transform dict as list of {key, value} entries.
    Inverse of from_entries.
    """
```

#### `from_entries()` - Build dict from entries
```python
@pb
def from_entries(entries):
    """Convert [{key, value}] format to dict."""
```

#### `to_entries()` - Convert dict to entries
```python
@pb
def to_entries(data):
    """Convert dict to [{key, value}] format."""
```

### 5. Conditional Operators

#### `when()` - Conditional transformation
```python
@pb
def when(data, condition, then_op, else_op=None):
    """Apply operator conditionally."""
```

#### `default()` - Provide defaults
```python
@pb
def default(data, defaults):
    """Fill in missing values with defaults."""
```

#### `coalesce()` - First non-null value
```python
@pb
def coalesce(data, *paths):
    """Return first non-null value from paths."""
```

### 6. Type Conversion Operators

#### `as_type()` - Safe type conversion
```python
@pb
def as_type(data, type_name, default=None):
    """
    Safely convert to type with optional default.
    Types: "int", "float", "str", "bool", "list", "dict"
    """
```

#### `parse_json()` - Parse JSON strings
```python
@pb
def parse_json(data, safe=True):
    """Parse JSON string to Python object."""
```

#### `to_json()` - Convert to JSON string
```python
@pb
def to_json(data, indent=None, sort_keys=False):
    """Convert Python object to JSON string."""
```

### 7. String Operations

#### `interpolate()` - String interpolation
```python
@pb
def interpolate(data, template):
    """
    Interpolate values into template string.
    "Hello {name}" with {"name": "World"} -> "Hello World"
    """
```

#### `capture()` - Regex capture groups
```python
@pb
def capture(data, pattern, path=None):
    """Extract regex groups as dict."""
```

### 8. Aggregation Operators

#### `group_by_field()` - Group by field value
```python
@pb
def group_by_field(data, key):
    """
    Group items by field value.
    Different from iterops.groupby - returns dict of lists.
    """
```

#### `count_by()` - Count occurrences
```python
@pb
def count_by(data, key):
    """Count items grouped by key."""
```

#### `sum_by()` - Sum field values
```python
@pb
def sum_by(data, key):
    """Sum numeric field across items."""
```

#### `stats()` - Calculate statistics
```python
@pb
def stats(data, key=None):
    """Calculate min, max, mean, sum, count for field."""
```

### 9. Validation Operators

#### `validate()` - Schema validation
```python
@pb
def validate(data, schema):
    """Validate data against schema, yield if valid."""
```

#### `assert_that()` - Assert condition
```python
@pb
def assert_that(data, condition, message=None):
    """Assert condition or raise error."""
```

### 10. Advanced Operators

#### `walk()` - Deep transformation
```python
@pb
def walk(data, visitor):
    """
    Recursively visit and transform all values.
    Similar to jq's walk.
    """
```

#### `recurse()` - Recursive descent
```python
@pb
def recurse(data, selector):
    """Recursively apply selector until no matches."""
```

#### `stream()` - Convert to event stream
```python
@pb
def stream(data):
    """
    Convert nested structure to stream of (path, value) events.
    Useful for large JSON processing.
    """
```

#### `debug()` - Debug inspection
```python
@pb
def debug(data, label=None):
    """Print data with optional label, pass through unchanged."""
```

## String Selector Syntax

The `jq()` operator will support a subset of jq's syntax optimized for common use cases:

### Basic Syntax
- `.` - Identity (current value)
- `.field` - Field access
- `.field.subfield` - Nested field access
- `.[0]` - Array index
- `.[-1]` - Negative index (from end)
- `.[1:3]` - Array slice
- `.[*]` - All array elements
- `.[]` - Explode array

### Advanced Syntax
- `.field?` - Optional field (no error if missing)
- `.field//default` - Default value if null/missing
- `{name,email}` - Multi-select fields
- `{id,name:.user.name}` - Select with rename
- `.users[*].name` - Map over array
- `.. | .field` - Recursive descent
- `select(.age > 18)` - Filter with condition
- `|` - Pipe within jq expression

### Examples
```python
# Simple field access
data >> jq(".user.email")

# Array operations
data >> jq(".items[0].name")
data >> jq(".users[*].email")

# Multi-select with rename
data >> jq("{id, username:.user.name, age}")

# Optional chaining
data >> jq(".meta?.tags?[0]")

# With default
data >> jq(".price // 0")

# Complex pipeline in jq syntax
data >> jq(".items[] | select(.active) | {id, name}")
```

## Implementation Strategy

### Phase 1: Core Infrastructure (Week 1)
1. Set up module structure and basic operators
2. Implement `jq()` string parser for basic paths
3. Implement fundamental operators: `pick`, `omit`, `explode`, `path`
4. Write comprehensive tests for core operators

### Phase 2: Transformation Operators (Week 2)
1. Implement object transformation: `map_values`, `map_keys`, `with_entries`
2. Implement array operations: `index_by`, `unique_by`, `implode`
3. Add type conversion: `as_type`, `parse_json`, `to_json`
4. Extend tests for transformation operators

### Phase 3: Advanced Selectors (Week 3)
1. Enhance `jq()` parser for advanced syntax (wildcards, slices, optional)
2. Implement conditional operators: `when`, `default`, `coalesce`
3. Add aggregation operators: `group_by_field`, `count_by`, `sum_by`
4. Implement `walk` and `recurse` for deep transformations

### Phase 4: Integration & Polish (Week 4)
1. Add validation operators: `validate`, `assert_that`
2. Implement debugging aids: `debug`, `stream`
3. Create comprehensive examples covering jq-fu-43-examples.md scenarios
4. Performance optimization and memory profiling
5. Documentation and tutorials

## Usage Examples

### Example 1: Basic Field Selection
```python
from pdum.plumbum import pb
from pdum.plumbum.jqops import jq, pick

# Using jq string syntax
user_email = data >> jq(".user.email")

# Using programmatic approach
user_info = data >> pick("id", "name", email="user.email")
```

### Example 2: Array Processing
```python
from pdum.plumbum.jqops import jq, explode, where, pick

# Extract active users' emails
active_emails = (
    data
    >> jq(".users[]")  # Explode users array
    >> where(lambda u: u.get("active", False))
    >> jq(".email")
)

# Alternative with explode
active_users = (
    data
    >> explode("users")
    >> where(lambda u: u["active"])
    >> pick("id", "email")
)
```

### Example 3: Complex Transformation
```python
from pdum.plumbum.jqops import jq, group_by_field, map_values, sum_by

# Group orders by customer and calculate totals
customer_totals = (
    data
    >> jq(".orders[]")
    >> group_by_field("customer_id")
    >> map_values(sum_by("total"))
)
```

### Example 4: Nested Array Processing
```python
from pdum.plumbum.jqops import jq, explode, pick, flatten_obj

# Flatten nested structure with parent context
flattened = (
    data
    >> explode("departments", preserve_parent=True)
    >> jq(".employees[]")
    >> pick("id", "name", dept="parent.name")
    >> flatten_obj()
)
```

### Example 5: Conditional Transformations
```python
from pdum.plumbum.jqops import when, default, as_type

# Process with conditions and defaults
processed = (
    data
    >> default({"status": "pending", "priority": 0})
    >> when(
        lambda d: d["status"] == "urgent",
        then_op=pick("id", "title") | merge({"priority": 100})
    )
    >> as_type("priority", "int", default=0)
)
```

### Example 6: Validation Pipeline
```python
from pdum.plumbum.jqops import validate, assert_that, where

# Validate and filter data
schema = {
    "required": ["id", "email"],
    "types": {"age": int, "email": str}
}

valid_users = (
    data
    >> jq(".users[]")
    >> validate(schema)
    >> where(lambda u: u.get("age", 0) >= 18)
    >> assert_that(lambda u: "@" in u["email"], "Invalid email")
)
```

## Integration with Existing iterops

The jqops module will seamlessly integrate with existing iterops:

```python
from pdum.plumbum.iterops import select, where, batched, dedup
from pdum.plumbum.jqops import jq, explode, pick

# Combine jqops with iterops
pipeline = (
    jq(".items[]")           # jqops: explode array
    | where(lambda x: x)     # iterops: filter
    | pick("id", "name")     # jqops: select fields
    | dedup(key="id")        # iterops: remove duplicates
    | batched(10)            # iterops: batch results
)

results = data >> pipeline
```

## Performance Considerations

### Optimization Strategies

1. **Lazy Evaluation**: Use generators wherever possible
2. **Path Caching**: Cache parsed path expressions in jq()
3. **Short-circuit Evaluation**: Stop early when possible (e.g., coalesce)
4. **Memory Management**: Stream large datasets instead of loading fully
5. **C Extensions**: Consider Cython for hot paths (future enhancement)

### Benchmarks to Track

1. Simple field access vs native dict access
2. Large array processing (explode performance)
3. Deep nesting navigation
4. Complex jq expression parsing
5. Memory usage with large datasets

## Testing Strategy

### Unit Tests
- Each operator tested independently
- Edge cases: empty data, missing fields, type mismatches
- Error handling and useful error messages

### Integration Tests
- Complex pipelines combining multiple operators
- Compatibility with existing iterops
- Async operator integration (future)

### Scenario Tests
- Implement all 43 examples from jq-fu-43-examples.md
- Real-world data transformation scenarios
- Performance regression tests

## Documentation Plan

### API Documentation
- Comprehensive docstrings for all operators
- Type hints for better IDE support
- Examples in each docstring

### Tutorials
1. Getting Started with jqops
2. Migrating from jq to jqops
3. Advanced Transformation Patterns
4. Performance Best Practices

### Reference Materials
- Operator quick reference card
- jq syntax support matrix
- Common patterns cookbook

## Future Enhancements

### Phase 2 Features (Future)
1. **Async Support**: Async versions of all operators (ajqops)
2. **Schema Support**: JSON Schema validation integration
3. **Type Safety**: Runtime type checking with better error messages
4. **Performance**: C extensions for critical paths
5. **Extended Syntax**: More jq syntax support in string selectors

### Community Features
1. **Plugin System**: Allow custom operators
2. **Recipe Library**: Community-contributed patterns
3. **Online Playground**: Web-based testing environment
4. **Migration Tools**: Automated jq to jqops converter

## Risk Mitigation

### Technical Risks
1. **Parser Complexity**: Start with subset, expand gradually
2. **Performance**: Profile early, optimize critical paths
3. **API Surface**: Keep core small, extensions in submodules
4. **Backward Compatibility**: Version string syntax separately

### Adoption Risks
1. **Learning Curve**: Provide excellent documentation
2. **jq Compatibility**: Clear documentation on differences
3. **Integration**: Ensure seamless iterops integration

## Success Metrics

1. **Coverage**: Support 90% of jq-fu-43-examples.md patterns
2. **Performance**: Within 2x of native Python for simple operations
3. **Adoption**: Clear migration path from jq
4. **Quality**: 95%+ test coverage
5. **Usability**: Intuitive API requiring minimal documentation lookup

## Conclusion

The jqops module will provide a powerful, Pythonic approach to JSON-like data transformation that leverages plumbum's elegant pipeline syntax. By balancing programmatic flexibility with jq's proven string-based selectors, we can create a tool that's both powerful and accessible. The modular design ensures that users can adopt jqops incrementally, using only the operators they need while maintaining full compatibility with existing plumbum operators.

The implementation will proceed in phases, with core functionality delivered early and advanced features added based on user feedback. This approach ensures we can validate the design with real usage before committing to more complex features.
