from __future__ import annotations

import asyncio
import itertools
from builtins import anext
from collections import deque
from collections.abc import AsyncIterator, Callable
from typing import Any, Awaitable, Iterable, TypeAlias, TypeVar

from .aiterops_internals import async_iter_operator, ensure_async_callable, to_async_iterator

T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")
AsyncMapper: TypeAlias = Callable[[T], Awaitable[U]] | Callable[[T], U]
AsyncPredicate: TypeAlias = Callable[[T], Awaitable[bool]] | Callable[[T], bool]


@async_iter_operator
async def aselect(iterator: AsyncIterator[T], mapper: AsyncMapper) -> AsyncIterator[U]:
    """
    Apply ``mapper`` to each item in an async iterator.

    Parameters
    ----------
    iterator
        Source async iterator to transform.
    mapper
        Callable used to transform each element. May return awaitable results.

    Returns
    -------
    AsyncIterator[U]
        Async iterator yielding the transformed values.
    """

    async for item in iterator:
        yield await mapper(item)


@async_iter_operator
async def awhere(iterator: AsyncIterator[T], predicate: AsyncPredicate) -> AsyncIterator[T]:
    """
    Yield items from an async iterator for which ``predicate`` returns ``True``.

    Parameters
    ----------
    iterator
        Source async iterator to filter.
    predicate
        Callable returning ``True`` for values that should pass through. May return awaitable results.

    Returns
    -------
    AsyncIterator[T]
        Async iterator yielding values that satisfy the predicate.
    """

    async for item in iterator:
        if await predicate(item):
            yield item


@async_iter_operator
def aiter(iterator: AsyncIterator[Any]) -> AsyncIterator[Any]:
    """
    Normalize async iterables, iterators, or awaitables into an async iterator.
    """

    return iterator


@async_iter_operator
async def atake(iterator: AsyncIterator[T], count: int) -> AsyncIterator[T]:
    """Yield at most ``count`` items from ``iterator``."""

    remaining = max(count, 0)

    async for item in iterator:
        if remaining <= 0:
            break
        remaining -= 1
        yield item


@async_iter_operator
async def askip(iterator: AsyncIterator[T], count: int) -> AsyncIterator[T]:
    """Skip ``count`` items from ``iterator`` before yielding the rest."""

    remaining = max(count, 0)
    async for item in iterator:
        if remaining > 0:
            remaining -= 1
            continue
        yield item


@async_iter_operator
async def atake_while(iterator: AsyncIterator[T], predicate: AsyncPredicate) -> AsyncIterator[T]:
    """Yield items while ``predicate`` remains true."""

    async_predicate = ensure_async_callable(predicate)
    async for item in iterator:
        if await async_predicate(item):
            yield item
        else:
            break


@async_iter_operator
async def askip_while(iterator: AsyncIterator[T], predicate: AsyncPredicate) -> AsyncIterator[T]:
    """Skip items while ``predicate`` stays true, then yield the remainder."""

    async_predicate = ensure_async_callable(predicate)
    async for item in iterator:
        if await async_predicate(item):
            continue
        yield item
        break
    async for item in iterator:
        yield item


@async_iter_operator
async def adedup(iterator: AsyncIterator[T], key: Callable[[T], V] = lambda x: x) -> AsyncIterator[T]:
    """Yield unique items from ``iterator`` by tracking ``key`` values."""

    seen: set[V] = set()
    async_key = ensure_async_callable(key)
    async for item in iterator:
        dedup_key = await async_key(item)
        if dedup_key not in seen:
            seen.add(dedup_key)
            yield item


@async_iter_operator
async def auniq(iterator: AsyncIterator[T], key: Callable[[T], V] = lambda x: x) -> AsyncIterator[T]:
    """Yield items from ``iterator`` removing consecutive duplicates."""

    previous_key: V | None = None
    has_previous = False
    async_key = ensure_async_callable(key)
    async for item in iterator:
        current_key = await async_key(item)
        if not has_previous or current_key != previous_key:
            yield item
            has_previous = True
            previous_key = current_key


@async_iter_operator
async def apermutations(iterator: AsyncIterator[T], r: int | None = None) -> AsyncIterator[tuple[T, ...]]:
    """Yield permutations of items from ``iterator``."""

    items = [item async for item in iterator]
    for perm in itertools.permutations(items, r):
        yield perm


@async_iter_operator
async def atail(iterator: AsyncIterator[T], count: int) -> deque[T]:
    """Collect the last ``count`` items into a deque."""

    result: deque[T] = deque(maxlen=count if count >= 0 else 0)
    async for item in iterator:
        result.append(item)
    return result


@async_iter_operator
async def asort(iterator: AsyncIterator[T], key=None, reverse: bool = False) -> list[T]:
    """Return a sorted list of the items from ``iterator``."""

    items = [item async for item in iterator]
    return sorted(items, key=key, reverse=reverse)


@async_iter_operator
async def areverse(iterator: AsyncIterator[T]) -> AsyncIterator[T]:
    """Yield items from ``iterator`` in reverse order."""

    items = [item async for item in iterator]
    for item in reversed(items):
        yield item


@async_iter_operator
async def at(iterator: AsyncIterator[T], value: T) -> list[T]:
    """Append ``value`` to the items from ``iterator`` and return a list."""

    items = [item async for item in iterator]
    items.append(value)
    return items


@async_iter_operator
async def alist(iterator: AsyncIterator[T]) -> list[T]:
    """
    Collect all items from ``iterator`` into a list.

    Parameters
    ----------
    iterator
        Source async iterator to exhaust.

    Returns
    -------
    list[T]
        List containing every item produced by ``iterator``.
    """

    return [item async for item in iterator]


@async_iter_operator
async def atranspose(iterator: AsyncIterator[Iterable[T]]) -> list[tuple[T, ...]]:
    """Transpose rows and columns of the provided iterables."""

    rows = [list(row) async for row in iterator]
    return list(zip(*rows)) if rows else []


@async_iter_operator
async def abatched(iterator: AsyncIterator[T], size: int) -> AsyncIterator[tuple[T, ...]]:
    """Yield fixed-size batches from ``iterator``."""

    if size <= 0:
        raise ValueError("Batch size must be positive")
    batch: list[T] = []
    async for item in iterator:
        batch.append(item)
        if len(batch) == size:
            yield tuple(batch)
            batch.clear()
    if batch:
        yield tuple(batch)


@async_iter_operator
async def atee(iterator: AsyncIterator[T]) -> AsyncIterator[T]:
    """Print each item before yielding it."""

    async for item in iterator:
        print(repr(item))
        yield item


@async_iter_operator
async def atraverse(iterator: AsyncIterator[T]) -> AsyncIterator[T]:
    """Traverse nested iterables and yield leaf values."""

    async for item in iterator:
        async for nested in _atraverse_impl(item):
            yield nested


async def _atraverse_impl(value: Any) -> AsyncIterator[Any]:
    if isinstance(value, (str, bytes)):
        yield value
        return

    try:
        async_iter = await to_async_iterator(value)
    except TypeError:
        yield value
        return

    async for element in async_iter:
        async for nested in _atraverse_impl(element):
            yield nested


@async_iter_operator
async def agroupby(iterator: AsyncIterator[T], keyfunc) -> list[tuple[Any, list[T]]]:
    """Group items by ``keyfunc`` returning a list of (key, values)."""

    items = [item async for item in iterator]
    grouped: list[tuple[Any, list[T]]] = []
    for key, group in itertools.groupby(sorted(items, key=keyfunc), keyfunc):
        grouped.append((key, list(group)))
    return grouped


@async_iter_operator
async def achain(iterator: AsyncIterator[Iterable[T]]) -> AsyncIterator[T]:
    """Flatten iterables yielded by ``iterator``."""

    async for iterable in iterator:
        async_iter = await to_async_iterator(iterable)
        async for item in async_iter:
            yield item


@async_iter_operator
async def achain_with(iterator: AsyncIterator[T], *others: Any) -> AsyncIterator[T]:
    """Chain ``iterator`` with additional iterables."""

    async for item in iterator:
        yield item
    for other in others:
        async_iter = await to_async_iterator(other)
        async for item in async_iter:
            yield item


@async_iter_operator
async def aislice(iterator: AsyncIterator[T], *args: int) -> list[T]:
    """Return a slice of items as a list using start/stop/step semantics."""

    items = [item async for item in iterator]
    return list(itertools.islice(items, *args))


@async_iter_operator
async def aizip(iterator: AsyncIterator[T], *others: Any) -> AsyncIterator[tuple[Any, ...]]:
    """Zip ``iterator`` with additional iterables, producing tuples."""

    async_iters = [iterator]
    for other in others:
        async_iters.append(await to_async_iterator(other))

    while True:
        tuple_items = []
        for async_iter in async_iters:
            try:
                value = await anext(async_iter)
            except StopAsyncIteration:
                return
            tuple_items.append(value)
        yield tuple(tuple_items)


@async_iter_operator
async def anetcat(iterator: AsyncIterator[bytes], host: str, port: int) -> AsyncIterator[bytes]:
    """Async TCP client sending bytes and yielding responses."""

    reader, writer = await asyncio.open_connection(host, port)

    async def finalize() -> None:
        writer.close()
        await writer.wait_closed()

    try:
        async for chunk in iterator:
            writer.write(chunk)
            await writer.drain()
        try:
            writer.write_eof()
        except (NotImplementedError, ConnectionResetError):
            pass
        while True:
            data = await reader.read(4096)
            if not data:
                break
            yield data
    finally:
        await finalize()


@async_iter_operator
async def aenumerate(iterator: AsyncIterator[T], start: int = 0) -> AsyncIterator[tuple[int, T]]:
    """Enumerate items from ``iterator`` starting at ``start``."""

    index = start
    async for item in iterator:
        yield index, item
        index += 1


amap = aselect
afilter = awhere
acollect = alist


__all__ = [
    "aselect",
    "awhere",
    "aiter",
    "async_iter_operator",
    "AsyncMapper",
    "AsyncPredicate",
    "atake",
    "askip",
    "atake_while",
    "askip_while",
    "adedup",
    "auniq",
    "apermutations",
    "atail",
    "asort",
    "areverse",
    "at",
    "alist",
    "atranspose",
    "abatched",
    "atee",
    "atraverse",
    "agroupby",
    "achain",
    "achain_with",
    "aislice",
    "aizip",
    "anetcat",
    "aenumerate",
    "amap",
    "afilter",
    "acollect",
]
