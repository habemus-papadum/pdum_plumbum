from __future__ import annotations

import builtins
import itertools
import socket
from collections import deque
from contextlib import closing
from typing import Iterable, Iterator, TypeVar

from .core import pb

T = TypeVar("T")
U = TypeVar("U")
K = TypeVar("K")


@pb
def take(iterable: Iterable[T], count: int) -> Iterator[T]:
    """
    Yield the first ``count`` items from ``iterable``.

    Parameters
    ----------
    iterable
        Source iterable to consume.
    count
        Maximum number of items to yield.

    Returns
    -------
    Iterator[T]
        Iterator of the first ``count`` items.
    """
    yield from itertools.islice(iterable, max(count, 0))


@pb
def tail(iterable: Iterable[T], count: int) -> deque[T]:
    """
    Return a deque containing the last ``count`` items of ``iterable``.

    Parameters
    ----------
    iterable
        Source iterable to inspect.
    count
        Number of items to retain.

    Returns
    -------
    collections.deque[T]
        Deque containing the most recent items.
    """
    return deque(iterable, maxlen=count if count >= 0 else 0)


@pb
def skip(iterable: Iterable[T], count: int) -> Iterator[T]:
    """
    Skip ``count`` items in ``iterable`` before yielding the remainder.

    Parameters
    ----------
    iterable
        Source iterable to consume.
    count
        Number of items to drop from the front.

    Returns
    -------
    Iterator[T]
        Iterator yielding the remaining values.
    """
    iterator = iter(iterable)
    for _ in range(max(count, 0)):
        next(iterator, None)
    yield from iterator


@pb
def dedup(iterable: Iterable[T], key=lambda x: x) -> Iterator[T]:
    """
    Yield only unique items from ``iterable`` by tracking seen keys.

    Parameters
    ----------
    iterable
        Source iterable to deduplicate.
    key
        Callable returning the deduplication key for each item.

    Returns
    -------
    Iterator[T]
        Iterator yielding unique items.
    """
    seen: set[K] = set()
    for item in iterable:
        dedup_key = key(item)
        if dedup_key not in seen:
            seen.add(dedup_key)
            yield item


@pb
def uniq(iterable: Iterable[T], key=lambda x: x) -> Iterator[T]:
    """
    Yield items from ``iterable`` removing consecutive duplicates.

    Parameters
    ----------
    iterable
        Source iterable to deduplicate.
    key
        Callable returning the comparison key for each item.

    Returns
    -------
    Iterator[T]
        Iterator yielding items without consecutive duplicates.
    """
    iterator = iter(iterable)
    try:
        previous = next(iterator)
    except StopIteration:
        return
    yield previous
    prev_key = key(previous)
    for item in iterator:
        current_key = key(item)
        if current_key != prev_key:
            yield item
            prev_key = current_key


@pb
def permutations(iterable: Iterable[T], r: int | None = None) -> Iterator[tuple[T, ...]]:
    """
    Yield permutations of ``iterable``.

    Parameters
    ----------
    iterable
        Source iterable to permute.
    r
        Length of each permutation.

    Returns
    -------
    Iterator[tuple[T, ...]]
        Iterator over permutations.
    """
    yield from itertools.permutations(iterable, r)


@pb
def netcat(to_send: Iterable[bytes], host: str, port: int) -> Iterator[bytes]:
    """
    Send bytes to ``host``/``port`` and yield responses.

    Parameters
    ----------
    to_send
        Iterable of byte chunks to transmit.
    host
        Target hostname.
    port
        Target port.

    Returns
    -------
    Iterator[bytes]
        Iterator yielding response chunks.
    """
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.connect((host, port))
        for chunk in to_send:
            sock.sendall(chunk)
        sock.shutdown(socket.SHUT_WR)
        while True:
            data = sock.recv(4096)
            if not data:
                break
            yield data


def _traverse_impl(obj: Iterable[T] | T) -> Iterator[T]:
    if isinstance(obj, (str, bytes)):
        yield obj  # type: ignore[misc]
        return
    if isinstance(obj, Iterable):
        for element in obj:
            yield from _traverse_impl(element)
        return
    yield obj  # type: ignore[misc]


@pb
def traverse(obj: Iterable[T] | T) -> Iterator[T]:
    """
    Traverse nested iterables yielding leaf values.

    Parameters
    ----------
    obj
        A potentially nested iterable structure.

    Returns
    -------
    Iterator[T]
        Iterator yielding flattened values.
    """

    yield from _traverse_impl(obj)


@pb
def tee(iterable: Iterable[T]) -> Iterator[T]:
    """
    Echo items to stdout while yielding them unchanged.

    Parameters
    ----------
    iterable
        Source iterable to observe.

    Returns
    -------
    Iterator[T]
        Iterator yielding the original items.
    """
    for item in iterable:
        print(repr(item))
        yield item


@pb
def select(iterable: Iterable[T], mapper) -> Iterator[U]:
    """
    Apply ``mapper`` to each item in ``iterable``.
    """
    for item in iterable:
        yield mapper(item)


@pb
def where(iterable: Iterable[T], predicate) -> Iterator[T]:
    """
    Yield items for which ``predicate`` returns ``True``.
    """
    for item in iterable:
        if predicate(item):
            yield item


@pb
def take_while(iterable: Iterable[T], predicate) -> Iterator[T]:
    """
    Yield items from ``iterable`` while ``predicate`` stays true.
    """
    yield from itertools.takewhile(predicate, iterable)


@pb
def skip_while(iterable: Iterable[T], predicate) -> Iterator[T]:
    """
    Skip items in ``iterable`` while ``predicate`` stays true.
    """
    yield from itertools.dropwhile(predicate, iterable)


@pb
def groupby(iterable: Iterable[T], keyfunc) -> Iterator[tuple[K, Iterator[T]]]:
    """
    Group items by ``keyfunc`` using ``itertools.groupby`` on sorted data.
    """
    sorted_items = sorted(iterable, key=keyfunc)
    yield from itertools.groupby(sorted_items, keyfunc)


@pb
def sort(iterable: Iterable[T], key=None, reverse: bool = False) -> list[T]:
    """
    Return a new list with items sorted.
    """
    return sorted(iterable, key=key, reverse=reverse)


@pb
def reverse(iterable: Iterable[T]) -> Iterator[T]:
    """
    Yield items from ``iterable`` in reverse order.
    """
    yield from reversed(tuple(iterable))


@pb
def t(iterable: Iterable[T], value: T) -> list[T]:
    """
    Append ``value`` to ``iterable`` (if possible) and return the result.
    """
    if hasattr(iterable, "__iter__") and not isinstance(iterable, str):
        try:
            return iterable + type(iterable)([value])  # type: ignore[operator]
        except TypeError:
            pass
    return [iterable, value]  # type: ignore[list-item]


@pb
def transpose(iterable: Iterable[Iterable[T]]) -> list[tuple[T, ...]]:
    """
    Transpose rows and columns within ``iterable``.
    """
    return list(zip(*iterable))


@pb
def batched(iterable: Iterable[T], size: int) -> Iterator[tuple[T, ...]]:
    """
    Yield fixed-size batches from ``iterable``.
    """
    if size <= 0:
        raise ValueError("Batch size must be positive")
    iterator = iter(iterable)
    while batch := tuple(itertools.islice(iterator, size)):
        yield batch


enumerate = pb(builtins.enumerate)
map = select
filter = where
chain = pb(itertools.chain.from_iterable)
chain_with = pb(itertools.chain)
islice = pb(itertools.islice)
izip = pb(zip)

__all__ = [
    "take",
    "tail",
    "skip",
    "dedup",
    "uniq",
    "permutations",
    "netcat",
    "traverse",
    "tee",
    "select",
    "where",
    "take_while",
    "skip_while",
    "groupby",
    "sort",
    "reverse",
    "t",
    "transpose",
    "batched",
    "enumerate",
    "map",
    "filter",
    "chain",
    "chain_with",
    "islice",
    "izip",
]
