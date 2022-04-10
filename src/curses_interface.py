#!/usr/bin/env python3
from __future__ import annotations

import curses
from itertools import compress, islice
from typing import TYPE_CHECKING, Callable, Any, Reversible, Optional

from src.Dictionaries.utils import wrap_and_pad
from src.colors import Color as _Color
from src.data import HORIZONTAL_BAR, config

if TYPE_CHECKING:
    from src.Dictionaries.dictionary_base import Dictionary

ansi_to_pair = {
    '\033[39m': 0, '\033[30m': 1, '\033[31m': 2, '\033[32m': 3,
    '\033[33m': 4, '\033[34m': 5, '\033[35m': 6, '\033[36m': 7,
    '\033[37m': 8, '\033[90m': 9, '\033[91m': 10, '\033[92m': 11,
    '\033[93m': 12, '\033[94m': 13, '\033[95m': 14, '\033[96m': 15,
    '\033[97m': 16,
}


class MetaColor(type, _Color):
    def __getattribute__(self, item: str) -> int:
        return curses.color_pair(ansi_to_pair[super().__getattribute__(item)])


class Color(metaclass=MetaColor):
    pass


def _log(*msg: Any) -> None:
    messages = map(repr, msg)
    with open('log.log', 'a', encoding='UTF-8') as f:
        f.write(f'{" ".join(messages)}\n')


def format_dictionary(
        dictionary: Dictionary,
        column_width: int,
) -> tuple[list[list[curses._CursesWindow]], int]:
    # Format self.contents' list of (op, body)
    # into wrapped, colored and padded body lines.
    # Available instructions:
    #  (DEF,    'definition', 'example_sentence', 'label')
    #  (SUBDEF, 'definition', 'example_sentence')
    #  (LABEL,  'pos_label', 'additional_info')
    #  (PHRASE, 'phrase', 'phonetic_spelling')
    #  (HEADER, 'filling_character', 'header_title')
    #  (POS,    'pos|phonetic_spelling', ...)  ## `|` acts as a separator.
    #  (AUDIO,  'audio_url')
    #  (SYN,    'synonyms', 'gloss', 'examples')
    #  (NOTE,   'note')

    wrap_method = wrap_and_pad(config['textwrap'], column_width)
    indent = config['indent'][0]
    signed = config['showsign']

    boxes = []
    lines_total = 0

    def _push_chain(_s1: str, _c1: int, _s2: str, _c2: int) -> None:
        _first_line, _rest = wrap_method(f'{_s1} \0{_s2}', 1, 0)
        left, _, right = _first_line.partition('\0')
        _box = curses.newwin(1, column_width)
        if right:
            _box.insstr(right, _c2)
            _box.insstr(' ' + left, _c1)
            if not _rest:
                temp_boxes.append(_box)
                return
            current_color = _c2
        else:
            _box.insstr(' ' + left, _c1)
            current_color = _c1

        temp_boxes.append(_box)
        for _line in _rest:
            left, _, right = _line.partition('\0')
            _box = curses.newwin(1, column_width)
            if right:
                _box.insstr(right, _c2)
                _box.insstr(left, _c1)
                current_color = _c2
            else:
                _box.insstr(left, current_color)
            temp_boxes.append(_box)

    def _into_boxes(
            fl_string_color_pairs: Reversible[tuple[str, int]],
            rest: Optional[tuple[list[str], int]] = None
    ) -> list[curses._CursesWindow]:
        result = []
        _box = curses.newwin(1, column_width)
        for s, c in reversed(fl_string_color_pairs):
            _box.insstr(s, c)
        result.append(_box)
        if rest is not None:
            lines, c = rest
            for line in lines:
                _box = curses.newwin(1, column_width)
                _box.insstr(line, c)
                result.append(_box)
        return result

    index = 0
    for op, *body in dictionary.contents:
        # sys.stdout.write(f'{op}\n{body}\n'); continue  # DEBUG
        temp_boxes = []

        if 'DEF' in op:
            index += 1
            index_len = len(str(index))

            _def, _exsen, _label = body
            if _label:
                _label = '{' + _label + '} '
                label_len = len(_label)
            else:
                label_len = 0

            if signed:
                _def_s = f"{Color.sign}{' ' if 'SUB' in op else '>'}"
                gaps = 2
            else:
                _def_s = ''
                gaps = 1

            first_line, rest = wrap_method(
                _def, gaps + index_len + label_len, indent - label_len
            )
            def_c = Color.def1 if index % 2 else Color.def2
            temp_boxes.extend(_into_boxes(
                (
                    (f'{index} ', Color.index),
                    (_label, Color.label),
                    (first_line, def_c)
                ),
                (
                    rest, def_c
                )
            ))

            if _exsen:
                for ex in _exsen.split('<br>'):
                    first_line, rest = wrap_method(ex, gaps + index_len - 1, 1 + indent)
                    temp_boxes.extend(_into_boxes(
                        (
                            ((index_len + gaps - 1) * ' ', Color.exsen),
                            (first_line, Color.exsen)
                        ),
                        (
                            rest, Color.exsen
                        )
                    ))
        elif op == 'LABEL':
            label, inflections = body
            temp_boxes.append(curses.newwin(1, column_width))
            if label:
                if inflections:
                    _push_chain(label, Color.label, inflections, Color.inflection)
                else:
                    first_line, rest = wrap_method(label, 1, 0)
                    temp_boxes.extend(_into_boxes(
                        (
                            (' ' + first_line, Color.label),
                        ),
                        (
                            rest, Color.label
                        )
                    ))
        elif op == 'PHRASE':
            phrase, phon = body
            if phon:
                _push_chain(phrase, Color.phrase, phon, Color.phon)
            else:
                first_line, rest = wrap_method(phrase, 1, 0)
                temp_boxes.extend(_into_boxes(
                    (
                        (' ' + first_line, Color.phrase),
                    ),
                    (
                        rest, Color.phrase
                    )
                ))
        elif op == 'HEADER':
            title = body[0]
            box = curses.newwin(1, column_width)
            if title:
                box.insstr(' ]' + curses.COLS * HORIZONTAL_BAR, Color.delimit)
                box.insstr(title, Color.delimit | curses.A_BOLD)
                box.insstr(HORIZONTAL_BAR + '[ ', Color.delimit)
            else:
                box.insstr(column_width * HORIZONTAL_BAR, Color.delimit)
            temp_boxes.append(box)
        elif op == 'ETYM':
            etym = body[0]
            if etym:
                temp_boxes.append(curses.newwin(1, column_width))
                first_line, rest = wrap_method(etym, 1, indent)
                temp_boxes.extend(_into_boxes(
                    (
                        (' ' + first_line, Color.etym),
                    ),
                    (
                        rest, Color.etym
                    )
                ))
        elif op == 'POS':
            if body[0].strip(' |'):
                temp_boxes.append(curses.newwin(1, column_width))
                for elem in body:
                    pos, phon = elem.split('|')
                    temp_boxes.extend(_into_boxes(
                        (
                            (' ' + pos, Color.pos),
                            ('  ' + phon, Color.phon)
                        )
                    ))
        elif op == 'AUDIO':
            pass
        elif op == 'SYN':
            first_line, rest = wrap_method(body[0], 1, 0)
            temp_boxes.extend(_into_boxes(
                (
                    (' ' + first_line, Color.syn),
                ),
                (
                    rest, Color.syn
                )
            ))
            first_line, rest = wrap_method(body[1], 2, 0)
            temp_boxes.extend(_into_boxes(
                (
                    (': ', Color.sign),
                    (first_line, Color.syngloss)
                ),
                (
                    rest, Color.syngloss
                )
            ))
            for ex in body[2].split('<br>'):
                first_line, rest = wrap_method(ex, 1, 1)
                temp_boxes.extend(_into_boxes(
                    (
                        (' ' + first_line, Color.exsen),
                    ),
                    (
                        rest, Color.exsen
                    )
                ))
        elif op == 'NOTE':
            first_line, rest = wrap_method(body[0], 2, 0)
            temp_boxes.extend(_into_boxes(
                (
                    ('> ', Color.YEX | curses.A_BOLD),
                    (first_line, 0 | curses.A_BOLD)
                ),
                (
                    rest, 0 | curses.A_BOLD
                )
            ))
        else:
            raise AssertionError(f'unreachable dictionary operation: {op!r}')

        boxes.append(temp_boxes)
        lines_total += len(temp_boxes)

    return boxes, lines_total


def get_column_parameters(width: int) -> tuple[int, int]:
    ncols = width // 40
    r = width % 40
    if not r:
        return 39, ncols

    try:
        fill = r // ncols
    except ZeroDivisionError:
        return width, 1

    col_width = 39 + fill
    return col_width, ncols


BORDER_PAD = 1

class Screen:
    MARGIN = 0

    def __init__(self,
            stdscr: curses.window,
            dictionary: Dictionary,
            formatter: Callable[[Dictionary, int], tuple[list[list[curses.window]], int]]
    ) -> None:
        # Static.
        self.stdscr = stdscr
        self.dictionary = dictionary
        self.formatter = formatter

        col_width, self.ncols = get_column_parameters(curses.COLS - BORDER_PAD)
        self.col_width = col_width - 2 * self.MARGIN

        _boxes, self.lines_total = formatter(dictionary, self.col_width)

        self.boxes = _boxes
        self.columns = self._split_into_columns(_boxes)

        # User facing state.
        self.box_toggles = [False] * len(_boxes)
        self.scroll_pos = 0

    def update_for_redraw(self) -> None:
        curses.update_lines_cols()

        col_width, self.ncols = get_column_parameters(curses.COLS - BORDER_PAD)
        self.col_width = col_width - 1 * self.MARGIN

        _boxes, self.lines_total = self.formatter(self.dictionary, self.col_width)
        if _boxes is None:
            return
        # Keep toggled boxes toggled.
        for lines in compress(_boxes, self.box_toggles):
            for line in lines:
                line.bkgd(0, curses.A_STANDOUT)

        self.boxes = _boxes
        self.columns = self._split_into_columns(_boxes)
        self.stdscr.clear()

    def _split_into_columns(
            self, boxes: list[list[curses._CursesWindow]]
    ) -> list[list[curses._CursesWindow]]:
        col_width = self.col_width
        max_col_height = self.lines_total // self.ncols
        result: list[list[curses._CursesWindow]] = [[]]
        current_height = 0
        # TODO: move certain boxes to the next column.
        for lines, _ in zip(boxes, self.dictionary.contents):
            current_height += len(lines)
            result[-1].extend(lines)
            if current_height > max_col_height:
                header = curses.newwin(1, col_width)
                header.hline(0, col_width)
                result.append([header])
                current_height = 0

        return result

    def _draw_header(self) -> None:
        h = self.columns[0][0]
        try:
            h.mvwin(0, BORDER_PAD)
        except curses.error:
            return
        h.noutrefresh()

    def draw(self) -> None:
        if curses.LINES < 2:
            return

        columns = self.columns
        col_width = self.col_width
        margin = self.MARGIN

        self.stdscr.box()
        shift = BORDER_PAD + col_width + 2 * margin
        for i in range(1, len(columns)):
            self.stdscr.vline(BORDER_PAD, i * shift, 0, curses.LINES - 2 * BORDER_PAD)
        self.stdscr.noutrefresh()
        self._draw_header()

        tx = BORDER_PAD
        scroll_pos = self.scroll_pos
        # reset window positions up until the scroll position.
        for column in columns:
            for box in islice(column, None, scroll_pos):
                box.mvwin(0, 1)

        vertical_line_positions = []
        for column in columns:
            for y, box in enumerate(
                    islice(column, scroll_pos + BORDER_PAD, scroll_pos + curses.LINES - BORDER_PAD), 1
            ):
                try:
                    box.mvwin(y, tx + margin)
                except curses.error:  # prevent crash if curses.COLS <= 2
                    break
                box.noutrefresh()
            tx += col_width + 1 + 2 * margin
            vertical_line_positions.append(tx)

        curses.doupdate()

    def mark_box_at(self, y: int, x: int) -> None:
        if not y:  # header clicked.
            return

        # Because scrolling is implemented by moving windows around, these that
        # are not in view are tucked under the header to not interfere with box
        # toggling.  We should consider decoupling the scrolling functionality
        # from box toggling and maybe use a class to represent a Box if more
        # tightly coupled functionality is needed.  It is impossible to have a
        # pointer to an immutable type like a `bool` and as far as I know you
        # cannot remove/reset the top-left corner position from the curses
        # window.
        not_in_view = {
            column[i]
            for column in self.columns
            for i in range(self.scroll_pos)
        }
        for i, (toggle, lines) in enumerate(zip(self.box_toggles, self.boxes)):
            for line in lines:
                if id(line) not in not_in_view and line.enclose(y, x):
                    break
            else:
                continue

            highlight = curses.A_NORMAL if toggle else curses.A_STANDOUT
            for line in lines:
                line.bkgd(0, highlight)

            self.box_toggles[i] = not toggle
            return

    def view_down(self, n: int = 1) -> None:
        max_boxes_in_column = 2 + max(map(len, self.columns)) - curses.LINES
        if max_boxes_in_column < 0:
            return
        self.scroll_pos += n
        if self.scroll_pos > max_boxes_in_column:
            self.scroll_pos = max_boxes_in_column

    def view_up(self, n: int = 1) -> None:
        self.scroll_pos -= n
        if self.scroll_pos < 0:
            self.scroll_pos = 0


def _c_main(stdscr: curses.window, dictionaries: list[Dictionary]) -> int:
    dictionary = dictionaries[0]
    if not dictionary.contents:
        return -1

    screen = Screen(stdscr, dictionary, formatter=format_dictionary)
    while True:
        if curses.is_term_resized(curses.LINES, curses.COLS):
            screen.update_for_redraw()

        screen.draw()
        c = stdscr.get_wch()
        if c in {'q', 'Q'}:
            break
        elif c == curses.KEY_MOUSE:
            _, x, y, _, bstate = curses.getmouse()
            if bstate & curses.BUTTON1_PRESSED:
                screen.mark_box_at(y, x)
            elif bstate & curses.BUTTON4_PRESSED:
                screen.view_up(2)
            elif bstate & curses.BUTTON5_PRESSED:
                screen.view_down(2)
        elif c in {curses.KEY_DOWN, 'j'}:
            screen.view_down(2)
        elif c in {curses.KEY_UP, 'k'}:
            screen.view_up(2)
        else:
            # raise AssertionError(repr(c))
            pass

    return 0


def curses_init(dictionaries: list[Dictionary]) -> int:
    try:
        stdscr = curses.initscr()

        curses.curs_set(0)
        curses.cbreak()
        curses.noecho()
        curses.mousemask(-1)
        curses.mouseinterval(0)

        stdscr.keypad(True)

        try:
            curses.start_color()
        except:
            pass

        curses.use_default_colors()
        for i in range(16):
            curses.init_pair(i + 1, i, -1)

        return _c_main(stdscr, dictionaries)
    finally:
        # Set everything back to normal
        if 'stdscr' in locals():
            stdscr.keypad(False)
            curses.echo()
            curses.nocbreak()
            curses.endwin()
