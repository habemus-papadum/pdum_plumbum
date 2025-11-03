# Async/Await Support Design Notes

## Goals and Constraints
- Preserve the ergonomic `|` (compose) and `>` (thread) syntax.
- Keep data vs. operator separation; operators should remain first-class values that can be composed before execution.
- Support partial application semantics identical to the synchronous API.
- Avoid surprising implicit `await` calls that could consume values meant to stay awaitable.
- Minimise disruption to the existing synchronous API and its performance characteristics.

## Option 1 – Extend Existing Classes with Runtime Detection
**Idea:** Teach `PbFunc`/`PbPair` to inspect the wrapped callable or threaded value and `await` whenever an awaitable shows up.

### Mechanics
- Detect coroutine functions with `inspect.iscoroutinefunction`; wrap them so `__rrshift__` awaits the call.
- Detect awaitable results from synchronous functions and await them before passing along.
- Propagate awaitables through `PbPair.__rrshift__`, awaiting as needed before chaining.

### Issues
- **Ambiguity of awaitables:** Pipelines may intentionally thread awaitable objects (e.g., `asyncio.Task` used as plain data). Automatically awaiting them changes semantics and breaks those scenarios.
- **Partial application + dynamic dispatch:** After partial application, we may lose access to the original function object (e.g., `functools.partial`, bound methods). Detection would need to occur on every call anyway, effectively reintroducing branching cost each pipeline execution.
- **Mixing sync and async:** Once a coroutine-producing stage appears, every downstream stage must be aware that it receives an awaited value rather than a coroutine object. Retrofitting this logic into existing synchronous classes complicates reasoning and increases coupling.
- **Operator consistency:** Today `data > pipeline` returns a value immediately. Switching to sometimes returning coroutines would silently change usage patterns and risk un-awaited coroutines or blocking calls.

### Verdict
This approach is error-prone, obscures execution semantics, and introduces subtle behavioural changes. It also makes testing and typing harder (return type becomes `Any | Awaitable[Any]` everywhere). Not recommended.

## Option 2 – Introduce Parallel Async Pipeline Types
**Idea:** Provide async-aware counterparts to the existing abstractions while keeping the synchronous path untouched and introducing a dedicated `apb` decorator for async pipelines.

### Core Types
- `AsyncPb` (base class) mirroring `Pb` but with `async def __rrshift__`.
- `AsyncPbFunc` for coroutine functions:
  - Partial application works the same; calling it returns another `AsyncPbFunc`.
  - `__rrshift__` awaits the wrapped coroutine and returns its result.
- `AsyncPbPair` to compose async operators:
  - `async def __rrshift__(self, data): return await self.right.__rrshift__(await self.left.__rrshift__(data))`.

### Decorators
- Leave the existing `pb` decorator unchanged; it continues to wrap synchronous callables only.
- Introduce `apb`:
  - Wrap coroutine functions as `AsyncPbFunc`.
  - Wrap synchronous callables (e.g., `print`) by adapting them into `AsyncPbFunc` via an `async` wrapper so they can participate in async pipelines without blocking.

### Operator Overloading
- `|` still composes operators. When combining async with sync:
  - Promote synchronous `Pb` objects to `AsyncPb` via a lightweight adapter that wraps `__rrshift__` in an async function (e.g., `async def __rrshift__(data): return sync_operator.__rrshift__(data)`).
  - Preserve reference semantics so the operator can still be reused in synchronous contexts.
- `>` remains the threading operator:
  - `data > async_pipeline` yields a coroutine object; users must `await` it (`result = await (data > pipeline)`).
  - Chaining remains left-associative, and partial pipelines can still be assigned to variables.

### Partial Application & Composition
- Partial application simply stores args/kwargs, identical to the sync version.
- Because the async types mirror the API, doc examples and mental models stay aligned.

### Error Handling
- Downstream errors raise within the coroutine, making them naturally awaitable exceptions.
- Type hints can distinguish `AsyncPbFunc` returning `Awaitable[T]` from synchronous ones, aiding static analysis.

### Pros
- Clear separation of synchronous and asynchronous semantics.
- Predictable operator behaviour; no hidden or implicit awaiting.
- Facilitates hybrid pipelines by explicit promotion rather than magical detection.

### Cons
- Slightly more surface area (additional classes/decorators).
- Users must remember to `await` pipeline execution explicitly.
- Need to document the promotion rules when mixing sync and async operators.

## Recommendation
Build a parallel async pipeline stack and introduce an explicit `apb` decorator for async composition. This keeps the synchronous API stable, provides explicit async semantics, and leverages the same operator syntax without overloading meaning. Automatic detection of awaitables should be avoided to prevent unintended consumption of coroutine objects and to keep operator behaviour transparent.

## Next Steps
1. Prototype `AsyncPb`, `AsyncPbFunc`, and `AsyncPbPair` mirroring the synchronous implementations.
2. Implement the `apb` decorator, including adaptation logic for synchronous callables used in async pipelines.
3. Update documentation and tests to cover async usage patterns (`await (value > pipeline)`).
4. Evaluate typing strategy (PEP 484/PEP 544) to expose awaitable return types for async pipelines.
