from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from typing import Callable, Iterator, Tuple, TypeVar

from .typing import (
    Field,
    FieldWildcard,
    Index,
    IndexWildcard,
    JsonValue,
    PathElement,
    PathToken,
    ResolvedPath,
    ensure_resolved_path,
)

_DELETE = object()
_TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_PathFunc = Callable[[JsonValue], JsonValue]

T = TypeVar("T")


class PathSyntaxError(ValueError):
    """Raised when a path expression cannot be parsed."""


def parse_path(expression: str) -> Tuple[PathToken, ...]:
    """
    Parse a dotted path expression into path tokens.

    Supported syntax:
    - ``foo.bar``: field access
    - ``items[0]``: numeric index
    - ``items[]`` or ``[]``: index wildcard
    - ``*``: field wildcard
    - Optional leading ``.`` is ignored
    """

    if not expression:
        return ()
    expr = expression.strip()
    if not expr:
        return ()
    if expr.startswith("."):
        expr = expr[1:]

    tokens: list[PathToken] = []
    index = 0
    length = len(expr)

    while index < length:
        char = expr[index]
        if char == ".":
            index += 1
            continue
        if char == "*":
            tokens.append(FieldWildcard())
            index += 1
            continue
        if char == "[":
            index, bracket_token = _parse_bracket(expr, index + 1)
            tokens.append(bracket_token)
            continue

        match = _TOKEN_PATTERN.match(expr, index)
        if match:
            name = match.group(0)
            tokens.append(Field(name))
            index = match.end()
            if index < length and expr[index] == "[":
                continue
            if index < length and expr[index] not in (".", "["):
                raise PathSyntaxError(f"Unexpected character at position {index}: {expr[index]!r}")
            continue

        raise PathSyntaxError(f"Unexpected character at position {index}: {expr[index]!r}")

    return tuple(tokens)


def _parse_bracket(expr: str, start_index: int) -> tuple[int, PathToken]:
    end = expr.find("]", start_index)
    if end == -1:
        raise PathSyntaxError("Unmatched '[' in path expression")

    content = expr[start_index:end].strip()
    if not content:
        return end + 1, IndexWildcard()
    if content == "*":
        return end + 1, IndexWildcard()

    try:
        value = int(content, 10)
    except ValueError as exc:
        raise PathSyntaxError(f"Invalid array index: {content!r}") from exc
    return end + 1, Index(value)


def normalize_path(path: str | Iterable[PathToken]) -> Tuple[PathToken, ...]:
    if isinstance(path, str):
        tokens = parse_path(path)
    else:
        tokens = tuple(path)
    for token in tokens:
        if not isinstance(token, (Field, Index, FieldWildcard, IndexWildcard)):
            raise TypeError(f"Invalid path token: {token!r}")
    return tokens


def iter_paths(value: JsonValue, path: str | Iterable[PathToken]) -> Iterator[tuple[ResolvedPath, JsonValue]]:
    tokens = normalize_path(path)
    yield from _iter_paths(value, tokens, ())


def _iter_paths(value: JsonValue, tokens: Tuple[PathToken, ...], prefix: Tuple[PathElement, ...]):
    if not tokens:
        yield ensure_resolved_path(prefix), value
        return

    head, tail = tokens[0], tokens[1:]

    if isinstance(head, Field):
        if isinstance(value, Mapping) and head.name in value:
            child = value[head.name]
            yield from _iter_paths(child, tail, prefix + (head.name,))
        return

    if isinstance(head, FieldWildcard):
        if isinstance(value, Mapping):
            for key, child in value.items():
                yield from _iter_paths(child, tail, prefix + (key,))
        return

    if isinstance(head, Index):
        if _is_sequence(value):
            sequence = value
            idx = head.index
            idx = idx if idx >= 0 else idx + len(sequence)
            if 0 <= idx < len(sequence):
                child = sequence[idx]
                yield from _iter_paths(child, tail, prefix + (idx,))
        return

    if isinstance(head, IndexWildcard):
        if _is_sequence(value):
            for idx, child in enumerate(value):
                yield from _iter_paths(child, tail, prefix + (idx,))
        return


def resolve_path(value: JsonValue, path: str | Iterable[PathToken]) -> Iterator[JsonValue]:
    for _, match in iter_paths(value, path):
        yield match


def get_path(value: JsonValue, path: str | Iterable[PathToken], default: T | None = None) -> JsonValue | T | None:
    for _, match in iter_paths(value, path):
        return match
    return default


def apply_path(value: JsonValue, path: str | Iterable[PathToken], func: Callable[[JsonValue], JsonValue]) -> JsonValue:
    tokens = normalize_path(path)
    return _apply_tokens(value, tokens, func)


def set_path(value: JsonValue, path: str | Iterable[PathToken], new_value: JsonValue) -> JsonValue:
    return apply_path(value, path, lambda _: new_value)


def transform_path(
    value: JsonValue,
    path: str | Iterable[PathToken],
    func: Callable[[JsonValue], JsonValue],
) -> JsonValue:
    return apply_path(value, path, func)


def delete_path(value: JsonValue, path: str | Iterable[PathToken]) -> JsonValue:
    tokens = normalize_path(path)
    result = _delete_tokens(value, tokens)
    if result is _DELETE:
        raise ValueError("Deleting the root value is not supported")
    return result


def walk_tree(value: JsonValue) -> Iterator[tuple[ResolvedPath, JsonValue]]:
    yield from _walk(value, ())


def _walk(value: JsonValue, prefix: Tuple[PathElement, ...]) -> Iterator[tuple[ResolvedPath, JsonValue]]:
    yield ensure_resolved_path(prefix), value
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield from _walk(child, prefix + (key,))
    elif _is_sequence(value):
        for idx, child in enumerate(value):
            yield from _walk(child, prefix + (idx,))


def _apply_tokens(current: JsonValue, tokens: Tuple[PathToken, ...], func: _PathFunc) -> JsonValue:
    if not tokens:
        return func(current)

    head, tail = tokens[0], tokens[1:]

    if isinstance(head, Field):
        if not isinstance(current, Mapping) or head.name not in current:
            return current
        child = current[head.name]
        new_child = _apply_tokens(child, tail, func)
        if new_child is child:
            return current
        copy = dict(current)
        copy[head.name] = new_child
        return copy

    if isinstance(head, FieldWildcard):
        if not isinstance(current, Mapping):
            return current
        changed = False
        copy: dict[str, JsonValue] = dict(current)
        for key, child in current.items():
            new_child = _apply_tokens(child, tail, func)
            if new_child is not child:
                changed = True
                copy[key] = new_child
        return current if not changed else copy

    if isinstance(head, Index):
        sequence = _as_sequence(current)
        if sequence is None:
            return current
        idx = head.index
        idx = idx if idx >= 0 else idx + len(sequence)
        if idx < 0 or idx >= len(sequence):
            return current
        child = sequence[idx]
        new_child = _apply_tokens(child, tail, func)
        if new_child is child:
            return current
        items = list(sequence)
        items[idx] = new_child
        return _rebuild_sequence(current, items)

    if isinstance(head, IndexWildcard):
        sequence = _as_sequence(current)
        if sequence is None:
            return current
        changed = False
        items = list(sequence)
        for idx, child in enumerate(sequence):
            new_child = _apply_tokens(child, tail, func)
            if new_child is not child:
                changed = True
                items[idx] = new_child
        return current if not changed else _rebuild_sequence(current, items)

    return current


def _delete_tokens(current: JsonValue, tokens: Tuple[PathToken, ...]):
    if not tokens:
        return _DELETE

    head, tail = tokens[0], tokens[1:]

    if isinstance(head, Field):
        if not isinstance(current, Mapping) or head.name not in current:
            return current
        child = current[head.name]
        new_child = _delete_tokens(child, tail)
        if new_child is child:
            return current
        copy = dict(current)
        if new_child is _DELETE:
            copy.pop(head.name, None)
        else:
            copy[head.name] = new_child
        return copy

    if isinstance(head, FieldWildcard):
        if not isinstance(current, Mapping):
            return current
        changed = False
        copy = dict(current)
        for key, child in list(current.items()):
            new_child = _delete_tokens(child, tail)
            if new_child is _DELETE:
                copy.pop(key, None)
                changed = True
            elif new_child is not child:
                copy[key] = new_child
                changed = True
        return current if not changed else copy

    if isinstance(head, Index):
        sequence = _as_sequence(current)
        if sequence is None:
            return current
        idx = head.index
        idx = idx if idx >= 0 else idx + len(sequence)
        if idx < 0 or idx >= len(sequence):
            return current
        child = sequence[idx]
        new_child = _delete_tokens(child, tail)
        if new_child is child:
            return current
        items = list(sequence)
        if new_child is _DELETE:
            del items[idx]
        else:
            items[idx] = new_child
        return _rebuild_sequence(current, items)

    if isinstance(head, IndexWildcard):
        sequence = _as_sequence(current)
        if sequence is None:
            return current
        changed = False
        items = list(sequence)
        new_items: list[JsonValue] = []
        for idx, child in enumerate(sequence):
            new_child = _delete_tokens(child, tail)
            if new_child is _DELETE:
                changed = True
                continue
            if new_child is not child:
                changed = True
                new_items.append(new_child)
            else:
                new_items.append(child)
        if not changed:
            return current
        return _rebuild_sequence(current, new_items)

    return current


def _is_sequence(value: JsonValue) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _as_sequence(value: JsonValue) -> Sequence[JsonValue] | None:
    if _is_sequence(value):
        return value  # type: ignore[return-value]
    return None


def _rebuild_sequence(original: JsonValue, items: list[JsonValue]) -> JsonValue:
    if isinstance(original, list):
        return items
    if isinstance(original, tuple):
        return tuple(items)
    try:
        return original.__class__(items)
    except Exception:
        return items


__all__ = [
    "PathSyntaxError",
    "apply_path",
    "delete_path",
    "get_path",
    "iter_paths",
    "parse_path",
    "resolve_path",
    "set_path",
    "transform_path",
    "walk_tree",
]
