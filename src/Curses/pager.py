from __future__ import annotations

import curses
from typing import NamedTuple, Callable

import src.Curses.env as env
from src.Curses.colors import Color
from src.Curses.prompt import Prompt
from src.Curses.utils import BUTTON5_PRESSED, get_key, terminal_resize, truncate_if_needed


class PagerHighlight(NamedTuple):
    hl_map: dict[int, list[int]]
    nmatches: int
    span: int


class PagerStatus(NamedTuple):
    message: str
    expire: bool


class Pager:
    def __init__(self,
            win: curses._CursesWindow,
            contents: str, *,
            hscroll_const: float = 0.67
    ) -> None:
        self._buffer = Color.parse_ansi_str(contents)
        self._height = len(self._buffer)
        self._width = max(sum(map(lambda x: len(x[0]), line)) for line in self._buffer)
        self._line = self._col = 0
        self._hl: PagerHighlight | None = None
        self._status: PagerStatus | None = None

        self.win = win
        self.hscroll_const = hscroll_const

    @property
    def _hscroll_value(self) -> int:
        return int(self.hscroll_const * env.COLS)

    def _vscroll_end(self) -> int:
        r = self._height - env.LINES
        return r if r > 0 else 0

    def _hscroll_end(self) -> int:
        r = self._width - env.COLS
        return r if r > 0 else 0

    def _draw_hl(self, hl: PagerHighlight) -> None:
        win = self.win
        hl_attr = Color.heed | curses.A_REVERSE | curses.A_BOLD

        for line_i in filter(
            lambda x: x in hl.hl_map, range(self._line, self._line + env.LINES - 1)
        ):
            y = line_i - self._line
            for x in hl.hl_map[line_i]:
                x_with_offset = x - self._col
                if x_with_offset < 0:
                    # x_with_offset < 0 can be true only if self._col > 0
                    # |re  <= highlight even if off-screen
                    # /more
                    partial = x_with_offset + hl.span
                    if partial > 0:
                        win.chgat(y, 0, partial, hl_attr)
                else:
                    try:
                        win.chgat(y, x_with_offset, hl.span, hl_attr)
                    except curses.error:  # window too small
                        pass

    def _draw_scroll_hint(self) -> None:
        loc = f'{self._line},{self._col}'
        if not self._line:
            t = f'{loc} <TOP>'
        elif self._line >= self._vscroll_end():
            t = f'{loc} <END>'
        else:
            perc = round((self._line + env.LINES) / len(self._buffer) * 100)
            t = f'{loc}  {perc}% '

        r = truncate_if_needed(t, env.COLS, fromleft=True)
        if r is not None:
            self.win.insstr(env.LINES - 1, env.COLS - len(r), r)

    def draw(self) -> None:
        if env.COLS < 2:
            return

        win = self.win
        win.erase()

        buffer_slice = self._buffer[self._line:self._line + env.LINES - 1]
        if self._col:
            for y, line in enumerate(buffer_slice):
                # TODO: A cleaner way to draw with the col offset?
                x = 0
                void = self._col
                try:
                    for text, attr in line:
                        for ch in text:
                            if void:
                                void -= 1
                            else:
                                win.addch(y, x, ch, attr)
                                x += 1
                except curses.error:  # window too small.
                    pass
        else:
            for y, line in enumerate(buffer_slice):
                for text, attr in reversed(line):
                    win.insstr(y, 0, text, attr)

        if len(buffer_slice) < env.LINES - 1:
            for y in range(len(buffer_slice), env.LINES - 1):
                win.addch(y, 0, '~')

        if self._hl is not None:
            self._draw_hl(self._hl)

        self._draw_scroll_hint()

        if self._status is not None:
            s = truncate_if_needed(self._status.message, env.COLS, fromleft=True)
            if s is not None:
                try:
                    self.win.addstr(env.LINES - 1, 0, s, curses.A_REVERSE)
                except curses.error:  # bottom-right corner write
                    pass
                if self._status.expire:
                    self._status = None

        win.noutrefresh()

    def resize(self) -> None:
        terminal_resize()

        vbound = self._vscroll_end()
        if self._line > vbound:
            self._line = vbound

        hbound = self._hscroll_end()
        if self._col > hbound:
            self._col = hbound

        self.win.clearok(True)

    def move_down(self, n: int = 2) -> None:
        self._line += n
        bound = self._vscroll_end()
        if self._line > bound:
            self._line = bound

    def move_up(self, n: int = 2) -> None:
        self._line -= n
        if self._line < 0:
            self._line = 0

    def move_right(self, n: int | None = None) -> None:
        self._col += n or self._hscroll_value
        bound = self._hscroll_end()
        if self._col > bound:
            self._col = bound

    def move_left(self, n: int | None = None) -> None:
        self._col -= n or self._hscroll_value
        if self._col < 0:
            self._col = 0

    def go_bottom(self) -> None:
        self._line = self._vscroll_end()

    def go_top(self) -> None:
        self._line = 0

    def page_down(self) -> None:
        self.move_down(env.LINES - 2)

    def page_up(self) -> None:
        self.move_up(env.LINES - 2)

    def _get_highlights(self, s: str) -> PagerHighlight | None:
        against_lowercase = s.islower()
        hl_span = len(s)

        result = {}
        nmatches = 0
        for i, line in enumerate(self._buffer):
            text = ''.join(x[0] for x in line)
            if against_lowercase:
                text = text.lower()
            # TODO: Maybe there is a more efficient way to get indices
            #       of every occurrence of a substring?
            indices = []
            x = text.find(s)
            while ~x:
                nmatches += 1
                indices.append(x)
                x = text.find(s, x + hl_span)

            if indices:
                result[i] = indices

        if not nmatches:
            return None

        return PagerHighlight(result, nmatches, hl_span)

    def hl_init(self, s: str) -> None:
        self._hl = self._get_highlights(s)
        if self._hl is None:
            self._status = PagerStatus(f'PATTERN NOT FOUND: {s}', expire=True)
        else:
            self._line = next(iter(self._hl.hl_map))
            self._status = PagerStatus(f'MATCHES: {self._hl.nmatches}', expire=False)

    def hl_next(self, hl: PagerHighlight) -> None:
        for line_i in hl.hl_map:
            if line_i > self._line:
                self._line = line_i
                self._col = 0
                return

    def hl_prev(self, hl: PagerHighlight) -> None:
        for line_i in reversed(hl.hl_map):
            if line_i < self._line:
                self._line = line_i
                self._col = 0
                return

    def hl_clear(self) -> None:
        self._hl = self._status = None

    ACTIONS: dict[bytes, Callable[[Pager], None]] = {
        b'KEY_RESIZE': resize, b'^L': resize,
        b'j': move_down,  b'^N': move_down, b'KEY_DOWN': move_down,
        b'k': move_up,    b'^P': move_up,   b'KEY_UP': move_up,
        b'l': move_right, b'KEY_RIGHT': move_right,
        b'h': move_left,  b'KEY_LEFT': move_left,
        b'G': go_bottom,  b'KEY_END': go_bottom,
        b'g': go_top,     b'KEY_HOME': go_top,
        b'KEY_NPAGE': page_down, b'KEY_SNEXT': page_down,
        b'KEY_PPAGE': page_up,   b'KEY_SPREVIOUS': page_up,
    }

    def run(self) -> None:
        while True:
            self.draw()
            curses.doupdate()

            c = curses.keyname(get_key(self.win))
            if c in (b'q', b'Q', b'^X'):
                return
            elif c in Pager.ACTIONS:
                Pager.ACTIONS[c](self)
            elif c == b'KEY_MOUSE':
                _, x, y, _, bstate = curses.getmouse()
                if bstate & curses.BUTTON4_PRESSED:
                    self.move_up()
                elif bstate & BUTTON5_PRESSED:
                    self.move_down()
            elif c == b'/':
                typed = Prompt(self, self.win, '/').run()
                if typed is not None and typed:
                    self.hl_init(typed)
            elif self._hl is not None:
                if c == b'n':
                    self.hl_next(self._hl)
                elif c == b'N':
                    self.hl_prev(self._hl)
                elif c in (b'^J', b'^M'):
                    self.hl_clear()

