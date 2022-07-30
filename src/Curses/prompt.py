from __future__ import annotations

import curses
from typing import TYPE_CHECKING

import src.Curses.env as env
from src.Curses.utils import (
    clipboard_or_selection,
    get_key,
    hide_cursor,
    mouse_wheel_clicked,
    show_cursor,
    truncate_if_needed,
)
from src.data import WINDOWS, ON_TERMUX

if TYPE_CHECKING:
    from src.proto import DrawAndResizeInterface


class Prompt:
    def __init__(self,
            implementor: DrawAndResizeInterface,
            win: curses._CursesWindow,
            prompt: str = '', *,
            pretype: str = '',
            exit_if_empty: bool = True,
    ) -> None:
        self.implementor = implementor
        self.win = win
        self.prompt: str = prompt
        self.exit_if_empty: bool = exit_if_empty
        self._cursor = len(pretype)
        self._entered = pretype

    def draw_prompt(self, y_draw: int) -> None:
        # Prevents going into an infinite loop on some terminals, or even
        # something worse, as the terminal (32-bit xterm)
        # locks up completely when env.COLS < 2.
        if env.COLS < 2:
            return

        width = env.COLS - 1
        offset = width // 3

        if self.prompt:
            prompt_text = truncate_if_needed(self.prompt, width - 6, fromleft=True)
            if prompt_text is None:
                prompt_text = '..' + self.prompt[-1]
        else:
            prompt_text = ''

        self.win.move(y_draw, 0)
        self.win.clrtoeol()

        visual_cursor = self._cursor + len(prompt_text)
        if visual_cursor < width:
            self.win.insstr(y_draw, 0, prompt_text)
            if len(self._entered) > width - len(prompt_text):
                text = f'{self._entered[:width - len(prompt_text)]}>'
            else:
                text = ''.join(self._entered)
            text_x = len(prompt_text)
        else:
            while visual_cursor >= width:
                visual_cursor = visual_cursor - width + offset

            start = self._cursor - visual_cursor
            if start + width > len(self._entered):
                text = f'<{self._entered[start + 1:start + width]}'
            else:
                text = f'<{self._entered[start + 1:start + width]}>'
            text_x = 0

        self.win.insstr(y_draw, text_x, text)
        self.win.move(y_draw, visual_cursor)

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

    def _delete_right(self, start: int, n: int) -> None:
        self._entered = self._entered[:start] + self._entered[start + n:]

    def delete(self) -> None:
        self._delete_right(self._cursor, 1)

    def backspace(self) -> None:
        if not self._entered and self.exit_if_empty:
            curses.ungetch(3)  # ^C
            return
        if self._cursor <= 0:
            return
        self._cursor -= 1
        self._delete_right(self._cursor, 1)

    def ctrl_backspace(self) -> None:
        if not self._entered and self.exit_if_empty:
            curses.ungetch(3)  # ^C
            return
        if self._cursor <= 0:
            return
        nskipped = self._jump_left()
        t = self._cursor - nskipped
        self._cursor = t if t > 0 else 0
        self._delete_right(self._cursor, nskipped)

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

    def _run(self) -> str | None:
        while True:
            self.implementor.draw()
            self.draw_prompt(env.LINES - 1)

            c_code = get_key(self.win)
            if 32 <= c_code <= 126:  # printable
                self.insert(chr(c_code))
                continue

            c = curses.keyname(c_code)
            if c in (b'^C', b'^['):
                return None
            elif c in Prompt.ACTIONS:
                Prompt.ACTIONS[c](self)
            elif c == b'KEY_MOUSE':
                bstate = curses.getmouse()[4]
                if mouse_wheel_clicked(bstate):
                    try:
                        self.insert(clipboard_or_selection())
                    except (ValueError, LookupError):
                        pass
                elif bstate & curses.BUTTON3_PRESSED:
                    ret = self._entered
                    self._clear()
                    return ret
            elif c in (b'^J', b'^M'):  # ^M: Enter on Windows
                ret = self._entered
                self._clear()
                return ret

    def run(self) -> str | None:
        curses.raw()
        show_cursor()
        try:
            return self._run()
        finally:
            hide_cursor()
            curses.cbreak()

