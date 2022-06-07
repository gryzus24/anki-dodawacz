from __future__ import annotations

import sys
from shutil import get_terminal_size, which
from subprocess import Popen, DEVNULL, PIPE, call
from typing import Any, Callable, NoReturn, Optional

from src.colors import R, Color
from src.data import ON_TERMUX, ON_WINDOWS_CMD, POSIX, USER_AGENT, WINDOWS, config

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
         f'{Color.err}-----------------------------------------------------------------{R}\n'
         'Your version of beautifulsoup is out of date, please update:\n'
         'pip install -U --no-deps beautifulsoup4\n'
         'And while you are at it, kindly, uninstall the soupsieve package:\n'
         'pip uninstall soupsieve\n'
    )
    raise SystemExit
else:
    del __version__

import urllib3
from urllib3.exceptions import ConnectTimeoutError, NewConnectionError

http = urllib3.PoolManager(timeout=10, headers=USER_AGENT)


def handle_connection_exceptions(func: Callable) -> Callable:
    def wrapper(*args: Any, **kwargs: Any) -> NoReturn | Callable | None:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if isinstance(e.__context__, NewConnectionError):
                print(f'{Color.err}Could not establish connection,\n'
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
    # At the moment only WordNet uses other than UTF-8 encoding (iso-8859-1),
    # so as long as there are no decoding problems we'll use UTF-8.
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
            call(('clear',))
    else:
        def _clear_screen() -> None:
            # Even though `clear -x` is slower than directly using ANSI escapes
            # it doesn't have flickering issues, and it's more robust.
            sys.stdout.write('\033[?25l')  # Hide cursor
            sys.stdout.flush()
            call(('clear', '-x'))  # I hope the `-x` option works on macOS.

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


def display_in_less(s: str) -> int:
    executable = which('less')
    if executable is None:
        if WINDOWS:
            print(
                f"'less'{Color.err} is not available in %PATH% or in the current directory.\n"
                f"You can grab the latest Windows executable from:\n"
                f"{R}https://github.com/jftuga/less-Windows/releases"
            )
        else:
            print(f"{Color.err}Could not find the 'less' executable.\n"
                  f"Install 'less' or disable this feature: '-less off'")
        return 1

    # r - accept escape sequences. -R does not produce desirable results on Windows.
    # F - do not open the pager if output fits on the screen.
    # K - exit on SIGINT. *This is important not to break keyboard input.
    # X - do not clear the screen after exiting from the pager.
    if WINDOWS:
        env = {'LESSCHARSET': 'UTF-8'}
        options = '-rFKX'
    else:
        env = None
        options = '-RFKX'
    with Popen((executable, options), stdin=PIPE, stderr=DEVNULL, env=env) as process:
        try:
            process.communicate(s.encode())
        except:
            process.kill()

        # less returns 2 on SIGINT.
        rc = process.poll()
        if rc and rc != 2:
            print(f"{Color.err}Could not open 'less' as: 'less {options}'\n")
            return 1

    return 0


def less_wrapper(func: Callable[..., str]) -> Callable[..., None]:
    def wrapper(*args: Any, **kwargs: Any) -> None:
        string = func(*args, **kwargs)
        if config['-less']:
            with ClearScreen():
                rc = display_in_less(string)
                if rc:
                    sys.stdout.write(string)
        else:
            with ClearScreen():
                sys.stdout.write(string)

    return wrapper


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
