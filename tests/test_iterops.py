from __future__ import annotations

from collections import deque
from itertools import groupby as itertools_groupby

import pytest

from pdum.plumbum.iterops import (
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
from pdum.plumbum.iterops import (
    enumerate as iter_enumerate,
)
from pdum.plumbum.iterops import (
    filter as iter_filter,  # noqa: F401
)
from pdum.plumbum.iterops import (
    map as iter_map,  # noqa: F401
)


def test_select_and_where_pipeline():
    pipeline = select(lambda value: value + 1) | where(lambda value: value % 2 == 0)
    assert list([1, 2, 3, 4] > pipeline) == [2, 4]


def test_take_returns_limited_items():
    assert list(range(5) > take(3)) == [0, 1, 2]


def test_tail_returns_deque_with_last_items():
    result = [1, 2, 3, 4, 5] > tail(2)
    assert isinstance(result, deque)
    assert list(result) == [4, 5]


def test_skip_skips_requested_items():
    assert list([1, 2, 3, 4] > skip(2)) == [3, 4]


def test_dedup_removes_duplicates():
    assert list([1, 1, 2, 2, 3] > dedup()) == [1, 2, 3]


def test_uniq_removes_consecutive_duplicates():
    assert list([1, 1, 2, 1, 1, 3] > uniq()) == [1, 2, 1, 3]


def test_uniq_handles_empty_iterable():
    assert list([] > uniq()) == []


def test_permutations_generates_expected_sequences():
    items = ["a", "b"]
    assert list(items > permutations()) == [("a", "b"), ("b", "a")]


def test_traverse_flattens_nested_iterables():
    nested = [1, [2, [3, 4]], 5]
    assert list(nested > traverse) == [1, 2, 3, 4, 5]


def test_tee_prints_items(capsys):
    result = list([1, 2] > tee)
    captured = capsys.readouterr().out.splitlines()
    assert result == [1, 2]
    assert captured == ["1", "2"]


def test_take_while_stops_when_predicate_false():
    assert list([1, 2, 3, 1] > take_while(lambda value: value < 3)) == [1, 2]


def test_skip_while_skips_until_predicate_false():
    assert list([1, 2, 3, 1] > skip_while(lambda value: value < 3)) == [3, 1]


def test_groupby_matches_itertools_output():
    items = ["apple", "apricot", "banana"]
    expected = [(key, list(group)) for key, group in itertools_groupby(sorted(items), key=lambda word: word[0])]
    result = [(key, list(group)) for key, group in (items > groupby(lambda word: word[0]))]
    assert result == expected


def test_sort_returns_sorted_list():
    assert ([3, 1, 2] > sort()) == [1, 2, 3]


def test_reverse_yields_items_in_reverse_order():
    assert list([1, 2, 3] > reverse) == [3, 2, 1]


def test_t_appends_value_to_iterable():
    assert ([1, 2] > t(3)) == [1, 2, 3]


def test_transpose_swaps_rows_and_columns():
    assert ([[1, 2], [3, 4]] > transpose) == [(1, 3), (2, 4)]


def test_batched_yields_batches():
    assert list(range(5) > batched(2)) == [(0, 1), (2, 3), (4,)]


def test_map_alias_behaves_like_select():
    assert list([1, 2] > iter_map(lambda value: value + 1)) == [2, 3]


def test_filter_alias_behaves_like_where():
    assert list([1, 2, 3] > iter_filter(lambda value: value > 1)) == [2, 3]


def test_enumerate_wraps_builtin():
    assert list(["a", "b"] > iter_enumerate()) == [(0, "a"), (1, "b")]


def test_chain_flattens_iterables():
    assert list([[1, 2], [3]] > chain) == [1, 2, 3]


def test_chain_with_combines_iterables():
    assert list([1, 2] > chain_with([3, 4])) == [1, 2, 3, 4]


def test_islice_limits_output():
    assert list(range(5) > islice(1, 4)) == [1, 2, 3]


def test_izip_combines_iterables():
    assert list([1, 2] > izip(["a", "b"])) == [(1, "a"), (2, "b")]


def test_netcat_round_trip():
    import socket
    import threading

    received = []

    def server(sock):
        conn, _ = sock.accept()
        with conn:
            while data := conn.recv(4096):
                received.append(data)
                conn.sendall(data.upper())

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.bind(("localhost", 0))
        server_sock.listen(1)
        host, port = server_sock.getsockname()
        thread = threading.Thread(target=server, args=(server_sock,), daemon=True)
        thread.start()
        responses = list([b"hello", b"world"] > netcat(host, port))

    assert b"".join(received) == b"helloworld"
    assert b"".join(responses) == b"HELLOWORLD"


def test_batched_requires_positive_size():
    with pytest.raises(ValueError):
        list(range(4) > batched(0))


def test_t_fallback_to_list_for_non_concat():
    result = {1, 2} > t(3)
    assert isinstance(result, list)
    assert result == [{1, 2}, 3]


def test_traverse_handles_scalar():
    assert list(42 > traverse) == [42]


def test_traverse_preserves_strings():
    assert list("ab" > traverse) == ["ab"]
