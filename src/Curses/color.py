from __future__ import annotations

import curses

from src.data import colorkey_t
from src.data import config
from src.data import config_t
from src.data import WINDOWS

# For some reason (RED and BLUE) and (CYAN and YELLOW)
# are swapped on windows-curses.
if WINDOWS:
    COLOR_NAME_TO_COLOR = {
        'fg': 0, 'black': 0,
        'red': 4,
        'green': 2,
        'yellow': 6, 'orange': 6, 'brown': 6,
        'blue': 1,
        'magenta': 5, 'purple': 5,
        'cyan': 3,
        'white': 7,
        'gray': 8, 'grey': 8, 'lightblack': 8,
        'lightred': 12,
        'lightgreen': 10,
        'lightyellow': 14,
        'lightblue': 9,
        'lightmagenta': 13,
        'lightcyan': 11,
        'lightwhite': 15,
    }
else:
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


class _Color:
    __slots__ = (
        'def1', 'def2', 'delimit', 'err', 'etym', 'exsen', 'heed', 'index',
        'infl', 'label', 'phon', 'phrase', 'pos', 'sign', 'success', 'syn',
    )

    @staticmethod
    def get_color(c: config_t, key: colorkey_t) -> int:
        return curses.color_pair(COLOR_NAME_TO_COLOR.get(c[key], 0))

    def refresh(self, c: config_t) -> None:
        self.def1    = _Color.get_color(c, 'c.def1')
        self.def2    = _Color.get_color(c, 'c.def2')
        self.delimit = _Color.get_color(c, 'c.delimit')
        self.err     = _Color.get_color(c, 'c.err')
        self.etym    = _Color.get_color(c, 'c.etym')
        self.exsen   = _Color.get_color(c, 'c.exsen')
        self.heed    = _Color.get_color(c, 'c.heed')
        self.index   = _Color.get_color(c, 'c.index')
        self.infl    = _Color.get_color(c, 'c.infl')
        self.label   = _Color.get_color(c, 'c.label')
        self.phon    = _Color.get_color(c, 'c.phon')
        self.phrase  = _Color.get_color(c, 'c.phrase')
        self.pos     = _Color.get_color(c, 'c.pos')
        self.sign    = _Color.get_color(c, 'c.sign')
        self.success = _Color.get_color(c, 'c.success')
        self.syn     = _Color.get_color(c, 'c.syn')

    def init(self, c: config_t, ncolors: int) -> None:
        for k, v in COLOR_NAME_TO_COLOR.items():
            COLOR_NAME_TO_COLOR[k] = v % ncolors

        self.refresh(c)


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
    for i in range(1, 16 if curses.COLORS >= 16 else curses.COLORS):
        curses.init_pair(i, i, -1)

    Color.init(config, curses.COLORS)
