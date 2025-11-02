import functools
from abc import ABC, abstractmethod
from typing import Any

"""A plumbing syntax for Python"""

__version__ = "0.1.0-alpha"

class Pb(ABC):
    """
    Abstract base class for plumbum pipe operations.

    Pb defines the core interface for threading data through function calls using
    pipe operators. It provides a clear distinction between data and operators,
    allowing operators to be composed and assigned without execution.

    The primary operators are:
    - `|` (pipe): Combines operators into a pipeline (creates PbPair)
    - `>>` (thread): Threads data through the pipeline

    Notes
    -----
    Subclasses must implement the `__rrshift__` method to define how data
    is threaded through the operator.

    Examples
    --------
    >>> @pb
    ... def add(x, n):
    ...     return x + n
    >>> @pb
    ... def multiply(x, n):
    ...     return x * n
    >>> op = add(1) | multiply(2)  # Define operator without executing
    >>> 5 >> op  # Thread data through the pipeline
    12
    """

    def __or__(self, other: "Pb | Any") -> "Pb":
        """
        Combine this operator with another using the pipe operator (|).

        Parameters
        ----------
        other : Pb or callable
            The operator to combine with. If not a Pb instance, it will be
            wrapped in a PbFunc.

        Returns
        -------
        Pb
            A PbPair representing the combined pipeline.

        Examples
        --------
        >>> op1 = add(1)
        >>> op2 = multiply(2)
        >>> combined = op1 | op2
        >>> 5 >> combined
        12
        """
        return PbPair(self, other)

    def __ror__(self, other: "Pb | Any") -> "Pb":
        """
        Combine another operator with this one using the reverse pipe operator.

        This is called when the left operand doesn't support the `|` operator.

        Parameters
        ----------
        other : Pb or callable
            The operator to place before this one in the pipeline.

        Returns
        -------
        Pb
            A PbPair representing the combined pipeline.
        """
        return PbPair(other, self)

    @abstractmethod
    def __rrshift__(self, data: Any) -> Any:
        """
        Thread data through this operator using the >> operator.

        This method must be implemented by subclasses to define how data
        flows through the operator.

        Parameters
        ----------
        data : Any
            The data to thread through the operator.

        Returns
        -------
        Any
            The result of applying the operator to the data.
        """
        pass

class PbPair(Pb):
    """
    Represents a pair of operators combined into a pipeline.

    PbPair is created when two operators are combined using the `|` operator.
    It threads data through the left operator first, then through the right
    operator, creating a sequential pipeline.

    Parameters
    ----------
    left : Pb or callable
        The first operator in the pipeline. If not a Pb instance, it will be
        wrapped in a PbFunc.
    right : Pb or callable
        The second operator in the pipeline. If not a Pb instance, it will be
        wrapped in a PbFunc.

    Attributes
    ----------
    left : Pb
        The first operator in the pipeline.
    right : Pb
        The second operator in the pipeline.

    Examples
    --------
    >>> @pb
    ... def add(x, n):
    ...     return x + n
    >>> @pb
    ... def multiply(x, n):
    ...     return x * n
    >>> pipeline = add(2) | multiply(3)  # Creates a PbPair
    >>> 5 >> pipeline  # (5 + 2) * 3
    21
    """

    def __init__(self, left: Pb | Any, right: Pb | Any):
        self.left = left if isinstance(left, Pb) else PbFunc(left)
        self.right = right if isinstance(right, Pb) else PbFunc(right)

    def __rrshift__(self, data: Any) -> Any:
        """
        Thread data sequentially through both operators.

        The data is first passed through the left operator, and the result
        is then passed through the right operator.

        Parameters
        ----------
        data : Any
            The data to thread through the pipeline.

        Returns
        -------
        Any
            The result after threading through both operators.

        Examples
        --------
        >>> pipeline = add(10) | multiply(2)
        >>> 5 >> pipeline  # (5 + 10) * 2
        30
        """
        return self.right.__rrshift__(self.left.__rrshift__(data))

    def __repr__(self) -> str:
        """
        Return a string representation of the pipeline.

        Returns
        -------
        str
            A string showing the left and right operators connected by |.
        """
        return "<%s> | <%s>" % (repr(self.left), repr(self.right))

class PbFunc(Pb):
    """
    Wraps a function to make it compatible with pipe operations.

    PbFunc represents a function that can be used in plumbum pipelines. When
    created with the @pb decorator or explicitly wrapped, it allows partial
    application of arguments and threading data through the function via the
    >> operator.

    The first parameter of the wrapped function is assumed to be the position
    where threaded data will be inserted.

    Parameters
    ----------
    function : callable
        The function to wrap for pipe operations.
    *args : Any
        Positional arguments to partially apply to the function (after the
        first parameter which receives the threaded data).
    **kwargs : Any
        Keyword arguments to partially apply to the function.

    Attributes
    ----------
    function : callable
        The wrapped function.
    args : tuple
        Partially applied positional arguments.
    kwargs : dict
        Partially applied keyword arguments.

    Examples
    --------
    >>> @pb
    ... def add(x, n):
    ...     return x + n
    >>> add_five = add(5)  # Partially apply argument
    >>> 10 >> add_five  # Thread data through
    15
    >>> 10 >> add(3)  # Can also use directly
    13
    """

    def __init__(self, function, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.function = function
        functools.update_wrapper(self, function)

    def __call__(self, *args, **kwargs):
        """
        Enable partial application by calling the PbFunc with additional arguments.

        This allows building up argument lists incrementally before threading
        data through the function.

        Parameters
        ----------
        *args : Any
            Additional positional arguments to apply.
        **kwargs : Any
            Additional keyword arguments to apply.

        Returns
        -------
        PbFunc
            A new PbFunc with the combined arguments.

        Examples
        --------
        >>> @pb
        ... def add_three(x, a, b, c):
        ...     return x + a + b + c
        >>> op = add_three(1, 2)  # Partial application
        >>> op = op(3)  # Further partial application
        >>> 10 >> op  # 10 + 1 + 2 + 3
        16
        """
        return PbFunc(
            self.function,
            *self.args,
            *args,
            **self.kwargs,
            **kwargs,
        )

    def __rrshift__(self, data: Any) -> Any:
        """
        Thread data through the wrapped function.

        The data is passed as the first argument to the function, followed by
        any partially applied arguments.

        Parameters
        ----------
        data : Any
            The data to thread through the function (becomes first argument).

        Returns
        -------
        Any
            The result of calling the function with the data and partial arguments.

        Examples
        --------
        >>> @pb
        ... def multiply(x, n):
        ...     return x * n
        >>> 5 >> multiply(3)
        15
        """
        return self.function(data, *self.args, **self.kwargs)

    def __repr__(self) -> str:
        """
        Return a string representation of the PbFunc.

        Returns
        -------
        str
            A string showing the function name and partial arguments.
        """
        return "<%s>(*%s, **%s)" % (
            self.function.__name__,
            self.args,
            self.kwargs,
        )


def pb(function):
    """
    Decorator to convert a function into a PbFunc.

    This allows the decorated function to be used in pipe operations.

    Parameters
    ----------
    function : callable
        The function to wrap as a PbFunc.

    Returns
    -------
    PbFunc
        A PbFunc instance wrapping the original function.

    Examples
    --------
    >>> @pb
    ... def add(x, n):
    ...     return x + n
    >>> 5 >> add(3)
    8
    """
    return PbFunc(function)


__all__ = ["__version__", "Pb", "PbFunc", "PbPair", "pb"]

if __name__ == "__main__":
    @pb
    def add(x, n):
        return x + n

    @pb
    def multiply(x, n):
        return x * n

    # Use in pipe operations
    result = 5 >> (add(3) | multiply(2))
    print(result)  # Output: 16

    op = multiply(2) | add(3)
    5 >> op >> pb(print)

    def add3(x):
        return x + 3

    5 >> (multiply(2) | add3) >> pb(print)
