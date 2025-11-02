"""A plumbing syntax for Python"""

from .aiter_pipeline import (
    AsyncIterPb,
    AsyncIterPbFunc,
    AsyncIterPbPair,
    aipb,
    ensure_async_iter_pb,
    to_async_iter,
)
from .async_pipeline import (
    AsyncPb,
    AsyncPbFunc,
    AsyncPbPair,
    apb,
)
from .core import Pb, PbFunc, PbPair, pb, to_f
from .iterops import select, where

__version__ = "0.1.0-alpha"

__all__ = [
    "__version__",
    "Pb",
    "PbFunc",
    "PbPair",
    "pb",
    "to_f",
    "AsyncPb",
    "AsyncPbFunc",
    "AsyncPbPair",
    "apb",
    "AsyncIterPb",
    "AsyncIterPbFunc",
    "AsyncIterPbPair",
    "aipb",
    "ensure_async_iter_pb",
    "to_async_iter",
    "iterops",
    "select",
    "where",
]
