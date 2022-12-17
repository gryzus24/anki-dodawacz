from __future__ import annotations

import sys
from typing import Any, Generator

import src.colors as ansi
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
         f'{ansi.ERR}----------------------------------------------------------------{ansi.R}\n'
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
        url: str, fields: dict[str, str] | None = None, **kw: Any
) -> BeautifulSoup:
    try:
        r = http.request_encode_url('GET', url, fields=fields, **kw)
    except Exception as e:
        if isinstance(e.__context__, NewConnectionError):
            raise ConnectionError(
                f'{ansi.ERR}Could not establish a connection,\n'
                f'check your network connection and try again.'
            )
        elif isinstance(e.__context__, ConnectTimeoutError):
            raise ConnectionError(f'{ansi.ERR}Connection timed out.')
        else:
            raise

    # At the moment only WordNet uses other than UTF-8 encoding (iso-8859-1),
    # so as long as there are no decoding problems we'll use UTF-8.
    return BeautifulSoup(r.data.decode(), 'lxml')


def _regular_wrap(string: str, textwidth: int, gap: int, indent: int) -> list[str]:
    result = []
    line = ''
    current_length = gap
    for word in string.split():
        word_len = len(word)
        if current_length + word_len > textwidth:
            result.append(line.rstrip())
            current_length = gap + indent + word_len + 1
            line = word + ' '
        else:
            line += word + ' '
            current_length += word_len + 1

    result.append(line.rstrip())

    return result


def _justify_wrap(string: str, textwidth: int, gap: int, indent: int) -> list[str]:
    result = []
    line: list[str] = []
    current_length = gap
    for word in string.split():
        word_len = len(word)
        if current_length + word_len >= textwidth:
            nwords = len(line)
            if nwords > 1:
                i = 0
                filling = textwidth - current_length
                # filling shouldn't be negative but just in case.
                while filling > 0:
                    if i > nwords - 2:
                        # go back to the first word
                        i = 0
                    line[i] += ' '
                    filling -= 1
                    i += 1

            result.append(' '.join(line))
            line = []
            current_length = gap + indent

        line.append(word)
        current_length += word_len + 1

    result.append(' '.join(line))

    return result


def _no_wrap(string: str, textwidth: int, gap: int, indent: int) -> list[str]:
    line = string[:textwidth - gap]
    if line.endswith(' '):
        line = line.replace(' ', '  ', 1)

    result = [line.strip()]
    string_ = string[textwidth - gap:].strip()
    while string_:
        llen = textwidth - indent - gap
        line = string_[:llen]
        if line.endswith(' '):
            line = line.replace(' ', '  ', 1)

        result.append(line.strip())
        string_ = string_[llen:].strip()

    return result


def wrap_stream(textwidth: int, string: str, gap: int, indent: int) -> Generator[str | None, None, None]:
    current_length = gap
    for word in string.split():
        if current_length + len(word) > textwidth:
            yield None
            yield word
            current_length = gap + indent + len(word) + 1
        else:
            yield word + ' '
            current_length += len(word) + 1


def wrap_lines(style: str, textwidth: int, s: str, gap: int, indent: int) -> list[str]:
    # gap: space left for characters before the start of the
    #        first line and indent for the subsequent lines.
    # indent: additional indent for the remaining lines.
    # This comment is wrapped with `gap=5, indent=2`.

    if len(s) <= textwidth - gap:
        return [s]

    if style == 'regular':
        wrapped = _regular_wrap(s, textwidth, gap, indent)
    elif style == 'justify':
        wrapped = _justify_wrap(s, textwidth, gap, indent)
    else:
        wrapped = _no_wrap(s, textwidth, gap, indent)

    for i in range(1, len(wrapped)):
        wrapped[i] = (indent * ' ') + wrapped[i]

    return wrapped

