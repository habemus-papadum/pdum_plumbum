from __future__ import annotations

import pytest

from pdum.plumbum.jq import acount_by, aexplode, agroup_by, astats, asum_by, aunwind


async def collect(iterator):
    return [item async for item in iterator]


@pytest.mark.asyncio
async def test_aexplode_expands_matches() -> None:
    async def source():
        yield {"items": [1, 2]}
        yield {"items": [3]}

    pipeline = await (source() > aexplode("items"))
    assert await collect(pipeline) == [1, 2, 3]


@pytest.mark.asyncio
async def test_aunwind_preserves_empty_when_requested() -> None:
    async def source():
        yield {"items": []}

    pipeline = await (source() > aunwind("items", keep_empty=True))
    assert await collect(pipeline) == [{"items": []}]


@pytest.mark.asyncio
async def test_agroup_by_and_acount_by() -> None:
    async def source():
        yield {"type": "a"}
        yield {"type": "b"}
        yield {"type": "a"}

    grouped = await (source() > agroup_by("type"))
    assert [(key, [item["type"] for item in group]) for key, group in grouped] == [("a", ["a", "a"]), ("b", ["b"])]

    counts = await (source() > acount_by("type"))
    assert counts == {"a": 2, "b": 1}


@pytest.mark.asyncio
async def test_asum_by_and_astats() -> None:
    async def source():
        yield {"category": "a", "amount": 2}
        yield {"category": "a", "amount": 3}
        yield {"category": "b", "amount": 5}

    totals = await (source() > asum_by("category", "amount"))
    assert totals == {"a": 5.0, "b": 5.0}

    summary = await (source() > astats("amount"))
    assert summary["count"] == pytest.approx(3.0)
    assert summary["sum"] == pytest.approx(10.0)
