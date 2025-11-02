from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple, TypeAlias

JsonScalar: TypeAlias = str | int | float | bool | None
JsonArray: TypeAlias = list["JsonValue"] | tuple["JsonValue", ...]
JsonObject: TypeAlias = dict[str, "JsonValue"]
JsonValue: TypeAlias = JsonScalar | JsonArray | JsonObject
PathElement: TypeAlias = str | int
ResolvedPath: TypeAlias = Tuple[PathElement, ...]


@dataclass(frozen=True, slots=True)
class Field:
    name: str


@dataclass(frozen=True, slots=True)
class Index:
    index: int


@dataclass(frozen=True, slots=True)
class FieldWildcard:
    pass


@dataclass(frozen=True, slots=True)
class IndexWildcard:
    pass


PathToken: TypeAlias = Field | Index | FieldWildcard | IndexWildcard


def ensure_resolved_path(path: Iterable[PathElement]) -> ResolvedPath:
    return tuple(path)


__all__ = [
    "Field",
    "FieldWildcard",
    "Index",
    "IndexWildcard",
    "JsonScalar",
    "JsonValue",
    "JsonArray",
    "JsonObject",
    "PathElement",
    "PathToken",
    "ResolvedPath",
    "ensure_resolved_path",
]
