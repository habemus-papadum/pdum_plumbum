from __future__ import annotations

from pdum.plumbum import pb
from pdum.plumbum.iterops import select, where


def test_iterops_select_example():
    double_values = select(lambda value: value * 2)
    assert list([1, 2, 3] >> double_values) == [2, 4, 6]


def test_iterops_where_example():
    only_evens = where(lambda value: value % 2 == 0)
    assert list([1, 2, 3, 4, 5] >> only_evens) == [2, 4]


def test_iterops_combination_example():
    normalize = select(lambda value: value + 1) | where(lambda value: value % 2 == 0)
    assert list([1, 2, 3, 4] >> normalize) == [2, 4]


def test_iterops_to_function_example():
    @pb
    def add_one(value: int) -> int:
        return value + 1

    @pb
    def mul_two(value: int) -> int:
        return value * 2

    combine = select(add_one | mul_two) | where(lambda value: value % 2 == 0)
    assert list([1, 2, 3, 4] >> combine) == [4, 6, 8, 10]
