from __future__ import annotations

import pytest

from pdum.plumbum import apb, pb
from pdum.plumbum.core import PbPair


@pb
def add_one(value: int) -> int:
    return value + 1


@pb
def multiply(value: int, factor: int) -> int:
    return value * factor


@pb
def apply(value: int, func) -> int:
    return func(value)


def test_pbfunc_normalizes_pb_argument() -> None:
    assert (3 > apply(add_one)) == 4


def test_pipeline_to_function() -> None:
    pipeline = add_one | multiply(2)
    as_function = pipeline.to_function()
    assert as_function(5) == 12


@pytest.mark.asyncio
async def test_asyncpbfunc_normalizes_async_argument() -> None:
    @apb
    async def apply_async(value: int, func) -> int:
        return await func(value)

    op = apply_async(add_one)
    assert await (2 > op) == 3


@pytest.mark.asyncio
async def test_asyncpbfunc_accepts_asyncpb_argument() -> None:
    @apb
    async def async_apply(value: int, func) -> int:
        return await func(value)

    @apb
    async def async_double(value: int) -> int:
        return value * 2

    op = async_apply(async_double)
    assert await (3 > op) == 6


def test_pb_ror_creates_pair() -> None:
    pair = add_one.__ror__(multiply(2))
    assert isinstance(pair, PbPair)
    assert (3 > pair) == 7


def test_pbpair_repr_includes_components() -> None:
    pair = add_one | multiply(2)
    representation = repr(pair)
    assert "add_one" in representation
    assert "multiply" in representation


def test_pbfunc_repr_includes_function_name() -> None:
    representation = repr(add_one)
    assert "add_one" in representation


def test_greater_operator_threads_like_rshift() -> None:
    assert (5 > add_one) == 6


def test_chained_greater_with_operator_raises_helpful_error() -> None:
    with pytest.raises(TypeError) as excinfo:
        5 > add_one > multiply(2)
    message = str(excinfo.value)
    assert "parentheses" in message
    assert "another plumbum operator" in message


def test_chained_greater_with_callable_raises_helpful_error() -> None:
    def collector(value: int) -> int:
        return value

    with pytest.raises(TypeError) as excinfo:
        5 > add_one > collector
    message = str(excinfo.value)
    assert "parentheses" in message
    assert "object of type function" in message
