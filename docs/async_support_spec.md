# Async Pipeline Implementation Spec

## Scope
- Add async-aware pipelines without changing the current synchronous API or `pb` decorator.
- Provide explicit async operator hierarchies for single-value pipelines and async-iterator pipelines.
- Support mixing synchronous callables inside async pipelines via adapters.

## New Decorator
- `apb(function)`:
  - If `function` is a coroutine function, return an `AsyncPbFunc`.
  - Otherwise wrap `function` in `async def wrapper(data, *args, **kwargs)` that forwards to `function`, then wrap that wrapper in `AsyncPbFunc`.
  - Preserve `functools.update_wrapper` behaviour for metadata.

## Async Scalar Pipeline Types
- `class AsyncPb(Pb, ABC)`:
  - Defines `__or__`, `__ror__`, and `async def __rrshift__`.
  - `__or__` should promote RHS into `AsyncPb` via `apb`/adapter if needed.
- `class AsyncPbFunc(AsyncPb)`:
  - Stores `function`, partial args/kwargs.
  - `__call__` returns a new `AsyncPbFunc` with accumulated arguments (same semantics as `PbFunc`).
  - `async def __rrshift__(self, data): return await self.function(data, *self.args, **self.kwargs)`.
- `class AsyncPbPair(AsyncPb)`:
  - Wrap non-async operands using an adapter that turns any `Pb` into `AsyncPb` by delegating to its synchronous `__rrshift__`.
  - `async def __rrshift__(self, data): return await self.right.__rrshift__(await self.left.__rrshift__(data))`.
- Threading syntax: `await (value >> async_pipeline)`; `__rshift__` should return a coroutine object.

## Async Iterator Pipeline Types
- `class AsyncIterPb(AsyncPb)` with `async def __rrshift__` returning an async iterable.
- `class AsyncIterPbFunc(AsyncIterPb)`:
  - Accepts functions that yield async iterables (async generators or callables returning `AsyncIterable`).
  - Partial application identical to `AsyncPbFunc`.
  - `async def __rrshift__(self, data)` returns an `AsyncIterator`.
- `class AsyncIterPbPair(AsyncIterPb)`:
  - `async def __rrshift__(self, data)` piping via `async for` and yielding downstream.
- Promotion rules:
  - When composing scalar async operators with iterator pipelines, wrap scalars as single-item async generators.
  - Provide `to_async_iter(operator)` helper for explicit promotion.
  - Ensure `value >> async_iter_pipeline` returns an async iterator consumable via `async for`.

## Adapters and Mixing Rules
- `wrap_sync_as_async(pb_instance)` returning an `AsyncPb` that calls the sync operator and returns its result (no implicit threadpool).
- `wrap_async_scalar_as_iter(async_pb)` returning `AsyncIterPb` that yields a single item.
- Ensure `apb` + `AsyncPbPair` can combine with legacy `Pb`/`PbPair` by auto-promoting sync operators (but keep original instances reusable).

## Error Handling & Typing
- Propagate exceptions naturally through awaited calls.
- Annotate return types: `AsyncPbFunc.__rrshift__ -> Awaitable[T]`, `AsyncIterPbFunc.__rrshift__ -> AsyncIterator[T]`.
- Update `__all__` to include new async classes and `apb`.

## Documentation & Tests
- Add README/md examples for `apb` and async iterator usage.
- Provide pytest coverage using `pytest.mark.asyncio`:
  - Scalar pipelines (`await (value >> apb_op)`).
  - Mixed sync/async operators via `apb`.
  - Async iterator pipelines consumed with `async for`.
