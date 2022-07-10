from __future__ import annotations

import sys
from typing import Any, Callable, Optional, NoReturn

from src.colors import R, Color
from src.data import USER_AGENT

# Silence warnings if soupsieve is not installed, which is good
# because its bloated "css parse" slows down import time a lot.
# ~70ms on my desktop and ~200ms on an android phone.
# bs4 itself compiles regexes on startup which slows it down by
# another 40-150ms. And guess what? Those regexes are useless.
try:
    sys.stderr = None  # type: ignore[assignment]
    from bs4 import BeautifulSoup, __version__  # type: ignore[import]
finally:
    sys.stderr = sys.__stderr__

if (*map(int, __version__.split('.')),) < (4, 10, 0):
    sys.stderr.write(
         f'{Color.err}----------------------------------------------------------------{R}\n'
         'Your version of beautifulsoup is out of date, please update:\n'
         'pip install -U beautifulsoup4\n'
         'If you are using a virtual environment, you can safely uninstall\n'
         'the soupsieve package to slightly speed up program startup:\n'
         'pip uninstall soupsieve\n'
    )
    raise SystemExit
else:
    del __version__

import urllib3
from urllib3.exceptions import ConnectTimeoutError, NewConnectionError

http = urllib3.PoolManager(timeout=10, headers=USER_AGENT)


def request_soup(
        url: str, fields: Optional[dict[str, str]] = None, **kw: Any
) -> BeautifulSoup | NoReturn:
    try:
        r = http.request_encode_url('GET', url, fields=fields, **kw)
    except Exception as e:
        if isinstance(e.__context__, NewConnectionError):
            raise ConnectionError(
                f'{Color.err}Could not establish a connection,\n'
                f'check your network connection and try again.'
            )
        elif isinstance(e.__context__, ConnectTimeoutError):
            raise ConnectionError(f'{Color.err}Connection timed out.')
        else:
            raise

    # At the moment only WordNet uses other than UTF-8 encoding (iso-8859-1),
    # so as long as there are no decoding problems we'll use UTF-8.
    return BeautifulSoup(r.data.decode(), 'lxml')


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
