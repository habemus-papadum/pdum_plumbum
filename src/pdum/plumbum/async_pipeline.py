from __future__ import annotations

import functools
import inspect
from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable

from .core import Pb


class AsyncPb(ABC):
    """
    Base class for asynchronous plumbum operators.
    """

    operator_kind = "async"

    def __lt__(self, other: Any) -> Any:
        setattr(self, "_last_right_comparison", other)
        return self.__rgt__(other)

    def __gt__(self, other: Any) -> Any:
        message = self._format_gt_chain_error(other)
        setattr(self, "_last_right_comparison", None)
        raise TypeError(message)

    def __rgt__(self, data: Any) -> Any:
        return self._thread(data)

    def __or__(self, other: Any) -> AsyncPb:
        return AsyncPbPair(self, other)

    def __ror__(self, other: Any) -> AsyncPb:
        return AsyncPbPair(other, self)

    async def __rrshift__(self, data: Any) -> Any:
        raise TypeError("The '>>' threading operator has been removed. Use 'await (value > operator)' instead.")

    @abstractmethod
    async def _thread(self, data: Any) -> Any: ...

    def to_async_function(self) -> Callable[[Any], Awaitable[Any]]:
        async def _call(value: Any) -> Any:
            return await (value > self)

        return _call

    def _format_gt_chain_error(self, other: Any) -> str:
        other_kind = getattr(other, "operator_kind", None)
        if other_kind in {"sync", "async"}:
            rhs_description = "another plumbum operator"
        else:
            rhs_description = f"an object of type {type(other).__name__}"

        return (
            "Chained '>' comparisons involving plumbum operators are not supported. "
            "Python interprets 'a > b > c' as a chained comparison, so the expression "
            f"you wrote ended up comparing the operator against {rhs_description}. "
            "Wrap the first comparison in parentheses—e.g. '(value > operator) > next'. "
            "When using async operators remember to await the result: 'await (value > operator)'."
        )


class AsyncPbFunc(AsyncPb):
    def __init__(self, function: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        self.function = function
        self.args = tuple(self._normalize(value) for value in args)
        self.kwargs = {key: self._normalize(value) for key, value in kwargs.items()}
        functools.update_wrapper(self, function)

    def __call__(self, *args: Any, **kwargs: Any) -> AsyncPbFunc:
        return AsyncPbFunc(
            self.function,
            *self.args,
            *args,
            **self.kwargs,
            **kwargs,
        )

    async def _thread(self, data: Any) -> Any:
        result = self.function(data, *self.args, **self.kwargs)
        if inspect.isawaitable(result):
            result = await result
        return result

    def __repr__(self) -> str:
        return f"<async {self.function.__name__}>(*{self.args}, **{self.kwargs})"

    @staticmethod
    def _normalize(value: Any) -> Any:
        if isinstance(value, AsyncPb):
            return value.to_async_function()
        if isinstance(value, Pb):
            return ensure_async_pb(value).to_async_function()
        return value


class AsyncPbPair(AsyncPb):
    def __init__(self, left: Any, right: Any) -> None:
        self.left = ensure_async_pb(left)
        self.right = ensure_async_pb(right)

    async def _thread(self, data: Any) -> Any:
        intermediate = await self.left._thread(data)
        return await self.right._thread(intermediate)

    def __repr__(self) -> str:
        return f"<{self.left!r}> | <{self.right!r}>"


class _SyncToAsyncAdapter(AsyncPb):
    def __init__(self, operator: Pb) -> None:
        self.operator = operator

    async def _thread(self, data: Any) -> Any:
        result = self.operator._thread(data)
        if inspect.isawaitable(result):
            result = await result
        return result

    def __repr__(self) -> str:
        return f"async({self.operator!r})"


def ensure_async_pb(obj: Any) -> AsyncPb:
    if isinstance(obj, AsyncPb):
        return obj
    if isinstance(obj, Pb):
        return _SyncToAsyncAdapter(obj)
    if callable(obj):
        return apb(obj)
    raise TypeError(f"Cannot convert {obj!r} to AsyncPb")


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
]
