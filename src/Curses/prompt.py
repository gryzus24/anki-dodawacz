from __future__ import annotations

import curses
from typing import TYPE_CHECKING

from src.Curses.util import (
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


class CompletionMenu:
    def __init__(self, win: curses._CursesWindow, elements: list[str]) -> None:
        self.win = win
        self.elements = elements
        self._completions = elements
        self._current_completion_str: str | None = None
        self._cur: int | None = None
        self._scroll = 0

    def height(self) -> int:
        r = min(len(self._completions), curses.LINES // 5)
        return r if r > 1 else 1

    @property
    def completions(self) -> list[str]:
        return self._completions

    def draw(self) -> None:
        cur = self._cur or 0
        menu_height = self.height()

        if cur >= self._scroll + menu_height:
            self._scroll = cur - menu_height + 1
        elif cur < self._scroll:
            self._scroll = cur

        y = curses.LINES - 2
        width = curses.COLS
        for i in range(self._scroll, self._scroll + menu_height):
            hl = curses.color_pair(curses.COLOR_GREEN)
            if self._cur == i:
                hl |= curses.A_STANDOUT | curses.A_BOLD

            text = truncate(f'{i + 1:<3d}  {self._completions[i]}', width)
            if text is None:
                return
            try:
                self.win.addstr(y, 0, text, hl)
            except curses.error:  # window too small
                return
            else:
                y -= 1

    def complete(self, s: str) -> None:
        if self._current_completion_str == s:
            return

        self._current_completion_str = s
        self._cur = None
        self._scroll = 0
        self._completions = [x for x in self.elements if x.startswith(s)]

    def _select(self, n: int) -> str | None:
        if not self._completions:
            return None

        if self._cur is None:
            self._cur = 0
        else:
            self._cur = (self._cur + n) % len(self._completions)

        return self._completions[self._cur]

    def next(self) -> str | None:
        return self._select(1)

    def prev(self) -> str | None:
        return self._select(-1)


class Prompt:
    def __init__(self,
            implementor: ScreenBufferInterface,
            prompt: str = '', *,
            pretype: str = '',
            exiting_bspace: bool = True
    ) -> None:
        self.implementor = implementor
        self.win = implementor.win
        self.prompt = prompt
        self.exiting_bspace = exiting_bspace
        self._cursor = len(pretype)
        self._entered = pretype

    def draw(self) -> None:
        # Prevents going into an infinite loop on some terminals, or even
        # something worse, as the terminal (32-bit xterm)
        # locks up completely when curses.COLS < 2.
        if curses.COLS < 2:
            return

        win = self.win
        width = curses.COLS - 1
        offset = width // 3

        if self.prompt:
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

    def _clear(self) -> None:
        self._entered = ''
        self._cursor = 0

    def resize(self) -> None:
        self.implementor.resize()

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

    def _run(self, completions: list[str]) -> str | None:
        cmenu = CompletionMenu(self.win, completions)
        do_completion = False

        while True:
            if do_completion:
                cmenu.complete(self._entered.strip())
            else:
                do_completion = True

            if cmenu.completions:
                with self.implementor.extra_margin(cmenu.height()):
                    self.implementor.draw()
                cmenu.draw()
            else:
                self.implementor.draw()

            self.draw()

            c = self.win.getch()
            if 32 <= c <= 126:  # printable
                self.insert(chr(c))
                continue

            key = curses.keyname(c)
            if key in Prompt.ACTIONS:
                Prompt.ACTIONS[key](self)
            elif key in (b'^I', b'^P'):
                do_completion = False
                choice = cmenu.next()
                if choice is not None:
                    self._clear()
                    self.insert(choice)
            elif key in (b'KEY_BTAB', b'^N'):
                do_completion = False
                choice = cmenu.prev()
                if choice is not None:
                    self._clear()
                    self.insert(choice)
            elif key == b'KEY_MOUSE':
                bstate = curses.getmouse()[4]
                if mouse_wheel_click(bstate):
                    try:
                        self.insert(clipboard_or_selection())
                    except (ValueError, LookupError):
                        pass
                elif mouse_right_click(bstate):
                    ret = self._entered
                    self._clear()
                    return ret
            elif key in (b'^J', b'^M'):  # ^M: Enter on Windows
                ret = self._entered
                self._clear()
                return ret
            elif key in (b'^C', b'^\\', b'^['):
                return None

    def run(self, completions: list[str] | None = None) -> str | None:
        curses.raw()
        show_cursor()
        try:
            return self._run(completions or [])
        finally:
            hide_cursor()
            curses.cbreak()
