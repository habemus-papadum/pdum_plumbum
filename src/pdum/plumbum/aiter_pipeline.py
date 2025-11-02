from __future__ import annotations

import functools
import inspect
from abc import ABC, abstractmethod
from collections.abc import AsyncIterable, AsyncIterator
from typing import Any, Callable


class AsyncIterPb(ABC):
    def __or__(self, other: Any) -> AsyncIterPb:
        return AsyncIterPbPair(self, other)

    def __ror__(self, other: Any) -> AsyncIterPb:
        return AsyncIterPbPair(other, self)

    @abstractmethod
    async def __rrshift__(self, data: Any) -> AsyncIterator[Any]: ...


class AsyncIterPbFunc(AsyncIterPb):
    def __init__(self, function: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        self.function = function
        self.args = args
        self.kwargs = kwargs
        functools.update_wrapper(self, function)

    def __call__(self, *args: Any, **kwargs: Any) -> AsyncIterPbFunc:
        return AsyncIterPbFunc(
            self.function,
            *self.args,
            *args,
            **self.kwargs,
            **kwargs,
        )

    async def __rrshift__(self, data: Any) -> AsyncIterator[Any]:
        async_iter = await _to_async_iterator(data)
        result = self.function(async_iter, *self.args, **self.kwargs)
        return await _ensure_async_iterator(result)

    def __repr__(self) -> str:
        return f"<async-iter {self.function.__name__}>(*{self.args}, **{self.kwargs})"


class AsyncIterPbPair(AsyncIterPb):
    def __init__(self, left: Any, right: Any) -> None:
        self.left = ensure_async_iter_pb(left)
        self.right = ensure_async_iter_pb(right)

    async def __rrshift__(self, data: Any) -> AsyncIterator[Any]:
        intermediate = await self.left.__rrshift__(data)
        return await self.right.__rrshift__(intermediate)

    def __repr__(self) -> str:
        return f"<{self.left!r}> | <{self.right!r}>"


def ensure_async_iter_pb(obj: Any) -> AsyncIterPb:
    if isinstance(obj, AsyncIterPb):
        return obj
    if callable(obj):
        return aipb(obj)
    raise TypeError(f"Cannot convert {obj!r} to AsyncIterPb")


def aipb(function: Callable[..., Any]) -> AsyncIterPbFunc:
    if isinstance(function, AsyncIterPb):
        return function  # type: ignore[return-value]
    if inspect.isasyncgenfunction(function):
        return AsyncIterPbFunc(function)
    if inspect.iscoroutinefunction(function):
        return AsyncIterPbFunc(function)

    async def wrapper(stream: AsyncIterator[Any], *args: Any, **kwargs: Any) -> AsyncIterator[Any]:
        result = function(stream, *args, **kwargs)
        if inspect.isawaitable(result):
            result = await result
        return await _ensure_async_iterator(result)

    functools.update_wrapper(wrapper, function)
    return AsyncIterPbFunc(wrapper)


def to_async_iter(operator: Any) -> AsyncIterPb:
    return ensure_async_iter_pb(operator)


async def _to_async_iterator(data: Any) -> AsyncIterator[Any]:
    if isinstance(data, AsyncIterator):
        return data
    if isinstance(data, AsyncIterable):
        return data.__aiter__()
    if inspect.isawaitable(data):
        awaited = await data
        return await _to_async_iterator(awaited)
    raise TypeError("Expected an AsyncIterator or AsyncIterable")


async def _ensure_async_iterator(obj: Any) -> AsyncIterator[Any]:
    if isinstance(obj, AsyncIterator):
        return obj
    if isinstance(obj, AsyncIterable):
        return obj.__aiter__()
    if inspect.isawaitable(obj):
        awaited = await obj
        return await _ensure_async_iterator(awaited)
    raise TypeError("Expected an AsyncIterator or AsyncIterable")


__all__ = [
    "AsyncIterPb",
    "AsyncIterPbFunc",
    "AsyncIterPbPair",
    "aipb",
    "ensure_async_iter_pb",
    "to_async_iter",
]
