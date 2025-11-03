from __future__ import annotations

import asyncio
import inspect
from collections import deque
from collections.abc import AsyncIterator, Iterable
from typing import Callable

import pytest

from pdum.plumbum import apb, pb
from pdum.plumbum.aiterops import (
    AsyncMapper,
    AsyncPredicate,
    abatched,
    achain,
    achain_with,
    acollect,
    adedup,
    aenumerate,
    agroupby,
    aislice,
    aiter,
    aizip,
    alist,
    anetcat,
    apermutations,
    areverse,
    aselect,
    askip,
    askip_while,
    asort,
    at,
    atail,
    atake,
    atake_while,
    atee,
    atranspose,
    atraverse,
    auniq,
    awhere,
)
from pdum.plumbum.aiterops_internals import (
    _annotation_requires_async_callable,
    async_iter_operator,
    ensure_async_callable,
    to_async_iterator,
)


async def collect(iterator: AsyncIterator[int]) -> list[int]:
    return [item async for item in iterator]


async def async_source(values: Iterable[int]) -> AsyncIterator[int]:
    for value in values:
        await asyncio.sleep(0)
        yield value


@pytest.mark.asyncio
async def test_aiter_converts_sync_iterable() -> None:
    result_iterator = await ([1, 2, 3] > aiter)
    assert await collect(result_iterator) == [1, 2, 3]


@pytest.mark.asyncio
async def test_aselect_with_sync_mapper_on_list() -> None:
    pipeline = aiter | aselect(lambda value: value * 2)
    result = await collect(await ([1, 2, 3] > pipeline))
    assert result == [2, 4, 6]


@pytest.mark.asyncio
async def test_aselect_with_async_mapper_on_iterator() -> None:
    async def async_double(value: int) -> int:
        await asyncio.sleep(0)
        return value * 2

    iterator = iter([1, 2, 3])
    pipeline = aiter | aselect(async_double)
    assert await collect(await (iterator > pipeline)) == [2, 4, 6]


@pytest.mark.asyncio
async def test_awhere_with_sync_predicate_on_async_iterable() -> None:
    pipeline = awhere(lambda value: value % 2 == 0)
    result_iterator = await (async_source(range(5)) > pipeline)
    assert await collect(result_iterator) == [0, 2, 4]


@pytest.mark.asyncio
async def test_awhere_with_async_predicate_on_list() -> None:
    async def is_even(value: int) -> bool:
        await asyncio.sleep(0)
        return value % 2 == 0

    pipeline = aiter | awhere(is_even)
    result = await collect(await ([1, 2, 3, 4] > pipeline))
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
    result = await collect(await ([1, 2] > pipeline))
    assert result == [3, 4]


@pytest.mark.asyncio
async def test_aselect_accepts_apb_pipeline() -> None:
    mapper_pipeline: AsyncMapper[int, int] = async_add_one | async_add_one
    pipeline = aiter | aselect(mapper_pipeline)
    result = await collect(await ([0, 5] > pipeline))
    assert result == [2, 7]


@pytest.mark.asyncio
async def test_awhere_accepts_pb_pipeline() -> None:
    predicate_pipeline: AsyncPredicate[int] = is_positive
    pipeline = aiter | awhere(predicate_pipeline)
    result = await collect(await ([-2, -1, 0, 1] > pipeline))
    assert result == [1]


@pytest.mark.asyncio
async def test_awhere_accepts_apb_pipeline() -> None:
    predicate_pipeline: AsyncPredicate[int] = async_is_even
    pipeline = aiter | awhere(predicate_pipeline)
    result = await collect(await (range(5) > pipeline))
    assert result == [0, 2, 4]


@pytest.mark.asyncio
async def test_combined_aselect_and_awhere_pipeline() -> None:
    pipeline = aiter | aselect(lambda value: value + 1) | awhere(lambda value: value % 2 == 0) | aselect(async_add_one)
    result_iterator = await ([1, 2, 3, 4] > pipeline)
    assert await collect(result_iterator) == [3, 5]


@pytest.mark.asyncio
async def test_atake_limits_items() -> None:
    pipeline = aiter | atake(2)
    result_iterator = await ([1, 2, 3] > pipeline)
    assert await collect(result_iterator) == [1, 2]


@pytest.mark.asyncio
async def test_atail_collects_last_items() -> None:
    result = await ([1, 2, 3, 4] > (aiter | atail(2)))
    assert isinstance(result, deque)
    assert list(result) == [3, 4]


@pytest.mark.asyncio
async def test_askip_skips_requested_items() -> None:
    pipeline = aiter | askip(2)
    result_iterator = await ([1, 2, 3, 4] > pipeline)
    assert await collect(result_iterator) == [3, 4]


@pytest.mark.asyncio
async def test_atake_while_stops_predicate() -> None:
    pipeline = aiter | atake_while(lambda value: value < 3)
    result_iterator = await ([1, 2, 3, 4] > pipeline)
    assert await collect(result_iterator) == [1, 2]


@pytest.mark.asyncio
async def test_askip_while_drops_prefix() -> None:
    pipeline = aiter | askip_while(lambda value: value < 3)
    result_iterator = await ([1, 2, 3, 4] > pipeline)
    assert await collect(result_iterator) == [3, 4]


@pytest.mark.asyncio
async def test_adedup_removes_duplicates() -> None:
    pipeline = aiter | adedup()
    result_iterator = await ([1, 1, 2, 2, 3] > pipeline)
    assert await collect(result_iterator) == [1, 2, 3]


@pytest.mark.asyncio
async def test_auniq_removes_consecutive_duplicates() -> None:
    pipeline = aiter | auniq()
    result_iterator = await ([1, 1, 2, 1, 1, 3] > pipeline)
    assert await collect(result_iterator) == [1, 2, 1, 3]


@pytest.mark.asyncio
async def test_apermutations_generates_expected_sequences() -> None:
    pipeline = aiter | apermutations()
    result_iterator = await (["a", "b"] > pipeline)
    assert await collect(result_iterator) == [("a", "b"), ("b", "a")]


@pytest.mark.asyncio
async def test_asort_returns_sorted_list() -> None:
    result = await ([3, 1, 2] > (aiter | asort()))
    assert result == [1, 2, 3]


@pytest.mark.asyncio
async def test_areverse_yields_reverse_order() -> None:
    pipeline = aiter | areverse
    result_iterator = await ([1, 2, 3] > pipeline)
    assert await collect(result_iterator) == [3, 2, 1]


@pytest.mark.asyncio
async def test_at_appends_value() -> None:
    result = await ([1, 2] > (aiter | at(3)))
    assert result == [1, 2, 3]


@pytest.mark.asyncio
async def test_atranspose_swaps_rows_and_columns() -> None:
    result = await ([[1, 2], [3, 4]] > (aiter | atranspose))
    assert result == [(1, 3), (2, 4)]


@pytest.mark.asyncio
async def test_alist_collects_items() -> None:
    pipeline = aiter | alist
    result = await ([1, 2, 3] > pipeline)
    assert result == [1, 2, 3]


@pytest.mark.asyncio
async def test_acollect_alias_matches_alist() -> None:
    pipeline = aiter | acollect
    result = await (async_source([4, 5, 6]) > pipeline)
    assert result == [4, 5, 6]


@pytest.mark.asyncio
async def test_abatched_emits_batches() -> None:
    pipeline = aiter | abatched(2)
    result_iterator = await (range(5) > pipeline)
    assert await collect(result_iterator) == [(0, 1), (2, 3), (4,)]


@pytest.mark.asyncio
async def test_atee_echoes_items(capsys) -> None:
    pipeline = aiter | atee
    result_iterator = await (["a", "b"] > pipeline)
    assert await collect(result_iterator) == ["a", "b"]
    captured = capsys.readouterr().out.splitlines()
    assert captured == ["'a'", "'b'"]


@pytest.mark.asyncio
async def test_atraverse_flattens_nested_structures() -> None:
    nested = [1, [2, [3, 4]], 5]
    pipeline = aiter | atraverse
    result_iterator = await (nested > pipeline)
    assert await collect(result_iterator) == [1, 2, 3, 4, 5]


@pytest.mark.asyncio
async def test_agroupby_matches_sync_behaviour() -> None:
    items = ["apple", "apricot", "banana"]
    result = await (items > (aiter | agroupby(lambda word: word[0])))
    assert result == [("a", ["apple", "apricot"]), ("b", ["banana"])]


@pytest.mark.asyncio
async def test_achain_flattens_streams() -> None:
    pipeline = aiter | achain
    result_iterator = await ([[1, 2], [3]] > pipeline)
    assert await collect(result_iterator) == [1, 2, 3]


@pytest.mark.asyncio
async def test_achain_with_appends_iterables() -> None:
    pipeline = aiter | achain_with([3, 4])
    result_iterator = await ([1, 2] > pipeline)
    assert await collect(result_iterator) == [1, 2, 3, 4]


@pytest.mark.asyncio
async def test_aislice_returns_slice() -> None:
    result = await (range(5) > (aiter | aislice(1, 4)))
    assert result == [1, 2, 3]


@pytest.mark.asyncio
async def test_aenumerate_numbers_items() -> None:
    pipeline = aiter | aenumerate(start=1)
    result_iterator = await (["a", "b"] > pipeline)
    assert await collect(result_iterator) == [(1, "a"), (2, "b")]


@pytest.mark.asyncio
async def test_aizip_combines_streams() -> None:
    pipeline = aiter | aizip(["a", "b"], [True, False])
    result_iterator = await ([1, 2] > pipeline)
    assert await collect(result_iterator) == [(1, "a", True), (2, "b", False)]


@pytest.mark.asyncio
async def test_anetcat_round_trip():
    received: list[bytes] = []

    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        while data := await reader.read(4096):
            received.append(data)
            writer.write(data.upper())
            await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handle, "127.0.0.1", 0)
    host, port = server.sockets[0].getsockname()

    async with server:
        pipeline = aiter | anetcat(host, port)
        result_iterator = await ([b"hello", b"world"] > pipeline)
        responses = await collect(result_iterator)

    assert b"".join(received) == b"helloworld"
    assert b"".join(responses) == b"HELLOWORLD"


@pytest.mark.asyncio
async def test_to_async_iterator_supports_iterable() -> None:
    iterator = await to_async_iterator([1, 2, 3])
    assert [item async for item in iterator] == [1, 2, 3]


@pytest.mark.asyncio
async def test_to_async_iterator_supports_awaitable() -> None:
    async def produce() -> list[int]:
        await asyncio.sleep(0)
        return [4, 5]

    iterator = await to_async_iterator(produce())
    assert [item async for item in iterator] == [4, 5]


@pytest.mark.asyncio
async def test_to_async_iterator_rejects_invalid_input() -> None:
    with pytest.raises(TypeError):
        await to_async_iterator(42)


@pytest.mark.asyncio
async def test_to_async_iterator_returns_async_iterator_as_is() -> None:
    async def generator() -> AsyncIterator[int]:
        for value in [1, 2]:
            yield value

    gen = generator()
    result = await to_async_iterator(gen)
    assert result is gen
    assert [item async for item in result] == [1, 2]


@pytest.mark.asyncio
async def test_to_async_iterator_accepts_async_iterable() -> None:
    class AsyncIterableOnly:
        def __aiter__(self) -> AsyncIterator[int]:
            async def generator() -> AsyncIterator[int]:
                for value in [3, 4]:
                    yield value

            return generator()

    iterable = AsyncIterableOnly()
    iterator = await to_async_iterator(iterable)
    assert [item async for item in iterator] == [3, 4]


@pytest.mark.asyncio
async def test_ensure_async_callable_handles_asyncpb() -> None:
    @apb
    async def async_identity(value: int) -> int:
        return value

    wrapper = ensure_async_callable(async_identity)
    assert await wrapper(7) == 7


@pytest.mark.asyncio
async def test_ensure_async_callable_handles_pb() -> None:
    @pb
    def add_two(value: int) -> int:
        return value + 2

    wrapper = ensure_async_callable(add_two)
    assert await wrapper(3) == 5


@pytest.mark.asyncio
async def test_ensure_async_callable_returns_coroutine_function() -> None:
    async def double(value: int) -> int:
        return value * 2

    wrapper = ensure_async_callable(double)
    assert wrapper is double
    assert await wrapper(4) == 8


def test_async_iter_operator_requires_parameters() -> None:
    async def bad() -> AsyncIterator[int]:
        async def generator() -> AsyncIterator[int]:
            yield 1

        return generator()

    with pytest.raises(TypeError):
        async_iter_operator(bad)


@pytest.mark.asyncio
async def test_abatched_requires_positive_size() -> None:
    pipeline = aiter | abatched(0)
    iterator = await ([1, 2] > pipeline)
    with pytest.raises(ValueError):
        async for _ in iterator:
            pass


@pytest.mark.asyncio
async def test_atraverse_preserves_strings() -> None:
    pipeline = aiter | atraverse
    iterator = await (["ab"] > pipeline)
    assert await collect(iterator) == ["ab"]


def test_annotation_requires_async_callable_handles_empty_and_plain() -> None:
    assert not _annotation_requires_async_callable(inspect._empty)
    assert not _annotation_requires_async_callable(int)
    assert _annotation_requires_async_callable(Callable[[int], int])
    assert _annotation_requires_async_callable(Callable[[int], int] | int)
