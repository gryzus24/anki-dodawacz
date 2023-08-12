from __future__ import annotations

import curses
from typing import Callable
from typing import Literal
from typing import Mapping
from typing import NamedTuple
from typing import Sequence
from typing import TYPE_CHECKING

from src.Curses.color import Color
from src.Curses.util import Attr
from src.Curses.util import BORDER_PAD
from src.Curses.util import compose_attrs
from src.Curses.util import truncate
from src.data import getconf
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
    op_i: int
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
        op_i: int,
        s: str,
        hls: Sequence[tuple[int, int]],
        width: int, *,
        predent: str = '',
        indent: str = ''
) -> None:
    # displaying '\n' and '\r' is undesirable
    if '\n' in s:
        s = s.replace('\n', ' ')
    if '\r' in s:
        s = s.replace('\r', ' ')

    s_len = len(s)
    cur_indent = predent
    cur_indent_len = len(predent)

    # fast path
    if s_len <= width - cur_indent_len:
        attrs = []
        _attr_i = cur_indent_len
        for span, attr in hls:
            attrs.append(Attr(_attr_i, span, attr))
            _attr_i += span

        dest.append(FLine(op_i, predent + s, attrs))
        return

    indent_len = len(indent)
    hl_i = attr_i = line_i = brk_i = 0

    span_left, attr = hls[hl_i]
    attrs = []

    # skipping preceding spaces to avoid line breaks
    # if there is not enough space for single words.
    try:
        while s[brk_i] == ' ':
            brk_i += 1
    except IndexError:
        brk_i = 0
    else:
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
                # we don't want to lose any FLines,
                # even if they can't be displayed
                _trunc_line = ''
            else:
                # -1: space for the truncation character "»"
                _span = width - _attr_i - 1
                if _span > 0:
                    attrs.append(Attr(_attr_i, _span, attr))
                attrs.append(Attr(width - 1, 1, Color.err | curses.A_STANDOUT))
            dest.append(FLine(op_i, _trunc_line, attrs))
        else:
            span = line_i - attr_i
            if span > 0:
                attrs.append(Attr(_attr_i, span, attr))
                dest.append(FLine(op_i, _line, attrs))
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

            if op.subdef:
                sign = ' '
                hls = [
                    (1, 0),
                    (index_len, Color.index),
                    (1, 0),
                ]
            else:
                sign = '>'
                hls = [
                    (1, Color.sign),
                    (index_len, Color.index),
                    (1, 0),
                ]

            if op.label:
                buf = f'{sign}{index} {{{op.label}}} {op.definition}'
                hls.append((len(op.label) + 2, Color.label))
                hls.append((1, 0))
            else:
                buf = f'{sign}{index} {op.definition}'

            hls.append((len(op.definition), Color.def1 if index % 2 else Color.def2))

            nexamples = len(op.examples)
            if nexamples == 1:
                example = op.examples[0]
                if len(buf) + 2 + len(example) <= width or indent_weight:
                    buf += '  ' + example
                    hls.append((2, 0))
                    hls.append((len(example), Color.exsen))
                    nexamples -= 1

            wrap(result, i, buf, hls, width, indent=indent)

            if nexamples:
                predent = (indent_weight + index_len + 1) * ' '
                for example in op.examples:
                    wrap(result, i, example,
                        (
                            (len(example), Color.exsen),
                        ), width, predent=predent, indent=indent or ' ')

        elif isinstance(op, LABEL):
            result.append(FLine(i, '', []))
            if not op.label:
                continue

            if op.extra:
                wrap(result, i, f'{op.label}  {op.extra}',
                    (
                        (len(op.label), Color.label),
                        (2, 0),
                        (len(op.extra), Color.infl),
                    ), width)
            else:
                wrap(result, i, op.label,
                    ((len(op.label), Color.label),),
                    width)

        elif isinstance(op, PHRASE):
            if op.extra:
                wrap(result, i, f'{op.phrase}  {op.extra}',
                    (
                        (len(op.phrase), Color.phrase),
                        (2, 0),
                        (len(op.extra), Color.phon),
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
                        (len(pos), Color.pos),
                        (2, 0),
                        (len(phon), Color.phon),
                    ), width)

        elif isinstance(op, SYN):
            index += 1
            index_len = len(str(index))
            indent = (indent_weight + index_len + 2) * ' '

            wrap(result, i, op.synonyms,
                ((len(op.synonyms), Color.syn),),
                width)

            wrap(result, i, f'>{index} {op.definition}',
                (
                    (1, Color.sign),
                    (index_len, Color.index),
                    (1, 0),
                    (len(op.definition), Color.def1 if index % 2 else Color.def2),
                ), width, indent=indent)

            predent = (indent_weight + index_len + 1) * ' '
            for example in op.examples:
                wrap(result, i, example,
                    (
                        (len(example), Color.exsen),
                    ), width, predent=predent, indent=indent or ' ')

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
                        (len(op.note), curses.A_BOLD),
                    ), width)

        else:
            raise AssertionError(f'unreachable {op!r}')

    return result


def currently_selected_ops() -> tuple[type[op_t], ...]:
    result: list[type[op_t]] = [PHRASE]
    if getconf('audio'):
        result.append(AUDIO)
    if getconf('pos'):
        result.append(POS)
    if getconf('etym'):
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

        op = dictionary.contents[line.op_i]
        if (
                i > column_break
            and (isinstance(op, (DEF, SYN, ETYM)))
            and cur < ncolumns - 1
            and i + 1 != len(lines)
            and line.op_i != lines[i + 1].op_i
        ):
            column_break += max_column_height
            cur += 1

    return columns, column_width


class Cursor:
    def __init__(self, selector: EntrySelector, columns: list[list[FLine]]) -> None:
        self.columns = columns

        self._col = self._cur_indx = 0
        self._phantom_cur_indices = [-1] * len(columns)

        self._col_cur_lineof = []
        self._col_indx_to_cur = []

        contents = selector.dictionary.contents
        for col in columns:
            _cur_lineof = {}
            _indx_to_cur = []
            for i, line in enumerate(col):
                if (
                        line.op_i not in _cur_lineof
                    and isinstance(contents[line.op_i], selector.TOGGLEABLE)
                ):
                    _indx_to_cur.append(line.op_i)
                    _cur_lineof[line.op_i] = i

            self._col_cur_lineof.append(_cur_lineof)
            self._col_indx_to_cur.append(_indx_to_cur)

    def cur(self) -> int:
        return self._col_indx_to_cur[self._col][self._cur_indx]

    def line_at_cur(self) -> int:
        return self._col_cur_lineof[self._col][self.cur()]

    def line_at_next_cur_down(self) -> int:
        try:
            next_cur = self._col_indx_to_cur[self._col][self._cur_indx + 1]
        except IndexError:
            steps = 0
            cur = self.cur()
            for line in self.columns[self._col]:
                if line.op_i == cur:
                    steps += 1
                elif steps:
                    break

            return self._col_cur_lineof[self._col][cur] + steps
        else:
            return self._col_cur_lineof[self._col][next_cur]

    @property
    def _last_cur_indx(self) -> int:
        return len(self._col_indx_to_cur[self._col]) - 1

    def _invalidate_phantom_cur_indices(self) -> None:
        self._phantom_cur_indices = [-1] * len(self.columns)

    def down(self) -> bool:
        if self._cur_indx < self._last_cur_indx:
            self._cur_indx += 1
            self._invalidate_phantom_cur_indices()
            return True
        else:
            return False

    def up(self) -> bool:
        if self._cur_indx > 0:
            self._cur_indx -= 1
            self._invalidate_phantom_cur_indices()
            return True
        else:
            return False

    # return: True if column has changed, False otherwise.
    def _change_columns(self, direction: Literal[1, -1]) -> bool:
        if direction == 1:
            if self._col >= len(self.columns) - 1:
                return False
        else:
            if self._col <= 0:
                return False

        if (_i := self._phantom_cur_indices[self._col + direction]) != -1:
            self._cur_indx = _i
            self._col += direction
            return True
        else:
            self._phantom_cur_indices[self._col] = self._cur_indx

        prev_line = self.line_at_cur()

        self._col += direction
        lineof = self._col_cur_lineof[self._col]
        for i, line in enumerate(lineof.values()):
            if line > prev_line:
                self._cur_indx = i - 1 if i else 0
                break
        else:
            self._cur_indx = self._last_cur_indx

        return True

    def right(self) -> bool:
        return self._change_columns(1)

    def left(self) -> bool:
        return self._change_columns(-1)

    def go_bottom(self) -> None:
        self._cur_indx = self._last_cur_indx

    def go_top(self) -> None:
        self._cur_indx = 0

    def _cur_indx_by_cur(self, cur_to_find: int) -> int:
        for i, cur in enumerate(self._col_indx_to_cur[self._col]):
            if cur == cur_to_find:
                return i

        raise AssertionError('unreachable')

    def go_to_cur_at_line_after(self, line_i: int) -> None:
        if line_i <= 0:
            self._cur_indx = 0
            return

        lineof = self._col_cur_lineof[self._col]
        for cur, line in lineof.items():
            if line >= line_i:
                self._cur_indx = self._cur_indx_by_cur(cur)
                return

        self._cur_indx = self._last_cur_indx

    def go_to_cur_at_line_before(self, line_i: int) -> None:
        if line_i <= 0:
            self._cur_indx = 0
            return

        lineof = self._col_cur_lineof[self._col]
        for cur, line in reversed(lineof.items()):
            if line < line_i:
                self._cur_indx = self._cur_indx_by_cur(cur)
                return

        self._cur_indx = 0


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
        self._scroll = self.margin_bot = 0
        self.columns, self.column_width = layout(dictionary, self.page_height)
        self.hl: ScreenHighlight | None = None

        self.vmode = False
        self.cursor = Cursor(self.selector, self.columns)

    @property
    def page_height(self) -> int:
        r = curses.LINES - 2*BORDER_PAD - self.margin_bot
        return r if r > 0 else 0

    def _scroll_end(self) -> int:
        r = max(map(len, self.columns)) - self.page_height
        return r if r > 0 else 0

    def check_scroll_after_eof(self) -> None:
        end_of_scroll = self._scroll_end()
        if self._scroll > end_of_scroll:
            self._scroll = end_of_scroll

    def bring_cursor_to_view(self) -> None:
        cur_line = self.cursor.line_at_cur()
        if cur_line < self._scroll:
            self.cursor.go_to_cur_at_line_after(self._scroll)

        next_cur_line = self.cursor.line_at_next_cur_down()
        if next_cur_line > (end := self._scroll + self.page_height):
            self.cursor.go_to_cur_at_line_before(end)

        cur_line = self.cursor.line_at_cur()
        if (
               cur_line < self._scroll
            or cur_line > self._scroll + self.page_height
        ):
            self._scroll = cur_line

    def draw(self) -> None:
        win = self.win
        contents = self.selector.dictionary.contents
        page_height = self.page_height
        column_width = self.column_width

        try:
            for x in range(
                    BORDER_PAD + column_width,
                    len(self.columns) * (column_width + 1),
                    column_width + 1
            ):
                win.vline(BORDER_PAD, x, 0, page_height)
        except curses.error:  # window height too small
            return

        cur = self.cursor.cur()
        selected_ops = currently_selected_ops()
        hl_attr = Color.hl

        text_x = BORDER_PAD + COLUMN_MARGIN
        for col_i, column in enumerate(self.columns):
            for y, line_i in enumerate(
                    range(self._scroll, self._scroll + page_height), BORDER_PAD
            ):
                try:
                    op_i, text, attrs = column[line_i]
                except IndexError:
                    continue

                if not text:
                    continue

                win.addstr(y, text_x, text)

                sel_attr = 0
                if self.selector.is_toggled(op_i):
                    op = contents[op_i]
                    if isinstance(op, self.selector.TOGGLEABLE):
                        sel_attr |= Color.selection
                    elif isinstance(op, selected_ops):
                        sel_attr |= curses.A_BOLD

                if self.vmode and op_i == cur:
                    sel_attr |= Color.cursor
                    for i, span, attr in attrs:
                        attr &= ~curses.A_INVIS  # 'show on hover' effect
                        win.chgat(y, text_x + i, span, sel_attr | attr)
                else:
                    for i, span, attr in attrs:
                        win.chgat(y, text_x + i, span, sel_attr | attr)

                if self.hl is None:
                    continue

                hlindices = self.hl.hl[col_i]
                if line_i in hlindices:
                    span = self.hl.span
                    for hl_i in hlindices[line_i]:
                        win.chgat(y, text_x + hl_i, span, hl_attr)

            text_x += column_width + 1

    def resize(self) -> None:
        # save previous op index to avoid page scrolling off when terminal
        # window shrinks and content above wraps
        try:
            prev_op_i_at_scroll = self.columns[0][self._scroll].op_i
        except IndexError:
            # index error will occur if:
            # - len(self.columns) > 1, and
            # - column other than the first one has more rows, and
            # - self._scroll is after the eof mark of the first column
            #   (e.g. during hlsearch).
            # Just bail out.
            prev_op_i_at_scroll = -1

        self.columns, self.column_width = layout(
            self.selector.dictionary,
            self.page_height
        )

        if prev_op_i_at_scroll != -1:
            for i, line in enumerate(self.columns[0]):
                if prev_op_i_at_scroll == line.op_i:
                    self._scroll = i
                    break

        self.check_scroll_after_eof()
        if self.hl is not None:
            self.hlsearch(self.hl.phrase)

        # TODO: restore cursor position as it was before resize?
        self.cursor = Cursor(self.selector, self.columns)
        self.bring_cursor_to_view()

    def vmode_toggle(self) -> None:
        if self.vmode:
            self.vmode = False
        else:
            self.vmode = True
            self.bring_cursor_to_view()

    def dictionary_op_i_at(self, y: int, x: int) -> int | None:
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
                    return line.op_i

            col_x += self.column_width + 1

        return None

    # return: True if a box has been toggled, False otherwise.
    def mark_box_at(self, y: int, x: int) -> bool:
        op_i = self.dictionary_op_i_at(y, x)
        if op_i is None:
            return False

        contents = self.selector.dictionary.contents
        if isinstance(contents[op_i], self.selector.TOGGLEABLE):
            self.selector.toggle_by_index(op_i)
            return True
        else:
            return False

    # return: True if a box has been toggled, False otherwise.
    def mark_box_by_number(self, s: bytes) -> bool:
        try:
            self.selector.toggle_by_def_index(b'1234567890'.index(s) + 1)
        except ValueError:
            return False
        else:
            return True

    def mark_box_at_cursor(self) -> None:
        self.selector.toggle_by_index(self.cursor.cur())

    def deselect_all(self) -> None:
        self.selector.clear_selection()

    def move_down(self, n: int = 1) -> None:
        if self._scroll < self._scroll_end():
            self._scroll += n
            self.check_scroll_after_eof()

    def move_up(self, n: int = 1) -> None:
        self._scroll -= n
        if self._scroll < 0:
            self._scroll = 0

    def view_bottom(self) -> None:
        self._scroll = self._scroll_end()

    def view_top(self) -> None:
        self._scroll = 0

    def page_down(self) -> None:
        self.move_down(self.page_height - 2)

    def page_up(self) -> None:
        self.move_up(self.page_height - 2)

    def cursor_down(self) -> None:
        if self.cursor.down():
            cur_line = self.cursor.line_at_next_cur_down()
            if cur_line > (end := self._scroll + self.page_height):
                self._scroll += cur_line - end
            elif cur_line < self._scroll:
                self.cursor.go_to_cur_at_line_after(self._scroll)
        else:
            self._scroll = self._scroll_end()

    def cursor_up(self) -> None:
        if self.cursor.up():
            cur_line = self.cursor.line_at_cur()
            if cur_line < self._scroll:
                self._scroll = cur_line
            elif cur_line > (end := self._scroll + self.page_height):
                self.cursor.go_to_cur_at_line_before(end)
        else:
            self._scroll = 0

    def cursor_right(self) -> None:
        if self.cursor.right():
            self.bring_cursor_to_view()

    def cursor_left(self) -> None:
        if self.cursor.left():
            self.bring_cursor_to_view()

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
                # NOTE: On Python 3.11+ `x != -1` is finally faster than `~x`
                while x != -1:
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
        self.check_scroll_after_eof()

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

    def key_down(self) -> None:
        if self.vmode:
            self.cursor_down()
        else:
            self.move_down()

    def key_up(self) -> None:
        if self.vmode:
            self.cursor_up()
        else:
            self.move_up()

    def key_right(self) -> None:
        if self.vmode:
            self.cursor_right()

    def key_left(self) -> None:
        if self.vmode:
            self.cursor_left()

    def key_end(self) -> None:
        if self.vmode:
            self.cursor.go_bottom()
        self.view_bottom()

    def key_home(self) -> None:
        if self.vmode:
            self.cursor.go_top()
        self.view_top()

    def key_enter(self) -> None:
        if self.vmode:
            self.mark_box_at_cursor()
        else:
            self.hl_clear()

    def key_space(self) -> None:
        if self.vmode:
            self.mark_box_at_cursor()
            if not self.cursor.down() and self.cursor.right():
                self.cursor.go_to_cur_at_line_after(0)
                self._scroll = 0

    ACTIONS: Mapping[bytes, Callable[[Screen], None]] = {
        b'J': move_down,          b'^N': move_down,
        b'K': move_up,            b'^P': move_up,
        b'KEY_NPAGE': page_down,  b'KEY_SNEXT': page_down,
        b'KEY_PPAGE': page_up,    b'KEY_SPREVIOUS': page_up,
        b's': mark_box_at_cursor,
        b'd': deselect_all,
        b'v': vmode_toggle,
        b'n': hl_next,
        b'N': hl_prev,

        b'j': key_down,   b'KEY_DOWN': key_down,
        b'k': key_up,     b'KEY_UP': key_up,
        b'l': key_right,  b'KEY_RIGHT': key_right,
        b'h': key_left,   b'KEY_LEFT': key_left,
        b'G': key_end,    b'KEY_END': key_end,
        b'g': key_home,   b'KEY_HOME': key_home,
        b'^J': key_enter, b'^M': key_enter,
        b' ': key_space,
    }

    # Returns whether the key was recognized.
    def dispatch(self, key: bytes) -> bool:
        if key in self.ACTIONS:
            self.ACTIONS[key](self)
            return True

        return self.mark_box_by_number(key)
