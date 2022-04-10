# Copyright 2021-2022 Gryzus
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

import subprocess
import sys
from shutil import get_terminal_size
from typing import Any, Callable, NoReturn, Optional

import urllib3
from urllib3.exceptions import ConnectTimeoutError, NewConnectionError

from src.colors import Color
from src.data import ON_WINDOWS_CMD, ON_TERMUX, POSIX, USER_AGENT, WINDOWS

# Silence warnings if soupsieve is not installed, which is good
# because its bloated `css parse` slows down import time a lot.
# ~70ms on my desktop and ~200ms on an android phone.
try:
    sys.stderr = None  # type: ignore
    from bs4 import BeautifulSoup  # type: ignore
finally:
    sys.stderr = sys.__stderr__


PREPOSITIONS = {
    'beyond', 'of', 'outside', 'upon', 'with', 'within',
    'behind', 'from', 'like', 'opposite', 'to', 'under',
    'after', 'against', 'around', 'near', 'over', 'via',
    'among', 'except', 'for', 'out', 'since', 'through',
    'about', 'along', 'beneath', 'underneath', 'unlike',
    'below', 'into', 'on', 'onto', 'past', 'than', 'up',
    'across', 'by', 'despite', 'inside', 'off', 'round',
    'at', 'beside', 'between', 'in', 'towards', 'until',
    'above', 'as', 'before', 'down', 'during', 'without'
}

http = urllib3.PoolManager(timeout=10, headers=USER_AGENT)


def handle_connection_exceptions(func: Callable) -> Callable:
    def wrapper(*args: Any, **kwargs: Any) -> NoReturn | Callable | None:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if isinstance(e.__context__, NewConnectionError):
                print(f'{Color.err}Could not establish a connection,\n'
                      'check your Internet connection and try again.')
                return None
            elif isinstance(e.__context__, ConnectTimeoutError):
                print(f'{Color.err}Connection timed out.')
                return None
            else:
                print(f'{Color.err}An unexpected error occurred in {func.__qualname__}.')
                raise

    return wrapper


@handle_connection_exceptions
def request_soup(
        url: str, fields: Optional[dict[str, str]] = None, **kw: Any
) -> BeautifulSoup:
    r = http.request_encode_url('GET', url, fields=fields, **kw)
    # At the moment only WordNet uses other than utf-8 encoding (iso-8859-1),
    # so as long as there are no decoding problems we'll use utf-8.
    return BeautifulSoup(r.data.decode(), 'lxml')


if WINDOWS:
    # There has to exist a less hacky way of doing `clear -x` on Windows.
    # I'm not sure if it works on terminals other than cmd and WT
    if ON_WINDOWS_CMD:
        def _clear_screen() -> None:
            height = get_terminal_size().lines
            # Move cursor up and down
            sys.stdout.write(height * '\n' + f'\033[{height}A')
            sys.stdout.flush()
    else:
        def _clear_screen() -> None:
            height = get_terminal_size().lines
            # Use Windows ANSI sequence to clear the screen
            sys.stdout.write((height - 1) * '\n' + '\033[2J')
            sys.stdout.flush()

elif POSIX:
    if ON_TERMUX:
        def _clear_screen() -> None:
            sys.stdout.write('\033[?25l')  # Hide cursor
            sys.stdout.flush()
            # Termux's terminal dimensions depend on the on-screen keyboard size
            # Termux can't correctly preserve the buffer, so we'll do full clear.
            subprocess.call(('clear',))
    else:
        def _clear_screen() -> None:
            # Even though `clear -x` is slower than directly using ANSI escapes
            # it doesn't have flickering issues, and it's more robust.
            sys.stdout.write('\033[?25l')  # Hide cursor
            sys.stdout.flush()
            subprocess.call(('clear', '-x'))  # I hope the `-x` option works on macOS.

else:
    def _clear_screen() -> None:
        pass


class ClearScreen:
    def __enter__(self) -> None:
        _clear_screen()

    if POSIX:
        def __exit__(self, tp: Any, v: Any, tb: Any) -> None:
            sys.stdout.write('\033[?25h')  # Show cursor
            sys.stdout.flush()
    else:
        def __exit__(self, tp: Any, v: Any, tb: Any) -> None:
            pass


def hide(
        target: str,
        r: str,
        hide_with: str = '...', *,
        hide_prepositions: bool = False,
        keep_endings: bool = True
) -> str:
    # Hide every occurrence of words from string `r` in `target`.
    def case_replace(a: str, b: str) -> None:
        nonlocal target
        target = target.replace(a, b).replace(a.capitalize(), b).replace(a.upper(), b.upper())

    nonoes = {
        'the', 'and', 'a', 'is', 'an', 'it',
        'or', 'be', 'do', 'does', 'not', 'if', 'he'
    }

    elements_to_replace = r.lower().split()
    for elem in elements_to_replace:
        if elem in nonoes:
            continue

        if not hide_prepositions:
            if elem in PREPOSITIONS:
                continue

        # "Ω" is a placeholder
        case_replace(elem, f"{hide_with}Ω")
        if elem.endswith('e'):
            case_replace(elem[:-1] + 'ing', f'{hide_with}Ωing')
            if elem.endswith('ie'):
                case_replace(elem[:-2] + 'ying', f'{hide_with}Ωying')
        elif elem.endswith('y'):
            case_replace(elem[:-1] + 'ies', f'{hide_with}Ωies')
            case_replace(elem[:-1] + 'ied', f'{hide_with}Ωied')

    if keep_endings:
        return target.replace('Ω', '')
    else:
        # e.g. from "We weren't ...Ωed for this." -> "We weren't ... for this."
        split_content = target.split('Ω')
        temp = [split_content[0].strip()]
        for elem in split_content[1:]:
            for letter in elem:
                if letter in (' ', '.', ':'):
                    break
                elem = elem.replace(letter, '', 1)
            temp.append(elem.strip())
        return ' '.join(temp)


def wrap_lines(
        string: str, style: str, textwidth: int, gap: int, indent: int
) -> list[str]:
    # gap: space left for characters before the start of the
    #        first line and indent for the subsequent lines.
    # indent: additional indent for the remaining lines.
    # This comment is wrapped with `gap=5, indent=2`.

    def _indent_and_connect(_lines: list[str]) -> list[str]:
        for i in range(1, len(_lines)):
            _lines[i] = (gap + indent) * ' ' + _lines[i]
        return _lines

    def no_wrap() -> list[str]:
        line = string[:textwidth - gap]
        if line.endswith(' '):
            line = line.replace(' ', '  ', 1)

        lines = [line.strip()]
        string_ = string[textwidth - gap:].strip()
        while string_:
            llen = textwidth - indent - gap
            line = string_[:llen]
            if line.endswith(' '):
                line = line.replace(' ', '  ', 1)

            lines.append(line.strip())
            string_ = string_[llen:].strip()
        return _indent_and_connect(lines)

    def trivial_wrap() -> list[str]:
        lines = []
        line: list[str] = []
        current_llen = gap
        for word in string.split():
            # >= for one character right-side padding
            word_len = len(word)
            if current_llen + word_len >= textwidth:
                lines.append(' '.join(line))
                current_llen = gap + indent
                line = []

            line.append(word)
            current_llen += word_len + 1

        lines.append(' '.join(line))
        return _indent_and_connect(lines)

    def justification_wrap() -> list[str]:
        lines = []
        line: list[str] = []
        current_llen = gap
        for word in string.split():
            word_len = len(word)
            if current_llen + word_len >= textwidth:
                nwords = len(line)
                if nwords > 1:
                    i = 0
                    filling = textwidth - current_llen
                    # filling shouldn't be negative but just in case.
                    while filling > 0:
                        if i > nwords - 2:
                            # go back to the first word
                            i = 0
                        line[i] += ' '
                        filling -= 1
                        i += 1

                lines.append(' '.join(line))
                line = []
                current_llen = gap + indent

            line.append(word)
            current_llen += word_len + 1

        lines.append(' '.join(line))
        return _indent_and_connect(lines)

    # Gap is the gap between indexes and strings
    if len(string) <= textwidth - gap:
        return [string]

    if style == 'regular':
        textwidth += 1
        return trivial_wrap()
    elif style == 'justify':
        return justification_wrap()
    return no_wrap()


def wrap_and_pad(style: str, textwidth: int) -> Callable[[str, int, int], tuple[str, list[str]]]:
    # Wraps and adds right side padding that matches `textwidth`.

    def call(lines: str, gap: int, indent: int) -> tuple[str, list[str]]:
        fl, *rest = wrap_lines(lines, style, textwidth, gap, indent)
        first_line = fl + (textwidth - len(fl) - gap) * ' '
        rest = [line + (textwidth - len(line)) * ' ' for line in rest]
        return first_line, rest

    return call


def get_width_per_column(width: int, columns: int) -> tuple[int, int]:
    if columns < 1:
        return width, 0

    column_width = width // columns
    remainder = width % columns
    if remainder < columns - 1:
        return column_width - 1, remainder + 1
    return column_width, 0
