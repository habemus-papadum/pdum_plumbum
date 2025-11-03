from __future__ import annotations

import functools
from abc import ABC, abstractmethod
from typing import Any, Callable


class Pb(ABC):
    """
    Abstract base class for plumbum pipe operations.

    Pb defines the core interface for threading data through function calls using
    pipe operators. It provides a clear distinction between data and operators,
    allowing operators to be composed and assigned without execution.

    The primary operators are:
    - `|` (pipe): Combines operators into a pipeline (creates PbPair)
    - `>` (thread): Threads data through the pipeline

    Coercing an operator or pipeline into a plain callable can be done explicitly
    via :meth:`Pb.to_function`:

    >>> pipeline = add_one | mul_two
    >>> as_function = pipeline.to_function()
    >>> as_function(10)
    22

    This form mirrors ``Pb.to_function`` but fits naturally into pipeline
    expressions, enabling constructs like ``select((add_one | double).to_function())``
    to embed synchronous pipelines inside iterable operators.
    """

    operator_kind = "sync"

    def __lt__(self, other: Any) -> Any:
        setattr(self, "_last_right_comparison", other)
        return self.__rgt__(other)

    def __gt__(self, other: Any) -> Any:
        message = self._format_gt_chain_error(other)
        setattr(self, "_last_right_comparison", None)
        raise TypeError(message)

    def __rgt__(self, data: Any) -> Any:
        return self._thread(data)

    def __or__(self, other: "Pb | Any") -> "Pb":
        from .async_pipeline import AsyncPb, AsyncPbPair, ensure_async_pb

        if isinstance(other, AsyncPb):
            return AsyncPbPair(ensure_async_pb(self), other)
        return PbPair(self, other)

    def __ror__(self, other: "Pb | Any") -> "Pb":
        from .async_pipeline import AsyncPb, AsyncPbPair, ensure_async_pb

        if isinstance(other, AsyncPb):
            return AsyncPbPair(other, ensure_async_pb(self))
        return PbPair(other, self)

    def __rrshift__(self, data: Any) -> Any:
        raise TypeError("The '>>' threading operator has been removed. Use 'value > operator' instead.")

    @abstractmethod
    def _thread(self, data: Any) -> Any: ...

    def to_function(self) -> Callable[[Any], Any]:
        def _call(value: Any) -> Any:
            return value > self

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
            "Wrap the first comparison in parentheses—e.g. '(value > operator) > next'."
        )


class PbPair(Pb):
    def __init__(self, left: Pb | Any, right: Pb | Any) -> None:
        self.left = left if isinstance(left, Pb) else PbFunc(left)
        self.right = right if isinstance(right, Pb) else PbFunc(right)

    def _thread(self, data: Any) -> Any:
        return self.right._thread(self.left._thread(data))

    def __repr__(self) -> str:
        return "<%s> | <%s>" % (repr(self.left), repr(self.right))


class PbFunc(Pb):
    def __init__(self, function, *args, **kwargs):
        self.args = tuple(self._normalize(value) for value in args)
        self.kwargs = {key: self._normalize(value) for key, value in kwargs.items()}
        self.function = function
        functools.update_wrapper(self, function)

    def __call__(self, *args, **kwargs):
        return PbFunc(
            self.function,
            *self.args,
            *args,
            **self.kwargs,
            **kwargs,
        )

    def _thread(self, data: Any) -> Any:
        return self.function(data, *self.args, **self.kwargs)

    def __repr__(self) -> str:
        return "<%s>(*%s, **%s)" % (
            self.function.__name__,
            self.args,
            self.kwargs,
        )

    @staticmethod
    def _normalize(value: Any) -> Any:
        if isinstance(value, Pb):
            return value.to_function()
        return value


def pb(function):
    return PbFunc(function)


__all__ = ["Pb", "PbFunc", "PbPair", "pb"]
