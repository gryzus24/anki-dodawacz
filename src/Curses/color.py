from __future__ import annotations

import curses

from src.data import _defaults
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

ATTR_NAME_TO_ATTR = {
    'normal':     curses.A_NORMAL,
    'standout':   curses.A_STANDOUT,
    'underline':  curses.A_UNDERLINE,
    'underlined': curses.A_UNDERLINE,
    'u':          curses.A_UNDERLINE,
    'reverse':    curses.A_REVERSE,
    'reversed':   curses.A_REVERSE,
    'r':          curses.A_REVERSE,
    'blink':      curses.A_BLINK,
    'blinking':   curses.A_BLINK,
    'dim':        curses.A_DIM,
    'dimmed':     curses.A_DIM,
    'bold':       curses.A_BOLD,
    'b':          curses.A_BOLD,
    'protect':    curses.A_PROTECT,
    'protected':  curses.A_PROTECT,
    'invis':      curses.A_INVIS,
    'invisible':  curses.A_INVIS,
    'italic':     curses.A_ITALIC,
    'i':          curses.A_ITALIC,
}

class _Color:
    __slots__ = (
        'cursor', 'def1', 'def2', 'delimit', 'err', 'etym', 'exsen', 'heed',
        'hl', 'index', 'infl', 'label', 'phon', 'phrase', 'pos', 'selection',
        'sign', 'success', 'syn',
    )

    @staticmethod
    def color(c: config_t, key: colorkey_t) -> int:
        try:
            parts = c[key]
        except KeyError:
            parts = _defaults[key]

        attr = 0
        for part in parts.lower().split():
            if part in COLOR_NAME_TO_COLOR:
                attr |= curses.color_pair(COLOR_NAME_TO_COLOR[part])
            elif part in ATTR_NAME_TO_ATTR:
                attr |= ATTR_NAME_TO_ATTR[part]

        return attr

    def refresh(self, c: config_t) -> None:
        self.cursor    = _Color.color(c, 'c.cursor')
        self.def1      = _Color.color(c, 'c.def1')
        self.def2      = _Color.color(c, 'c.def2')
        self.delimit   = _Color.color(c, 'c.delimit')
        self.err       = _Color.color(c, 'c.err')
        self.etym      = _Color.color(c, 'c.etym')
        self.exsen     = _Color.color(c, 'c.exsen')
        self.heed      = _Color.color(c, 'c.heed')
        self.hl        = _Color.color(c, 'c.hl')
        self.index     = _Color.color(c, 'c.index')
        self.infl      = _Color.color(c, 'c.infl')
        self.label     = _Color.color(c, 'c.label')
        self.phon      = _Color.color(c, 'c.phon')
        self.phrase    = _Color.color(c, 'c.phrase')
        self.pos       = _Color.color(c, 'c.pos')
        self.selection = _Color.color(c, 'c.selection')
        self.sign      = _Color.color(c, 'c.sign')
        self.success   = _Color.color(c, 'c.success')
        self.syn       = _Color.color(c, 'c.syn')

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
