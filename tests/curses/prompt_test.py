import pytest

import curses

from src.curses_main import Prompt

stdscr = curses.initscr()


class DummyScreenBuffer:
    def __init__(self, stdscr):
        self.stdscr = stdscr


def _run_ctrl_t_test(pretype, cursor_index, expected):
    prompt = Prompt(DummyScreenBuffer(stdscr), 'prompt:', pretype=pretype)  # type: ignore[arg-type]
    prompt._cursor = cursor_index
    prompt.ctrl_t()
    assert prompt._entered == expected


@pytest.mark.parametrize(
    ('pretype', 'cursor_index', 'expected'),
    (
        ('test', 4, 'test'),
        ('test', 0, 'test'),
        ('test', 2, 'test'),
    )
)
def test_ctrl_t_one_word(pretype, cursor_index, expected):
    _run_ctrl_t_test(pretype, cursor_index, expected)


@pytest.mark.parametrize(
    ('pretype', 'cursor_index', 'expected'),
    (
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
    )
)
def test_ctrl_t_one_word_and_whitespace(pretype, cursor_index, expected):
    _run_ctrl_t_test(pretype, cursor_index, expected)


@pytest.mark.parametrize(
    ('pretype', 'cursor_index', 'expected'),
    (
        ('0123456 test', 0, '0123456'),
        ('0123456 test', 5, '0123456'),
        ('0123456 test', 6, '0123456'),
        ('0123456 test', 7, '0123456'),
        ('0123456 test', 8, 'test'),
        ('0123456 test', 11, 'test'),
    )
)
def test_ctrl_t_two_words(pretype, cursor_index, expected):
    _run_ctrl_t_test(pretype, cursor_index, expected)


@pytest.mark.parametrize(
    ('pretype', 'cursor_index', 'expected'),
    (
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
    )
)
def test_ctrl_t_multiple_words(pretype, cursor_index, expected):
    _run_ctrl_t_test(pretype, cursor_index, expected)


@pytest.mark.parametrize(
    ('pretype', 'cursor_index', 'expected'),
    (
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
    )
)
def test_ctrl_t_inconsistent_spacing(pretype, cursor_index, expected):
    _run_ctrl_t_test(pretype, cursor_index, expected)


@pytest.mark.parametrize(
    ('pretype', 'cursor_index', 'expected'),
    (
        ('', 0, ''),
        ('            ', 0, '            '),
        ('            ', 2, '            '),
        ('            ', 13, '            '),
    )
)
def test_ctrl_t_no_contents(pretype, cursor_index, expected):
    _run_ctrl_t_test(pretype, cursor_index, expected)

