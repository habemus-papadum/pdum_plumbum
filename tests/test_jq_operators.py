from __future__ import annotations

import pytest

from pdum.plumbum import pb
from pdum.plumbum.iterops import select, where
from pdum.plumbum.jq import (
    coalesce,
    contains,
    count_by,
    explode,
    field,
    flatten,
    group_by,
    keys,
    match,
    merge,
    pick,
    pluck,
    project,
    remove,
    set_value,
    stats,
    sum_by,
    transform,
    unwind,
    values,
    walk,
    where_equals,
    where_exists,
    where_type,
    zip_fields,
)


def sample_data() -> dict[str, object]:
    return {
        "users": [
            {"id": 1, "name": "Ada", "active": True, "scores": [10, 15]},
            {"id": 2, "name": "Linus", "active": False, "scores": [20]},
        ],
        "meta": {"region": "eu", "tags": ["beta"]},
    }


def test_field_returns_first_match_by_default() -> None:
    data = sample_data()
    assert (data > field("meta.region")) == "eu"


def test_field_returns_all_matches_when_multi_flag_set() -> None:
    data = sample_data()
    assert (data > field("users[].id", multi=True)) == [1, 2]


def test_pick_and_pluck_extract_fields() -> None:
    data = sample_data()["users"][0]
    picked = data > pick("id", "name")
    assert picked == {"id": 1, "name": "Ada"}
    plucked = data > pluck("id", "name")
    assert plucked == (1, "Ada")


def test_keys_and_values_extract_nested_data() -> None:
    data = sample_data()
    assert (data > keys("meta")) == ["region", "tags"]
    assert (data > values("meta.tags")) == ["beta"]


def test_where_helpers_integrate_with_iterops() -> None:
    users = sample_data()["users"]
    pipeline = where(where_exists("scores[]")) | select(lambda user: user["id"])
    active_users = users > pipeline
    assert list(active_users) == [1, 2]


def test_where_equals_and_where_type() -> None:
    user = sample_data()["users"][0]
    assert (user > where_equals("name", "Ada")) is True
    assert (user > where_type("scores", list)) is True


def test_contains_and_match_operations() -> None:
    data = sample_data()
    assert (data > contains("meta.tags", "beta")) is True
    assert (data > match("users[].name", r"^A")) is True


def test_project_applies_pipeline_to_matches() -> None:
    data = sample_data()

    @pb
    def uppercase(value: str) -> str:
        return value.upper()

    assert (data > project("users[].name", uppercase)) == ["ADA", "LINUS"]


def test_set_value_and_transform_update_structure() -> None:
    data = sample_data()
    incremented = data > transform("users[].scores[]", lambda score: score + 1)
    assert incremented["users"][0]["scores"] == [11, 16]
    replacement = data > set_value("meta.tags", ["ga"])
    assert replacement["meta"]["tags"] == ["ga"]
    assert data["meta"]["tags"] == ["beta"]


def test_remove_deletes_paths() -> None:
    data = sample_data()
    trimmed = data > remove("meta.tags")
    assert "tags" not in trimmed["meta"]


def test_coalesce_returns_first_non_null_match() -> None:
    data = sample_data()
    assert (data > coalesce("users[].nickname", "meta.region")) == "eu"


def test_walk_collects_path_values() -> None:
    data = sample_data()
    results = data > walk("users[].scores[]", pb(lambda path_value: path_value))
    assert results == [
        (("users", 0, "scores", 0), 10),
        (("users", 0, "scores", 1), 15),
        (("users", 1, "scores", 0), 20),
    ]


def test_group_by_and_count_by_operations() -> None:
    users = sample_data()["users"]
    grouped = users > group_by("active")
    assert [(key, [u["id"] for u in group]) for key, group in grouped] == [(False, [2]), (True, [1])]
    counts = users > count_by("active")
    assert counts == {False: 1, True: 1}


def test_sum_by_and_stats() -> None:
    records = [
        {"category": "a", "value": 4},
        {"category": "a", "value": 6},
        {"category": "b", "value": 2},
    ]
    totals = records > sum_by("category", "value")
    assert totals == {"a": 10.0, "b": 2.0}
    summary = records > stats("value")
    assert summary["count"] == pytest.approx(3.0)
    assert summary["sum"] == pytest.approx(12.0)
    assert summary["mean"] == pytest.approx(4.0)


def test_flatten_and_explode_expand_values() -> None:
    data = sample_data()
    flattened = data > flatten("users[].scores")
    assert flattened == [10, 15, 20]
    exploded = list(data > explode("users[].scores"))
    assert exploded == [10, 15, 20]


def test_unwind_handles_empty_sequences() -> None:
    data = {"item": {"values": []}}
    results = list(data > unwind("item.values", keep_empty=True))
    assert results == [{"item": {"values": []}}]


def test_zip_fields_and_merge_helpers() -> None:
    record = {"scores": [1, 2], "weights": [3, 4]}
    assert (record > zip_fields("scores", "weights")) == [(1, 3), (2, 4)]

    profile = {"base": {"a": 1}, "extra": {"b": 2}}
    merged = profile > merge("base", "extra")
    assert merged["a"] == 1
    assert merged["b"] == 2


def test_transform_returns_new_structure_without_mutating_input() -> None:
    records = [
        {"user": {"id": 1, "name": "Ada"}, "scores": [10, 15]},
        {"user": {"id": 2, "name": "Linus"}, "scores": [20]},
    ]
    curved = records > select(transform("scores[]", lambda score: score * 1.1)) | list

    assert curved == [
        {"user": {"id": 1, "name": "Ada"}, "scores": [11.0, 16.5]},
        {"user": {"id": 2, "name": "Linus"}, "scores": [22.0]},
    ]
    # Original input remains unchanged because transform applies updates immutably.
    assert records == [
        {"user": {"id": 1, "name": "Ada"}, "scores": [10, 15]},
        {"user": {"id": 2, "name": "Linus"}, "scores": [20]},
    ]
