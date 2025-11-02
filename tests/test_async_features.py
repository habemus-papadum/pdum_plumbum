from __future__ import annotations

import asyncio

import pytest

from pdum.plumbum import AsyncPbPair, aipb, apb, ensure_async_iter_pb, ensure_async_pb, pb
from pdum.plumbum.aiterops import filter as aiter_filter
from pdum.plumbum.aiterops import map as aiter_map
from pdum.plumbum.iterops import filter as iter_filter
from pdum.plumbum.iterops import map as iter_map


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


def test_pb_call_threads_value():
    assert add_one(5) == 6


def test_pb_partial_helper():
    @pb
    def add_two_numbers(x, amount):
        return x + amount

    op = add_two_numbers.partial(4)
    assert 6 >> op == 10


def test_iterops_map_filter_with_pb():
    pipeline = iter_map(add_one) | iter_filter(lambda x: x % 2 == 0)
    result = list([1, 2, 3, 4] >> pipeline)
    assert result == [2, 4]


def test_iterops_map_filter_with_plain_callable():
    pipeline = iter_map(lambda x: x * 10) | iter_filter(lambda x: x > 15)
    result = list([1, 2, 3] >> pipeline)
    assert result == [20, 30]


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
async def test_ensure_async_pb_with_callable():
    op = ensure_async_pb(lambda x: x + 3)
    result = await (7 >> op)
    assert result == 10


async def async_source(limit: int = 5):
    for value in range(limit):
        await asyncio.sleep(0)
        yield value


@pytest.mark.asyncio
async def test_aiterops_map_filter_with_async_function():
    pipeline = aiter_map(async_double) | aiter_filter(lambda x: x % 3 == 0)
    iterator = await (async_source(6) >> pipeline)
    values = [value async for value in iterator]
    assert values == [0, 6]


@pytest.mark.asyncio
async def test_aiterops_map_filter_with_pb():
    pipeline = aiter_map(add_one) | aiter_filter(lambda x: x > 2)
    iterator = await (async_source(4) >> pipeline)
    values = [value async for value in iterator]
    assert values == [3, 4]


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
