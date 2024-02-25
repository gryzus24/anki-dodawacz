from __future__ import annotations

import curses
from collections import defaultdict
from collections import deque
from typing import Callable
from typing import ClassVar
from typing import Mapping
from typing import NamedTuple
from typing import Sequence
from typing import TYPE_CHECKING

from src.Curses.color import Color
from src.Curses.util import clipboard_or_selection
from src.Curses.util import CURSES_COLS_MIN_VALUE
from src.Curses.util import hide_cursor
from src.Curses.util import mouse_right_click
from src.Curses.util import mouse_wheel_click
from src.Curses.util import norm_wch
from src.Curses.util import show_cursor
from src.Curses.util import truncate
from src.data import ON_TERMUX
from src.data import WINDOWS

if TYPE_CHECKING:
    from src.Curses.proto import ScreenBufferProto

COMPLETION_MENU_INDENT = 2


class SelectionResult(NamedTuple):
    completion: str | None
    wrapped: bool


def _lookup_add(lookup: defaultdict[str, list[str]], s: str) -> None:
    lookup[s[0].lower()].insert(0, s)


def _lookup_remove(lookup: defaultdict[str, list[str]], s: str) -> None:
    lookup[s[0].lower()].remove(s)


def _lookup_prepare(elements: deque[str]) -> defaultdict[str, list[str]]:
    result = defaultdict(list)
    for e in elements:
        result[e[0].lower()].append(e)

    return result


class CompletionMenu:
    def __init__(self,
            win: curses._CursesWindow,
            entries: deque[str] | None = None
    ) -> None:
        self.win = win
        self._entries = entries or deque()
        self._completions: Sequence[str] = self._entries
        self._lookup = _lookup_prepare(self._entries)
        self._completion_prefix: str | None = None
        self._cur: int | None = None
        self._scroll = 0

    @classmethod
    def from_file(cls, win: curses._CursesWindow, path: str) -> CompletionMenu:
        try:
            with open(path) as f:
                entries = deque(map(str.strip, f))
        except FileNotFoundError:
            entries = deque()

        return cls(win, entries)

    def save_entries(self, path: str) -> None:
        with open(path, 'w') as f:
            f.write('\n'.join(self._entries))

    @property
    def cur(self) -> int | None:
        return self._cur

    def height(self) -> int:
        r = min(len(self._completions), curses.LINES // 5)
        return r if r > 1 else 1

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

    def has_completions(self) -> bool:
        return bool(self._completions)

    # return: True if the order of entries has changed, False otherwise.
    def add_entry(self, s: str) -> bool:
        if not s:
            return False

        # Don't bother removing and adding if 's' is the same as the most
        # recently added entry (its position won't change).
        if self._entries and self._entries[0] == s:
            return False

        try:
            _lookup_remove(self._lookup, s)
            self._entries.remove(s)
        except ValueError:
            pass

        _lookup_add(self._lookup, s)
        self._entries.appendleft(s)

        return True

    def complete(self, s: str) -> None:
        self._cur = None
        self._scroll = 0

        s = s.lstrip().lower()
        if self._completion_prefix == s:
            return

        self._completion_prefix = s

        if not s:
            self._completions = self._entries
        elif len(s) == 1:
            self._completions = self._lookup[s]
        else:
            self._completions = [
                x for x in self._lookup[s[0]]
                if x.lower().startswith(s)
            ]

    def deactivate(self) -> None:
        self._cur = None
        self._scroll = 0
        self._completion_prefix = None
        self._completions = self._entries

    def _select(self, forward: bool) -> SelectionResult:
        if not self._completions:
            completion = None
            wrapped = False
        elif self._cur is None:
            self._cur = (0 if forward else len(self._completions) - 1)
            completion = self._completions[self._cur]
            wrapped = False
        elif self._cur == (len(self._completions) - 1 if forward else 0):
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
            screenbuf: ScreenBufferProto,
            prompt: str = '', *,
            pretype: str = '',
            exiting_bspace: bool = True,
            completion_separator: str | None = None,
            up_arrow_entries: deque[str] | None = None
    ) -> None:
        self.screenbuf = screenbuf
        self.win = screenbuf.win
        self.prompt = prompt
        self.exiting_bspace = exiting_bspace
        self.completion_separator = completion_separator
        self._cursor = len(pretype)
        self._entered = pretype
        self._up_arrow_entries = up_arrow_entries or deque()
        self._up_arrow_i: int | None = None

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

    def current_word(self) -> str:
        if self.completion_separator is None:
            return self._entered
        else:
            return self._entered.rpartition(self.completion_separator)[2]

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

    def _jump(self, start: int, end: int, step: int) -> int:
        nskipped = 0
        skip = True
        for i in range(start, end, step):
            c = self._entered[i]
            if c.isspace() or c == ',' or c == '-':
                if skip:
                    nskipped += 1
                else:
                    break
            else:
                nskipped += 1
                skip = False

        return nskipped

    def ctrl_left(self) -> None:
        self._cursor -= self._jump(self._cursor - 1, -1, -1)

    def ctrl_right(self) -> None:
        self._cursor += self._jump(self._cursor, len(self._entered), 1)

    # Insertion and deletion
    def insert(self, s: str) -> None:
        self._entered = (
            self._entered[:self._cursor] + s + self._entered[self._cursor:]
        )
        self._cursor += len(s)

    def clear(self) -> None:
        self._entered = ''
        self._cursor = 0

    def clear_insert(self, s: str) -> None:
        self.clear()
        self.insert(s)

    def _delete(self, start: int, n: int) -> None:
        self._entered = self._entered[:start] + self._entered[start + n:]

    def delete(self) -> None:
        self._delete(self._cursor, 1)

    def backspace(self) -> None:
        if not self._entered and self.exiting_bspace:
            curses.ungetch(3)  # ^C
        elif self._cursor:
            self._cursor -= 1
            self._delete(self._cursor, 1)

    def ctrl_backspace(self) -> None:
        if not self._entered and self.exiting_bspace:
            curses.ungetch(3)  # ^C
        elif self._cursor:
            nskipped = self._jump(self._cursor - 1, -1, -1)
            self._cursor -= nskipped
            self._delete(self._cursor, nskipped)

    def ctrl_k(self) -> None:
        self._entered = self._entered[:self._cursor]

    def ctrl_u(self) -> None:
        self._entered = self._entered[self._cursor:]
        self._cursor = 0

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

    _A: ClassVar[dict[str, Callable[[Prompt], None]]] = {
        'KEY_RESIZE': resize, '^L': resize,
        'KEY_LEFT': left,     '^B': left,
        'KEY_RIGHT': right,   '^F': right,
        'KEY_HOME': home,     '^A': home,
        'KEY_END': end,       '^E': end,
        'KEY_DC': delete,     '^D': delete,
        '^W': ctrl_backspace,
        '^K': ctrl_k,
        '^U': ctrl_u,
        '^T': ctrl_t,
    }
    if WINDOWS:
        _A['CTL_LEFT'] = _A['ALT_LEFT'] = ctrl_left
        _A['CTL_RIGHT'] = _A['ALT_RIGHT'] = ctrl_right
        _A['^H'] = backspace
        _A['^?'] = ctrl_backspace
    else:
        _A['kLFT5'] = _A['kLFT3'] = ctrl_left
        _A['kRIT5'] = _A['kRIT3'] = ctrl_right
        if ON_TERMUX:
            _A['^?'] = backspace
            _A['KEY_BACKSPACE'] = ctrl_backspace
        else:
            _A['KEY_BACKSPACE'] = backspace
            _A['^H'] = ctrl_backspace

    ACTIONS: Mapping[str, Callable[[Prompt], None]] = _A

    COMPLETION_NEXT_KEYS = ('^I', '^P')
    COMPLETION_PREV_KEYS = ('KEY_BTAB', '^N')

    def _run(self, cmenu: CompletionMenu) -> str | None:
        entered_before_completion = self._entered
        if entered_before_completion:
            cmenu.complete(entered_before_completion)

        while True:
            if cmenu.has_completions():
                with self.screenbuf.extra_margin(cmenu.height()):
                    self.screenbuf.draw()
                cmenu.draw()
            else:
                self.screenbuf.draw()

            self.draw()

            key, cntrl_char = norm_wch(self.win.get_wch())
            if not cntrl_char:
                self.insert(key)
                cmenu.complete(self.current_word())

            elif key in Prompt.ACTIONS:
                Prompt.ACTIONS[key](self)
                cmenu.complete(self.current_word())

            elif key == 'KEY_UP':
                if not self._up_arrow_entries:
                    continue
                if self._up_arrow_i is None:
                    self._up_arrow_i = 0
                elif self._up_arrow_i < len(self._up_arrow_entries) - 1:
                    self._up_arrow_i += 1

                self.clear_insert(self._up_arrow_entries[self._up_arrow_i])
                cmenu.complete(self.current_word())

            elif key == 'KEY_DOWN':
                if not self._up_arrow_entries or self._up_arrow_i is None:
                    continue
                if self._up_arrow_i <= 0:
                    self._up_arrow_i = None
                    entry = ''
                else:
                    self._up_arrow_i -= 1
                    entry = self._up_arrow_entries[self._up_arrow_i]

                self.clear_insert(entry)
                cmenu.complete(self.current_word())

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
                elif self.completion_separator is None:
                    self.clear_insert(r.completion)
                else:
                    head, sep, tail = self._entered.rpartition(self.completion_separator)
                    self.clear_insert(
                          head
                        + sep
                        + (' ' if tail.startswith(' ') else '')
                        + r.completion
                    )

            elif key == 'KEY_MOUSE':
                bstate = curses.getmouse()[4]
                if mouse_wheel_click(bstate):
                    try:
                        self.insert(clipboard_or_selection())
                    except (ValueError, LookupError):
                        pass
                    else:
                        cmenu.complete(self.current_word())
                elif mouse_right_click(bstate):
                    ret = self._entered
                    self.clear()
                    return ret

            elif key in {'^J', '^M'}:  # ^M: Enter on Windows
                ret = self._entered
                self.clear()
                return ret

            elif key in {'^C', '^\\', '^['}:  #]
                if cmenu.cur is None:
                    return None
                else:
                    self.clear_insert(entered_before_completion)
                    cmenu.complete(self.current_word())

    def run(self, c: CompletionMenu | Sequence[str] | None = None) -> str | None:
        if isinstance(c, CompletionMenu):
            cmenu = c
        elif c is None:
            cmenu = CompletionMenu(self.win)
        elif isinstance(c, deque):
            cmenu = CompletionMenu(self.win, c)
        else:
            cmenu = CompletionMenu(self.win, deque(c))

        curses.raw()
        show_cursor()
        try:
            return self._run(cmenu)
        finally:
            hide_cursor()
            curses.cbreak()
