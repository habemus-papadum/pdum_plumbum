# JQ-Like Operator Module — Design & Implementation Plan

This document outlines a proposed design for a `pdum.plumbum.jq` module that
brings jq-style data wrangling primitives to the plumbum operator ecosystem.
The goal is *not* to recreate jq wholesale, but to provide a composable toolbox
that covers the common patterns captured in
`docs/jq-fu-43-examples.md` while embracing plumbum's pipeline-first API.

---

## Design Goals

- **Composable primitives** – prefer many small operators over a single
  all-powerful function so that users can build pipelines tailored to their data.
- **Leverage existing operators** – reuse `iterops`/`aiterops` where possible
  (e.g. `select`, `where`, `groupby`, `traverse`, `batched`) to avoid duplication.
- **JSON-ish focus** – assume inputs are Python structures composed of dicts,
  lists/tuples, scalars, and `None`. Operators should degrade gracefully when
  encountering missing or heterogeneous shapes.
- **Lightweight jq syntax** – provide a minimal string syntax for common jq dot
  operations (field selection, list indexing, wildcards) to avoid lambda boilerplate,
  but keep the grammar intentionally small.
- **Sync and async parity** – mirror the API in both sync and async flavors so
  pipelines can operate on regular iterables or async streams.
- **Observability & safety** – lean on pure functions; avoid mutating inputs;
  provide predictable error handling (prefer explicit exceptions over silent
  failure except where jq traditionally yields `null`/empty results).

---

## Module Overview

```
src/pdum/plumbum/jq/
├── __init__.py           # re-export public operators
├── paths.py              # path parser & navigation helpers
├── operators.py          # sync operators, pb-decorated
├── async_operators.py    # async wrappers mirroring sync API
└── typing.py             # common type aliases (JsonValue, JsonPath, etc.)
```

Key entry points:

- `pdum.plumbum.jq.field("foo.bar")` → select nested fields via mini jq string.
- `pdum.plumbum.jq.pluck(["id", "name"])` → project dicts to subset of keys.
- `pdum.plumbum.jq.walk(...)` → traverse trees applying pipelines at matched nodes.
- `pdum.plumbum.jq.filter_contains("tags[]"; value="error")`
- `pdum.plumbum.jq.group_by("path.to.key")` → leverage `iterops.groupby`.

`__init__.py` will expose sync operators and namespace objects
(`jq.iterops` if we need grouped exports). Async variants (prefixed `a`)
will live in `async_operators.py` and be re-exported as well.

---

## Lightweight Path Syntax

We introduce a minimal grammar for path expressions:

- Dot-separated identifiers: `user.address.city`
- Bracket notation for numeric index: `items[0]`
- Wildcard index: `items[]` → expand each element (akin to jq `[]`)
- Wildcard field: `user.*` → expand all values under the dict
- Optional filter placeholder for future extension (e.g. predicates)

Grammar sketch (EBNF):

```
path        = segment { "." segment } ;
segment     = identifier | wildcard | array_wildcard | array_index ;
identifier  = ALPHA { ALPHA | DIGIT | "_" } ;
wildcard    = "*" ;
array_index = identifier "[" INT "]" | "[" INT "]" ;
array_wildcard = identifier "[]" | "[]" ;
```

Parsing approach:

- Implement `parse_path(expr: str) -> list[PathSegment]` in `paths.py`.
- `PathSegment` variants: `Field(name)`, `Index(idx)`, `FieldWildcard`,
  `IndexWildcard`.
- Provide helpers:
  - `resolve_path(value, segments) -> Iterator[Any]` (yield matches)
  - `get_path` (first match or default)
  - `set_path` (immutably update values)
  - `delete_path`
  - `walk_path` (generate `(path, value)` pairs)

These utilities will underpin the operators.

---

## Operator Categories

### 1. Selection & Projection

| Operator | Description | Backing Building Blocks |
| --- | --- | --- |
| `field(expr: str, default=...)` | Yield values at `expr`, similar to jq `.foo.bar` | `paths.resolve_path`; returns list/first match |
| `pick(keys: Iterable[str])` | Keep subset of dict keys | simple dict comprehension |
| `pluck(*exprs)` | For each expression yield tuple/dict of values | reuse `field` |
| `keys(expr="")` | Yield keys at path | `field` + `builtins.sorted`/`iterops` |
| `values(expr="")` | Yield values at path | `field` |
| `path(expr: str)` | Convert matches into `PathValue(path, value)` (namedtuple) | `paths.walk_path` |

### 2. Filtering

| Operator | Description | Building Blocks |
| --- | --- | --- |
| `where_exists(expr)` | Keep items where `expr` resolves | reuse `field` + truthy check |
| `where_equals(expr, value)` | Compare path value | `iterops.where` w/ callable |
| `contains(expr, needle)` | For strings/lists/dicts | path extraction + python `in` |
| `match(expr, pattern)` | Regex match on string value | `re` + `where` |
| `where_type(expr, type_)` | Filter by type | builtin `isinstance` |

### 3. Transformation

| Operator | Description | Building Blocks |
| --- | --- | --- |
| `project(expr, pipeline)` | Apply pipeline to each resolved value, reassemble | path utils + `pb` |
| `set_value(expr, new_value | pipeline)` | Immutably set value(s) | `paths.set_path` |
| `remove(expr)` | Delete nodes | `paths.delete_path` |
| `transform(expr, pipeline)` | Map pipeline over each item produced by expr | integration with `iterops.select` |
| `walk(expr, pipeline)` | Depth-first traverse; pipeline receives `(path, value)` | `paths.walk_path` + `iterops.select` |
| `coalesce(*exprs, default)` | Choose first non-null path | combine `field` results |

### 4. Aggregation & Grouping

| Operator | Description | Building Blocks |
| --- | --- | --- |
| `group_by(expr)` | Equivalent to jq `group_by(.foo)` | use `iterops.groupby` with key pipeline |
| `count_by(expr)` | Add counts per key | `group_by` + `select(len)` |
| `sum_by(expr, value_expr)` | Summation | `group_by` + pipeline |
| `stats(expr)` | Basic stats (min/max/avg) | small helper + `iterops.select` |

### 5. Structural

| Operator | Description | Building Blocks |
| --- | --- | --- |
| `flatten(expr="")` | Flatten nested lists/dicts like jq `..` | `iterops.traverse` + path context |
| `explode(expr)` | Expand arrays at path | path resolution w/ wildcard |
| `zip_fields(*exprs)` | Combine multiple paths into dict/tuple | `field` + `zip` |
| `merge(*exprs)` | Merge objects found at paths | `collections.ChainMap` |
| `unwind(expr, keep_empty=False)` | Equivalent to SQL UNNEST | path wildcard expansion |

### 6. Async Counterparts

- Mirror the sync API under `pdum.plumbum.jq.async_operators`.
- Each operator uses the same path utilities (sync safe) but returns awaitable
  behavior; utilize `aiterops` helpers where available.

---

## Path Utilities (Implementation Notes)

1. **Segment representation**
   ```python
   @dataclass(frozen=True)
   class Field: name: str
   @dataclass(frozen=True)
   class Index: index: int
   class FieldWildcard: ...
   class IndexWildcard: ...
   ```

2. **Resolver behavior**
   - Accept scalars: yield value only if no remaining segments.
   - Dict: access by key; wildcard yields values for all keys.
   - List/Tuple: numeric index; wildcard yields each item.
   - Missing keys/index out of range: no results (mirrors jq returning empty).

3. **Immutable updates**
   - Return new structure; avoid mutating input.
   - For lists/dicts copy only necessary branches (structural sharing).

4. **Performance**
   - Use iterative traversal rather than recursion where possible.
   - For wildcard expansions yield iterables lazily.

---

## Sample Pipelines (Mapping jq-fu Patterns)

> Numbers refer to sections in `jq-fu-43-examples.md`.

1. **Tag child items with parent fields (#1)**
   ```python
   from pdum.plumbum import pb
   from pdum.plumbum.iterops import select, chain
   from pdum.plumbum.jq import field, pluck, set_value

   pipeline = (
       select(
           pluck("name", "group", "items[]")
           | pb(lambda name, group, item: {"name": name, "group": group, "item": item})
       )
       | chain
   )
   data > pipeline
   ```

2. **Flatten nested arrays with lineage (#3)**
   ```python
   from pdum.plumbum.jq import field, explode

   pipeline = (
       explode("[]")
       | select(
           pluck("id", "buckets[]")
           | pb(lambda parent, bucket: {"parent": parent, "bucket": bucket["name"], "item": bucket["items[]"]})
       )
       | chain
   )
   ```

3. **Drop null/empty fields recursively (#6)**
   ```python
   from pdum.plumbum.jq import walk, remove

   def is_empty(value):
       if value in (None, "", [], {}):
           return True
       return False

   pipeline = walk("..", pb(lambda path, value: remove(path) if is_empty(value) else None))
   ```

4. **Join against side table (#22)**
   ```python
   index_users = pb(lambda left, users: left | set_value("user", users.get(left["user_id"], {})))

   pipeline = (
      pb(lambda records, users: records > select(index_users(users)))
   )
   ```

These sketches demonstrate how jq-like behavior can be composed from the core
operators plus a few JSON-specific utilities.

---

## Implementation Plan

1. **Define types and path DSL**
   - `JsonValue = dict[str, Any] | list[Any] | str | int | float | bool | None`
   - `JsonPath = str | Sequence[PathSegment]`
   - Implement parser (`parse_path`) and serializer (`stringify_path`).
   - Provide normalization helper to accept pre-parsed segments.

2. **Implement resolver + mutation helpers**
   - `resolve_path(value, path)` → iterator of matches
   - `first_path(value, path, default=_MISSING)` for convenience
   - `set_path(value, path, new_value)` → returns copy with value set
   - `delete_path(value, path)` → returns copy with nodes removed
   - `walk_tree(value, include_self=False)` → depth-first yield `(path, value)`

3. **Author sync operators (`operators.py`)**
   - Decorate with `@pb`
   - Each operator should:
     - Accept either string path or parsed segments.
     - Return iterables or updated JSON structures.
     - Where practical, build on `iterops` pipelines (e.g. `select`, `where`).
   - Provide simple data validation (raise `TypeError` on unsupported operations).

4. **Async operators**
   - Wrap sync logic with async awareness using `ensure_async_callable`
     from `aiterops_internals`.
   - For data traversal operations, reuse sync path utilities (they are CPU-bound).
   - Use `async_iter_operator` to integrate with async iterables.

5. **Public API packaging**
   - `jq/__init__.py` re-exports sync + async functions.
   - Add `__all__` list.
   - Consider exposing a namespaced object `jq = SimpleNamespace(...)` for
     easier import (e.g. `from pdum.plumbum import jq`).

6. **Documentation**
   - Update README: quickstart example for jq module.
   - Add reference in `docs/reference.md` pointing to new module.
   - Create tutorial notebook section demonstrating jq-like recipes.
   - Expand `jq-fu-43-examples` with corresponding plumbum pipelines/examples.

7. **Testing Strategy**
   - Unit tests for path parser (valid/invalid expressions, edge cases).
   - Verify resolver handles dicts, lists, mixed types, missing fields.
   - Operator tests covering each category (selection, transform, grouping).
   - Contract tests replicating the 43 jq examples (or representative subset).
   - Async tests mirroring sync behavior.
   - Property-style tests (Hypothesis) for `set_path`/`delete_path` to ensure
     immutability and idempotence.

8. **Performance & Ergonomics Considerations**
   - Benchmark core operations on moderately large JSON arrays.
   - Provide guidance for users on when to switch between lambda and string paths.
   - Evaluate caching of parsed paths to reduce repeated parsing overhead.

9. **Future Extensions (Beyond Initial Scope)**
   - Add expression support for simple arithmetic/boolean operators in path DSL.
   - Provide pattern-matching / filter blocks (e.g. `.items[] | select(.price > 10)`).
   - Integrate with `uv` CLI to offer command-line jq-like usage.
   - Support JSON Pointer compatibility for interoperability.

---

## Summary

The proposed `pdum.plumbum.jq` module delivers jq-inspired ergonomics without
compromising plumbum's composable design philosophy. By layering a lightweight
path DSL and JSON-aware helpers atop existing iter/async operators, we achieve:

- Familiar dot/wildcard field access.
- Powerful filtering, projection, and aggregation primitives.
- Reusable pipelines that combine seamlessly with current plumbum operators.

The staged implementation plan emphasizes robust path handling first, followed
by incremental operator development, documentation, and comprehensive tests.
