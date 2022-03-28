#!/usr/bin/env python3
from __future__ import annotations

import curses

from src.Dictionaries.ahdictionary import ask_ahdictionary
from src.Dictionaries.utils import wrap_and_pad
from src.colors import *
from src.data import HORIZONTAL_BAR, config

from itertools import compress, islice


COLOR_RESET = -1
BLACK = 1
RED = 2
GREEN = 3
YELLOW = 4
BLUE = 5
MAGENTA = 6
CYAN = 7
WHITE = 8
BRIGHT_BLACK = 9
BRIGHT_RED = 10
BRIGHT_GREEN = 11
BRIGHT_YELLOW = 12
BRIGHT_BLUE = 13
BRIGHT_MAGENTA = 14
BRIGHT_CYAN = 15
BRIGHT_WHITE = 16

color_name_to_color_pair = {
    '\033[30m': 1,
    '\033[31m': 2,
    '\033[32m': 3,
    '\033[33m': 4,
    '\033[34m': 5,
    '\033[35m': 6,
    '\033[36m': 7,
    '\033[37m': 8,
    '\033[90m': 9,
    '\033[91m': 10,
    '\033[92m': 11,
    '\033[93m': 12,
    '\033[94m': 13,
    '\033[95m': 14,
    '\033[96m': 15,
    '\033[97m': 16,
    '\033[39m': 0,
}


def color(c):
    return curses.color_pair(color_name_to_color_pair[config[c]])


def format_title(window: curses._CursesWindow, title: str) -> curses.window:
    window.addstr(HORIZONTAL_BAR + '[ ', color('delimit_c'))
    # TODO: add BOLD color. Fix window overflow on small textwidth.

    window.addstr(title)
    window.addstr(' ]', color('delimit_c'))
    while True:
        try:
            window.addstr(HORIZONTAL_BAR, color('delimit_c'))
        except curses.error:
            break
    return window


def log(msg):
    with open('log.log', 'a', encoding='UTF-8') as f:
        f.write(repr(msg) + '\n')


def format_dictionary(
        dictionary,
        column_width: int,
        wrap_style: str = 'regular',
        indent: int = 0,
        signed: bool = False
) -> tuple[list[curses._CursesWindow], int]:
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

    wrap_method = wrap_and_pad(wrap_style, column_width - 1)
    boxes = []
    lines_total = 0


    def _new_window(height):
        nonlocal lines_total
        lines_total += height
        _new_win = curses.newwin(height, column_width)
        return _new_win

    def _add_box(_box):
        boxes.append(_box)

    def _push_chain(_s1: str, _c1: int, _s2: str, _c2: int) -> None:
        # TODO: fix color chaining.
        _first_line, *_rest = wrap_method(f'{_s1} \0{_s2}', 1, 0)
        left, _, right = _first_line.partition('\0')
        _box = _create_box(left, _c1)
        if right:
            _box.addstr(right, _c2)
            if not _rest:
                temp_boxes.append(_box)
                return
            current_color = _c2
        else:
            current_color = _c1

        temp_boxes.append(_box)
        for _line in _rest:
            left, _, right = _line.partition('\0')
            _box = _create_box(left, current_color)
            if right:
                _box.addstr(right, _c2)
                current_color = _c2
            temp_boxes.append(_box)

    def _create_box(_s: str, _c: int = 0):
        _box = curses.newwin(1, column_width)
        _box.addstr(_s, _c)
        return _box


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
                _def_s = f"{sign_c}{' ' if 'SUB' in op else '>'}"
                gaps = 2
            else:
                _def_s = ''
                gaps = 1

            first_line, *rest = wrap_method(
                _def, gaps + index_len + label_len, indent - label_len
            )
            box = _create_box(str(index) + ' ', color('index_c'))
            if _label:
                box.addstr(_label, color('label_c'))
            box.addstr(first_line, color('def1_c'))
            temp_boxes.append(box)
            for line in rest:
                temp_boxes.append(_create_box(line, color('def1_c')))

            if _exsen:
                for ex in _exsen.split('<br>'):
                    first_line, *rest = wrap_method(ex, gaps + index_len - 1, 1 + indent)
                    box = _create_box((index_len + gaps - 1) * ' ')
                    box.addstr(first_line, color('exsen_c'))
                    temp_boxes.append(box)
                    for line in rest:
                        temp_boxes.append(_create_box(line, color('exsen_c')))
        elif op == 'LABEL':
            label, inflections = body
            temp_boxes.append(_create_box(''))
            if label:
                if inflections:
                    _push_chain(label, color('label_c'), inflections, color('inflection_c'))
                else:
                    first_line, *rest = wrap_method(label, 1, 0)
                    temp_boxes.append(_create_box(' ' + first_line, color('label_c')))
                    for line in rest:
                        temp_boxes.append(_create_box(line, color('label_c')))
        elif op == 'PHRASE':
            phrase, phon = body
            if phon:
                _push_chain(phrase, color('phrase_c'), phon, color('phon_c'))
            else:
                first_line, *rest = wrap_method(phrase, 1, 0)
                temp_boxes.append(_create_box(' ' + first_line, color('phrase_c')))
                for line in rest:
                    temp_boxes.append(_create_box(line, color('phrase_c')))
        elif op == 'HEADER':
            title = body[0]
            box = _create_box('')
            if title:
                temp_boxes.append(format_title(box, title))
            else:
                while True:
                    try:
                        box.addstr(HORIZONTAL_BAR, color('delimit_c'))
                    except curses.error:
                        break
                temp_boxes.append(box)
        elif op == 'ETYM':
            etym = body[0]
            if etym:
                temp_boxes.append(_create_box(''))
                first_line, *rest = wrap_method(etym, 1, indent)
                temp_boxes.append(_create_box(' ' + first_line, color('etym_c')))
                for line in rest:
                    temp_boxes.append(_create_box(line, color('etym_c')))
        elif op == 'POS':
            if body[0].strip(' |'):
                temp_boxes.append(_create_box(''))
                # TODO: Fix overflow.
                for elem in body:
                    pos, phon = elem.split('|')
                    # padding = (textwidth - len(pos) - len(phon) - 3) * ' '
                    box = _create_box(' ' + pos, color('pos_c'))
                    box.addstr('  ' + phon, color('phon_c'))
                    temp_boxes.append(box)
        elif op == 'AUDIO':
            pass
        elif op == 'SYN':
            first_line, *rest = wrap_method(body[0], 1, 0)
            syn_box = _new_window(1 + len(rest))
            syn_box.addstr(' ' + first_line, color('syn_c'))
            for line in rest:
                syn_box.addstr(line, color('syn_c'))
            _add_box(syn_box)

            first_line, *rest = wrap_method(body[1], 2, 0)
            syngloss_box = _new_window(1 + len(rest))
            syngloss_box.addstr(': ', color('sign_c'))
            syngloss_box.addstr(first_line, color('syngloss_c'))
            for line in rest:
                syngloss_box.addstr(line, color('syngloss_c'))
            _add_box(syngloss_box)

            for ex in body[2].split('<br>'):
                first_line, *rest = wrap_method(ex, 1, 1)
                synex_box = _new_window(1 + len(rest))
                synex_box.addstr(' ' + first_line, color('exsen_c'))
                for line in rest:
                    synex_box.addstr(line, color('exsen_c'))
                _add_box(synex_box)
        elif op == 'NOTE':
            first_line, *rest = wrap_method(body[0], 2, 0)
            note_box = _new_window(1 + len(rest))
            note_box.addstr('> ', color('attention_c'))
            note_box.addstr(first_line, color('reset'))
            # buffer.append(f'!{BOLD}{YEX}> {R}{first_line}{DEFAULT}')
            for line in rest:
                note_box.addstr(line, color('reset'))
                # buffer.append(f'!{BOLD}{line}{DEFAULT}')
            _add_box(note_box)
        else:
            raise AssertionError(f'unreachable dictionary operation: {op!r}')

        boxes.append(temp_boxes)
        lines_total += len(temp_boxes)

    return boxes, lines_total


def box_contents(dictionary):
    width_per_column, ncols = get_column_parameters()
    boxes, lines_total = format_dictionary(dictionary, width_per_column)
    return boxes, lines_total


def get_column_parameters():
    width = curses.COLS

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


class Screen:
    def __init__(self, stdscr, dictionary):
        # Static.
        self.stdscr = stdscr
        self.dictionary = dictionary

        # Updated every redraw.
        _boxes, self.lines_total = box_contents(dictionary)
        self.boxes = _boxes
        self.columns = self.split_into_columns()
        self.col_width = _boxes[0][0].getmaxyx()[1]

        # User facing state.
        self.box_toggles = [False] * len(_boxes)
        self.scroll_pos = 0

    def _draw_header(self):
        self.stdscr.insstr(
            0, 0, '  ' + self.dictionary.contents[0][1].ljust(curses.COLS),
            curses.color_pair(17)
        )

    def split_into_columns(self) -> list[curses._CursesWindow]:
        _, ncols = get_column_parameters()
        max_col_height = self.lines_total // ncols
        result = [[]]
        current_height = 0
        for lines in self.boxes:
            current_height += len(lines)
            result[-1].extend(lines)
            if current_height > max_col_height:
                result.append([])
                current_height = 0

        return result

    def update_for_redraw(self) -> None:
        curses.update_lines_cols()

        _boxes, self.lines_total = box_contents(self.dictionary)
        # Keep toggled boxes toggled.
        for lines in compress(_boxes, self.box_toggles):
            for line in lines:
                line.bkgd(0, curses.A_STANDOUT)

        self.boxes = _boxes
        self.columns = self.split_into_columns()
        self.col_width = _boxes[0][0].getmaxyx()[1]

    def draw(self) -> None:
        try:
            self.stdscr.move(1, 0)  # (0, 0) is reserved for the header.
        except curses.error:
            pass
        self.stdscr.clrtobot()
        self.stdscr.noutrefresh()

        tx = 0
        col_width = self.col_width
        scroll_pos = self.scroll_pos
        columns = self.columns

        # reset window positions up until the scroll position.
        for column in columns:
            for box in islice(column, None, scroll_pos):
                box.mvwin(0, 0)

        for column in columns:
            for y, box in enumerate(
                islice(column, scroll_pos, None), 1
            ):
                try:
                    box.mvwin(y, tx)
                except curses.error:
                    break
                box.noutrefresh()
            tx += col_width

        self._draw_header()
        curses.doupdate()

    def mark_box_at(self, y: int, x: int) -> None:
        if not y:  # header clicked.
            return

        # Because scrolling is implemented by moving windows around, these that
        # are not in view are tucked under the header to not interfere with box
        # toggling.  We should consider decoupling the scrolling functionality
        # from box toggling and maybe use a class to represent a Box if more
        # tightly coupled functionality is needed.  It is impossible to have
        # a pointer to an immutable type like a `bool` and as far as I know you
        # cannot remove/reset the top-left corner position from the curses window.
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

    def scroll_up(self, n: int = 1) -> None:
        max_boxes_in_column = 2 + max(map(len, self.columns)) - curses.LINES
        self.scroll_pos += n
        if self.scroll_pos > max_boxes_in_column:
            self.scroll_pos = max_boxes_in_column

    def scroll_down(self, n: int = 1) -> None:
        self.scroll_pos -= n
        if self.scroll_pos < 0:
            self.scroll_pos = 0


def c_main(stdscr: curses._CursesWindow, dictionary) -> int:
    curses.mousemask(-1)
    curses.mouseinterval(0)
    curses.curs_set(0)

    if curses.has_colors():
        curses.use_default_colors()
        for i in range(16):
            curses.init_pair(i + 1, i, -1)
        curses.init_pair(17, -1, 235)

    screen = Screen(stdscr, dictionary)
    while True:
        if curses.is_term_resized(curses.LINES, curses.COLS):
            screen.update_for_redraw()
            log('term resized!')

        screen.draw()
        c = stdscr.get_wch()
        if c == 'q':
            break
        elif c == curses.KEY_MOUSE:
            _, x, y, _, bstate = curses.getmouse()
            if bstate & curses.BUTTON1_PRESSED:
                screen.mark_box_at(y, x)
            elif bstate & curses.BUTTON4_PRESSED:
                screen.scroll_down(2)
            elif bstate & curses.BUTTON5_PRESSED:
                screen.scroll_up(2)
        elif c == curses.KEY_DOWN:
            screen.scroll_up(2)
        elif c == curses.KEY_UP:
            screen.scroll_down(2)
        else:
            #raise AssertionError(repr(c))
            pass

    return 0


def main():
    dictionary = ask_ahdictionary('get')
    curses.wrapper(c_main, dictionary)


if __name__ == '__main__':
    raise SystemExit(main())
