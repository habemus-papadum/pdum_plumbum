from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, AsyncIterable

from ..aiterops_internals import async_iter_operator, to_async_iterator
from ..async_pipeline import apb
from . import operators as jq_ops
from .paths import iter_paths
from .typing import JsonValue


@async_iter_operator
async def aexplode(iterator: AsyncIterator[JsonValue], expr: str, keep_path: bool = False) -> AsyncIterator[Any]:
    async def generator() -> AsyncIterator[Any]:
        async for item in iterator:
            for path, match in iter_paths(item, expr):
                if isinstance(match, (list, tuple)):
                    for element in match:
                        yield (path, element) if keep_path else element
                else:
                    yield (path, match) if keep_path else match

    return generator()


@async_iter_operator
async def aunwind(iterator: AsyncIterator[JsonValue], expr: str, keep_empty: bool = False) -> AsyncIterator[Any]:
    async def generator() -> AsyncIterator[Any]:
        async for item in iterator:
            yielded = False
            for value in item > jq_ops.explode(expr):
                yielded = True
                yield value
            if not yielded and keep_empty:
                yield item

    return generator()


@apb
async def agroup_by(stream: AsyncIterable[JsonValue] | JsonValue, expr: str) -> list[tuple[Any, list[JsonValue]]]:
    iterator = await to_async_iterator(stream)
    items = [item async for item in iterator]
    return items > jq_ops.group_by(expr)


@apb
async def acount_by(stream: AsyncIterable[JsonValue] | JsonValue, expr: str) -> dict[Any, int]:
    iterator = await to_async_iterator(stream)
    items = [item async for item in iterator]
    return items > jq_ops.count_by(expr)


@apb
async def asum_by(
    stream: AsyncIterable[JsonValue] | JsonValue,
    key_expr: str,
    value_expr: str,
    *,
    default: float = 0.0,
) -> dict[Any, float]:
    iterator = await to_async_iterator(stream)
    items = [item async for item in iterator]
    return items > jq_ops.sum_by(key_expr, value_expr, default=default)


@apb
async def astats(stream: AsyncIterable[JsonValue] | JsonValue, expr: str) -> dict[str, float]:
    iterator = await to_async_iterator(stream)
    items = [item async for item in iterator]
    return items > jq_ops.stats(expr)


__all__ = ["aexplode", "aunwind", "agroup_by", "acount_by", "asum_by", "astats"]
