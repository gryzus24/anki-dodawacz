#!/usr/bin/env python3
from __future__ import annotations

import curses

from src.Dictionaries.ahdictionary import ask_ahdictionary
from src.Dictionaries.utils import wrap_lines, wrap_and_pad
from src.colors import *
from src.data import HORIZONTAL_BAR, config
from typing import NamedTuple



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
    def __init__(self, this_box, *, toggleable=True):
        self.this_box = this_box
        self.toggleable = toggleable
        self._toggled = False

    def toggle(self):
        if not self.toggleable:
            return

        if self._toggled:
            self.this_box.bkgd(0, curses.A_NORMAL)
            self._toggled = False
        else:
            self.this_box.bkgd(0, curses.A_STANDOUT)
            self._toggled = True

        self.this_box.refresh()


class DictionaryEntry(NamedTuple):
    box: curses.window
    toggleable: bool


def format_dictionary(dictionary, stdscr: curses._CursesWindow) -> list[curses._CursesWindow.box]:
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

    textwidth = 47
    wrap_style = 'regular'
    signed = False
    indent = 0

    y = x = 0
    buffer = []
    blank = textwidth * ' '
    wrap_method = wrap_and_pad(wrap_style, textwidth)
    boxes = []

    def _new_window(height):
        nonlocal y, x
        _new_win = curses.newwin(height, textwidth + 1, y, x)
        y += height
        if y > 40:
            x += textwidth + 1
            y = 0
        return _new_win

    def _push_chain(_s1: str, _c1: int, _s2: str, _c2: int) -> None:
        # TODO: fix color chaining.
        nonlocal y
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
        boxes.append(Box(chain_box))

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

            boxes.append(Box(box))

            if _exsen:
                for ex in _exsen.split('<br>'):
                    first_line, *rest = wrap_method(ex, gaps + index_len - 1, 1 + indent)
                    exsen_box = _new_window(1 + len(rest))
                    exsen_box.addstr((index_len + gaps - 1) * ' ')
                    exsen_box.addstr(first_line, color('exsen_c'))
                    for line in rest:
                        exsen_box.addstr('\n' + line, color('exsen_c'))
                    boxes.append(Box(exsen_box))
        elif op == 'LABEL':
            buffer.append(blank)
            label, inflections = body
            if label:
                if inflections:
                    _push_chain(label, color('label_c'), inflections, color('inflection_c'))
                else:
                    first_line, *rest = wrap_method(label, 1, 0)
                    label_box = _new_window(1 + len(rest))
                    label_box.addstr(' ' + first_line, color('label_c'))
                    for line in rest:
                        label_box.addstr('\n' + line, color('label_c'))

                    boxes.append(Box(label_box))
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

                boxes.append(Box(phrase_box))
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
            boxes.append(Box(header_box))
        elif op == 'ETYM':
            etym = body[0]
            if etym:
                buffer.append(blank)
                first_line, *rest = wrap_method(etym, 1, indent)
                buffer.append(f' {etym_c}{first_line}')
                for line in rest:
                    buffer.append(f'${etym_c}{line}')
        elif op == 'POS':
            if body[0].strip(' |'):
                buffer.append(blank)
                for elem in body:
                    pos, phon = elem.split('|')
                    padding = (textwidth - len(pos) - len(phon) - 3) * ' '
                    buffer.append(f' {pos_c}{pos}  {phon_c}{phon}{padding}')
        elif op == 'AUDIO':
            pass
        elif op == 'SYN':
            first_line, *rest = wrap_method(body[0], 1, 0)
            buffer.append(f'! {syn_c}{first_line}')
            for line in rest:
                buffer.append(f'!{syn_c}{line}')

            first_line, *rest = wrap_method(body[1], 2, 0)
            buffer.append(f'!{sign_c}: {syngloss_c}{first_line}')
            for line in rest:
                buffer.append(f'!{syngloss_c}{line}')

            for ex in body[2].split('<br>'):
                first_line, *rest = wrap_method(ex, 1, 1)
                buffer.append(f' {exsen_c}{first_line}')
                for line in rest:
                    buffer.append(f'${exsen_c}{line}')
        elif op == 'NOTE':
            first_line, *rest = wrap_method(body[0], 2, 0)
            buffer.append(f'!{BOLD}{YEX}> {R}{first_line}{DEFAULT}')
            for line in rest:
                buffer.append(f'!{BOLD}{line}{DEFAULT}')
        else:
            raise AssertionError(f'unreachable dictionary operation: {op!r}')

    return boxes


def c_main(stdscr: curses._CursesWindow) -> int:
    curses.mousemask(-1)
    curses.mouseinterval(0)
    curses.curs_set(0)

    if curses.has_colors():
        curses.use_default_colors()

        for i in range(16):
            curses.init_pair(i + 1, i, -1)

    dictionary = ask_ahdictionary('get')
    boxes = format_dictionary(dictionary, stdscr)

    max_y, max_x = stdscr.getmaxyx()

    stdscr.noutrefresh()
    for box in boxes:
        box.this_box.noutrefresh()

    curses.doupdate()
    max_cur = len(boxes)
    cur = 0
    while True:

        c = stdscr.get_wch()
        if c == 'q':
            break
        elif c == curses.KEY_MOUSE:
            _, x, y, _, bstate = curses.getmouse()
            if bstate & curses.BUTTON1_PRESSED:
                for i in range(cur, len(boxes)):
                    box = boxes[i]
                    if box.this_box.enclose(y, x):
                        box.toggle()
                        break
            elif bstate & curses.BUTTON4_PRESSED:
                cur -= 2
                if cur < 1:
                    cur = 0
            elif bstate & curses.BUTTON5_PRESSED:
                cur += 2
                if cur > max_cur - 1:
                    cur = max_cur - 1
            else:
                pass
                # for i in range(9):
                #     stdscr.delch(0, i)
                # stdscr.addstr(0, 100, str(boxes[cur].this_box.getyx()) + ' ' + str(cur))

            i = cur
            ty = tx = 0
            while ty < max_y:
                try:
                    box = boxes[i]
                except IndexError:
                    stdscr.move(ty, 0)
                    stdscr.deleteln()
                    stdscr.addstr('(END)')
                    break

                # ty, tx = box.this_box.getbegyx()
                # stdscr.addstr(0, 0, f'{b} {z}')

                try:
                    box.this_box.mvwin(ty, 0)
                except curses.error:
                    stdscr.move(ty, 0)
                    stdscr.deleteln()

                box.this_box.noutrefresh()
                box_y, _ = box.this_box.getmaxyx()
                ty += box_y

                i += 1

            if ty >= max_y:
                curses.doupdate()
            else:
                max_cur = cur
        else:
            #raise AssertionError(repr(c))
            pass

    return 0


def main():
    curses.wrapper(c_main)


if __name__ == '__main__':
    raise SystemExit(main())
