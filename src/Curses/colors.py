from __future__ import annotations

import curses

from src.colors import Color as _Color
from src.data import WINDOWS

# Custom color pairs.
BLACK_ON_GREEN = 31
BLACK_ON_RED = 32
BLACK_ON_YELLOW = 33


class _CursesColor:
    _lookup = _attrs = None

    # It's better to wait for "curses.COLORS" variable to become available,
    # instead of fiddling with terminfo or some environment variables to
    # properly initialize color_pair lookup. The instance of this class requires
    # calling "setup_colors" after curses.start_color. As far as I know, this
    # is the only way to provide a common API with that of console UI without
    # using metaclasses.

    def __getattr__(self, item: str) -> int:
        return self._lookup[getattr(_Color, item)]  # type: ignore[index]

    def setup_colors(self, ncolors: int) -> None:
        if self._lookup is not None:
            return

        if WINDOWS:
            # For some reason, (RED and BLUE) and (CYAN and YELLOW)
            # are swapped on windows-curses.
            self._lookup = {
                '\033[39m': curses.color_pair(0),
                '\033[30m': curses.color_pair(1), '\033[90m': curses.color_pair(9),
                '\033[31m': curses.color_pair(5), '\033[91m': curses.color_pair(13),
                '\033[32m': curses.color_pair(3), '\033[92m': curses.color_pair(11),
                '\033[33m': curses.color_pair(7), '\033[93m': curses.color_pair(15),
                '\033[34m': curses.color_pair(2), '\033[94m': curses.color_pair(10),
                '\033[35m': curses.color_pair(6), '\033[95m': curses.color_pair(14),
                '\033[36m': curses.color_pair(4), '\033[96m': curses.color_pair(12),
                '\033[37m': curses.color_pair(8), '\033[97m': curses.color_pair(16),
            }
        elif ncolors == 8 or ncolors == 16777216:
            # Curses does not throw an error when accessing uninitialized color pairs.
            self._lookup = {
                '\033[39m': curses.color_pair(0),
                '\033[30m': curses.color_pair(1), '\033[90m': curses.color_pair(1),
                '\033[31m': curses.color_pair(2), '\033[91m': curses.color_pair(2),
                '\033[32m': curses.color_pair(3), '\033[92m': curses.color_pair(3),
                '\033[33m': curses.color_pair(4), '\033[93m': curses.color_pair(4),
                '\033[34m': curses.color_pair(5), '\033[94m': curses.color_pair(5),
                '\033[35m': curses.color_pair(6), '\033[95m': curses.color_pair(6),
                '\033[36m': curses.color_pair(7), '\033[96m': curses.color_pair(7),
                '\033[37m': curses.color_pair(8), '\033[97m': curses.color_pair(8),
            }
        else:
            self._lookup = {
                '\033[39m': curses.color_pair(0),
                '\033[30m': curses.color_pair(1), '\033[90m': curses.color_pair(9),
                '\033[31m': curses.color_pair(2), '\033[91m': curses.color_pair(10),
                '\033[32m': curses.color_pair(3), '\033[92m': curses.color_pair(11),
                '\033[33m': curses.color_pair(4), '\033[93m': curses.color_pair(12),
                '\033[34m': curses.color_pair(5), '\033[94m': curses.color_pair(13),
                '\033[35m': curses.color_pair(6), '\033[95m': curses.color_pair(14),
                '\033[36m': curses.color_pair(7), '\033[96m': curses.color_pair(15),
                '\033[37m': curses.color_pair(8), '\033[97m': curses.color_pair(16),
            }
        self._attrs = {k.strip('\033m'): v for k, v in self._lookup.items()}

    def parse_ansi_str(self, s: str) -> list[list[tuple[str, int]]]:
        if self._attrs is None:
            raise RuntimeError('setup_colors has not been called')

        result: list[list[tuple[str, int]]] = [[]]
        reading = False
        text = a_code = ''
        t_attrs = [0, 0]
        for ch in s:
            if ch == '\n':
                result[-1].append((text, t_attrs[0] | t_attrs[1]))
                result.append([])
                text = ''
            elif ch == '\b':
                text = text[:-1]
            elif ch == '\033':
                reading = True
                result[-1].append((text, t_attrs[0] | t_attrs[1]))
                text = ''
            elif reading:
                if ch == 'm':
                    try:
                        t_attrs[0] = self._attrs[a_code]
                    except KeyError:
                        if a_code == '[1':
                            t_attrs[1] = curses.A_BOLD
                        elif a_code == '[0':
                            t_attrs[1] = 0

                    a_code = ''
                    reading = False
                else:
                    a_code += ch
            else:
                text += ch

        result[-1].append((text, t_attrs[0] | t_attrs[1]))

        return result


Color = _CursesColor()


def init_colors() -> None:
    try:
        curses.start_color()
    except curses.error:  # some internal table cannot be allocated?
        pass
    try:
        curses.use_default_colors()
    except curses.error:  # not supported
        pass

    ncolors = curses.COLORS
    Color.setup_colors(ncolors)
    if ncolors < 8:
        return

    for i in range(8 if ncolors == 8 else 16):
        curses.init_pair(i + 1, i, -1)

    curses.init_pair(BLACK_ON_GREEN, curses.COLOR_BLACK, curses.COLOR_GREEN)
    curses.init_pair(BLACK_ON_RED, curses.COLOR_BLACK, curses.COLOR_RED)
    curses.init_pair(BLACK_ON_YELLOW, curses.COLOR_BLACK, curses.COLOR_YELLOW)

