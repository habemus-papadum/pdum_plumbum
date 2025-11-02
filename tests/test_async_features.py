from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable

import pytest

from pdum.plumbum import AsyncPbPair, apb, ensure_async_pb, pb
from pdum.plumbum.async_pipeline import _wrap_sync_callable


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


def test_ensure_async_pb_rejects_invalid_type() -> None:
    with pytest.raises(TypeError):
        ensure_async_pb(42)


@pytest.mark.asyncio
async def test_sync_operator_is_adapted_to_async() -> None:
    @pb
    def add_one(value: int) -> int:
        return value + 1

    async_op = ensure_async_pb(add_one)
    result = await (5 >> async_op)
    assert result == 6


@pytest.mark.asyncio
async def test_wrap_sync_callable_preserves_behavior() -> None:
    def double(value: int, factor: int) -> int:
        return value * factor

    wrapped = _wrap_sync_callable(double)
    assert await wrapped(3, 2) == 6


def test_apb_returns_asyncpb_when_given_asyncpb() -> None:
    assert apb(async_double) is async_double


@pytest.mark.asyncio
async def test_asyncpb_ror_creates_pair() -> None:
    pair = async_double.__ror__(add_one)
    assert isinstance(pair, AsyncPbPair)
    result = await (2 >> pair)
    assert result == 6


@pytest.mark.asyncio
async def test_sync_to_async_adapter_handles_coroutines() -> None:
    @pb
    def call_async(value: int) -> Awaitable[int]:
        async def inner() -> int:
            return value + 5

        return inner()

    adapter = ensure_async_pb(call_async)
    assert await (3 >> adapter) == 8


@pytest.mark.asyncio
async def test_ensure_async_pb_accepts_plain_callable() -> None:
    async def plain(value: int) -> int:
        return value * value

    op = ensure_async_pb(plain)
    assert await (4 >> op) == 16
