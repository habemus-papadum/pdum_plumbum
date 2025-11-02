from __future__ import annotations

import functools
import inspect
import types
from collections import abc as collections_abc
from collections.abc import AsyncIterable, AsyncIterator, Callable, Iterable
from typing import Any, Awaitable, get_args, get_origin, get_type_hints

from .async_pipeline import AsyncPb, apb, ensure_async_pb
from .core import Pb


async def to_async_iterator(stream: Any) -> AsyncIterator[Any]:
    if isinstance(stream, AsyncIterator):
        return stream
    if isinstance(stream, AsyncIterable):
        return stream.__aiter__()
    if isinstance(stream, Iterable):
        iterator = iter(stream)

        async def generator() -> AsyncIterator[Any]:
            for item in iterator:
                yield item

        return generator()
    if inspect.isawaitable(stream):
        awaited = await stream
        return await to_async_iterator(awaited)
    raise TypeError("Expected an AsyncIterator or AsyncIterable")


def ensure_async_callable(func: Any) -> Callable[[Any], Awaitable[Any]]:
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


def _annotation_requires_async_callable(annotation: Any) -> bool:
    if annotation is inspect._empty:
        return False
    if annotation is None:
        return False
    origin = get_origin(annotation)
    if origin in (Callable, collections_abc.Callable):  # type: ignore[attr-defined]
        return True
    if origin in (types.UnionType, getattr(types, "UnionType", types.UnionType)):
        return any(_annotation_requires_async_callable(arg) for arg in get_args(annotation))
    if origin is None:
        return False
    return any(_annotation_requires_async_callable(arg) for arg in get_args(annotation))


def async_iter_operator(func: Callable[..., Awaitable[AsyncIterator[Any]]]) -> Callable[..., Any]:
    signature = inspect.signature(func)
    parameters = list(signature.parameters.values())
    if not parameters:
        raise TypeError("Async iterator operators must accept at least one parameter")

    stream_param = parameters[0].name
    type_hints = get_type_hints(func, include_extras=True)  # type: ignore[arg-type]
    async_callable_params = {
        param.name for param in parameters[1:] if _annotation_requires_async_callable(type_hints.get(param.name))
    }

    @apb
    async def wrapper(stream: Any, *args: Any, **kwargs: Any) -> AsyncIterator[Any]:
        bound = signature.bind(stream, *args, **kwargs)
        bound.apply_defaults()
        bound.arguments[stream_param] = await to_async_iterator(bound.arguments[stream_param])
        for name in async_callable_params:
            if name in bound.arguments:
                bound.arguments[name] = ensure_async_callable(bound.arguments[name])
        result = func(*bound.args, **bound.kwargs)
        if inspect.isawaitable(result):
            result = await result
        return result

    functools.update_wrapper(wrapper, func)
    return wrapper


__all__ = ["to_async_iterator", "ensure_async_callable", "async_iter_operator"]
