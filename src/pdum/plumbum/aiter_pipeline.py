from __future__ import annotations

import functools
import inspect
from abc import ABC, abstractmethod
from collections.abc import AsyncIterable, AsyncIterator, Iterable
from typing import Any, Callable

from .async_pipeline import AsyncPb
from .core import Pb


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


class _AsyncScalarToIterAdapter(AsyncIterPb):
    def __init__(self, operator: AsyncPb) -> None:
        self.operator = operator

    async def __rrshift__(self, data: Any) -> AsyncIterator[Any]:
        async_iter = await _to_async_iterator(data)

        async def generator() -> AsyncIterator[Any]:
            async for item in async_iter:
                yield await self.operator.__rrshift__(item)

        return generator()

    def __repr__(self) -> str:
        return f"iter({self.operator!r})"


class _SyncIterToAsyncAdapter(AsyncIterPb):
    def __init__(self, operator: Pb) -> None:
        self.operator = operator

    async def __rrshift__(self, data: Any) -> AsyncIterator[Any]:
        result = self.operator.__rrshift__(data)
        return await _ensure_async_iterator(result)

    def __repr__(self) -> str:
        return f"async-iter({self.operator!r})"


def ensure_async_iter_pb(obj: Any) -> AsyncIterPb:
    if isinstance(obj, AsyncIterPb):
        return obj
    if isinstance(obj, AsyncPb):
        return wrap_async_scalar_as_iter(obj)
    if isinstance(obj, Pb):
        return _SyncIterToAsyncAdapter(obj)
    if callable(obj):
        return aipb(obj)
    raise TypeError(f"Cannot convert {obj!r} to AsyncIterPb")


def wrap_async_scalar_as_iter(operator: AsyncPb) -> AsyncIterPb:
    return _AsyncScalarToIterAdapter(operator)


def _wrap_sync_iter_function(function: Callable[..., Any]) -> Callable[..., Any]:
    async def wrapper(data: AsyncIterator[Any], *args: Any, **kwargs: Any) -> AsyncIterator[Any]:
        items = []
        async for item in data:
            items.append(item)
        result = function(items, *args, **kwargs)
        return await _ensure_async_iterator(result)

    functools.update_wrapper(wrapper, function)
    return wrapper


def aipb(function: Callable[..., Any]) -> AsyncIterPbFunc:
    if isinstance(function, AsyncIterPb):
        return function  # type: ignore[return-value]
    if inspect.isasyncgenfunction(function):
        return AsyncIterPbFunc(function)
    if inspect.iscoroutinefunction(function):
        return AsyncIterPbFunc(function)
    return AsyncIterPbFunc(_wrap_sync_iter_function(function))


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
    if isinstance(data, Iterable):

        async def generator() -> AsyncIterator[Any]:
            for item in data:
                yield item

        return generator()

    async def single() -> AsyncIterator[Any]:
        yield data

    return single()


async def _ensure_async_iterator(obj: Any) -> AsyncIterator[Any]:
    if isinstance(obj, AsyncIterator):
        return obj
    if isinstance(obj, AsyncIterable):
        return obj.__aiter__()
    if inspect.isawaitable(obj):
        awaited = await obj
        return await _ensure_async_iterator(awaited)
    if isinstance(obj, Iterable):

        async def from_iterable() -> AsyncIterator[Any]:
            for item in obj:
                yield item

        return from_iterable()

    async def single() -> AsyncIterator[Any]:
        yield obj

    return single()


__all__ = [
    "AsyncIterPb",
    "AsyncIterPbFunc",
    "AsyncIterPbPair",
    "aipb",
    "ensure_async_iter_pb",
    "wrap_async_scalar_as_iter",
    "to_async_iter",
]
