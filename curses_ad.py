#!/usr/bin/env python3
from __future__ import annotations

import curses

from src.Dictionaries.ahdictionary import ask_ahdictionary
from src.Dictionaries.utils import wrap_and_pad
from src.colors import *
from src.data import HORIZONTAL_BAR, config

from itertools import islice


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


class Box:
    def __init__(self, this_box, *, is_toggled):
        self.this_box = this_box
        self.is_toggled = is_toggled

    def toggle(self):
        if self.is_toggled:
            self.this_box.bkgd(0, curses.A_NORMAL)
            self.is_toggled = False
        else:
            self.this_box.bkgd(0, curses.A_STANDOUT)
            self.is_toggled = True


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
        _first_line, *_rest = wrap_method(f'{_s1} {_s2}', 1, 0)
        chain_box = _new_window(1 + len(_rest))
        # if '\0' in _first_line:
        #     _first_line = _first_line.replace('\0', ' ' + _c2)
        #     current_color = _c2
        # else:
        #     current_color = _c1
        current_color = _c1
        chain_box.addstr(' ' + _first_line, _c1)
        for _line in _rest:
            if '\0' in _line:
                #_line = _line.replace('\0', ' ' + _c2)
                chain_box.addstr(_line, current_color)
                current_color = _c2
            else:
                chain_box.addstr('\n' + _line, current_color)
        _add_box(chain_box)

    index = 0

    for op, *body in dictionary.contents:
        # sys.stdout.write(f'{op}\n{body}\n'); continue  # DEBUG

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
            box = _new_window(1 + len(rest))
            box.addstr(str(index) + ' ', color('index_c'))
            if _label:
                box.addstr(_label, color('label_c'))
            box.addstr(first_line, color('def1_c'))

            for line in rest:
                box.addstr('\n' + line, color('def1_c'))

            _add_box(box)

            if _exsen:
                for ex in _exsen.split('<br>'):
                    first_line, *rest = wrap_method(ex, gaps + index_len - 1, 1 + indent)
                    exsen_box = _new_window(1 + len(rest))
                    exsen_box.addstr((index_len + gaps - 1) * ' ')
                    exsen_box.addstr(first_line, color('exsen_c'))
                    for line in rest:
                        exsen_box.addstr('\n' + line, color('exsen_c'))
                    _add_box(exsen_box)
        elif op == 'LABEL':
            label, inflections = body
            blank = _new_window(1)
            _add_box(blank)
            if label:
                if inflections:
                    _push_chain(label, color('label_c'), inflections, color('inflection_c'))
                else:
                    first_line, *rest = wrap_method(label, 1, 0)
                    label_box = _new_window(1 + len(rest))
                    label_box.addstr(' ' + first_line, color('label_c'))
                    for line in rest:
                        label_box.addstr('\n' + line, color('label_c'))

                    _add_box(label_box)
        elif op == 'PHRASE':
            phrase, phon = body
            if phon:
                _push_chain(phrase, color('phrase_c'), phon, color('phon_c'))
            else:
                first_line, *rest = wrap_method(phrase, 1, 0)
                phrase_box = _new_window(1 + len(rest))
                phrase_box.addstr(' ' + first_line, color('phrase_c'))
                for line in rest:
                    phrase_box.addstr('\n' + line, color('phrase_c'))

                _add_box(phrase_box)
        elif op == 'HEADER':
            title = body[0]
            header_box = _new_window(1)
            if title:
                header_box = format_title(header_box, title)
            else:
                while True:
                    try:
                        header_box.addstr(HORIZONTAL_BAR, color('delimit_c'))
                    except curses.error:
                        break
            _add_box(header_box)
        elif op == 'ETYM':
            etym = body[0]
            if etym:
                blank = _new_window(1)
                _add_box(blank)
                first_line, *rest = wrap_method(etym, 1, indent)
                etym_box = _new_window(1 + len(rest))
                etym_box.addstr(' ' + first_line, color('etym_c'))
                for line in rest:
                    etym_box.addstr(line, color('etym_c'))
                _add_box(etym_box)
        elif op == 'POS':
            if body[0].strip(' |'):
                blank = _new_window(1)
                _add_box(blank)
                # TODO: Fix overflow.
                for elem in body:
                    pos, phon = elem.split('|')
                    # padding = (textwidth - len(pos) - len(phon) - 3) * ' '
                    pos_box = _new_window(1)
                    pos_box.addstr(' ' + pos, color('pos_c'))
                    pos_box.addstr('  ' + phon, color('phon_c'))
                    _add_box(pos_box)
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

    return boxes, lines_total


def prepare_columns(boxes, lines_total, ncols):
    col_height = int(lines_total / ncols + 1)
    result = [[]]
    ty = 0
    for box in boxes:
        box_y, _ = box.this_box.getmaxyx()
        result[-1].append(box)
        ty += box_y
        if ty > col_height:
            result.append([])
            ty = 0

    return result


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

    fill = r // ncols
    col_width = 39 + fill
    return col_width, ncols


class Screen:
    def __init__(self, stdscr, dictionary):
        self.stdscr = stdscr
        self.dictionary = dictionary
        self._curses_boxes, self._lines_total = box_contents(dictionary)
        self.boxes = [Box(box, is_toggled=False) for box in self._curses_boxes]
        self.columns = self.prepare_columns()
        self.scroll_pos = 0

    @property
    def col_width(self):
        return self._curses_boxes[0].getmaxyx()[1]

    def prepare_columns(self):
        _, ncols = get_column_parameters()
        max_col_height = int(self._lines_total / ncols + 1)
        result = [[]]
        current_height = 0
        for box in self.boxes:
            box_y, _ = box.this_box.getmaxyx()
            result[-1].append(box)
            current_height += box_y
            if current_height > max_col_height:
                result.append([])
                current_height = 0

        return result

    def update_columns(self):
        curses.update_lines_cols()
        self._curses_boxes, self._lines_total = box_contents(self.dictionary)
        for box, curses_box in zip(self.boxes, self._curses_boxes):
            if box.is_toggled:
                curses_box.bkgd(0, curses.A_STANDOUT)
            box.this_box = curses_box
        self.columns = self.prepare_columns()

    def draw(self):
        self.stdscr.erase()
        self.stdscr.noutrefresh()
        tx = 0
        col_width = self.col_width
        for column in self.columns:
            ty = 0
            for box in islice(column, self.scroll_pos, None):
                try:
                    box.this_box.mvwin(ty, tx)
                except curses.error:
                    break
                box.this_box.noutrefresh()
                ty += box.this_box.getmaxyx()[0]
            tx += col_width
        curses.doupdate()

    def mark_box_at(self, y, x):
        # This is fast enough, ~100_000ns worst case scenario.
        # Bisection won't help because of the language overhead.
        for box in self.boxes:
            if box.this_box.enclose(y, x):
                box.toggle()
                return

    def scroll_up(self, n=1):
        self.scroll_pos += n
        if self.scroll_pos > self._lines_total:
            self.scroll_pos = self._lines_total

    def scroll_down(self, n=1):
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

    screen = Screen(stdscr, dictionary)
    screen.draw()
    while True:
        if curses.is_term_resized(curses.LINES, curses.COLS):
            screen.update_columns()
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
                screen.scroll_down()
            elif bstate & curses.BUTTON5_PRESSED:
                screen.scroll_up()
        elif c == curses.KEY_DOWN:
            screen.scroll_up()
        elif c == curses.KEY_UP:
            screen.scroll_down()
        else:
            #raise AssertionError(repr(c))
            pass

    return 0


def main():
    dictionary = ask_ahdictionary('get')
    curses.wrapper(c_main, dictionary)


if __name__ == '__main__':
    raise SystemExit(main())
