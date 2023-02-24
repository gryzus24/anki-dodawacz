from __future__ import annotations

import curses
from typing import Callable
from typing import NamedTuple
from typing import TYPE_CHECKING

from src.Curses.color import Color
from src.Curses.util import BORDER_PAD
from src.Curses.util import CURSES_COLS_MIN_VALUE
from src.Curses.util import FUNCTION_BAR_PAD
from src.Curses.util import HIGHLIGHT
from src.Curses.util import mouse_wheel_down
from src.Curses.util import mouse_wheel_up
from src.Curses.util import truncate

if TYPE_CHECKING:
    from src.Curses.util import Attr


class PagerHighlight(NamedTuple):
    hlmap: dict[int, list[int]]
    nmatches: int
    span: int


class Pager:
    def __init__(self,
            win: curses._CursesWindow,
            buf: list[tuple[str, list[Attr]]]
    ) -> None:
        self.win = win
        self._buf = buf
        self.margin_bot = FUNCTION_BAR_PAD
        self._line = 0
        self._hl: PagerHighlight | None = None

    @property
    def screen_height(self) -> int:
        r = curses.LINES - self.margin_bot - BORDER_PAD - 1
        return r if r > 0 else 0

    def _vscroll_end(self) -> int:
        r = len(self._buf) - self.screen_height
        return r if r > 0 else 0

    def adjust_scroll_past_eof(self) -> None:
        end_of_scroll = self._vscroll_end()
        if self._line > end_of_scroll:
            self._line = end_of_scroll

    def scroll_hint(self) -> str:
        if self._line >= self._vscroll_end():
            if self._line <= 0:
                return '<ALL>'
            else:
                return '<END>'
        elif self._line <= 0:
            return '<TOP>'
        else:
            return f' {(self._line + self.screen_height) / len(self._buf):.0%} '

    def draw(self) -> None:
        if curses.COLS < CURSES_COLS_MIN_VALUE:
            return

        win = self.win
        width = curses.COLS - 2*BORDER_PAD

        hl_attr = Color.heed | HIGHLIGHT
        for y, line_i in enumerate(range(self._line, self._line + self.screen_height), BORDER_PAD):
            try:
                line, attrs = self._buf[line_i]
            except IndexError:
                win.addch(y, 1, '~')
                continue

            text = truncate(line, width)
            if text is None:
                return

            win.addstr(y, BORDER_PAD, text)
            for attr_i, span, attr in attrs:
                if BORDER_PAD + attr_i + span > width:
                    span = width - attr_i
                    if span <= 0:
                        break
                win.chgat(y, BORDER_PAD + attr_i, span, attr)

            if (self._hl is None) or (line_i not in self._hl.hlmap):
                continue

            span = self._hl.span
            for attr_i in self._hl.hlmap[line_i]:
                if BORDER_PAD + attr_i + span > width:
                    span = width - attr_i
                    if span <= 0:
                        break
                win.chgat(y, BORDER_PAD + attr_i, span, hl_attr)

    def resize(self) -> None:
        self.adjust_scroll_past_eof()

    def move_down(self, n: int = 1) -> None:
        if self._line < self._vscroll_end():
            self._line += n
            self.adjust_scroll_past_eof()

    def move_up(self, n: int = 1) -> None:
        self._line -= n
        if self._line < 0:
            self._line = 0

    def go_bottom(self) -> None:
        self._line = self._vscroll_end()

    def go_top(self) -> None:
        self._line = 0

    def page_down(self) -> None:
        self.move_down(curses.LINES - 2)

    def page_up(self) -> None:
        self.move_up(curses.LINES - 2)

    def hlsearch(self, s: str) -> int:
        against_lowercase = s.islower()

        hl_span = len(s)

        hlmap = {}
        nmatches = 0
        for i, (text, _) in enumerate(self._buf):
            if against_lowercase:
                text = text.lower()

            indices = []
            x = text.find(s)
            while ~x:
                nmatches += 1
                indices.append(x)
                x = text.find(s, x + hl_span)

            if indices:
                hlmap[i] = indices

        if nmatches:
            self._hl = PagerHighlight(hlmap, nmatches, hl_span)
        else:
            self._hl = None

        return nmatches

    @property
    def highlight_nmatches(self) -> int:
        if self._hl is None:
            return 0
        else:
            return self._hl.nmatches

    def is_highlight_active(self) -> bool:
        return self._hl is not None

    def highlight_clear(self) -> None:
        self._hl = None

    def highlight_next(self) -> None:
        if self._hl is None:
            return
        for line_i in self._hl.hlmap:
            if line_i > self._line:
                self._line = line_i
                return

    def highlight_prev(self) -> None:
        if self._hl is None:
            return
        for line_i in reversed(self._hl.hlmap):
            if line_i < self._line:
                self._line = line_i
                return

    ACTIONS: dict[bytes, Callable[[Pager], None]] = {
        b'j': move_down,  b'^N': move_down, b'KEY_DOWN': move_down,
        b'k': move_up,    b'^P': move_up,   b'KEY_UP': move_up,
        b'G': go_bottom,  b'KEY_END': go_bottom,
        b'g': go_top,     b'KEY_HOME': go_top,
        b'KEY_NPAGE': page_down, b'KEY_SNEXT': page_down,
        b'KEY_PPAGE': page_up,   b'KEY_SPREVIOUS': page_up,
        b'n': highlight_next,
        b'N': highlight_prev,
        b'^J': highlight_clear, b'^M': highlight_clear,
    }

    def dispatch(self, key: bytes) -> bool:
        if key in self.ACTIONS:
            self.ACTIONS[key](self)
            return True

        return False

    def run(self) -> None:
        while True:
            self.draw()

            c = curses.keyname(self.win.getch())
            if c in (b'q', b'Q', b'^X'):
                return
            elif c in Pager.ACTIONS:
                Pager.ACTIONS[c](self)
            elif c == b'KEY_MOUSE':
                _, x, y, _, bstate = curses.getmouse()
                if mouse_wheel_up(bstate):
                    self.move_up()
                elif mouse_wheel_down(bstate):
                    self.move_down()
