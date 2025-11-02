from __future__ import annotations

import inspect
from collections.abc import AsyncIterator
from typing import Any, Awaitable, Callable, TypeVar

from .aiter_pipeline import AsyncIterPb, aipb
from .async_pipeline import AsyncPb
from .core import Pb

T = TypeVar("T")
U = TypeVar("U")


async def _maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


def _normalize(func: Callable[[Any], Any] | Pb | AsyncPb) -> Callable[[Any], Awaitable[Any] | Any]:
    if isinstance(func, AsyncPb):
        return func.to_async_function()
    if isinstance(func, Pb):
        return func.to_function()
    return func


def map(func: Callable[[T], U] | Pb) -> AsyncIterPb:
    callable_func = _normalize(func)

    async def _do(stream: AsyncIterator[T]) -> AsyncIterator[U]:
        async for item in stream:
            result = callable_func(item)
            result = await _maybe_await(result)
            yield result

    return aipb(_do)


def filter(func: Callable[[T], bool] | Pb) -> AsyncIterPb:
    callable_func = _normalize(func)

    async def _do(stream: AsyncIterator[T]) -> AsyncIterator[T]:
        async for item in stream:
            decision = callable_func(item)
            decision = await _maybe_await(decision)
            if decision:
                yield item

    return aipb(_do)


__all__ = ["map", "filter"]
