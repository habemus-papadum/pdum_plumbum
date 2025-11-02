from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterable

import pytest

from pdum.plumbum import apb, pb
from pdum.plumbum.aiterops import AsyncMapper, AsyncPredicate, aiter, aselect, awhere


async def collect(iterator: AsyncIterator[int]) -> list[int]:
    return [item async for item in iterator]


async def async_source(values: Iterable[int]) -> AsyncIterator[int]:
    for value in values:
        await asyncio.sleep(0)
        yield value


@pytest.mark.asyncio
async def test_aiter_converts_sync_iterable() -> None:
    result_iterator = await ([1, 2, 3] >> aiter)
    assert await collect(result_iterator) == [1, 2, 3]


@pytest.mark.asyncio
async def test_aselect_with_sync_mapper_on_list() -> None:
    pipeline = aiter | aselect(lambda value: value * 2)
    result = await collect(await ([1, 2, 3] >> pipeline))
    assert result == [2, 4, 6]


@pytest.mark.asyncio
async def test_aselect_with_async_mapper_on_iterator() -> None:
    async def async_double(value: int) -> int:
        await asyncio.sleep(0)
        return value * 2

    iterator = iter([1, 2, 3])
    pipeline = aiter | aselect(async_double)
    assert await collect(await (iterator >> pipeline)) == [2, 4, 6]


@pytest.mark.asyncio
async def test_awhere_with_sync_predicate_on_async_iterable() -> None:
    pipeline = awhere(lambda value: value % 2 == 0)
    result_iterator = await (async_source(range(5)) >> pipeline)
    assert await collect(result_iterator) == [0, 2, 4]


@pytest.mark.asyncio
async def test_awhere_with_async_predicate_on_list() -> None:
    async def is_even(value: int) -> bool:
        await asyncio.sleep(0)
        return value % 2 == 0

    pipeline = aiter | awhere(is_even)
    result = await collect(await ([1, 2, 3, 4] >> pipeline))
    assert result == [2, 4]


@pb
def add_one(value: int) -> int:
    return value + 1


@pb
def is_positive(value: int) -> bool:
    return value > 0


@apb
async def async_add_one(value: int) -> int:
    await asyncio.sleep(0)
    return value + 1


@apb
async def async_is_even(value: int) -> bool:
    await asyncio.sleep(0)
    return value % 2 == 0


@pytest.mark.asyncio
async def test_aselect_accepts_pb_pipeline() -> None:
    mapper_pipeline: AsyncMapper[int, int] = add_one | add_one
    pipeline = aiter | aselect(mapper_pipeline)
    result = await collect(await ([1, 2] >> pipeline))
    assert result == [3, 4]


@pytest.mark.asyncio
async def test_aselect_accepts_apb_pipeline() -> None:
    mapper_pipeline: AsyncMapper[int, int] = async_add_one | async_add_one
    pipeline = aiter | aselect(mapper_pipeline)
    result = await collect(await ([0, 5] >> pipeline))
    assert result == [2, 7]


@pytest.mark.asyncio
async def test_awhere_accepts_pb_pipeline() -> None:
    predicate_pipeline: AsyncPredicate[int] = is_positive
    pipeline = aiter | awhere(predicate_pipeline)
    result = await collect(await ([-2, -1, 0, 1] >> pipeline))
    assert result == [1]


@pytest.mark.asyncio
async def test_awhere_accepts_apb_pipeline() -> None:
    predicate_pipeline: AsyncPredicate[int] = async_is_even
    pipeline = aiter | awhere(predicate_pipeline)
    result = await collect(await (range(5) >> pipeline))
    assert result == [0, 2, 4]


@pytest.mark.asyncio
async def test_combined_aselect_and_awhere_pipeline() -> None:
    pipeline = aiter | aselect(lambda value: value + 1) | awhere(lambda value: value % 2 == 0) | aselect(async_add_one)
    result_iterator = await ([1, 2, 3, 4] >> pipeline)
    assert await collect(result_iterator) == [3, 5]
