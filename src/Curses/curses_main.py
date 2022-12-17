from __future__ import annotations

import curses
import contextlib
from typing import Callable, TypeVar, Sequence, Iterable, NamedTuple, Iterator, TYPE_CHECKING

import src.Curses.env as env
import src.anki_interface as anki
from src.Curses.colors import Color, init_colors, BLACK_ON_RED, BLACK_ON_GREEN, BLACK_ON_YELLOW
from src.Curses.pager import Pager
from src.Curses.prompt import Prompt
from src.Curses.utils import (
    BUTTON5_PRESSED,
    clipboard_or_selection,
    get_key,
    hide_cursor,
    mouse_wheel_clicked,
    terminal_resize,
    truncate_if_needed,
    update_global_lines_cols,
)
from src.Dictionaries.dictionary_base import EntrySelector
from src.cards import create_and_add_card
from src.commands import INTERACTIVE_COMMANDS, NO_HELP_ARG_COMMANDS, HELP_ARG_COMMANDS
from src.data import STRING_TO_BOOL, HORIZONTAL_BAR, WINDOWS, config
from src.search import search_dictionaries

if TYPE_CHECKING:
    from src.Dictionaries.dictionary_base import Dictionary
    from src.search import QuerySettings


class Attr(NamedTuple):
    i:    int
    span: int
    attr: int


def compose_attrs(elements: Iterable[tuple[int, int, int]], *, width: int, start: int = 0) -> list[Attr]:
    attrs = []
    index = start
    for span, attr, gap in elements:
        if index + span > width:
            if index < width:
                attrs.append(Attr(index, width - index, attr))
            break
        else:
            attrs.append(Attr(index, span, attr))
            index += span + gap

    return attrs


class RefreshWriter:
    def __init__(self, screen_buffer: ScreenBuffer) -> None:
        self.screen_buffer = screen_buffer

    def writeln(self, s: str) -> None:
        self.screen_buffer.status.error(s)
        self.screen_buffer.draw()
        self.screen_buffer.win.refresh()


class CardWriter:
    def __init__(self, screen_buffer: ScreenBuffer) -> None:
        self.screen_buffer = screen_buffer

    def writeln(self, s: str) -> None:
        self.screen_buffer.status.error(s)
        self.screen_buffer.draw()
        self.screen_buffer.win.refresh()

    def preview_card(self, card: dict[str, str]) -> None:
        # TODO: Find a nice and concise way to preview cards in curses.
        pass


class Wrapper:
    def __init__(self, textwidth: int):
        self.textwidth = textwidth
        self._cur = 0

    @property
    def current_line_pos(self):
        return self._cur

    def wrap(self, s: str, initial: str | int, indent: str):
        if isinstance(initial, str):
            self._cur = len(initial)
            line = initial
        else:
            self._cur = initial
            line = ''
        for word in s.split():
            if self._cur + len(word) > self.textwidth:
                yield line.rstrip()
                line = indent + word + ' '
                self._cur = len(indent) + len(word) + 1
            else:
                line += word + ' '
                self._cur += len(word) + 1

        yield line.rstrip()


class ParsedLine(NamedTuple):
    op_index: int
    text: str
    attrs: list[Attr]


def format_dictionary(dictionary: Dictionary, column_width: int) -> list[ParsedLine]:
    def1_c, def2_c, sign_c = Color.def1, Color.def2, Color.sign
    index_c, label_c, exsen_c = Color.index, Color.label, Color.exsen
    inflection_c, phrase_c, phon_c = Color.inflection, Color.phrase, Color.phon
    delimit_c, etym_c, pos_c = Color.delimit, Color.etym, Color.pos
    syn_c, syngloss_c, heed_c = Color.syn, Color.syngloss, Color.heed

    index = 0
    wrapper = Wrapper(column_width)

    result: list[ParsedLine] = []
    for i, entry in enumerate(dictionary.contents):
        op = entry[0]

        if 'DEF' in op:
            index += 1
            index_len = len(str(index))

            _def, _exsen, _label = entry[1], entry[2], entry[3]
            if _label:
                _label = '{' + _label + '} '
                label_len = len(_label)
            else:
                label_len = 0

            sign = ' ' if 'SUB' in op else '>'

            def_color = def1_c if index % 2 else def2_c

            lines = wrapper.wrap(_def, f'{sign}{index} {_label}', (index_len + 2) * ' ')
            attrs = compose_attrs(
                (
                    (len(sign), sign_c, 0),
                    (index_len, index_c, 1),
                    (label_len, label_c, 0),
                    (column_width, def_color, 0),
                ), width=column_width
            )
            result.append(ParsedLine(i, next(lines), attrs))
            for line in lines:
                result.append(ParsedLine(i, line, [Attr(0, column_width, def_color)]))

            if _exsen:
                for ex in _exsen.split('<br>'):
                    for line in wrapper.wrap(ex, (index_len + 1) * ' ', (index_len + 2) * ' '):
                        result.append(ParsedLine(i, line, [Attr(0, column_width, exsen_c)]))

        elif op == 'LABEL':
            label, inflections = entry[1], entry[2]
            result.append(ParsedLine(i, '', [Attr(0, 0, 0)]))
            if label:
                if inflections:
                    *lines, last_line = wrapper.wrap(label, ' ', ' ')
                    for line in lines:
                        result.append(ParsedLine(i, line, [Attr(0, column_width, label_c)]))

                    mutual_attrs = compose_attrs(
                        (
                            (len(last_line), label_c, 1),
                            (column_width, inflection_c, 0),
                        ), width=column_width
                    )
                    lines = wrapper.wrap(inflections, wrapper.current_line_pos + 1, ' ')
                    result.append(ParsedLine(i, last_line + ' ' + next(lines), mutual_attrs))

                    for line in lines:
                        result.append(ParsedLine(i, line, [Attr(0, column_width, inflection_c)]))
                else:
                    for line in wrapper.wrap(label, ' ', ' '):
                        result.append(ParsedLine(i, line, [Attr(0, column_width, label_c)]))

        elif op == 'PHRASE':
            phrase, phon = entry[1], entry[2]
            if phon:
                *lines, last_line = wrapper.wrap(phrase, ' ', ' ')
                for line in lines:
                    result.append(ParsedLine(i, line, [Attr(0, column_width, phrase_c)]))

                lines = wrapper.wrap(phon, wrapper.current_line_pos + 1, ' ')
                mutual_attrs = compose_attrs(
                    (
                        (len(last_line), phrase_c, 1),
                        (column_width, phon_c, 0),
                    ), width=column_width
                )
                result.append(ParsedLine(i, last_line + ' ' + next(lines), mutual_attrs))

                for line in lines:
                    result.append(ParsedLine(i, line, [Attr(0, column_width, phon_c)]))
            else:
                for line in wrapper.wrap(phrase, ' ', ' '):
                    result.append(ParsedLine(i, line, [Attr(0, column_width, phrase_c)]))

        elif op == 'HEADER':
            if i == 0:
                continue

            title = entry[1]
            if title:
                attrs = compose_attrs(
                    (
                        (3, delimit_c, 0),
                        (len(title), delimit_c | curses.A_BOLD, 0),
                        (column_width, delimit_c, 0),
                    ), width=column_width
                )
                result.append(
                    ParsedLine(i, f'{HORIZONTAL_BAR}[ {title} ]{(column_width - len(title) - 5) * HORIZONTAL_BAR}', attrs)
                )
            else:
                result.append(
                    ParsedLine(i, column_width * HORIZONTAL_BAR, [Attr(0, column_width, delimit_c)])
                )

        elif op == 'ETYM':
            etym = entry[1]
            if etym:
                result.append(ParsedLine(i, '', [Attr(0, 0, 0)]))
                for line in wrapper.wrap(etym, ' ', ' '):
                    result.append(ParsedLine(i, line, [Attr(0, column_width, etym_c)]))

        elif op == 'POS':
            if entry[1].strip(' |'):
                result.append(ParsedLine(i, '', [Attr(0, 0, 0)]))
                for elem in entry[1:]:
                    pos, phon = elem.split('|')
                    *lines, last_line = wrapper.wrap(pos, ' ', ' ')
                    for line in lines:
                        result.append(ParsedLine(i, line, [Attr(0, column_width, phrase_c)]))

                    lines = wrapper.wrap(phon, wrapper.current_line_pos + 1, ' ')
                    mutual_attrs = compose_attrs(
                        (
                            (len(last_line), pos_c, 1),
                            (column_width, phon_c, 0),
                        ), width=column_width
                    )
                    result.append(ParsedLine(i, last_line + ' ' + next(lines), mutual_attrs))

                    for line in lines:
                        result.append(ParsedLine(i, line, [Attr(0, column_width, phon_c)]))

        elif op == 'AUDIO':
            pass

        elif op == 'SYN':
            for line in wrapper.wrap(entry[1], ' ', ' '):
                result.append(ParsedLine(i, line, [Attr(0, column_width, syn_c)]))

            for line in wrapper.wrap(entry[2], ': ', ' '):
                result.append(ParsedLine(i, line, [Attr(0, column_width, syngloss_c)]))

            for ex in entry[3].split('<br>'):
                for line in wrapper.wrap(ex, ' ', '  '):
                    result.append(ParsedLine(i, line, [Attr(0, column_width, exsen_c)]))

        elif op == 'NOTE':
            lines = wrapper.wrap(entry[1], '> ', '  ')
            attrs = compose_attrs(
                (
                    (1, heed_c | curses.A_BOLD, 0),
                    (column_width, curses.A_BOLD, 0),
                ), width=column_width
            )
            result.append(ParsedLine(i, next(lines), attrs))
            for line in lines:
                result.append(ParsedLine(i, line, [Attr(0, column_width, curses.A_BOLD)]))

        else:
            raise AssertionError(f'unreachable dictionary op: {op!r}')

    return result


AUTO_COLUMN_WIDTH = 52
BORDER_PAD = MARGIN = 1
MINIMUM_COLUMN_WIDTH = 26


def current_related_entries() -> set[str]:
    result = {'PHRASE'}
    if config['-audio'] != '-':
        result.add('AUDIO')
    if config['-pos']:
        result.add('POS')
    if config['-etym']:
        result.add('ETYM')
    return result


def _create_layout(dictionary: Dictionary, height: int) -> tuple[list[list[ParsedLine]], int]:
    width = env.COLS - 2*BORDER_PAD + 1
    ndefinitions = dictionary.count(lambda x: 'DEF' in x)

    if ndefinitions < 6:
        maxcolumns = 1
    elif ndefinitions < 12 and len(dictionary.contents) < height:
        maxcolumns = 2
    else:
        maxcolumns = 3

    ncolumns = width // AUTO_COLUMN_WIDTH
    if ncolumns > maxcolumns:
        ncolumns = maxcolumns
    elif ncolumns < 1:
        ncolumns = 1

    try:
        column_width = (width // ncolumns) - 1
    except ZeroDivisionError:
        column_width = width

    lines = format_dictionary(dictionary, column_width - 2*MARGIN)
    max_column_height = len(lines) // ncolumns - 1
    column_break = max_column_height

    columns = [[] for _ in range(ncolumns)]
    cur = 0
    for i, line in enumerate(lines):
        columns[cur].append(line)

        op = dictionary.contents[line.op_index][0]
        if (
                i > column_break
            and ('DEF' in op or op == 'ETYM')
            and i + 1 != len(lines)
            and line.op_index != lines[i + 1].op_index
        ):
            if cur == ncolumns - 1:
                continue
            else:
                column_break += max_column_height
                cur += 1

    return columns, column_width


class HL(NamedTuple):
    hls: list[dict[int, list[int]]]
    nmatches: int
    hlphrase: str
    hllast_line: int

    @property
    def span(self) -> int:
        return len(self.hlphrase)


class Screen:
    def __init__(self, win: curses._CursesWindow,  dictionary: Dictionary) -> None:
        self.win = win
        self.selector = EntrySelector(dictionary)

        # self.margin_bot is needed for `self.screen_height`
        self.margin_bot = 0
        self.columns, self.column_width = _create_layout(dictionary, self.screen_height)
        self._hl: HL | None = None

        self._scroll = 0

    @property
    def screen_height(self) -> int:
        r = env.LINES - self.margin_bot - 2*BORDER_PAD
        return r if r > 0 else 0

    def _scroll_end(self) -> int:
        r = max(map(len, self.columns)) - self.screen_height
        return r if r > 0 else 0

    def adjust_scroll_past_eof(self) -> None:
        end_of_scroll = self._scroll_end()
        if self._scroll > end_of_scroll:
            self._scroll = end_of_scroll

    def draw(self) -> None:
        win = self.win
        contents = self.selector.dictionary.contents

        related_entries = current_related_entries()
        hlcolor = Color.heed | curses.A_STANDOUT | curses.A_BOLD 

        text_x = BORDER_PAD
        for col_i, column in enumerate(self.columns):
            for y, line_i in enumerate(
                    range(self._scroll, self._scroll + self.screen_height), 1
            ):
                try:
                    op_index, text, attrs = column[line_i]
                except IndexError:
                    continue

                if self.selector.is_toggled(op_index):
                    op = contents[op_index][0]
                    if op in self.selector.TOGGLEABLE:
                        selection_hl = curses.A_STANDOUT
                    elif op in related_entries:
                        selection_hl = curses.A_BOLD
                    else:
                        selection_hl = 0
                else:
                    selection_hl = 0

                try:
                    win.addstr(y, MARGIN + text_x, text, selection_hl)
                    for i, span, attr in attrs:
                        win.chgat(y, MARGIN + text_x + i, span, attr | selection_hl)
                except curses.error:  # window too small
                    return

                if self._hl is None:
                    continue

                hl_i = y + self._scroll - 1
                assert hl_i >= 0

                hlmap = self._hl.hls[col_i]
                if hl_i not in hlmap:
                    continue

                span = self._hl.span
                try:
                    for i in hlmap[hl_i]:
                        win.chgat(y, MARGIN + text_x + i, span, hlcolor)
                except curses.error:  # window too small
                    return

            text_x += self.column_width + 1

    def refresh_layout(self) -> None:
        self.columns, self.column_width = _create_layout(self.selector.dictionary, self.screen_height)
        self.adjust_scroll_past_eof()
        if self._hl is not None:
            self.highlight(self._hl.hlphrase)

    def mark_box_at(self, click_y: int, click_x: int) -> None:
        if click_y <= BORDER_PAD:
            return

        contents = self.selector.dictionary.contents

        separator_x = 0
        for column in self.columns:
            if click_x == separator_x:
                return
            elif click_x <= separator_x + self.column_width:
                assert self._scroll + click_y - 1 >= 0
                try:
                    line = column[self._scroll + click_y - 1]
                except IndexError:
                    return
                if contents[line.op_index][0] in self.selector.TOGGLEABLE:
                    self.selector.toggle_by_index(line.op_index)
                return
            else:
                separator_x += self.column_width + 1

    KEYBOARD_SELECTOR_CHARS = (
        b'1', b'2', b'3', b'4', b'5', b'6', b'7', b'8', b'9', b'0',
        b'!', b'@', b'#', b'$', b'%', b'^', b'&', b'*', b'(', b')',
    )
    def mark_box_by_selector(self, s: bytes) -> None:
        self.selector.toggle_by_def_index(self.KEYBOARD_SELECTOR_CHARS.index(s) + 1)

    def deselect_all(self) -> None:
        self.selector.clear_selection()

    def move_down(self, n: int = 2) -> None:
        if self._scroll < self._scroll_end():
            self._scroll += n
            self.adjust_scroll_past_eof()

    def move_up(self, n: int = 2) -> None:
        self._scroll -= n
        if self._scroll < 0:
            self._scroll = 0

    def go_bottom(self) -> None:
        self._scroll = self._scroll_end()

    def go_top(self) -> None:
        self._scroll = 0

    def page_down(self) -> None:
        self.move_down(self.screen_height - 2)

    def page_up(self) -> None:
        self.move_up(self.screen_height - 2)

    def highlight(self, s: str) -> None:
        hls: list[dict[int, list[int]]] = []
        nmatches = 0
        hllast_line = -1
        for column in self.columns:
            hlmap = {}
            for i, line in enumerate(column):
                indices = []

                x = line.text.find(s)
                while ~x:
                    nmatches += 1
                    indices.append(x)
                    x = line.text.find(s, x + len(s))

                if indices:
                    hlmap[i] = indices
                    if i > hllast_line:
                        hllast_line = i

            hls.append(hlmap)

        if nmatches:
            self._hl = HL(hls, nmatches, s, hllast_line)
        else:
            raise ValueError(repr(s))

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
        self.adjust_scroll_past_eof()

    def highlight_next(self) -> None:
        if self._hl is None:
            return
        for i in range(self._scroll + 1, self._hl.hllast_line + 1):
            for hlmap in self._hl.hls:
                if i in hlmap:
                    self._scroll = i
                    return

    def highlight_prev(self) -> None:
        if self._hl is None:
            return
        for i in range(self._scroll - 1, -1, -1):
            for hlmap in self._hl.hls:
                if i in hlmap:
                    self._scroll = i
                    return

    ACTIONS: dict[bytes, Callable[[Screen], None]] = {
        b'^J': highlight_clear, b'^M': highlight_clear,
        b'd': deselect_all,
        b'j': move_down, b'^N': move_down, b'KEY_DOWN': move_down,
        b'k': move_up,   b'^P': move_up,   b'KEY_UP': move_up,
        b'G': go_bottom, b'KEY_END': go_bottom,
        b'g': go_top,    b'KEY_HOME': go_top,
        b'KEY_NPAGE': page_down, b'KEY_SNEXT': page_down,
        b'KEY_PPAGE': page_up,   b'KEY_SPREVIOUS': page_up,
        b'n': highlight_next,
        b'N': highlight_prev,
    }


T = TypeVar('T')
class InteractiveCommandHandler:
    def __init__(self, screen_buffer: ScreenBuffer) -> None:
        self.screen_buffer = screen_buffer
        self.prompt = Prompt(
            screen_buffer, screen_buffer.win, exit_if_empty=False
        )

    def writeln(self, s: str) -> None:
        self.screen_buffer.status.writeln(s)

    def choose_item(self, prompt_name: str, seq: Sequence[T], default: int = 1) -> T | None:
        self.prompt.prompt = f'{prompt_name} [{default}]: '
        typed = self.prompt.run()
        if typed is None:
            return None
        typed = typed.strip()
        try:
            choice = int(typed) if typed else default
        except ValueError:
            return None
        if 0 < choice <= len(seq):
            return seq[choice - 1]
        return None

    def ask_yes_no(self, prompt_name: str, *, default: bool) -> bool:
        self.prompt.prompt = f'{prompt_name} [{"Y/n" if default else "y/N"}]: '
        typed = self.prompt.run()
        if typed is None:
            return default
        return STRING_TO_BOOL.get(typed.strip().lower(), default)


class StatusData(NamedTuple):
    header: str
    body: str | None
    color: int


class Status:
    def __init__(self, win: curses._CursesWindow, *, persistence: int) -> None:
        self.win = win
        self.persistence = persistence
        self._content: StatusData | None = None
        self._ticks = 0

    def put(self, header: str, body: str | None, color: int) -> None:
        self._ticks = 0
        self._content = StatusData(header, body, color)

    def error(self, header: str, body: str | None = None) -> None:
        self.put(header, body, curses.color_pair(BLACK_ON_RED) | curses.A_BOLD)

    def success(self, header: str, body: str | None = None) -> None:
        self.put(header, body, curses.color_pair(BLACK_ON_GREEN) | curses.A_BOLD)

    def attention(self, header: str, body: str | None = None) -> None:
        self.put(header, body, curses.color_pair(BLACK_ON_YELLOW) | curses.A_BOLD)

    def clear(self) -> None:
        self._content = None

    def tick(self) -> None:
        if self._ticks >= self.persistence:
            self._content = None
        else:
            self._ticks += 1

    def draw_if_available(self) -> bool:
        if self._content is None or env.LINES < 3:
            return False

        header, body, color = self._content
        if body is None:
            text = truncate_if_needed(header, env.COLS)
        else:
            text = truncate_if_needed(header + ' ' + body, env.COLS)

        if text is None:
            return False

        try:
            self.win.addstr(env.LINES - 1, 0, text)
        except curses.error:  # lower-left write
            pass

        self.win.chgat(env.LINES - 1, 0, len(header), color)

        return True


def draw_border(win: curses._CursesWindow, margin_bot: int) -> None:
    win.box()
    if margin_bot >= env.LINES - 1:
        return

    win.move(env.LINES - margin_bot - 2, 0)
    for _ in range(margin_bot):
        win.deleteln()


class ScreenBuffer:
    def __init__(self, win: curses._CursesWindow, screens: Sequence[Screen]) -> None:
        self.win = win
        self.screens = screens
        self.status = Status(win, persistence=7)
        self._cursor = 0

    @property
    def current(self) -> Screen:
        return self.screens[self._cursor]

    def next(self) -> Screen:
        if self._cursor < len(self.screens) - 1:
            self._cursor += 1
        return self.current

    def previous(self) -> Screen:
        if self._cursor > 0:
            self._cursor -= 1
        return self.current

    @contextlib.contextmanager
    def extra_margin(self, v: int) -> Iterator[None]:
        screen = self.current
        t = screen.margin_bot
        screen.margin_bot += v
        yield
        screen.margin_bot = t

    def _draw_border(self, margin_bot: int) -> None:
        screen = self.current
        win = self.win

        draw_border(win, margin_bot)

        header = truncate_if_needed(screen.selector.dictionary.contents[0][1], env.COLS - 8)
        if header is not None:
            win.addstr(0, 2, f'[ {header} ]')
            win.chgat(0, 4, len(header), Color.delimit | curses.A_BOLD)

        shift = BORDER_PAD + screen.column_width
        screen_height = screen.screen_height
        try:
            for i in range(1, len(screen.columns)):
                win.vline(BORDER_PAD, i * shift, 0, screen_height)
        except curses.error:
            pass

        items = []
        items_attr_values = []

        if screen.is_highlight_active():
            match_hint = f'MATCHES: {screen.highlight_nmatches}'
            items.append(match_hint)
            items_attr_values.append(
                (len(match_hint), curses.A_BOLD, 2)
            )

        if len(self.screens) > 1:
            screen_hint = f'{self._cursor + 1}/{len(self.screens)}'
            items.append(screen_hint)
            items_attr_values.append((len(screen_hint), curses.A_BOLD, 0))

        if not items:
            return

        btext = truncate_if_needed('╶╴'.join(items), env.COLS - 4)
        if btext is None:
            return

        y = env.LINES - margin_bot - 1
        x = env.COLS - len(btext) - 3
        win.addstr(y, x, f'╴{btext}╶')
        for i, span, attr in compose_attrs(
                items_attr_values,
                width=env.COLS - 4,
                start=1
        ):
            win.chgat(y, x + i, span, attr)

    def _draw_function_bar(self) -> None:
        bar = truncate_if_needed('F1 Help  F2 Anki-config', env.COLS)
        if bar is None:
            return

        attrs = compose_attrs(
            (
                (2, curses.A_STANDOUT | curses.A_BOLD, 7),
                (2, curses.A_STANDOUT | curses.A_BOLD, 11),
            ), width=env.COLS
        )
        win = self.win
        y = env.LINES - 1

        try:
            win.addstr(y, 0, bar)
        except curses.error:  # left lowermost corner
            pass

        for index, span, attr in attrs:
            win.chgat(y, index, span, attr)

    def draw(self) -> None:
        if env.COLS < 2:
            return

        self.win.erase()
        self.win.attrset(Color.delimit)

        screen = self.current

        if screen.margin_bot < 1:
            screen.margin_bot = 1

        self._draw_border(screen.margin_bot)
        if not self.status.draw_if_available():
            self._draw_function_bar()

        screen.draw()

    def resize(self) -> None:
        terminal_resize()

        for screen in self.screens:
            screen.refresh_layout()

        self.win.clearok(True)

    def highlight_prompt(self) -> None:
        typed = Prompt(self, self.win, 'Find in entries: ').run()
        if typed is not None and typed.strip():
            try:
                self.current.highlight(typed)
            except ValueError as e:
                self.status.error('Nothing matches', str(e))

    def _dispatch_command(self, s: str) -> bool:
        args = s.split()
        cmd = args[0]
        if cmd in NO_HELP_ARG_COMMANDS:
            result = NO_HELP_ARG_COMMANDS[cmd](*args)
        elif cmd in HELP_ARG_COMMANDS:
            func, note, usage = HELP_ARG_COMMANDS[cmd]
            if (len(args) == 1 or
               (len(args) == 2 and args[1].strip(' -').lower() in ('h', 'help'))
            ):
                self.status.attention(note, f'{cmd} {usage}')
                return True
            else:
                result = func(*args)
        elif cmd in INTERACTIVE_COMMANDS:
            # change margin_bot to leave one line for the prompt.
            #with self.status.change(margin_bot=1, lock=True):
            #    result = INTERACTIVE_COMMANDS[cmd](
            #        InteractiveCommandHandler(self), *args
            #    )
            #self.status.writer.buffer.clear()
            raise NotImplementedError
        elif cmd.startswith('-'):
            self.status.error(f'{cmd}: command not found')
            return True
        else:
            return False

        out, err, reason = result
        if out:
            self.status.clear()
            #if out.count('\n') < self.status.writer.screen_coverage * env.LINES - 2:
            #    self.status.writeln(out)
            #else:
            Pager(self.win, out).run()

        if err:
            self.status.error(err, reason)

        return True

    def search_prompt(self, *, pretype: str = '') -> tuple[ScreenBuffer, QuerySettings] | None:
        pretype = ' '.join(pretype.split())
        typed = Prompt(self, self.win, 'Search $ ', pretype=pretype).run()
        if typed is None:
            return None
        typed = typed.strip()
        if not typed:
            return None

        if self._dispatch_command(typed):
            self.current.refresh_layout()
            return None

        ret = search_dictionaries(RefreshWriter(self), typed)
        if ret is None:
            return None

        dictionaries, settings = ret

        return ScreenBuffer(self.win, tuple(Screen(self.win, x) for x in dictionaries)), settings

    ACTIONS = {
        b'KEY_RESIZE': resize, b'^L': resize,
        b'l': next,     b'KEY_RIGHT': next,
        b'h': previous, b'KEY_LEFT': previous,
        b'^F': highlight_prompt, b'KEY_F(4)': highlight_prompt,
    }


def perror_clipboard_or_selection(status: Status) -> str | None:
    try:
        return clipboard_or_selection()
    except ValueError as e:
        status.error(str(e))
    except LookupError as e:
        status.error(
            f'Could not access the {"clipboard" if WINDOWS else "primary selection"}:',
            str(e)
        )

    return None


def perror_currently_reviewed_phrase(status: Status) -> str | None:
    try:
        return anki.currently_reviewed_phrase()
    except anki.AnkiError as e:
        status.error('Paste from the "Phrase" field failed:', str(e))
        return None


SEARCH_ENTER_ACTIONS = {
    b'p': perror_clipboard_or_selection,
    b'P': perror_currently_reviewed_phrase,
    b'-': lambda _: '-',
    b'/': lambda _: '',
}


class COption(NamedTuple):
    name: str
    description: str
    constraint: list[str] | None


class CColumn(NamedTuple):
    header: str
    options: list[COption]

    @property
    def noptions(self) -> int:
        return len(self.options)

    def __getitem__(self, key: int) -> COption:
        return self.options[key]


class CRow(NamedTuple):
    columns: list[CColumn]

    @property
    def height(self) -> int:
        return max(x.noptions for x in self.columns) + 1

    def __getitem__(self, key: int) -> CColumn:
        return self.columns[key]


class ConfigMenu:
    OPTION_NAME_WIDTH = 13
    OPTION_VALUE_WIDTH = 10
    COLUMN_WIDTH = OPTION_NAME_WIDTH + OPTION_VALUE_WIDTH
    COLUMN_PAD = 3

    def __init__(self, win: curses._CursesWindow, column_grid: list[CRow], min_y: int, min_x: int) -> None:
        self.win = win
        self.column_grid = column_grid
        self.min_y = min_y
        self.min_x = min_x
        self.margin_bot = 0
        self._row = self._col = self._line = 0

    @contextlib.contextmanager
    def extra_margin(self, v: int) -> Iterator[None]:
        t = self.margin_bot
        self.margin_bot += v
        yield
        self.margin_bot = t

    def _value_of_option(self, option: COption) -> tuple[str, Attr]:
        if isinstance(config[option.name], bool):
            if config[option.name]:
                return 'ON', Attr(0, 2, Color.success)
            else:
                return 'OFF', Attr(0, 3, Color.err)
        else:
            return str(config[option.name]), Attr(0, 0, 0)

    def _description_of_option(self, option: COption) -> str:
        if option.constraint is not None:
            return f'{option.description} ({"/".join(option.constraint)})'
        else:
            return option.description

    def draw(self) -> None:
        if env.COLS < self.min_x or env.LINES < self.min_y:
            raise ValueError(f'window too small (need at least {self.min_x}x{self.min_y})')

        win = self.win
        width = env.COLS - 2*BORDER_PAD

        win.erase()

        draw_border(win, self.margin_bot)

        current_option = self.column_grid[self._row][self._col][self._line]
        optdesc = truncate_if_needed(self._description_of_option(current_option), width)
        if optdesc is None:
            return

        value, attr = self._value_of_option(current_option)
        value = truncate_if_needed(f'-> {value}', width)
        if value is None:
            return

        win.addstr(BORDER_PAD, BORDER_PAD, optdesc)
        win.addstr(BORDER_PAD + 1, BORDER_PAD, value)
        # TODO: `BORDER_PAD + 3` might break.
        win.chgat(BORDER_PAD + 1, BORDER_PAD + 3 + attr.i, attr.span, attr.attr)
        win.hline(BORDER_PAD + 2, BORDER_PAD, curses.ACS_HLINE, width)

        row_y = BORDER_PAD + 3
        row_x = 1
        for row_i, row in enumerate(self.column_grid):
            for col_i, column in enumerate(row.columns):
                win.addstr(
                    row_y,
                    row_x,
                    f'{column.header:{self.COLUMN_WIDTH}s}',
                    curses.A_BOLD | curses.A_UNDERLINE
                )
                for line_i, option in enumerate(column.options):
                    if (
                            self._row == row_i
                        and self._col == col_i
                        and self._line == line_i
                    ):
                        selection_hl = curses.A_STANDOUT | curses.A_BOLD
                    else:
                        selection_hl = 0

                    value, attr = self._value_of_option(option)

                    entry = truncate_if_needed(
                        f'{option.name:{self.OPTION_NAME_WIDTH}s}{value:{self.OPTION_VALUE_WIDTH}s}',
                        self.COLUMN_WIDTH
                    )
                    if entry is None:
                        return

                    y = row_y + line_i + 1
                    win.addstr(y, row_x, entry, selection_hl)
                    win.chgat(y, row_x + 13 + attr.i, attr.span, attr.attr | selection_hl)

                row_x += self.COLUMN_WIDTH + self.COLUMN_PAD

            row_y += row.height + 1
            row_x = 1

    def resize(self) -> None:
        terminal_resize()
        self.win.clearok(True)

    def _rows_in_current_column(self) -> int:
        result = 0
        for row in self.column_grid:
            try:
                row[self._col]
            except IndexError:
                break
            else:
                result += 1

        return result

    def move_down(self) -> None:
        line_bound = self.column_grid[self._row][self._col].noptions - 1
        if self._line < line_bound:
            self._line += 1
            return

        if self._row < self._rows_in_current_column() - 1:
            self._row += 1
            self._line = 0

    def move_up(self) -> None:
        if self._line > 0:
            self._line -= 1
            return

        if self._row > 0:
            self._row -= 1
            self._line = self.column_grid[self._row][self._col].noptions - 1

    def move_right(self) -> None:
        column_bound = max(len(x.columns) for x in self.column_grid) - 1
        if self._col >= column_bound:
            return

        self._col += 1

        row_column_bound = self._rows_in_current_column() - 1
        if self._row > row_column_bound:
            self._row = row_column_bound

        line_bound = self.column_grid[self._row][self._col].noptions - 1
        if self._line > line_bound:
            self._line = line_bound

    def move_left(self) -> None:
        if self._col <= 0:
            return

        self._col -= 1

        line_bound = self.column_grid[self._row][self._col].noptions - 1
        if self._line > line_bound:
            self._line = line_bound

    def change_selected(self) -> None:
        name, _, constraint = self.column_grid[self._row][self._col][self._line]
        if isinstance(config[name], bool):
            config[name] = not config[name]
            return

        if not isinstance(config[name], str):
            return

        if constraint is None:
            with self.extra_margin(1):
                typed = Prompt(
                    self, self.win, 'Enter new value: ', pretype=config[name], exit_if_empty=True
                ).run()
            if typed is not None:
                config[name] = typed.strip()
        else:
            config[name] = constraint[
                (constraint.index(config[name]) + 1) % len(constraint)
            ]

    ACTIONS: dict[bytes, Callable[[ConfigMenu], None]] = {
        b'KEY_RESIZE': resize, b'^L': resize,
        b'j': move_down,  b'KEY_DOWN': move_down,
        b'k': move_up,    b'KEY_UP': move_up,
        b'l': move_right, b'KEY_RIGHT': move_right,
        b'h': move_left,  b'KEY_LEFT': move_left,
        b'^J': change_selected, b'^M': change_selected,
    }
    def run(self) -> None:
        while True:
            self.draw()

            c = curses.keyname(get_key(self.win))
            if c in self.ACTIONS:
                self.ACTIONS[c](self)
            elif c in (b'q', b'Q', b'^X', b'KEY_F(2)'):
                return


CONFIG_COLUMNS: list[CRow] = [
    CRow(
    [
        CColumn(
        'Cards',
        [
            COption('-pos', 'Add parts of speech', None),
            COption('-etym', 'Add etymologies', None),
            COption('-exsen', 'Add example sentences', None),
            COption('-formatdefs', 'Add HTML formatting to definitions', None),
            COption('-hidedef', 'Replace target word with `-hides` in definitions', None),
            COption('-hidesyn', 'Replace target word with `-hides` in synonyms', None),
            COption('-hideexsen', 'Replace target word with `-hides` in example sentences', None),
            COption('-hidepreps', 'Replace all prepositions with `-hides`', None),
            COption('-hides', 'Sequence of characters to use as target word replacement', None),
        ]
        ),
        CColumn(
        'Anki-connect',
        [
            COption('-note', 'Note used for adding cards', None),
            COption('-deck', 'Deck used for adding cards', None),
            COption('-mediapath', 'Audio save location', None),
            COption('-duplicates', 'Allow duplicates', None),
            COption('-dupescope', 'Look for duplicates in', ['deck', 'collection']),
            COption('-tags', 'Anki tags (comma separated list)', None),
        ]
        ),
    ]),
    CRow(
    [
        CColumn(
        'Sources',
        [
            COption('-dict', 'Primary dictionary', ['ahd', 'farlex', 'wordnet']),
            COption('-dict2', 'Secondary dictionary', ['ahd', 'farlex', 'wordnet', '-']),
            COption('-audio', 'Audio source', ['auto', 'ahd', 'diki', '-']),
        ]),
        CColumn(
        'Miscellaneous',
        [
            COption('-toipa', 'Translate AH Dictionary phonetic spelling into IPA', None),
            COption('-shortetyms', 'Shorten and simplify etymologies in AH Dictionary', None),
            COption('-textwrap', 'Text wrapping style', ['regular', 'justify']),
        ]),
    ]),
]

CONFIG_MIN_HEIGHT = (
      sum(x.height for x in CONFIG_COLUMNS)
    + (len(CONFIG_COLUMNS) - 1)
)

CONFIG_MIN_WIDTH = (
      len(CONFIG_COLUMNS) * ConfigMenu.COLUMN_WIDTH
    + (len(CONFIG_COLUMNS) - 1) * ConfigMenu.COLUMN_PAD
)


def _curses_main(
        stdscr: curses._CursesWindow,
        _dictionaries: list[Dictionary],
        _settings: QuerySettings
) -> None:
    update_global_lines_cols()

    # Resizing the terminal after calling curses.endwin inserts the resize
    # character into the buffer. Let's always start with a fresh buffer.
    curses.flushinp()

    settings = _settings
    screen_buffer = ScreenBuffer(stdscr, tuple(Screen(stdscr, x) for x in _dictionaries))
    while True:
        screen_buffer.status.tick()
        screen_buffer.draw()

        c = curses.keyname(get_key(stdscr))
        if c in Screen.ACTIONS:
            Screen.ACTIONS[c](screen_buffer.current)

        elif c in Screen.KEYBOARD_SELECTOR_CHARS:
            screen_buffer.current.mark_box_by_selector(c)

        elif c in ScreenBuffer.ACTIONS:
            ScreenBuffer.ACTIONS[c](screen_buffer)

        elif c == b'KEY_MOUSE':
            _, x, y, _, bstate = curses.getmouse()
            if bstate & curses.BUTTON1_PRESSED:  # left mouse
                screen_buffer.current.mark_box_at(y, x)
            elif bstate & curses.BUTTON4_PRESSED:  # mouse wheel
                screen_buffer.current.move_up()
            elif bstate & BUTTON5_PRESSED:  # mouse wheel
                screen_buffer.current.move_down()
            elif mouse_wheel_clicked(bstate):
                pretype = perror_clipboard_or_selection(screen_buffer.status)
                if pretype is None:
                    continue
                ret = screen_buffer.search_prompt(pretype=pretype)
                if ret is not None:  # new query
                    screen_buffer, settings = ret

        elif c in SEARCH_ENTER_ACTIONS:
            pretype = SEARCH_ENTER_ACTIONS[c](screen_buffer.status)
            if pretype is None:
                continue
            ret = screen_buffer.search_prompt(pretype=pretype)
            if ret is not None:  # new query
                screen_buffer, settings = ret

        elif c == b'B':
            try:
                anki.invoke('guiBrowse', query='added:1')
            except anki.AnkiError as e:
                screen_buffer.status.error('Could not open the card browser:', str(e))
            else:
                screen_buffer.status.success('Anki card browser opened')

        elif c == b'C':
            selections = screen_buffer.current.selector.dump_selection()
            if selections is None:
                screen_buffer.status.error('Nothing selected')
            else:
                create_and_add_card(
                    CardWriter(screen_buffer),
                    screen_buffer.current.selector.dictionary.name,
                    selections,
                    settings
                )
                screen_buffer.current.deselect_all()

        elif c == b'KEY_F(1)':
            screen_buffer.status.attention(
                'Help commands:', '--help-{config|console|curses|define-all|rec}'
            )

        elif c == b'KEY_F(2)':
            try:
                ConfigMenu(
                    stdscr,
                    CONFIG_COLUMNS,
                    CONFIG_MIN_HEIGHT + 2*BORDER_PAD + 3,
                    CONFIG_MIN_WIDTH + 2*BORDER_PAD
                ).run()
            except ValueError as e:
                screen_buffer.status.error('Error(F2):', str(e))

            screen_buffer.resize()

        elif c in (b'q', b'Q', b'^X'):
            return


def curses_entry(dictionaries: list[Dictionary], settings: QuerySettings) -> None:
    stdscr = curses.initscr()
    try:
        hide_cursor()
        stdscr.keypad(True)

        curses.cbreak()
        curses.noecho()
        curses.mousemask(-1)
        curses.mouseinterval(0)

        init_colors()

        _curses_main(stdscr, dictionaries, settings)
    finally:
        # Clear the whole window to prevent a flash
        # of contents from the previous drawing.
        stdscr.erase()
        curses.endwin()
