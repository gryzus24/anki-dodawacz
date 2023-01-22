from __future__ import annotations

import curses
from typing import Callable, Iterator, NamedTuple, TYPE_CHECKING

from src.Curses.color import Color
from src.Curses.util import (
    Attr,
    BORDER_PAD,
    FUNCTION_BAR_PAD,
    MARGIN,
    compose_attrs,
    truncate_if_needed,
)
from src.Dictionaries.dictionary_base import EntrySelector
from src.data import config

if TYPE_CHECKING:
    from src.Dictionaries.dictionary_base import Dictionary

AUTO_COLUMN_WIDTH = 52
MINIMUM_COLUMN_WIDTH = 26


class Wrapper:
    # TODO: Add justify.
    def __init__(self, textwidth: int):
        self.textwidth = textwidth
        self._cur = 0

    @property
    def current_line_pos(self) -> int:
        return self._cur

    def wrap(self, s: str, initial: str | int, indent: str) -> Iterator[str]:
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
    index = 0
    wrapper = Wrapper(column_width)

    result: list[ParsedLine] = []

    def ADD_LINE(line: str, attrs: list[Attr]) -> None:
        result.append(ParsedLine(i, truncate_if_needed(line, column_width) or '', attrs))

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

            def_color = Color.def1 if index % 2 else Color.def2

            lines = wrapper.wrap(_def, f'{sign}{index} {_label}', (index_len + 2) * ' ')
            attrs = compose_attrs(
                (
                    (len(sign), Color.sign, 0),
                    (index_len, Color.index, 1),
                    (label_len, Color.label, 0),
                    (column_width, def_color, 0),
                ), width=column_width
            )
            ADD_LINE(next(lines), attrs)
            for line in lines:
                ADD_LINE(line, [Attr(0, column_width, def_color)])

            if _exsen:
                for ex in _exsen.split('<br>'):
                    for line in wrapper.wrap(ex, (index_len + 1) * ' ', (index_len + 2) * ' '):
                        ADD_LINE(line, [Attr(0, column_width, Color.exsen)])

        elif op == 'LABEL':
            label, inflections = entry[1], entry[2]
            ADD_LINE('', [Attr(0, 0, 0)])
            if label:
                if inflections:
                    *lines, last_line = wrapper.wrap(label, ' ', ' ')  # type: ignore[assignment]
                    for line in lines:
                        ADD_LINE(line, [Attr(0, column_width, Color.label)])

                    mutual_attrs = compose_attrs(
                        (
                            (len(last_line), Color.label, 1),
                            (column_width, Color.inflection, 0),
                        ), width=column_width
                    )
                    lines = wrapper.wrap(inflections, wrapper.current_line_pos + 1, ' ')
                    ADD_LINE(last_line + ' ' + next(lines), mutual_attrs)

                    for line in lines:
                        ADD_LINE(line, [Attr(0, column_width, Color.inflection)])
                else:
                    for line in wrapper.wrap(label, ' ', ' '):
                        ADD_LINE(line, [Attr(0, column_width, Color.label)])

        elif op == 'PHRASE':
            phrase, phon = entry[1], entry[2]
            if phon:
                *lines, last_line = wrapper.wrap(phrase, ' ', ' ')  # type: ignore[assignment]
                for line in lines:
                    ADD_LINE(line, [Attr(0, column_width, Color.phrase)])

                lines = wrapper.wrap(phon, wrapper.current_line_pos + 1, ' ')
                mutual_attrs = compose_attrs(
                    (
                        (len(last_line), Color.phrase, 1),
                        (column_width, Color.phon, 0),
                    ), width=column_width
                )
                ADD_LINE(last_line + ' ' + next(lines), mutual_attrs)

                for line in lines:
                    ADD_LINE(line, [Attr(0, column_width, Color.phon)])
            else:
                for line in wrapper.wrap(phrase, ' ', ' '):
                    ADD_LINE(line, [Attr(0, column_width, Color.phrase)])

        elif op == 'HEADER':
            if i == 0:
                continue

            title = entry[1]
            if title:
                attrs = compose_attrs(
                    (
                        (3, Color.delimit, 0),
                        (len(title), Color.delimit | curses.A_BOLD, 0),
                        (column_width, Color.delimit, 0),
                    ), width=column_width
                )

                ADD_LINE(f'─[ {title} ]{(column_width - len(title) - 5) * "─"}', attrs)
            else:
                ADD_LINE(column_width * '─', [Attr(0, column_width, Color.delimit)])

        elif op == 'ETYM':
            etym = entry[1]
            if etym:
                ADD_LINE('', [Attr(0, 0, 0)])
                for line in wrapper.wrap(etym, ' ', ' '):
                    ADD_LINE(line, [Attr(0, column_width, Color.etym)])

        elif op == 'POS':
            if entry[1].strip(' |'):
                ADD_LINE('', [Attr(0, 0, 0)])
                for elem in entry[1:]:
                    pos, phon = elem.split('|')
                    *lines, last_line = wrapper.wrap(pos, ' ', ' ')  # type: ignore[assignment]
                    for line in lines:
                        ADD_LINE(line, [Attr(0, column_width, Color.phrase)])

                    lines = wrapper.wrap(phon, wrapper.current_line_pos + 1, ' ')
                    mutual_attrs = compose_attrs(
                        (
                            (len(last_line), Color.pos, 1),
                            (column_width, Color.phon, 0),
                        ), width=column_width
                    )
                    ADD_LINE(last_line + ' ' + next(lines), mutual_attrs)

                    for line in lines:
                        ADD_LINE(line, [Attr(0, column_width, Color.phon)])

        elif op == 'AUDIO':
            pass

        elif op == 'SYN':
            synonyms = entry[1]
            gloss = entry[2]
            examples = entry[3]
            for line in wrapper.wrap(synonyms, ' ', ' '):
                ADD_LINE(line, [Attr(0, column_width, Color.syn)])

            for line in wrapper.wrap(gloss, ': ', ' '):
                ADD_LINE(line, [Attr(0, column_width, Color.syngloss)])

            for ex in examples.split('<br>'):
                for line in wrapper.wrap(ex, ' ', '  '):
                    ADD_LINE(line, [Attr(0, column_width, Color.exsen)])

        elif op == 'NOTE':
            lines = wrapper.wrap(entry[1], '> ', '  ')
            attrs = compose_attrs(
                (
                    (1, Color.heed | curses.A_BOLD, 0),
                    (column_width, curses.A_BOLD, 0),
                ), width=column_width
            )
            ADD_LINE(next(lines), attrs)
            for line in lines:
                ADD_LINE(line, [Attr(0, column_width, curses.A_BOLD)])

        else:
            raise AssertionError(f'unreachable dictionary op: {op!r}')

    return result


def current_related_entries() -> set[str]:
    result = {'PHRASE'}
    if config['audio']:
        result.add('AUDIO')
    if config['pos']:
        result.add('POS')
    if config['etym']:
        result.add('ETYM')
    return result


def _create_layout(dictionary: Dictionary, height: int) -> tuple[list[list[ParsedLine]], int]:
    width = curses.COLS - 2*BORDER_PAD + 1
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

    columns: list[list[ParsedLine]] = [[] for _ in range(ncolumns)]
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
    HEADER_PAD = 1

    def __init__(self, win: curses._CursesWindow, dictionary: Dictionary) -> None:
        self.win = win
        self.selector = EntrySelector(dictionary)

        # self.margin_bot is needed for `self.screen_height`
        self.margin_bot = FUNCTION_BAR_PAD
        self.columns, self.column_width = _create_layout(dictionary, self.screen_height)
        self._hl: HL | None = None
        self._scroll = 0

    @property
    def screen_height(self) -> int:
        r = curses.LINES - Screen.HEADER_PAD - self.margin_bot - 1
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
        screen_height = self.screen_height

        vline_x = BORDER_PAD + self.column_width
        try:
            for _ in range(len(self.columns) - 1):
                win.vline(Screen.HEADER_PAD, vline_x, 0, screen_height)
                vline_x += self.column_width + 1
        except curses.error:  # window too small
            return

        related_entries = current_related_entries()
        hl_attr = Color.heed | curses.A_STANDOUT | curses.A_BOLD

        text_x = BORDER_PAD + MARGIN
        for col_i, column in enumerate(self.columns):
            for y, line_i in enumerate(
                    range(self._scroll, self._scroll + screen_height), 1
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
                    win.addstr(y, text_x, text, selection_hl)
                    for i, span, attr in attrs:
                        win.chgat(y, text_x + i, span, attr | selection_hl)
                except curses.error:  # window too small
                    return

                if self._hl is None:
                    continue

                hlmap = self._hl.hls[col_i]
                if line_i not in hlmap:
                    continue

                span = self._hl.span
                try:
                    for i in hlmap[line_i]:
                        win.chgat(y, text_x + i, span, hl_attr)
                except curses.error:  # window too small
                    return

            text_x += self.column_width + 1

    def resize(self) -> None:
        self.columns, self.column_width = _create_layout(self.selector.dictionary, self.screen_height)
        self.adjust_scroll_past_eof()
        if self._hl is not None:
            self.hlsearch(self._hl.hlphrase)

    def mark_box_at(self, click_y: int, click_x: int) -> None:
        if click_y < Screen.HEADER_PAD or click_y >= curses.LINES - self.margin_bot:
            return

        contents = self.selector.dictionary.contents

        click_range_x = BORDER_PAD
        for column in self.columns:
            if click_range_x <= click_x < click_range_x + self.column_width:
                assert self._scroll + click_y - 1 >= 0
                try:
                    line = column[self._scroll + click_y - 1]
                except IndexError:
                    return
                if contents[line.op_index][0] in self.selector.TOGGLEABLE:
                    self.selector.toggle_by_index(line.op_index)
                return

            click_range_x += self.column_width + 1

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

    def hlsearch(self, s: str) -> None:
        against_lowercase = s.islower()

        hls: list[dict[int, list[int]]] = []
        nmatches = 0
        hllast_line = -1
        for column in self.columns:
            hlmap = {}
            for i, (_, text, _) in enumerate(column):
                if against_lowercase:
                    text = text.lower()

                indices = []
                x = text.find(s)
                while ~x:
                    nmatches += 1
                    indices.append(x)
                    x = text.find(s, x + len(s))

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
    def hl(self) -> HL | None:
        return self._hl

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

    def dispatch(self, key: bytes) -> bool:
        if key in self.ACTIONS:
            self.ACTIONS[key](self)
            return True
        if key in self.KEYBOARD_SELECTOR_CHARS:
            self.mark_box_by_selector(key)
            return True

        return False
