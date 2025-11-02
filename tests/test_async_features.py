from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable

import pytest

from pdum.plumbum import AsyncPbPair, aipb, apb, ensure_async_iter_pb, pb


@pb
def add_one(value: int) -> int:
    return value + 1


@pb
def square(value: int) -> int:
    return value * value


@apb
async def async_double(value: int) -> int:
    await asyncio.sleep(0)
    return value * 2


def test_pb_to_function():
    fn = add_one.to_function()
    assert fn(5) == 6


@pytest.mark.asyncio
async def test_async_pipeline_composition():
    pipeline = async_double | async_double
    result = await (3 >> pipeline)
    assert result == 12


@pytest.mark.asyncio
async def test_async_pipeline_mixing_pb():
    pipeline = async_double | add_one | async_double
    result = await (2 >> pipeline)
    assert result == 10


@pytest.mark.asyncio
async def test_async_pair_repr():
    pair = AsyncPbPair(async_double, async_double)
    assert "async" in repr(pair)
    result = await (5 >> pair)
    assert result == 20


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "pipeline, expected",
    [
        (async_double | async_double, 12),
        (add_one | square, 16),
    ],
)
async def test_asyncpbfunc_normalizes_arguments(pipeline: Any, expected: int) -> None:
    @apb
    async def apply(value: int, func: Callable[[int], Awaitable[int]]) -> int:
        return await func(value)

    op = apply(pipeline)
    result = await (3 >> op)
    assert result == expected


async def async_source(limit: int = 5):
    for value in range(limit):
        await asyncio.sleep(0)
        yield value


@pytest.mark.asyncio
async def test_aipb_accepts_async_generator_function():
    async def passthrough(stream):
        async for item in stream:
            yield item

    op = aipb(passthrough)
    iterator = await (async_source(2) >> op)
    assert [value async for value in iterator] == [0, 1]


@pytest.mark.asyncio
async def test_aipb_accepts_coroutine_returning_async_iterator():
    async def passthrough(stream):
        async def inner():
            async for item in stream:
                yield item

        return inner()

    op = aipb(passthrough)
    iterator = await (async_source(1) >> op)
    assert [value async for value in iterator] == [0]


@pytest.mark.asyncio
async def test_aipb_rejects_sync_iterable_results():
    def bad(stream):
        return [1, 2]

    op = aipb(bad)
    with pytest.raises(TypeError):
        iterator = await (async_source(1) >> op)
        await anext(iterator)


def test_ensure_async_iter_pb_errors_on_invalid():
    with pytest.raises(TypeError):
        ensure_async_iter_pb(42)


def test_aipb_idempotent():
    async def passthrough(stream):
        async for item in stream:
            yield item

    op = aipb(passthrough)
    assert aipb(op) is op
