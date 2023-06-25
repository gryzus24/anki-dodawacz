from __future__ import annotations

import contextlib
import curses
from typing import Iterator

import pytest

from src.Curses.prompt import Prompt

stdscr = curses.initscr()


class DummyScreenBuffer:
    def __init__(self, win: curses._CursesWindow) -> None:
        self.win = win

    @contextlib.contextmanager
    def extra_margin(self, n: int) -> Iterator[None]:
        yield

    def draw(self) -> None:
        pass

    def resize(self) -> None:
        pass


def make_test_prompt(pretype: str, cursor_index: int) -> Prompt:
    prompt = Prompt(DummyScreenBuffer(stdscr), 'prompt:', pretype=pretype)
    prompt._cursor = cursor_index
    return prompt


@pytest.mark.parametrize(
    ('pretype', 'cursor_index', 'expected'),
    (
        ('test', 4, 'test'),
        ('test', 0, 'test'),
        ('test', 2, 'test'),
        ('test   ', 0, 'test'),
        ('test   ', 3, 'test'),
        ('test   ', 4, 'test'),
        ('   test', 0, '   test'),
        ('   test', 3, 'test'),
        ('   test', 6, 'test'),
        ('   test    ', 0, '   test    '),
        ('   test    ', 3, 'test'),
        ('   test    ', 6, 'test'),
        ('   test    ', 7, 'test'),
        ('   test    ', 9, 'test'),
        ('   test    ', 10, 'test'),
        ('0123456 test', 0, '0123456'),
        ('0123456 test', 5, '0123456'),
        ('0123456 test', 6, '0123456'),
        ('0123456 test', 7, '0123456'),
        ('0123456 test', 8, 'test'),
        ('0123456 test', 11, 'test'),
        ('01 345 7 9a', 0, '01'),
        ('01 345 7 9a', 1, '01'),
        ('01 345 7 9a', 2, '01'),
        ('01 345 7 9a', 3, '345'),
        ('01 345 7 9a', 4, '345'),
        ('01 345 7 9a', 5, '345'),
        ('01 345 7 9a', 6, '345'),
        ('01 345 7 9a', 7, '7'),
        ('01 345 7 9a', 8, '7'),
        ('01 345 7 9a', 9, '9a'),
        ('01 345 7 9a', 10, '9a'),
        ('01 345 7 9a', 11, '9a'),
        (' 12   678 a ', 0, ' 12   678 a '),
        (' 12   678 a ', 1, '12'),
        (' 12   678 a ', 2, '12'),
        (' 12   678 a ', 3, '12'),
        (' 12   678 a ', 4, ' 12   678 a '),
        (' 12   678 a ', 5, ' 12   678 a '),
        (' 12   678 a ', 6, '678'),
        (' 12   678 a ', 7, '678'),
        (' 12   678 a ', 8, '678'),
        (' 12   678 a ', 9, '678'),
        (' 12   678 a ', 10, 'a'),
        (' 12   678 a ', 11, 'a'),
        (' 12   678 a ', 12, 'a'),
        (' 12  a      ', 12, 'a'),
        ('', 0, ''),
        ('            ', 0, '            '),
        ('            ', 2, '            '),
        ('            ', 13, '            '),
    )
)
def test_ctrl_t(pretype, cursor_index, expected):
    prompt = make_test_prompt(pretype, cursor_index)
    prompt.ctrl_t()
    assert prompt._entered == expected


@pytest.mark.parametrize(
    ('pretype', 'cursor_index', 'expected'),
    (
        ('', 0, 0),
        (' ', 0, 0),
        (' ', 1, 0),
        ('  ', 1, 0),
        ('  ', 2, 0),
        ('      ', 5, 0),
        ('a', 0, 0),
        ('a', 1, 0),
        ('aa', 1, 0),
        ('aa', 2, 0),
        ('aaaaaa', 5, 0),
        ('a a', 1, 0),
        ('a a', 2, 0),
        ('a    a', 0, 0),
        ('a    a', 1, 0),
        ('a    a', 2, 0),
        ('a    a', 3, 0),
        ('a    a', 4, 0),
        ('a    a', 5, 0),
        ('a    a', 6, 5),
        ('foo bar baz', 4, 0),
        ('foo bar baz', 5, 4),
        ('foo bar baz', 6, 4),
        ('foo bar baz', 7, 4),
        ('foo bar baz', 8, 4),
        ('foo bar baz', 9, 8),
        ('foo    barbaz', 7, 0),
        ('foo    barbaz', 8, 7),
        ('foo    barbaz', 9, 7),
        ('foo    barbaz', 12, 7),
        ('foo    barbaz', 13, 7),
        (' foo    barbaz', 4, 1),
        (' foo    barbaz', 3, 1),
        (' foo    barbaz', 1, 0),
        ('   foo    barbaz', 4, 3),
        ('   foo    barbaz', 3, 0),
        ('   foo    barbaz', 2, 0),
    )
)
def test_ctrl_left(pretype, cursor_index, expected):
    prompt = make_test_prompt(pretype, cursor_index)
    prompt.ctrl_left()
    assert prompt._cursor == expected


@pytest.mark.parametrize(
    ('pretype', 'cursor_index', 'expected'),
    (
        ('', 0, 0),
        (' ', 0, 1),
        (' ', 1, 1),
        ('  ', 0, 2),
        ('  ', 1, 2),
        ('  ', 2, 2),
        ('      ', 0, 6),
        ('      ', 1, 6),
        ('a', 0, 1),
        ('a', 1, 1),
        ('aa', 0, 2),
        ('aa', 1, 2),
        ('aa', 2, 2),
        ('aaaaaa', 0, 6),
        ('aaaaaa', 1, 6),
        ('a a', 1, 3),
        ('a a', 2, 3),
        ('a    a', 0, 1),
        ('a    a', 1, 6),
        ('a    a', 2, 6),
        ('a    a', 3, 6),
        ('a    a', 4, 6),
        ('a    a', 5, 6),
        ('a    a', 6, 6),
        ('foo bar baz', 4, 7),
        ('foo bar baz', 5, 7),
        ('foo bar baz', 6, 7),
        ('foo bar baz', 7, 11),
        ('foo bar baz', 8, 11),
        ('foo bar baz', 9, 11),
        ('foobar    baz', 0, 6),
        ('foobar    baz', 1, 6),
        ('foobar    baz', 5, 6),
        ('foobar    baz', 6, 13),
        ('foobar    baz', 7, 13),
        ('foobar    baz', 8, 13),
        ('foobar    baz', 9, 13),
        ('foobar    baz', 10, 13),
        ('foobar    baz', 11, 13),
        ('foobar    baz ', 6, 13),
        ('foobar    baz ', 7, 13),
        ('foobar    baz ', 12, 13),
        ('foobar    baz   ', 12, 13),
        ('foobar    baz   ', 13, 16),
    )
)
def test_ctrl_right(pretype, cursor_index, expected):
    prompt = make_test_prompt(pretype, cursor_index)
    prompt.ctrl_right()
    assert prompt._cursor == expected
