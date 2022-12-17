from __future__ import annotations

import curses

from typing import NamedTuple
from src.data import config

# Custom color pairs.
BLACK_ON_GREEN = 31
BLACK_ON_RED = 32
BLACK_ON_YELLOW = 33


COLOR_NAME_TO_COLOR = {
    'black': 0,
    'blue': 1,
    'green': 2,
    'cyan': 3,
    'red': 4,
    'magenta': 5,
    'yellow': 6, 'brown': 6,
    'lightgray': 7, 'lightgrey': 7,
    'gray': 8, 'grey': 8,
    'lightblue': 9,
    'lightgreen': 10,
    'lightcyan': 11,
    'lightred': 12,
    'lightmagenta': 13,
    'lightyellow': 14,
    'white': 15, 'lightwhite': 15,
}

class _Color(NamedTuple):
    def1: int
    def2: int
    delimit: int
    err: int
    etym: int
    exsen: int
    heed: int
    index: int
    inflection: int
    label: int
    phon: int
    phrase: int
    pos: int
    sign: int
    success: int
    syn: int
    syngloss: int


def _set_color(colorname: str) -> int:
    return curses.color_pair(COLOR_NAME_TO_COLOR.get(config['color'][colorname], 0))


Color = None

def init_colors() -> None:
    global Color

    try:
        curses.start_color()
    except curses.error:  # some internal table cannot be allocated?
        pass
    try:
        curses.use_default_colors()
    except curses.error:  # not supported
        pass

    Color = _Color(
        _set_color('def1'),
        _set_color('def2'),
        _set_color('delimit'),
        _set_color('err'),
        _set_color('etym'),
        _set_color('exsen'),
        _set_color('heed'),
        _set_color('index'),
        _set_color('inflection'),
        _set_color('label'),
        _set_color('phon'),
        _set_color('phrase'),
        _set_color('pos'),
        _set_color('sign'),
        _set_color('success'),
        _set_color('syn'),
        _set_color('syngloss'),
    )

    ncolors = curses.COLORS
    if ncolors < 8:
        return

    for i in range(8 if ncolors == 8 else 16):
        curses.init_pair(i, i, -1)

    curses.init_pair(BLACK_ON_GREEN, curses.COLOR_GREEN, -1)
    curses.init_pair(BLACK_ON_RED, curses.COLOR_RED, -1)
    curses.init_pair(BLACK_ON_YELLOW, curses.COLOR_YELLOW, -1)
