from __future__ import annotations

import asyncio

import pytest

from pdum.plumbum import (
    AsyncPbFunc,
    AsyncPbPair,
    aipb,
    apb,
    ensure_async_iter_pb,
    ensure_async_pb,
    pb,
    to_async_iter,
    wrap_async_scalar_as_iter,
    wrap_sync_as_async,
)


@pb
def add_one(x: int) -> int:
    return x + 1


@pb
def duplicate_values(seq) -> list:
    return list(seq) + list(seq)


@pb
def coroutine_result(x: int):
    async def inner():
        await asyncio.sleep(0)
        return x + 5

    return inner()


@apb
async def async_double(x: int) -> int:
    await asyncio.sleep(0)
    return x * 2


@apb
def add_sync(x: int, delta: int) -> int:
    return x + delta


@apb
async def async_add(x: int, delta: int) -> int:
    await asyncio.sleep(0)
    return x + delta


@aipb
async def async_map(data, factor: int):
    async for item in data:
        yield item * factor


@aipb
async def async_filter_gt(data, threshold: int):
    async for item in data:
        if item > threshold:
            yield item


@aipb
def sync_collect(data):
    return [item * 10 for item in data]


@aipb
async def async_sum(data):
    total = 0
    async for item in data:
        total += item
    return total


@aipb
def return_async_iterable(data):
    class SimpleAsyncIterable:
        def __init__(self, values):
            self._values = values

        def __aiter__(self):
            async def generator():
                for value in self._values:
                    yield value

            return generator()

    return SimpleAsyncIterable(list(data))


class SimpleAsyncOnlyIterable:
    def __init__(self, values):
        self.values = values

    def __aiter__(self):
        async def generator():
            for value in self.values:
                yield value

        return generator()


async def async_source(count: int = 5):
    for value in range(count):
        await asyncio.sleep(0)
        yield value


@pytest.mark.asyncio
async def test_async_pipeline_basic():
    pipeline = async_double | async_add(3)
    result = await (5 >> pipeline)
    assert result == (5 * 2) + 3


@pytest.mark.asyncio
async def test_async_pipeline_with_sync_callable():
    pipeline = async_double | add_sync(5)
    result = await (4 >> pipeline)
    assert result == (4 * 2) + 5


@pytest.mark.asyncio
async def test_async_pipeline_mixing_sync_operator():
    pipeline = async_double | add_one | async_add(2)
    result = await (3 >> pipeline)
    # (3 * 2) -> 6, add_one -> 7, async_add -> 9
    assert result == 9


@pytest.mark.asyncio
async def test_wrap_sync_as_async_adapter():
    async_op = wrap_sync_as_async(add_one)
    result = await (10 >> async_op)
    assert result == 11
    assert "async(" in repr(async_op)

    converted = ensure_async_pb(add_one)
    result_converted = await (7 >> converted)
    assert result_converted == 8

    coroutine_adapter = wrap_sync_as_async(coroutine_result)
    coroutine_value = await (2 >> coroutine_adapter)
    assert coroutine_value == 7

    async_add_one = async_add(1)
    assert wrap_sync_as_async(async_add_one) is async_add_one


@pytest.mark.asyncio
async def test_ensure_async_pb_with_callable():
    op = ensure_async_pb(lambda value: value * 4)
    assert isinstance(op, AsyncPbFunc)
    result = await (6 >> op)
    assert result == 24
    with pytest.raises(TypeError):
        ensure_async_pb(42)


def test_apb_idempotent_and_invalid():
    base = apb(lambda value: value)
    assert apb(base) is base

    async_op = async_add(0)
    assert apb(async_op) is async_op


@pytest.mark.asyncio
async def test_async_pair_repr_and_execution():
    pair = AsyncPbPair(async_double, async_add(1))
    result = await (2 >> pair)
    assert result == 5
    assert "async" in repr(pair)
    assert "async" in repr(async_add(1))


@pytest.mark.asyncio
async def test_async_reverse_pipe_operator():
    pipeline = (lambda value: value + 1) | async_add(0)
    result = await (5 >> pipeline)
    assert result == 6


@pytest.mark.asyncio
async def test_async_iter_pipeline_basic():
    pipeline = async_map(2) | async_filter_gt(3)
    iterator = await (async_source(5) >> pipeline)
    values = [value async for value in iterator]
    assert values == [4, 6, 8]


@pytest.mark.asyncio
async def test_async_iter_pipeline_with_sync_function():
    pipeline = async_map(2) | sync_collect()
    iterator = await (async_source(4) >> pipeline)
    values = [value async for value in iterator]
    assert values == [value * 20 for value in range(4)]


@pytest.mark.asyncio
async def test_async_iter_pipeline_scalar_adapter():
    scalar_iter = wrap_async_scalar_as_iter(async_add(2))
    pipeline = scalar_iter | sync_collect()
    iterator = await (async_source(3) >> pipeline)
    values = [value async for value in iterator]
    assert values == [(value + 2) * 10 for value in range(3)]


@pytest.mark.asyncio
async def test_async_iter_pipeline_with_coroutine_output():
    pipeline = async_map(2) | async_sum()
    iterator = await (async_source(4) >> pipeline)
    result = [value async for value in iterator]
    assert result == [12]


async def _awaitable_source():
    await asyncio.sleep(0)
    return [1, 2, 3]


@pytest.mark.asyncio
async def test_async_iter_pipeline_from_awaitable_source():
    iterator = await (_awaitable_source() >> sync_collect())
    values = [value async for value in iterator]
    assert values == [10, 20, 30]


@pytest.mark.asyncio
async def test_to_async_iter_with_scalar_operator():
    iter_op = to_async_iter(async_add(1))
    pipeline = iter_op | sync_collect()
    iterator = await (async_source(3) >> pipeline)
    values = [value async for value in iterator]
    assert values == [(value + 1) * 10 for value in range(3)]


@pytest.mark.asyncio
async def test_async_iter_pipeline_with_plain_callable():
    iter_op = to_async_iter(lambda data: data)
    iterator = await (async_source(3) >> iter_op)
    values = [value async for value in iterator]
    assert values == list(range(3))


@pytest.mark.asyncio
async def test_ensure_async_iter_pb_with_pb_operator():
    iter_op = ensure_async_iter_pb(duplicate_values)
    iterator = await ([1, 2] >> iter_op)
    values = [value async for value in iterator]
    assert values == [1, 2, 1, 2]


@pytest.mark.asyncio
async def test_async_iter_reverse_pipe_operator():
    pipeline = (lambda data: data) | async_map(1)
    iterator = await (async_source(3) >> pipeline)
    values = [value async for value in iterator]
    assert values == [0, 1, 2]


def test_async_iter_repr_helpers():
    pair = async_map(1) | async_filter_gt(10)
    assert "async-iter" in repr(async_map(1))
    assert "async-iter" in repr(pair)
    assert "iter(" in repr(wrap_async_scalar_as_iter(async_add(1)))
    assert "async-iter" in repr(ensure_async_iter_pb(duplicate_values))


@pytest.mark.asyncio
async def test_async_iter_single_value_source():
    iterator = await (42 >> async_map(2))
    values = [value async for value in iterator]
    assert values == [84]


@pytest.mark.asyncio
async def test_async_iter_asynciter_branch():
    iterable = SimpleAsyncOnlyIterable([1, 2, 3])
    iterator = await (iterable >> async_map(1))
    values = [value async for value in iterator]
    assert values == [1, 2, 3]


@pytest.mark.asyncio
async def test_async_iter_asynciter_result_branch():
    iterator = await (async_source(3) >> return_async_iterable())
    values = [value async for value in iterator]
    assert values == [0, 1, 2]


def test_aipb_idempotent_and_invalid():
    base = aipb(lambda data: data)
    assert aipb(base) is base
    mapped = async_map(1)
    assert aipb(mapped) is mapped
    with pytest.raises(TypeError):
        ensure_async_iter_pb(0.5)


def test_async_exports_available():
    from pdum.plumbum import aipb as exported_aipb
    from pdum.plumbum import apb as exported_apb

    assert exported_apb is not None
    assert exported_aipb is not None
