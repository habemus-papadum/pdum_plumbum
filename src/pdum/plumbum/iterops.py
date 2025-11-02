from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Any, Callable, TypeVar, cast

from .core import Pb, pb

T = TypeVar("T")
U = TypeVar("U")


def _normalize(func: Callable[[Any], Any] | Pb) -> Callable[[Any], Any]:
    if isinstance(func, Pb):
        return cast(Callable[[Any], Any], func)
    return func


def map(func: Callable[[T], U] | Pb) -> Pb:
    callable_func = _normalize(func)

    def _do(it: Iterable[T]) -> Iterator[U]:
        for item in it:
            yield callable_func(item)

    return pb(_do)


def filter(func: Callable[[T], bool] | Pb) -> Pb:
    callable_func = _normalize(func)

    def _do(it: Iterable[T]) -> Iterator[T]:
        for item in it:
            if callable_func(item):
                yield item

    return pb(_do)


__all__ = ["map", "filter"]
