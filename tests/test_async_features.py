from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable

import pytest

from pdum.plumbum import AsyncPbPair, apb, pb


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
