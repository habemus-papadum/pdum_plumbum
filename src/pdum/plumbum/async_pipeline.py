from __future__ import annotations

import functools
import inspect
from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable

from .core import Pb


class AsyncPb(ABC):
    def __or__(self, other: Any) -> AsyncPb:
        return AsyncPbPair(self, other)

    def __ror__(self, other: Any) -> AsyncPb:
        return AsyncPbPair(other, self)

    def __call__(self, value: Any) -> Awaitable[Any]:
        return value >> self

    @abstractmethod
    async def __rrshift__(self, data: Any) -> Any: ...


class AsyncPbFunc(AsyncPb):
    def __init__(self, function: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        self.function = function
        self.args = args
        self.kwargs = kwargs
        functools.update_wrapper(self, function)

    def partial(self, *args: Any, **kwargs: Any) -> AsyncPbFunc:
        return AsyncPbFunc(
            self.function,
            *self.args,
            *args,
            **self.kwargs,
            **kwargs,
        )

    async def __rrshift__(self, data: Any) -> Any:
        result = self.function(data, *self.args, **self.kwargs)
        if inspect.isawaitable(result):
            result = await result
        return result

    def __repr__(self) -> str:
        return f"<async {self.function.__name__}>(*{self.args}, **{self.kwargs})"


class AsyncPbPair(AsyncPb):
    def __init__(self, left: Any, right: Any) -> None:
        self.left = ensure_async_pb(left)
        self.right = ensure_async_pb(right)

    async def __rrshift__(self, data: Any) -> Any:
        intermediate = await self.left.__rrshift__(data)
        return await self.right.__rrshift__(intermediate)

    def __repr__(self) -> str:
        return f"<{self.left!r}> | <{self.right!r}>"


class _SyncToAsyncAdapter(AsyncPb):
    def __init__(self, operator: Pb) -> None:
        self.operator = operator

    async def __rrshift__(self, data: Any) -> Any:
        result = self.operator.__rrshift__(data)
        if inspect.isawaitable(result):
            result = await result
        return result

    def __repr__(self) -> str:
        return f"async({self.operator!r})"


def ensure_async_pb(obj: Any) -> AsyncPb:
    if isinstance(obj, AsyncPb):
        return obj
    if isinstance(obj, Pb):
        return wrap_sync_as_async(obj)
    if callable(obj):
        return apb(obj)
    raise TypeError(f"Cannot convert {obj!r} to AsyncPb")


def wrap_sync_as_async(operator: Pb) -> AsyncPb:
    if isinstance(operator, AsyncPb):
        return operator
    return _SyncToAsyncAdapter(operator)


def _wrap_sync_callable(function: Callable[..., Any]) -> Callable[..., Any]:
    async def wrapper(data: Any, *args: Any, **kwargs: Any) -> Any:
        return function(data, *args, **kwargs)

    functools.update_wrapper(wrapper, function)
    return wrapper


def apb(function: Callable[..., Any]) -> AsyncPbFunc:
    if isinstance(function, AsyncPb):
        return function  # type: ignore[return-value]
    if inspect.iscoroutinefunction(function) or inspect.isasyncgenfunction(function):
        return AsyncPbFunc(function)
    return AsyncPbFunc(_wrap_sync_callable(function))


__all__ = [
    "AsyncPb",
    "AsyncPbFunc",
    "AsyncPbPair",
    "apb",
    "ensure_async_pb",
    "wrap_sync_as_async",
]
