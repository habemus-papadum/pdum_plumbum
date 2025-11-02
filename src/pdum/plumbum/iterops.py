from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from typing import TypeVar

from .core import pb

T = TypeVar("T")
U = TypeVar("U")


@pb
def select(iterable: Iterable[T], mapper: Callable[[T], U]) -> Iterator[U]:
    """
    Apply ``func`` to each item in ``iterable``.

    Parameters
    ----------
    iterable
        Source iterable to transform.
    mapper
        Callable used to transform each element.

    Returns
    -------
    Iterator[U]
        Iterator yielding the transformed values.
    """
    for item in iterable:
        yield mapper(item)


@pb
def where(iterable: Iterable[T], predicate: Callable[[T], bool]) -> Iterator[T]:
    """
    Yield items from ``iterable`` for which ``predicate`` returns ``True``.

    Parameters
    ----------
    iterable
        Source iterable to filter.
    predicate
        Callable returning ``True`` for values that should pass through.

    Returns
    -------
    Iterator[T]
        Iterator yielding values that satisfy the predicate.
    """
    for item in iterable:
        if predicate(item):
            yield item


__all__ = ["select", "where"]
