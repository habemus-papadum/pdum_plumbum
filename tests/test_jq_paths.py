from __future__ import annotations

from pdum.plumbum.jq.paths import (
    PathSyntaxError,
    apply_path,
    delete_path,
    iter_paths,
    parse_path,
    resolve_path,
    walk_tree,
)
from pdum.plumbum.jq.typing import Field, FieldWildcard, Index, IndexWildcard, ResolvedPath


def test_parse_path_supports_fields_and_indices() -> None:
    tokens = parse_path("user.addresses[0].city")
    assert tokens == (Field("user"), Field("addresses"), Index(0), Field("city"))


def test_parse_path_supports_wildcards() -> None:
    tokens = parse_path("items[].*")
    assert tokens == (Field("items"), IndexWildcard(), FieldWildcard())


def test_parse_path_rejects_invalid_input() -> None:
    try:
        parse_path("foo[bar]")
    except PathSyntaxError as exc:
        assert "Invalid array index" in str(exc)
    else:
        raise AssertionError("Expected PathSyntaxError")


def test_resolve_path_yields_matches() -> None:
    data = {"users": [{"id": 1}, {"id": 2}]}
    assert list(resolve_path(data, "users[].id")) == [1, 2]


def test_iter_paths_returns_resolved_paths() -> None:
    data = {"user": {"addresses": [{"city": "Berlin"}, {"city": "Lisbon"}]}}
    paths = list(iter_paths(data, "user.addresses[].city"))
    resolved_paths = [path for path, _ in paths]
    assert resolved_paths == [
        ("user", "addresses", 0, "city"),
        ("user", "addresses", 1, "city"),
    ]


def test_apply_path_updates_nested_value() -> None:
    data = {"user": {"name": "Ada", "stats": {"score": 1}}}
    updated = apply_path(data, "user.stats.score", lambda value: value + 1)
    assert updated["user"]["stats"]["score"] == 2
    assert data["user"]["stats"]["score"] == 1  # original untouched


def test_apply_path_handles_wildcards() -> None:
    data = {"values": [1, 2, 3]}
    updated = apply_path(data, "values[]", lambda value: value * 2)
    assert updated["values"] == [2, 4, 6]


def test_delete_path_removes_keys_and_indices() -> None:
    data = {"items": [{"id": 1}, {"id": 2}], "meta": {"count": 2}}
    removed = delete_path(data, "items[0]")
    assert removed["items"] == [{"id": 2}]


def test_walk_tree_visits_all_nodes() -> None:
    data = {"a": [1, {"b": 2}]}
    visited: list[ResolvedPath] = []
    for path, _ in walk_tree(data):
        visited.append(path)
    assert visited == [
        (),
        ("a",),
        ("a", 0),
        ("a", 1),
        ("a", 1, "b"),
    ]
