from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from typing import Any, Awaitable, TypeAlias, TypeVar

from .aiterops_internals import async_iter_operator

T = TypeVar("T")
U = TypeVar("U")
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


__all__ = ["aselect", "awhere", "aiter", "async_iter_operator", "AsyncMapper", "AsyncPredicate"]
