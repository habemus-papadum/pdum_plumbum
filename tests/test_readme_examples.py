from __future__ import annotations

from functools import partial

import pytest

from pdum.plumbum import pb


@pb
def add(x, n):
    return x + n


@pb
def multiply(x, n):
    return x * n


@pb
def power(x, n):
    return x**n


@pb
def format_number(value, prefix: str = "Result:", decimals: int = 2) -> str:
    return f"{prefix} {value:.{decimals}f}"


@pb
def greet(name: str, greeting: str = "Hello", punctuation: str = "!") -> str:
    return f"{greeting}, {name}{punctuation}"


@pb
def add_three(x, a, b, c):
    return x + a + b + c


@pb
def strip(text: str) -> str:
    return text.strip()


@pb
def uppercase(text: str) -> str:
    return text.upper()


@pb
def replace(text: str, old: str, new: str) -> str:
    return text.replace(old, new)


@pb
def filter_positive(numbers):
    for number in numbers:
        if number > 0:
            yield number


@pb
def square_all(numbers):
    for number in numbers:
        yield number**2


class Point:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Point):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __repr__(self) -> str:
        return f"Point({self.x}, {self.y})"


def test_quick_start_examples():
    assert (5 > add(3)) == 8
    assert (5 > (add(3) | multiply(2))) == 16

    transform = multiply(2) | add(10) | power(2)
    assert (3 > transform) == 256

    double_and_square = multiply(2) | power(2)
    assert (5 > double_and_square) == 100
    assert (10 > double_and_square) == 400


def test_pb_decorator_examples(capsys: pytest.CaptureFixture[str]):
    assert (5 > add(10)) == 15
    assert (3.14159 > format_number(decimals=3)) == "Result: 3.142"

    10 > (add(5) | pb(print))
    captured = capsys.readouterr()
    assert captured.out.strip().endswith("15")


def test_keyword_argument_examples():
    assert ("Alice" > greet(greeting="Hi")) == "Hi, Alice!"
    assert ("Bob" > greet(punctuation=".")) == "Hello, Bob."
    assert ("Charlie" > greet(greeting="Hey", punctuation="!!!")) == "Hey, Charlie!!!"
    assert ("Diana" > greet("Greetings", punctuation="...")) == "Greetings, Diana..."

    formal_greet = greet(greeting="Good day", punctuation=".")
    assert ("Elizabeth" > formal_greet) == "Good day, Elizabeth."


def test_operator_threading_examples():
    pipeline = add(1) | multiply(2) | add(3)
    assert (5 > pipeline) == 15


def test_partial_application_examples():
    op = add_three(1)
    op = op(2)
    op = op(3)
    assert (10 > op) == 16


def test_plain_function_auto_wrapping():
    def plain_increment(x):
        return x + 3

    def plain_add(x, n):
        return x + n

    pipeline = multiply(2) | plain_increment
    assert (5 > pipeline) == 13

    pipeline_with_partial = multiply(2) | partial(plain_add, n=3)
    assert (5 > pipeline_with_partial) == 13


def test_data_type_flexibility_examples():
    assert (5 > (add(3) | multiply(2))) == 16
    assert ("hello" > (pb(str.upper) | pb(lambda s: s + "!"))) == "HELLO!"
    assert ({"a": 1} > pb(lambda d: {**d, "b": 2})) == {"a": 1, "b": 2}

    @pb
    def translate(point: Point, dx: int, dy: int) -> Point:
        return Point(point.x + dx, point.y + dy)

    assert (Point(1, 2) > translate(5, 3)) == Point(6, 5)
    assert ([1, 2, 3] > pb(lambda lst: [x * 2 for x in lst])) == [2, 4, 6]


def test_data_processing_pipeline_examples():
    process = filter_positive | square_all | sum

    assert ([-2, 3, -1, 4, 5] > process) == 50
    assert ([-10, 2, -5, 6] > process) == 40


def test_string_processing_pipeline():
    clean_text = strip() | replace(" ", "_") | uppercase()
    assert ("  hello world  " > clean_text) == "HELLO_WORLD"


def test_chaining_with_builtins_examples(capsys: pytest.CaptureFixture[str]):
    pipeline = pb(str.strip) | pb(str.upper) | pb(print)
    "  test  " > pipeline

    captured = capsys.readouterr()
    assert captured.out.strip().endswith("TEST")
