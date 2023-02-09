from __future__ import annotations

import curses

from src.data import config

COLOR_NAME_TO_COLOR = {
    'fg': 0, 'black': 0,
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


def _color_num(color: str) -> int:
    return COLOR_NAME_TO_COLOR.get(config['colors'][color], 0)


class _Color:
    __slots__ = (
        'def1', 'def2', 'delimit', 'err', 'etym', 'exsen', 'heed', 'index',
        'infl', 'label', 'phon', 'phrase', 'pos', 'sign', 'success', 'syn',
    )

    def refresh(self) -> None:
        self.def1       = curses.color_pair(_color_num('def1'))
        self.def2       = curses.color_pair(_color_num('def2'))
        self.delimit    = curses.color_pair(_color_num('delimit'))
        self.err        = curses.color_pair(_color_num('err'))
        self.etym       = curses.color_pair(_color_num('etym'))
        self.exsen      = curses.color_pair(_color_num('exsen'))
        self.heed       = curses.color_pair(_color_num('heed'))
        self.index      = curses.color_pair(_color_num('index'))
        self.infl       = curses.color_pair(_color_num('infl'))
        self.label      = curses.color_pair(_color_num('label'))
        self.phon       = curses.color_pair(_color_num('phon'))
        self.phrase     = curses.color_pair(_color_num('phrase'))
        self.pos        = curses.color_pair(_color_num('pos'))
        self.sign       = curses.color_pair(_color_num('sign'))
        self.success    = curses.color_pair(_color_num('success'))
        self.syn        = curses.color_pair(_color_num('syn'))

    def init(self, ncolors: int) -> None:
        for k, v in COLOR_NAME_TO_COLOR.items():
            COLOR_NAME_TO_COLOR[k] = v % ncolors

        self.refresh()


Color = _Color()


def init_colors() -> None:
    try:
        curses.start_color()
    except curses.error:  # some internal table cannot be allocated?
        pass
    try:
        curses.use_default_colors()
    except curses.error as e:  # not supported
        raise SystemExit(f'{e}: check if $TERM is set correctly')

    # Unfortuantely, we cannot override pair 0 so that invoking color
    # pairs as `curses.color_pair(curses.COLOR_BLACK)` gives black.
    # COLOR_* are not intended to be used like that, but still.
    for i in range(16 if curses.COLORS >= 16 else curses.COLORS):
        curses.init_pair(i, i, -1)

    Color.init(curses.COLORS)
