from __future__ import annotations

import curses
import shutil
from subprocess import DEVNULL
from subprocess import PIPE
from subprocess import Popen
from typing import Iterable
from typing import NamedTuple

from src.data import WINDOWS

# Some terminal emulators cause curses to segfault when trying to draw under
# low `curses.COLS` values. Set a global limit and make sure that every
# `draw()` function does not attempt drawing if `curses.COLS` is lower than
# this value.
CURSES_COLS_MIN_VALUE = 4

BORDER_PAD = 1

# Pythons < 3.10 and ncurses < 6 do not
# define BUTTON5_PRESSED. (mouse wheel down)
BUTTON5_PRESSED = 2097152

HIGHLIGHT = curses.A_STANDOUT | curses.A_BOLD

if WINDOWS:
    def _selection_command() -> tuple[str, ...] | None:
        powershell = shutil.which('powershell.exe')
        if powershell is not None:
            return powershell, '-Command', 'Get-Clipboard'
        return None

else:
    def _selection_command() -> tuple[str, ...] | None:
        xsel = shutil.which('xsel')
        if xsel is not None:
            return xsel, '-p'
        xclip = shutil.which('xclip')
        if xclip is not None:
            return xclip, '-o'
        return None


_sel_cmd = None
def clipboard_or_selection() -> str:
    global _sel_cmd
    if _sel_cmd is None:
        _sel_cmd = _selection_command()
        if _sel_cmd is None:
            raise LookupError(
                "Something's wrong (could not find powershell.exe)" if WINDOWS else
                'Install xsel or xclip and try again'
            )

    with Popen(_sel_cmd, stdout=PIPE, stderr=DEVNULL, encoding='UTF-8') as p:
        stdout, _ = p.communicate()

    stdout = stdout.strip()
    if stdout:
        return stdout

    raise ValueError(f'{"Clipboard" if WINDOWS else "Primary selection"} is empty')


_mpv_cmd = None
def play_audio_url(url: str) -> None:
    global _mpv_cmd
    if _mpv_cmd is None:
        _mpv_cmd = shutil.which('mpv')
        if _mpv_cmd is None:
            raise LookupError(
                'Could not find mpv in ' + ('%PATH%' if WINDOWS else '$PATH')
            )

    with Popen(
        (_mpv_cmd,
         '--no-terminal',
         '--force-window=no',
         '--audio-display=no',
         url)
    ) as p:
        rc = p.wait()
        if rc == 2:
            raise ValueError(f'Bad url: {url!r}')
        elif rc:
            raise ValueError(f'Something failed: exit code: {rc}, url: {url!r}')


def draw_border(win: curses._CursesWindow, margin_bot: int) -> None:
    try:
        win.move(curses.LINES - 1 - margin_bot, 0)
    except curses.error:
        return

    win.box()
    while margin_bot:
        win.deleteln()
        margin_bot -= 1


class Attr(NamedTuple):
    i:    int
    span: int
    attr: int


def compose_attrs(
        elements: Iterable[tuple[int, int, int]], *,
        width: int,
        start: int = 0
) -> list[Attr]:
    attrs = []
    index = start
    for span, attr, gap in elements:
        if index + span > width:
            if index < width:
                attrs.append(Attr(index, width - index, attr))
            break
        else:
            attrs.append(Attr(index, span, attr))
            index += span + gap

    return attrs


def mouse_left_click(bstate: int) -> bool:
    return bool(bstate & curses.BUTTON1_PRESSED)


def mouse_right_click(bstate: int) -> bool:
    return bool(bstate & curses.BUTTON3_PRESSED)


def mouse_wheel_click(bstate: int) -> bool:
    # Not sure what's the difference between PRESSED and CLICKED
    # clicking the mouse wheel reports PRESSED, but clicking the
    # "middle mouse" on a laptop reports CLICKED.
    return bool(
        bstate & curses.BUTTON2_PRESSED or
        bstate & curses.BUTTON2_CLICKED
    )


def mouse_wheel_up(bstate: int) -> bool:
    return bool(bstate & curses.BUTTON4_PRESSED)


def mouse_wheel_down(bstate: int) -> bool:
    return bool(bstate & BUTTON5_PRESSED)


def truncate(s: str, n: int, *, fromleft: bool = False) -> str | None:
    if len(s) <= n:
        return s
    if n <= 1:
        return None
    if fromleft:
        return '«' + s[1-n:]
    else:
        return s[:n-1] + '»'


def hide_cursor() -> None:
    try:
        curses.curs_set(0)
    except curses.error:  # not supported by the terminal
        pass


def show_cursor() -> None:
    try:
        curses.curs_set(1)
    except curses.error:  # not supported by the terminal
        pass
