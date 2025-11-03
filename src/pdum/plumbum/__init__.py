"""A plumbing syntax for Python"""

from . import aiterops as _aiterops_module
from . import iterops as _iterops_module
from . import jq as _jq_module
from .aiterops import (
    AsyncMapper,
    AsyncPredicate,
    abatched,
    achain,
    achain_with,
    adedup,
    aenumerate,
    afilter,
    agroupby,
    aislice,
    aiter,
    aizip,
    amap,
    anetcat,
    apermutations,
    areverse,
    aselect,
    askip,
    askip_while,
    asort,
    async_iter_operator,
    at,
    atail,
    atake,
    atake_while,
    atee,
    atranspose,
    atraverse,
    auniq,
    awhere,
)
from .async_pipeline import AsyncPb, AsyncPbFunc, AsyncPbPair, apb, ensure_async_pb
from .core import Pb, PbFunc, PbPair, pb
from .iterops import (
    batched,
    chain,
    chain_with,
    dedup,
    groupby,
    islice,
    izip,
    netcat,
    permutations,
    reverse,
    select,
    skip,
    skip_while,
    sort,
    t,
    tail,
    take,
    take_while,
    tee,
    transpose,
    traverse,
    uniq,
    where,
)
from .iterops import (
    enumerate as iter_enumerate,
)
from .iterops import (
    filter as iter_filter,
)
from .iterops import (
    map as iter_map,
)

__version__ = "0.6.0"

# Re-export module objects for convenience
iterops = _iterops_module
aiterops = _aiterops_module
jq = _jq_module

# Re-export sync iterable operators with convenient aliases
enumerate = iter_enumerate
map = iter_map
filter = iter_filter

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
    "take",
    "tail",
    "skip",
    "dedup",
    "uniq",
    "permutations",
    "netcat",
    "traverse",
    "tee",
    "select",
    "where",
    "take_while",
    "skip_while",
    "groupby",
    "sort",
    "reverse",
    "t",
    "transpose",
    "batched",
    "enumerate",
    "map",
    "filter",
    "chain",
    "chain_with",
    "islice",
    "izip",
    "aiterops",
    "aiter",
    "aselect",
    "awhere",
    "atake",
    "askip",
    "atake_while",
    "askip_while",
    "adedup",
    "auniq",
    "apermutations",
    "atail",
    "asort",
    "areverse",
    "at",
    "atranspose",
    "abatched",
    "atee",
    "atraverse",
    "agroupby",
    "achain",
    "achain_with",
    "aislice",
    "aizip",
    "anetcat",
    "aenumerate",
    "amap",
    "afilter",
    "AsyncMapper",
    "AsyncPredicate",
    "async_iter_operator",
    "jq",
]
