# Async Pipeline Implementation Spec

## Scope
- Add async-aware pipelines without changing the current synchronous API or `pb` decorator.
- Provide explicit async operator hierarchy for single-value pipelines.
- Support mixing synchronous callables inside async pipelines via adapters.

## New Decorators
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
- Threading syntax: `await (value > async_pipeline)`; the existing `>` entry point should return a coroutine object when the pipeline is async.

## Adapters and Mixing Rules
- `wrap_sync_as_async(pb_instance)` returning an `AsyncPb` that calls the sync operator and returns its result (no implicit threadpool).
- Ensure `apb` + `AsyncPbPair` can combine with legacy `Pb`/`PbPair` by auto-promoting sync operators (but keep original instances reusable).

## Error Handling & Typing
- Propagate exceptions naturally through awaited calls.
- Annotate return types: `AsyncPbFunc.__rrshift__ -> Awaitable[T]`.
- Update `__all__` to include new async classes and `apb`.

## Documentation & Tests
- Add README/md examples for `apb`.
- Provide pytest coverage using `pytest.mark.asyncio`:
- Scalar pipelines (`await (value > apb_op)`).
  - Mixed sync/async operators via `apb`.
