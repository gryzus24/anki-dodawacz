from __future__ import annotations

import curses
import shutil
from subprocess import Popen, DEVNULL, PIPE
from typing import Any

import src.Curses.env as env
from src.data import WINDOWS, LINUX

# Pythons < 3.10 and ncurses < 6 do not
# define BUTTON5_PRESSED. (mouse wheel down)
BUTTON5_PRESSED = 2097152

# Unfortunately Python's readline API does not expose functions and variables
# responsible for signal handling, which makes it impossible to reconcile
# curses' signal handling with the readline's one.
# We have to manage env.COLS and env.LINES variables ourselves.

if LINUX:
    def get_key(win: curses._CursesWindow) -> int:
        c = win.getch()
        return 410 if c == -1 else c  # 410: KEY_RESIZE  (546 on Windows?)
else:
    def get_key(win: curses._CursesWindow) -> int:
        return win.getch()


if WINDOWS:
    def _selection_command() -> tuple[str, ...] | None:
        powershell = shutil.which('powershell.exe')
        if powershell is not None:
            return powershell, '-Command', 'Get-Clipboard'
        return None

    # We cannot rely on shutil.get_terminal_size to update
    # env.LINES and env.COLS on Windows and as we don't have readline
    # problems here (it's not imported) we can rely on curses.
    def update_global_lines_cols() -> None:
        curses.update_lines_cols()
        env.LINES, env.COLS = curses.LINES, curses.COLS
else:
    def _selection_command() -> tuple[str, ...] | None:
        xsel = shutil.which('xsel')
        if xsel is not None:
            return xsel, '-p'
        xclip = shutil.which('xclip')
        if xclip is not None:
            return xclip, '-o'
        return None

    def update_global_lines_cols() -> None:
        env.COLS, env.LINES = shutil.get_terminal_size()


def terminal_resize() -> None:
    update_global_lines_cols()
    # prevents malloc() errors from ncurses on 32-bit binaries.
    if env.COLS < 2:
        return
    curses.resize_term(env.LINES, env.COLS)


###############################################################################


_cmd = None
def clipboard_or_selection() -> str:
    global _cmd
    if _cmd is None:
        _cmd = _selection_command()
        if _cmd is None:
            raise LookupError(
                'Error reason unknown' if WINDOWS else
                'Install xsel or xclip and try again'
            )

    with Popen(_cmd, stdout=PIPE, stderr=DEVNULL, encoding='UTF-8') as p:
        stdout, _ = p.communicate()

    stdout = stdout.strip()
    if stdout:
        return stdout

    raise ValueError(
        f'{"Clipboard" if WINDOWS else "Primary selection"} is empty'
    )


def mouse_wheel_clicked(bstate: int) -> bool:
    # Not sure what's the difference between PRESSED and CLICKED
    # clicking the mouse wheel reports PRESSED, but clicking the
    # "middle mouse" on a laptop reports CLICKED.
    return bool(
        bstate & curses.BUTTON2_PRESSED or
        bstate & curses.BUTTON2_CLICKED
    )


def truncate_if_needed(s: str, n: int, *, fromleft: bool = False) -> str | None:
    if len(s) <= n:
        return s
    if n <= 2:
        return None
    if fromleft:
        return '..' + s[2-n:]
    else:
        return s[:n-2] + '..'


class new_stdscr:
    def __init__(self) -> None:
        self.stdscr = curses.initscr()

    def __enter__(self) -> curses._CursesWindow:
        curses.cbreak()
        curses.noecho()

        self.stdscr.keypad(True)

        return self.stdscr

    def __exit__(self, *_: Any) -> None:
        # Clear the whole window to prevent a flash
        # of contents from the previous drawing.
        self.stdscr.erase()
        curses.endwin()


def hide_cursor() -> None:
    try:
        curses.curs_set(0)
    except curses.error:  # not supported by the terminal
        pass


def show_cursor() -> None:
    curses.curs_set(1)

