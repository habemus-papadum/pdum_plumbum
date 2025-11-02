"""A plumbing syntax for Python"""

from . import aiterops as _aiterops_module
from . import iterops as _iterops_module
from .aiterops import AsyncMapper, AsyncPredicate, aiter, aselect, async_iter_operator, awhere
from .async_pipeline import AsyncPb, AsyncPbFunc, AsyncPbPair, apb, ensure_async_pb
from .core import Pb, PbFunc, PbPair, pb
from .iterops import select, where

__version__ = "0.4.0-alpha"

# Re-export module objects for convenience
iterops = _iterops_module
aiterops = _aiterops_module

__all__ = [
    "__version__",
    "Pb",
    "PbFunc",
    "PbPair",
    "pb",
    "AsyncPb",
    "AsyncPbFunc",
    "AsyncPbPair",
    "apb",
    "ensure_async_pb",
    "iterops",
    "select",
    "where",
    "aiterops",
    "aiter",
    "aselect",
    "awhere",
    "AsyncMapper",
    "AsyncPredicate",
    "async_iter_operator",
]
