from __future__ import annotations

import inspect
import math
import re
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from statistics import mean
from typing import Any, Callable, Iterator

from ..core import Pb, pb
from ..iterops import groupby as iter_groupby
from .paths import apply_path, delete_path, iter_paths, resolve_path, walk_tree
from .typing import JsonValue, PathToken, ResolvedPath

_DEFAULT = object()


def _ensure_callable(candidate: Any) -> Callable[[Any], Any]:
    if isinstance(candidate, Pb):
        return candidate.to_function()
    if callable(candidate):
        return candidate
    raise TypeError(f"Expected callable or pipeline, got {candidate!r}")


def _is_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _first_match(value: JsonValue, path: str | Iterable[PathToken]) -> Any:
    matches = list(resolve_path(value, path))
    return matches[0] if matches else None


def _prepare_path_callable(candidate: Any) -> Callable[[ResolvedPath, Any], Any]:
    func = _ensure_callable(candidate)
    signature = inspect.signature(func)
    if len(signature.parameters) >= 2:
        return lambda path, value: func(path, value)
    return lambda path, value: func((path, value))


@pb
def field(
    value: JsonValue,
    expr: str,
    *,
    default: Any = None,
    multi: bool = False,
    raise_on_missing: bool = False,
) -> Any:
    matches = list(resolve_path(value, expr))
    if not matches:
        if raise_on_missing and not multi:
            raise KeyError(expr)
        return [] if multi else default
    return matches if multi else matches[0]


@pb
def pluck(value: JsonValue, *exprs: str, as_dict: bool = False, **named_exprs: str) -> Any:
    if as_dict or named_exprs:
        result: dict[str, Any] = {}
        for expr in exprs:
            result[expr] = _first_match(value, expr)
        for alias, expr in named_exprs.items():
            result[alias] = _first_match(value, expr)
        return result

    return tuple(_first_match(value, expr) for expr in exprs)


@pb
def pick(value: JsonValue, *keys: str, default: Any = _DEFAULT, **aliases: str) -> JsonValue:
    if not isinstance(value, Mapping):
        return {}
    result: dict[str, Any] = {}
    for key in keys:
        if key in value:
            result[key] = value[key]
        elif default is not _DEFAULT:
            result[key] = default
    for alias, expr in aliases.items():
        match = _first_match(value, expr)
        if match is None and default is not _DEFAULT:
            result[alias] = default
        else:
            result[alias] = match
    return result


@pb
def keys(value: JsonValue, expr: str | None = None) -> list[Any]:
    if expr is None:
        if isinstance(value, Mapping):
            return list(value.keys())
        return []

    result: list[Any] = []
    seen: set[Any] = set()
    for _, match in iter_paths(value, expr):
        if isinstance(match, Mapping):
            for key in match.keys():
                if key not in seen:
                    seen.add(key)
                    result.append(key)
    return result


@pb
def values(value: JsonValue, expr: str | None = None) -> list[Any]:
    if expr is None:
        if isinstance(value, Mapping):
            return list(value.values())
        if _is_sequence(value):
            return list(value)
        return [value]

    results: list[Any] = []
    for match in resolve_path(value, expr):
        if isinstance(match, Mapping):
            results.extend(match.values())
        elif _is_sequence(match):
            results.extend(match)
        else:
            results.append(match)
    return results


@pb
def where_exists(value: JsonValue, expr: str) -> bool:
    return any(True for _ in resolve_path(value, expr))


@pb
def where_equals(value: JsonValue, expr: str, expected: Any) -> bool:
    for match in resolve_path(value, expr):
        if match == expected:
            return True
    return False


@pb
def contains(value: JsonValue, expr: str, needle: Any) -> bool:
    for match in resolve_path(value, expr):
        if isinstance(match, Mapping):
            if needle in match.values() or needle in match.keys():
                return True
        elif isinstance(match, Sequence) and not isinstance(match, (str, bytes, bytearray)):
            if needle in match:
                return True
        elif isinstance(match, str):
            if str(needle) in match:
                return True
        elif match == needle:
            return True
    return False


@pb
def match(value: JsonValue, expr: str, pattern: str | re.Pattern[str]) -> bool:
    regex = re.compile(pattern) if isinstance(pattern, str) else pattern
    for match_value in resolve_path(value, expr):
        if isinstance(match_value, str) and regex.search(match_value):
            return True
    return False


@pb
def where_type(value: JsonValue, expr: str, expected_type: type | tuple[type, ...]) -> bool:
    for match_value in resolve_path(value, expr):
        if isinstance(match_value, expected_type):
            return True
    return False


@pb
def project(
    value: JsonValue,
    expr: str,
    pipeline: Callable[[Any], Any] | Pb,
) -> list[Any]:
    func = _ensure_callable(pipeline)
    return [func(match) for match in resolve_path(value, expr)]


@pb
def set_value(
    value: JsonValue,
    expr: str,
    replacement: Any | Callable[[Any], Any] | Pb,
) -> JsonValue:
    if isinstance(replacement, Pb) or callable(replacement):
        func = _ensure_callable(replacement)
    else:

        def func(_old: Any) -> Any:
            return replacement

    return apply_path(value, expr, func)


@pb
def transform(
    value: JsonValue,
    expr: str,
    pipeline: Callable[[Any], Any] | Pb,
) -> JsonValue:
    func = _ensure_callable(pipeline)
    return apply_path(value, expr, func)


@pb
def remove(value: JsonValue, expr: str) -> JsonValue:
    return delete_path(value, expr)


@pb
def walk(
    value: JsonValue,
    expr: str,
    pipeline: Callable[[ResolvedPath, Any], Any] | Pb,
) -> list[Any]:
    func = _prepare_path_callable(pipeline)
    return [func(path, match) for path, match in iter_paths(value, expr)]


@pb
def coalesce(
    value: JsonValue,
    *exprs: str,
    default: Any | None = None,
) -> Any:
    for expr in exprs:
        for match in resolve_path(value, expr):
            if match is not None:
                return match
    return default


@pb
def group_by(iterable: Iterable[JsonValue], expr: str) -> list[tuple[Any, list[JsonValue]]]:
    def key_func(item: JsonValue) -> Any:
        return _first_match(item, expr)

    groups = []
    for key, group in iterable > iter_groupby(key_func):
        groups.append((key, list(group)))
    return groups


@pb
def count_by(iterable: Iterable[JsonValue], expr: str) -> dict[Any, int]:
    counts: dict[Any, int] = defaultdict(int)
    for key, group in iterable > iter_groupby(lambda item: _first_match(item, expr)):
        counts[key] = sum(1 for _ in group)
    return dict(counts)


@pb
def sum_by(
    iterable: Iterable[JsonValue],
    key_expr: str,
    value_expr: str,
    *,
    default: float = 0.0,
) -> dict[Any, float]:
    totals: dict[Any, float] = defaultdict(float)

    for key, group in iterable > iter_groupby(lambda item: _first_match(item, key_expr)):
        total = 0.0
        for item in group:
            value = _first_match(item, value_expr)
            if isinstance(value, (int, float)):
                total += float(value)
        totals[key] = total if total else default
    return dict(totals)


@pb
def stats(
    iterable: Iterable[JsonValue],
    expr: str,
) -> dict[str, float]:
    values: list[float] = []
    for item in iterable:
        value = _first_match(item, expr)
        if isinstance(value, (int, float)):
            values.append(float(value))
    if not values:
        return {"count": 0, "sum": 0.0, "mean": math.nan, "min": math.nan, "max": math.nan}
    return {
        "count": float(len(values)),
        "sum": float(sum(values)),
        "mean": float(mean(values)),
        "min": float(min(values)),
        "max": float(max(values)),
    }


@pb
def flatten(value: JsonValue, expr: str | None = None) -> list[Any]:
    if expr is None:
        return [item for _, item in walk_tree(value)]
    results: list[Any] = []
    for _, match in iter_paths(value, expr):
        if isinstance(match, Mapping):
            results.extend(match.values())
        elif _is_sequence(match):
            results.extend(match)
        else:
            results.append(match)
    return results


@pb
def explode(value: JsonValue, expr: str, *, keep_path: bool = False) -> Iterator[Any]:
    for path, match in iter_paths(value, expr):
        if isinstance(match, Sequence) and not isinstance(match, (str, bytes, bytearray)):
            for item in match:
                yield (path, item) if keep_path else item
        else:
            yield (path, match) if keep_path else match


@pb
def zip_fields(value: JsonValue, *exprs: str, strict: bool = False) -> list[tuple[Any, ...]]:
    sequences: list[list[Any]] = []
    for expr in exprs:
        matches = list(resolve_path(value, expr))
        if len(matches) == 1 and _is_sequence(matches[0]):
            sequences.append(list(matches[0]))
        else:
            sequences.append(matches)
    lengths = {len(seq) for seq in sequences}
    if strict and len(lengths) > 1:
        raise ValueError("zip_fields requires equal-length sequences when strict=True")
    if not sequences:
        return []
    return list(zip(*sequences, strict=strict))


@pb
def merge(value: JsonValue, *exprs: str) -> JsonValue:
    result: dict[str, Any] = {}
    if isinstance(value, Mapping):
        result.update(value)
    for expr in exprs:
        for match in resolve_path(value, expr):
            if isinstance(match, Mapping):
                result.update(match)
    return result


@pb
def unwind(value: JsonValue, expr: str, *, keep_empty: bool = False) -> Iterator[JsonValue]:
    any_yielded = False
    for item in value > explode(expr):
        any_yielded = True
        yield item
    if not any_yielded and keep_empty:
        yield value


__all__ = [
    "coalesce",
    "contains",
    "count_by",
    "explode",
    "field",
    "flatten",
    "group_by",
    "keys",
    "match",
    "merge",
    "pick",
    "pluck",
    "project",
    "remove",
    "set_value",
    "stats",
    "sum_by",
    "transform",
    "unwind",
    "values",
    "walk",
    "where_equals",
    "where_exists",
    "where_type",
    "zip_fields",
]
