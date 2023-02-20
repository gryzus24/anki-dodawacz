from __future__ import annotations

import curses
import collections
from typing import TYPE_CHECKING, NamedTuple, Sequence

from src.Curses.color import Color
from src.Curses.util import (
    CURSES_COLS_MIN_VALUE,
    clipboard_or_selection,
    hide_cursor,
    mouse_right_click,
    mouse_wheel_click,
    show_cursor,
    truncate,
)
from src.data import WINDOWS, ON_TERMUX

if TYPE_CHECKING:
    from src.Curses.proto import ScreenBufferInterface


COMPLETION_MENU_INDENT = 2


def _prepare_lookup(elements: Sequence[str]) -> collections.defaultdict[str, list[str]]:
    result = collections.defaultdict(list)
    for e in elements:
        result[e[0].lower()].append(e)

    return result


class SelectionResult(NamedTuple):
    completion: str | None
    wrapped: bool


class CompletionMenu:
    def __init__(self, win: curses._CursesWindow, elements: Sequence[str]) -> None:
        self.win = win
        self.elements = elements
        self._completions = elements
        self._lookup = _prepare_lookup(elements)
        self._current_completion_str: str | None = None
        self._cur: int | None = None
        self._scroll = 0

    def height(self) -> int:
        r = min(len(self._completions), curses.LINES // 5)
        return r if r > 1 else 1

    @property
    def completions(self) -> Sequence[str]:
        return self._completions

    @property
    def cur(self) -> int | None:
        return self._cur

    def draw(self) -> None:
        cur = self._cur or 0
        menu_height = self.height()

        if cur >= self._scroll + menu_height:
            self._scroll = cur - menu_height + 1
        elif cur < self._scroll:
            self._scroll = cur

        y = curses.LINES - 2
        width = curses.COLS - COMPLETION_MENU_INDENT
        padding = len(str(len(self._completions)))
        for i in range(self._scroll, self._scroll + menu_height):
            text = truncate(f'{i + 1:{padding}d}  {self._completions[i]}', width)
            if text is None:
                return
            try:
                if self._cur == i:
                    self.win.addstr(y, 0, '> ', Color.heed | curses.A_BOLD)
                    self.win.addstr(y, COMPLETION_MENU_INDENT, text, curses.A_BOLD)
                else:
                    self.win.addstr(y, COMPLETION_MENU_INDENT, text)
            except curses.error:  # window too small
                return
            else:
                y -= 1

    def complete(self, s: str) -> None:
        self._cur = None
        self._scroll = 0

        s = s.lstrip().lower()
        if self._current_completion_str == s:
            return

        self._current_completion_str = s

        if s:
            self._completions = [
                x for x in self._lookup[s[0]]
                if x.lower().startswith(s)
            ]
        else:
            self._completions = self.elements

    def _select(self, forward: bool) -> SelectionResult:
        if not self._completions:
            completion = None
            wrapped = False
        elif self._cur is None:
            self._cur = (0 if forward else len(self._completions) - 1)
            completion = self._completions[self._cur]
            wrapped = False
        elif self._cur == ((len(self._completions) - 1) if forward else 0):
            self._cur = None
            completion = None
            wrapped = True
        else:
            self._cur += (1 if forward else -1)
            completion = self._completions[self._cur]
            wrapped = False

        return SelectionResult(completion, wrapped)

    def next(self) -> SelectionResult:
        return self._select(True)

    def prev(self) -> SelectionResult:
        return self._select(False)


class Prompt:
    def __init__(self,
            screenbuf: ScreenBufferInterface,
            prompt: str = '', *,
            pretype: str = '',
            exiting_bspace: bool = True
    ) -> None:
        self.screenbuf = screenbuf
        self.win = screenbuf.win
        self.prompt = prompt
        self.exiting_bspace = exiting_bspace
        self._cursor = len(pretype)
        self._entered = pretype

    def draw(self) -> None:
        if curses.COLS < CURSES_COLS_MIN_VALUE:
            return

        win = self.win
        width = curses.COLS - 1
        offset = width // 3

        if self.prompt:
            # 12: Prompt's minimum typing space.
            prompt_text = truncate(self.prompt, width - 12, fromleft=True)
            if prompt_text is None:
                prompt_text = '«' + self.prompt[-1]
        else:
            prompt_text = ''

        y = curses.LINES - 1

        win.move(y, 0)
        win.clrtoeol()

        visual_cursor = self._cursor + len(prompt_text)
        if visual_cursor < width:
            win.insstr(y, 0, prompt_text)
            if len(self._entered) > width - len(prompt_text):
                text = f'{self._entered[:width - len(prompt_text)]}»'
            else:
                text = ''.join(self._entered)
            text_x = len(prompt_text)
        else:
            while visual_cursor >= width:
                visual_cursor = visual_cursor - width + offset

            start = self._cursor - visual_cursor
            if start + width > len(self._entered):
                text = f'«{self._entered[start + 1:start + width]}'
            else:
                text = f'«{self._entered[start + 1:start + width]}»'
            text_x = 0

        win.insstr(y, text_x, text)
        win.move(y, visual_cursor)

    def resize(self) -> None:
        self.screenbuf.resize()

    def clear(self) -> None:
        self._entered = ''
        self._cursor = 0

    # Movement
    def left(self) -> None:
        if self._cursor > 0:
            self._cursor -= 1

    def right(self) -> None:
        if self._cursor < len(self._entered):
            self._cursor += 1

    def home(self) -> None:
        self._cursor = 0

    def end(self) -> None:
        self._cursor = len(self._entered)

    def _jump_left(self) -> int:
        entered = self._entered
        nskipped = 0
        skip = True
        for i in range(self._cursor - 1, -1, -1):
            if entered[i].isspace():
                if skip:
                    nskipped += 1
                    continue
                break
            else:
                nskipped += 1
                skip = False

        return nskipped

    def ctrl_left(self) -> None:
        t = self._cursor - self._jump_left()
        self._cursor = t if t > 0 else 0

    def _jump_right(self) -> int:
        entered = self._entered
        nskipped = 0
        skip = True
        for i in range(self._cursor, len(entered)):
            if entered[i].isspace():
                if skip:
                    nskipped += 1
                    continue
                break
            else:
                nskipped += 1
                skip = False

        return nskipped

    def ctrl_right(self) -> None:
        t = self._cursor + self._jump_right()
        self._cursor = t if t < len(self._entered) else len(self._entered)

    # Insertion and deletion
    def insert(self, s: str) -> None:
        self._entered = (
            self._entered[:self._cursor] + s + self._entered[self._cursor:]
        )
        self._cursor += len(s)

    def clear_insert(self, s: str) -> None:
        self.clear()
        self.insert(s)

    def _delete_from(self, start: int, n: int) -> None:
        self._entered = self._entered[:start] + self._entered[start + n:]

    def delete(self) -> None:
        self._delete_from(self._cursor, 1)

    def backspace(self) -> None:
        if not self._entered and self.exiting_bspace:
            curses.ungetch(3)  # ^C
            return
        if self._cursor <= 0:
            return
        self._cursor -= 1
        self._delete_from(self._cursor, 1)

    def ctrl_backspace(self) -> None:
        if not self._entered and self.exiting_bspace:
            curses.ungetch(3)  # ^C
            return
        if self._cursor <= 0:
            return
        nskipped = self._jump_left()
        t = self._cursor - nskipped
        self._cursor = t if t > 0 else 0
        self._delete_from(self._cursor, nskipped)

    def ctrl_k(self) -> None:
        self._entered = self._entered[:self._cursor]

    def ctrl_t(self) -> None:
        # Ignore only trailing whitespace to keep things simple.
        entered = self._entered.rstrip()
        if self._cursor > len(entered):
            self._cursor = len(entered)

        left = entered.rfind(' ', 0, self._cursor)
        left = left + 1 if ~left else 0

        right = entered.find(' ', self._cursor)
        right = right if ~right else len(entered)
        if left == right:
            # multiple spaces with cursor on top e.g. 'word [ ]word'
            return

        self._entered = entered[left:right]
        self._cursor = len(self._entered)

    ACTIONS = {
        b'KEY_RESIZE': resize, b'^L': resize,
        b'KEY_LEFT': left,     b'^B': left,
        b'KEY_RIGHT': right,   b'^F': right,
        b'KEY_HOME': home,     b'^A': home,
        b'KEY_END': end,       b'^E': end,
        b'KEY_DC': delete,     b'^D': delete,
        b'^W': ctrl_backspace,
        b'^K': ctrl_k,
        b'^T': ctrl_t,
    }
    if WINDOWS:
        ACTIONS[b'CTL_LEFT'] = ACTIONS[b'ALT_LEFT'] = ctrl_left
        ACTIONS[b'CTL_RIGHT'] = ACTIONS[b'ALT_RIGHT'] = ctrl_right
        ACTIONS[b'^H'] = backspace
        ACTIONS[b'^?'] = ctrl_backspace
    else:
        ACTIONS[b'kLFT5'] = ACTIONS[b'kLFT3'] = ctrl_left
        ACTIONS[b'kRIT5'] = ACTIONS[b'kRIT3'] = ctrl_right
        if ON_TERMUX:
            ACTIONS[b'^?'] = backspace
            ACTIONS[b'KEY_BACKSPACE'] = ctrl_backspace
        else:
            ACTIONS[b'KEY_BACKSPACE'] = backspace
            ACTIONS[b'^H'] = ctrl_backspace

    COMPLETION_NEXT_KEYS = (b'^I', b'^P')
    COMPLETION_PREV_KEYS = (b'KEY_BTAB', b'^N')

    def _run(self, completions: Sequence[str]) -> str | None:
        cmenu = CompletionMenu(self.win, completions)
        entered_before_completion = self._entered
        if entered_before_completion:
            cmenu.complete(entered_before_completion)

        while True:
            if cmenu.completions:
                with self.screenbuf.extra_margin(cmenu.height()):
                    self.screenbuf.draw()
                cmenu.draw()
            else:
                self.screenbuf.draw()

            self.draw()

            c = self.win.getch()
            if 32 <= c <= 126:  # printable
                self.insert(chr(c))
                cmenu.complete(self._entered)

            elif (key := curses.keyname(c)) in Prompt.ACTIONS:
                Prompt.ACTIONS[key](self)
                cmenu.complete(self._entered)

            elif (
                   key in Prompt.COMPLETION_NEXT_KEYS
                or key in Prompt.COMPLETION_PREV_KEYS
            ):
                if cmenu.cur is None:
                    entered_before_completion = self._entered

                if key in Prompt.COMPLETION_NEXT_KEYS:
                    r = cmenu.next()
                else:
                    r = cmenu.prev()
                if r.completion is None:
                    if r.wrapped:
                        self.clear_insert(entered_before_completion)
                    else:
                        pass  # no completion matches
                else:
                    self.clear_insert(r.completion)

            elif key == b'KEY_MOUSE':
                bstate = curses.getmouse()[4]
                if mouse_wheel_click(bstate):
                    try:
                        self.insert(clipboard_or_selection())
                    except (ValueError, LookupError):
                        pass
                    else:
                        cmenu.complete(self._entered)
                elif mouse_right_click(bstate):
                    ret = self._entered
                    self.clear()
                    return ret

            elif key in (b'^J', b'^M'):  # ^M: Enter on Windows
                ret = self._entered
                self.clear()
                return ret

            elif key in (b'^C', b'^\\', b'^['):
                if cmenu.cur is None:
                    return None
                else:
                    self.clear_insert(entered_before_completion)
                    cmenu.complete(self._entered)


    def run(self, completions: Sequence[str] | None = None) -> str | None:
        curses.raw()
        show_cursor()
        try:
            return self._run(completions or [])
        finally:
            hide_cursor()
            curses.cbreak()
