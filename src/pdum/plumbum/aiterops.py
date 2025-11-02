from __future__ import annotations

import functools
import inspect
from collections.abc import AsyncIterable, AsyncIterator, Callable
from typing import Any, Awaitable, TypeVar

from .async_pipeline import AsyncPb, apb, ensure_async_pb
from .core import Pb

T = TypeVar("T")
U = TypeVar("U")


async def _to_async_iterator(stream: Any) -> AsyncIterator[T]:
    if isinstance(stream, AsyncIterator):
        return stream
    if isinstance(stream, AsyncIterable):
        return stream.__aiter__()
    if inspect.isawaitable(stream):
        awaited = await stream
        return await _to_async_iterator(awaited)
    raise TypeError("Expected an AsyncIterator or AsyncIterable")


def _ensure_async_callable(func: Any) -> Callable[[Any], Awaitable[Any]]:
    if isinstance(func, AsyncPb):
        return func.to_async_function()
    if isinstance(func, Pb):
        return ensure_async_pb(func).to_async_function()
    if inspect.iscoroutinefunction(func):
        return func  # type: ignore[return-value]

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    return wrapper


@apb
async def aselect(stream: Any, mapper: Callable[[T], Awaitable[U]] | Callable[[T], U]) -> AsyncIterator[U]:
    """
    Apply ``mapper`` to each item in an async iterable ``stream``.

    Parameters
    ----------
    stream
        Source async iterable to transform.
    mapper
        Callable used to transform each element. May return awaitable results.

    Returns
    -------
    AsyncIterator[U]
        Async iterator yielding the transformed values.
    """

    iterator = await _to_async_iterator(stream)
    async_mapper = _ensure_async_callable(mapper)

    async def _generator() -> AsyncIterator[U]:
        async for item in iterator:
            yield await async_mapper(item)

    return _generator()


@apb
async def awhere(stream: Any, predicate: Callable[[T], Awaitable[bool]] | Callable[[T], bool]) -> AsyncIterator[T]:
    """
    Yield items from an async iterable ``stream`` for which ``predicate`` returns ``True``.

    Parameters
    ----------
    stream
        Source async iterable to filter.
    predicate
        Callable returning ``True`` for values that should pass through. May return awaitable results.

    Returns
    -------
    AsyncIterator[T]
        Async iterator yielding values that satisfy the predicate.
    """

    iterator = await _to_async_iterator(stream)
    async_predicate = _ensure_async_callable(predicate)

    async def _generator() -> AsyncIterator[T]:
        async for item in iterator:
            if await async_predicate(item):
                yield item

    return _generator()


@apb
async def aiter(stream: Any) -> AsyncIterator[Any]:
    """
    Normalize async iterables, iterators, or awaitables into an async iterator.
    """

    return await _to_async_iterator(stream)


__all__ = ["aselect", "awhere", "aiter"]
