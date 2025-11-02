from __future__ import annotations

import functools
from abc import ABC, abstractmethod
from typing import Any


class Pb(ABC):
    """
    Abstract base class for plumbum pipe operations.

    Pb defines the core interface for threading data through function calls using
    pipe operators. It provides a clear distinction between data and operators,
    allowing operators to be composed and assigned without execution.

    The primary operators are:
    - `|` (pipe): Combines operators into a pipeline (creates PbPair)
    - `>>` (thread): Threads data through the pipeline
    """

    def __or__(self, other: "Pb | Any") -> "Pb":
        return PbPair(self, other)

    def __ror__(self, other: "Pb | Any") -> "Pb":
        return PbPair(other, self)

    def __call__(self, value: Any) -> Any:
        return value >> self

    @abstractmethod
    def __rrshift__(self, data: Any) -> Any: ...


class PbPair(Pb):
    def __init__(self, left: Pb | Any, right: Pb | Any) -> None:
        self.left = left if isinstance(left, Pb) else PbFunc(left)
        self.right = right if isinstance(right, Pb) else PbFunc(right)

    def __rrshift__(self, data: Any) -> Any:
        return self.right.__rrshift__(self.left.__rrshift__(data))

    def __repr__(self) -> str:
        return "<%s> | <%s>" % (repr(self.left), repr(self.right))


class PbFunc(Pb):
    def __init__(self, function, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.function = function
        functools.update_wrapper(self, function)

    def partial(self, *args, **kwargs):
        return PbFunc(
            self.function,
            *self.args,
            *args,
            **self.kwargs,
            **kwargs,
        )

    def __rrshift__(self, data: Any) -> Any:
        return self.function(data, *self.args, **self.kwargs)

    def __repr__(self) -> str:
        return "<%s>(*%s, **%s)" % (
            self.function.__name__,
            self.args,
            self.kwargs,
        )


def pb(function):
    return PbFunc(function)


__all__ = ["Pb", "PbFunc", "PbPair", "pb"]
