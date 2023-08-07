from __future__ import annotations

import curses
from typing import Callable
from typing import Mapping
from typing import NamedTuple
from typing import Sequence
from typing import TYPE_CHECKING

from src.Curses.color import Color
from src.Curses.util import Attr
from src.Curses.util import BORDER_PAD
from src.Curses.util import compose_attrs
from src.Curses.util import HIGHLIGHT
from src.Curses.util import truncate
from src.data import config
from src.Dictionaries.base import AUDIO
from src.Dictionaries.base import DEF
from src.Dictionaries.base import EntrySelector
from src.Dictionaries.base import ETYM
from src.Dictionaries.base import HEADER
from src.Dictionaries.base import LABEL
from src.Dictionaries.base import NOTE
from src.Dictionaries.base import PHRASE
from src.Dictionaries.base import POS
from src.Dictionaries.base import SYN

if TYPE_CHECKING:
    from src.Dictionaries.base import Dictionary
    from src.Dictionaries.base import op_t

AUTO_COLUMN_WIDTH = 52
COLUMN_MARGIN = 1


class FLine(NamedTuple):
    op_indx: int
    text: str
    attrs: list[Attr]


def _next_hl(hls: Sequence[tuple[int, int]], hl_i: int) -> tuple[int, int, int]:
    try:
        while True:
            hl_i += 1
            span_left, attr = hls[hl_i]
            if span_left > 0:
                return hl_i, span_left, attr
    except IndexError:
        # TODO: If handling of incomplete hls is ever desired.
        w = sum(x[0] for x in hls)
        raise AssertionError(f'sum of lengths of hls spans ({w}) < len(s)')


def wrap(
        dest: list[FLine],
        op_indx: int,
        s: str,
        hls: Sequence[tuple[int, int]],
        column_width: int, *,
        indent: str = ''
) -> None:
    # displaying '\n' and '\r' is undesirable
    for c in '\n\r':
        if c in s:
            s = s.replace(c, ' ')

    s_len = len(s)

    # fast path
    if s_len <= column_width:
        attr_i = 0
        attrs = []
        for span, attr in hls:
            attrs.append(Attr(attr_i, span, attr))
            attr_i += span

        dest.append(FLine(op_indx, s, attrs))
        return

    cur_indent = ''
    hl_i = attr_i = line_i = brk_i = cur_indent_len = 0
    indent_len = len(indent)
    width = column_width

    span_left, attr = hls[hl_i]
    attrs = []

    # skipping preceding spaces to avoid line breaks
    # if there is not enough space for single words.
    while s[brk_i] == ' ':
        brk_i += 1

    brk_i = s.find(' ', brk_i + 1)
    if brk_i == -1:
        brk_i = 0

    break_line = word_cannot_fit = brk_i > width
    overflow = False

    def PUSH_LINE(_line: str) -> None:
        _attr_i = cur_indent_len + attr_i
        if overflow:
            _trunc_line = truncate(_line, width)
            if _trunc_line is None:
                return
            # -1: space for the truncation character "»"
            _span = width - _attr_i - 1
            if _span > 0:
                attrs.append(Attr(_attr_i, _span, attr))
            attrs.append(Attr(width - 1, 1, Color.err | curses.A_STANDOUT))
            dest.append(FLine(op_indx, _trunc_line, attrs))
        else:
            span = line_i - attr_i
            if span > 0:
                attrs.append(Attr(_attr_i, span, attr))
                dest.append(FLine(op_indx, _line, attrs))
            else:
                raise AssertionError('unreachable')

    for i in range(s_len):
        if line_i == brk_i:
            e = s.find(' ', i + 1)
            if e != -1:
                brk_i += e - i
            else:
                brk_i += s_len - i

            break_line = brk_i > width - cur_indent_len
            word_cannot_fit = break_line and not line_i

        if not break_line:
            if not span_left:
                span = line_i - attr_i
                if span > 0:
                    attrs.append(Attr(attr_i + cur_indent_len, span, attr))
                    attr_i = line_i

                hl_i, span_left, attr = _next_hl(hls, hl_i)

            line_i += 1
        elif word_cannot_fit:
            if not span_left:
                hl_i, span_left, attr = _next_hl(hls, hl_i)

            line_i += 1
            overflow = True
        else:
            PUSH_LINE(cur_indent + s[i - line_i:i])

            if not span_left:
                hl_i, span_left, attr = _next_hl(hls, hl_i)

            cur_indent = indent
            cur_indent_len = indent_len
            attr_i = line_i = brk_i = 0
            attrs = []
            overflow = False

        span_left -= 1

    if line_i:
        PUSH_LINE(cur_indent + s[-line_i:])


def format_dictionary(dictionary: Dictionary, width: int) -> list[FLine]:
    indent_weight = 0 if width > AUTO_COLUMN_WIDTH / 2 else -width

    index = 0
    result: list[FLine] = []
    for i, op in enumerate(dictionary.contents):
        if isinstance(op, DEF):
            index += 1
            index_len = len(str(index))
            indent = (indent_weight + index_len + 2) * ' '

            sign = ' ' if op.subdef else '>'
            label = '{' + op.label + '} ' if op.label else ''

            wrap(result, i, f'{sign}{index} {label}{op.definition}',
                (
                    (1, Color.sign),
                    (index_len + 1, Color.index),
                    (len(label), Color.label),
                    (len(op.definition), Color.def1 if index % 2 else Color.def2)
                ), width, indent=indent)

            predent = (indent_weight + index_len + 1) * ' '
            for example in op.examples:
                wrap(result, i, predent + example,
                    (
                        (len(predent), 0),
                        (len(example), Color.exsen)
                    ), width, indent=indent or ' ')

        elif isinstance(op, LABEL):
            result.append(FLine(i, '', []))
            if not op.label:
                continue

            if op.extra:
                wrap(result, i, f'{op.label}  {op.extra}',
                    (
                        (len(op.label) + 2, Color.label),
                        (len(op.extra), Color.infl)
                    ), width)
            else:
                wrap(result, i, op.label,
                    ((len(op.label), Color.label),),
                    width)

        elif isinstance(op, PHRASE):
            if op.extra:
                wrap(result, i, f'{op.phrase}  {op.extra}',
                    (
                        (len(op.phrase) + 2, Color.phrase),
                        (len(op.extra), Color.phon)
                    ), width)
            else:
                wrap(result, i, op.phrase,
                    ((len(op.phrase), Color.phrase),),
                    width)

        elif isinstance(op, HEADER):
            if i == 0:
                continue

            if op.header:
                header = truncate(op.header, width - 6)
                if header is None:
                    buf = width * '─'
                    attrs = [Attr(0, width, Color.delimit)]
                else:
                    buf = f'─[ {header} ]{(width - len(header) - 6) * "─"}─'
                    attrs = compose_attrs(
                        (
                            (3, Color.delimit, 0),
                            (len(header), Color.delimit | curses.A_BOLD, 0),
                            (width, Color.delimit, 0),
                        ), width=width
                    )
            else:
                buf = width * '─'
                attrs = [Attr(0, width, Color.delimit)]

            result.append(FLine(i, buf, attrs))

        elif isinstance(op, AUDIO):
            pass

        elif isinstance(op, ETYM):
            result.append(FLine(i, '', []))
            wrap(result, i, op.etymology,
                ((len(op.etymology), Color.etym),),
                width)

        elif isinstance(op, POS):
            result.append(FLine(i, '', []))
            for pos, phon in op.pos:
                wrap(result, i, f'{pos}  {phon}',
                    (
                        (len(pos) + 2, Color.pos),
                        (len(phon), Color.phon)
                    ), width)

        elif isinstance(op, SYN):
            index += 1
            indent = (indent_weight + 2) * ' '

            wrap(result, i, op.synonyms,
                ((len(op.synonyms), Color.syn),),
                width)

            wrap(result, i, f': {op.definition}',
                (
                    (len(op.definition) + 2, Color.def1 if index % 2 else Color.def2),
                ), width, indent=indent)

            for example in op.examples:
                wrap(result, i, ' ' + example,
                    (
                        (1, 0),
                        (len(example), Color.exsen),
                    ), width, indent=indent)

        elif isinstance(op, NOTE):
            buf = f'> {op.note}'
            if len(buf) < AUTO_COLUMN_WIDTH:
                buf = truncate(buf, width)  # type: ignore[assignment]
                if buf is None:
                    continue  # type: ignore[unreachable]
                attrs = compose_attrs(
                    (
                        (2, Color.heed | curses.A_BOLD, 0),
                        (len(op.note), curses.A_BOLD, 0),
                    ), width=width
                )
                result.append(FLine(i, buf, attrs))
            else:
                wrap(result, i, buf,
                    (
                        (2, Color.heed | curses.A_BOLD),
                        (len(op.note), curses.A_BOLD)
                    ), width)

        else:
            raise AssertionError(f'unreachable {op!r}')

    return result


def currently_selected_ops() -> tuple[type[op_t], ...]:
    result: list[type[op_t]] = [PHRASE]
    if config['audio']:
        result.append(AUDIO)
    if config['pos']:
        result.append(POS)
    if config['etym']:
        result.append(ETYM)

    return tuple(result)


def layout(
        dictionary: Dictionary,
        height: int
) -> tuple[list[list[FLine]], int]:
    width = curses.COLS - 2*BORDER_PAD + 1
    ndefinitions = dictionary.count(lambda x: isinstance(x, DEF))

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

    lines = format_dictionary(dictionary, column_width - 2*COLUMN_MARGIN)

    max_column_height = len(lines) // ncolumns - 1
    column_break = max_column_height

    cur = 0
    columns: list[list[FLine]] = [[] for _ in range(ncolumns)]
    for i, line in enumerate(lines):
        columns[cur].append(line)

        op = dictionary.contents[line.op_indx]
        if (
                i > column_break
            and (isinstance(op, (DEF, SYN, ETYM)))
            and cur < ncolumns - 1
            and i + 1 != len(lines)
            and line.op_indx != lines[i + 1].op_indx
        ):
            column_break += max_column_height
            cur += 1

    return columns, column_width


class ScreenHighlight(NamedTuple):
    hl: list[dict[int, list[int]]]
    nmatches: int
    phrase: str
    last_line: int

    @property
    def span(self) -> int:
        return len(self.phrase)


class Screen:
    def __init__(self, win: curses._CursesWindow, dictionary: Dictionary) -> None:
        self.win = win
        self.selector = EntrySelector(dictionary)

        # self.margin_bot is needed for `self.page_height`
        self.margin_bot = 0
        self.columns, self.column_width = layout(dictionary, self.page_height)
        self.hl: ScreenHighlight | None = None
        self._scroll = 0

    @property
    def page_height(self) -> int:
        r = curses.LINES - 2*BORDER_PAD - self.margin_bot
        return r if r > 0 else 0

    def _scroll_end(self) -> int:
        r = max(map(len, self.columns)) - self.page_height
        return r if r > 0 else 0

    def adjust_scroll_past_eof(self) -> None:
        end_of_scroll = self._scroll_end()
        if self._scroll > end_of_scroll:
            self._scroll = end_of_scroll

    def draw(self) -> None:
        win = self.win
        contents = self.selector.dictionary.contents
        page_height = self.page_height

        vline_x = BORDER_PAD + self.column_width
        try:
            for _ in range(len(self.columns) - 1):
                win.vline(BORDER_PAD, vline_x, 0, page_height)
                vline_x += self.column_width + 1
        except curses.error:  # window too small
            return

        selected_ops = currently_selected_ops()
        hl_attr = Color.heed | HIGHLIGHT

        text_x = BORDER_PAD + COLUMN_MARGIN
        for col_i, column in enumerate(self.columns):
            for y, line_i in enumerate(
                    range(self._scroll, self._scroll + page_height), BORDER_PAD
            ):
                try:
                    op_index, text, attrs = column[line_i]
                except IndexError:
                    continue

                if not text:
                    continue

                if self.selector.is_toggled(op_index):
                    op = contents[op_index]
                    if isinstance(op, self.selector.TOGGLEABLE):
                        selection_hl = curses.A_STANDOUT
                    elif isinstance(op, selected_ops):
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

                if self.hl is None:
                    continue

                hlmap = self.hl.hl[col_i]
                if line_i not in hlmap:
                    continue

                span = self.hl.span
                try:
                    for i in hlmap[line_i]:
                        win.chgat(y, text_x + i, span, hl_attr)
                except curses.error:  # window too small
                    return

            text_x += self.column_width + 1

    def resize(self) -> None:
        self.columns, self.column_width = layout(
            self.selector.dictionary,
            self.page_height
        )
        self.adjust_scroll_past_eof()
        if self.hl is not None:
            self.hlsearch(self.hl.phrase)

    def dictionary_index_at(self, y: int, x: int) -> int | None:
        if y < BORDER_PAD or y >= curses.LINES - 1 - self.margin_bot:
            return None

        col_x = BORDER_PAD
        for column in self.columns:
            if col_x <= x < col_x + self.column_width:
                assert self._scroll + y - 1 >= 0
                try:
                    line = column[self._scroll + y - 1]
                except IndexError:
                    return None
                else:
                    return line.op_indx

            col_x += self.column_width + 1

        return None

    # return: True if a box has been toggled, False otherwise.
    def mark_box_at(self, y: int, x: int) -> bool:
        index = self.dictionary_index_at(y, x)
        if index is None:
            return False

        if isinstance(self.selector.dictionary.contents[index], self.selector.TOGGLEABLE):
            self.selector.toggle_by_index(index)
            return True
        else:
            return False

    # return: True if a box has been toggled, False otherwise.
    def mark_box_by_selector(self, s: bytes) -> bool:
        try:
            self.selector.toggle_by_def_index(b'1234567890!@#$%^&*()'.index(s) + 1)
        except ValueError:
            return False
        else:
            return True

    def deselect_all(self) -> None:
        self.selector.clear_selection()

    def move_down(self, n: int = 1) -> None:
        if self._scroll < self._scroll_end():
            self._scroll += n
            self.adjust_scroll_past_eof()

    def move_up(self, n: int = 1) -> None:
        self._scroll -= n
        if self._scroll < 0:
            self._scroll = 0

    def go_bottom(self) -> None:
        self._scroll = self._scroll_end()

    def go_top(self) -> None:
        self._scroll = 0

    def page_down(self) -> None:
        self.move_down(self.page_height - 2)

    def page_up(self) -> None:
        self.move_up(self.page_height - 2)

    def hlsearch(self, s: str) -> int:
        # `hlsearch()` is entirely dependent on the output of
        # `format_dictionary()`. As a result of this, it is easy to search for
        # matches line by line with no regard for line breaks, but we have
        # the necessary information to make it more robust and not rely on
        # window dimensions to make successful multi-word searches.
        # TODO: Improve `format_dictionary()`, so that we can reliably merge
        #       its output and make multi-words searches across line breaks.

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
            self.hl = ScreenHighlight(hls, nmatches, s, hllast_line)
        else:
            self.hl = None

        return nmatches

    def hl_clear(self) -> None:
        self.hl = None
        self.adjust_scroll_past_eof()

    def hl_next(self) -> None:
        if self.hl is None:
            return
        for i in range(self._scroll + 1, self.hl.last_line + 1):
            for hlmap in self.hl.hl:
                if i in hlmap:
                    self._scroll = i
                    return

    def hl_prev(self) -> None:
        if self.hl is None:
            return
        for i in range(self._scroll - 1, -1, -1):
            for hlmap in self.hl.hl:
                if i in hlmap:
                    self._scroll = i
                    return

    def is_hl_in_view(self) -> bool:
        if self.hl is None:
            return False
        for i in range(self._scroll, self._scroll + self.page_height):
            for hlmap in self.hl.hl:
                if i in hlmap:
                    return True

        return False

    ACTIONS: Mapping[bytes, Callable[[Screen], None]] = {
        b'^J': hl_clear, b'^M': hl_clear,
        b'd': deselect_all,
        b'j': move_down, b'^N': move_down, b'KEY_DOWN': move_down,
        b'k': move_up,   b'^P': move_up,   b'KEY_UP': move_up,
        b'G': go_bottom, b'KEY_END': go_bottom,
        b'g': go_top,    b'KEY_HOME': go_top,
        b'KEY_NPAGE': page_down, b'KEY_SNEXT': page_down,
        b'KEY_PPAGE': page_up,   b'KEY_SPREVIOUS': page_up,
        b'n': hl_next,
        b'N': hl_prev,
    }

    # Returns whether the key was recognized.
    def dispatch(self, key: bytes) -> bool:
        if key in self.ACTIONS:
            self.ACTIONS[key](self)
            return True

        return self.mark_box_by_selector(key)
