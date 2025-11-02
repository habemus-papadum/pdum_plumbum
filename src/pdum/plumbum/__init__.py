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
    ensure_async_pb,
    wrap_sync_as_async,
)
from .core import Pb, PbFunc, PbPair, pb

__version__ = "0.1.0-alpha"

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
    "wrap_sync_as_async",
    "AsyncIterPb",
    "AsyncIterPbFunc",
    "AsyncIterPbPair",
    "aipb",
    "ensure_async_iter_pb",
    "to_async_iter",
    "iterops",
    "aiterops",
]
