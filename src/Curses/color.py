from __future__ import annotations

import curses

from src.data import config

COLOR_NAME_TO_COLOR = {
    'black': 0,
    'red': 1,
    'green': 2,
    'yellow': 3, 'orange': 3, 'brown': 3,
    'blue': 4,
    'magenta': 5, 'purple': 5,
    'cyan': 6,
    'white': 7,
    'gray': 8, 'grey': 8, 'lightblack': 8,
    'lightred': 9,
    'lightgreen': 10,
    'lightyellow': 11,
    'lightblue': 12,
    'lightmagenta': 13,
    'lightcyan': 14,
    'lightwhite': 15,
}


def _color(color: str) -> int:
    return curses.color_pair(
        COLOR_NAME_TO_COLOR.get(config['colors'][color], 0)
    )


class _Color:
    __slots__ = (
        'def1', 'def2', 'delimit', 'err', 'etym', 'exsen', 'heed', 'index',
        'inflection', 'label', 'phon', 'phrase', 'pos', 'sign', 'success',
        'syn', 'syngloss',
    )

    def init(self) -> None:
        self.def1       = _color('def1')
        self.def2       = _color('def2')
        self.delimit    = _color('delimit')
        self.err        = _color('err')
        self.etym       = _color('etym')
        self.exsen      = _color('exsen')
        self.heed       = _color('heed')
        self.index      = _color('index')
        self.inflection = _color('inflection')
        self.label      = _color('label')
        self.phon       = _color('phon')
        self.phrase     = _color('phrase')
        self.pos        = _color('pos')
        self.sign       = _color('sign')
        self.success    = _color('success')
        self.syn        = _color('syn')
        self.syngloss   = _color('syngloss')


Color = _Color()


def init_colors() -> None:
    try:
        curses.start_color()
    except curses.error:  # some internal table cannot be allocated?
        pass
    try:
        curses.use_default_colors()
    except curses.error:  # not supported
        pass

    Color.init()

    ncolors = curses.COLORS
    if ncolors < 8:
        return

    # Unfortuantely, we cannot override pair 0 so that invoking color
    # pairs as `curses.color_pair(curses.COLOR_BLACK)` gives black.
    # COLOR_* are not intended to be used like that, but still.
    for i in range(8 if ncolors == 8 else 16):
        curses.init_pair(i, i, -1)
