from __future__ import annotations

import curses
import shutil
from collections import Counter
from itertools import islice
from typing import (
    TYPE_CHECKING, NamedTuple, Callable, Any, Reversible, Optional, Container
)

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


# Intercepts every __getattribute__ to convert it to an equivalent color pair.
class MetaColor(type):
    def __getattribute__(self, item: str) -> int:
        return curses.color_pair(ansi_to_pair[getattr(_Color, item)])


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
    for entry in dictionary.contents:
        op = entry[0]
        temp_boxes = []

        if 'DEF' in op:
            index += 1
            index_len = len(str(index))

            _def, _exsen, _label = entry[1], entry[2], entry[3]
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
                ), (rest, def_c)
            ))
            if _exsen:
                for ex in _exsen.split('<br>'):
                    first_line, rest = wrap_method(ex, gaps + index_len - 1, 1 + indent)
                    temp_boxes.extend(_into_boxes(
                        (
                           ((index_len + gaps - 1) * ' ', Color.exsen),
                           (first_line, Color.exsen)
                        ), (rest, Color.exsen)
                    ))
        elif op == 'LABEL':
            label, inflections = entry[1], entry[2]
            temp_boxes.append(curses.newwin(1, column_width))
            if label:
                if inflections:
                    _push_chain(label, Color.label, inflections, Color.inflection)
                else:
                    first_line, rest = wrap_method(label, 1, 0)
                    temp_boxes.extend(_into_boxes(
                        (
                           (' ' + first_line, Color.label),
                        ), (rest, Color.label)
                    ))
        elif op == 'PHRASE':
            phrase, phon = entry[1], entry[2]
            if phon:
                _push_chain(phrase, Color.phrase, phon, Color.phon)
            else:
                first_line, rest = wrap_method(phrase, 1, 0)
                temp_boxes.extend(_into_boxes(
                    (
                       (' ' + first_line, Color.phrase),
                    ), (rest, Color.phrase)
                ))
        elif op == 'HEADER':
            title = entry[1]
            box = curses.newwin(1, column_width)
            if title:
                box.insstr(' ]' + column_width * HORIZONTAL_BAR, Color.delimit)
                box.insstr(title, Color.delimit | curses.A_BOLD)
                box.insstr(HORIZONTAL_BAR + '[ ', Color.delimit)
            else:
                box.insstr(column_width * HORIZONTAL_BAR, Color.delimit)
            temp_boxes.append(box)
        elif op == 'ETYM':
            etym = entry[1]
            if etym:
                temp_boxes.append(curses.newwin(1, column_width))
                first_line, rest = wrap_method(etym, 1, indent)
                temp_boxes.extend(_into_boxes(
                    (
                       (' ' + first_line, Color.etym),
                    ), (rest, Color.etym)
                ))
        elif op == 'POS':
            if entry[1].strip(' |'):
                temp_boxes.append(curses.newwin(1, column_width))
                for elem in entry[1:]:
                    pos, phon = elem.split('|')
                    _push_chain(pos, Color.pos, phon, Color.phon)
        elif op == 'AUDIO':
            pass
        elif op == 'SYN':
            first_line, rest = wrap_method(entry[1], 1, 0)
            temp_boxes.extend(_into_boxes(
                (
                   (' ' + first_line, Color.syn),
                ), (rest, Color.syn)
            ))
            first_line, rest = wrap_method(entry[2], 2, 0)
            temp_boxes.extend(_into_boxes(
                (
                   (': ', Color.sign),
                   (first_line, Color.syngloss)
                ), (rest, Color.syngloss)
            ))
            for ex in entry[3].split('<br>'):
                first_line, rest = wrap_method(ex, 1, 1)
                temp_boxes.extend(_into_boxes(
                    (
                       (' ' + first_line, Color.exsen),
                    ), (rest, Color.exsen)
                ))
        elif op == 'NOTE':
            first_line, rest = wrap_method(entry[1], 2, 0)
            temp_boxes.extend(_into_boxes(
                (
                   ('> ', Color.YEX | curses.A_BOLD),
                   (first_line, 0 | curses.A_BOLD)
                ), (rest, 0 | curses.A_BOLD)
            ))
        else:
            raise AssertionError(f'unreachable dictionary operation: {op!r}')

        boxes.append(temp_boxes)
        lines_total += len(temp_boxes)

    return boxes, lines_total


def column_should_wrap(contents: list[tuple[str, ...]], height: int) -> bool:
    # No need to simulate height with wrapping, this is good enough.
    approx_lines = sum(
        3 if op == 'SYN' else
        2 if op in ('LABEL', 'ETYM') or ('DEF' in op and body[1])
        else 1
        for op, *body in contents
    )
    return approx_lines > 0.01 * config['colviewat'][0] * height


def get_column_parameters(
        contents: list[tuple[str, ...]],
        height: int,
        width: int
) -> tuple[int, int]:
    # assume we have space for one more vertical line to simplify logic.
    width += 1

    if column_should_wrap(contents, height):
        config_ncols, state = config['columns']
        if state == '* auto':
            divisor = 40
        else:
            divisor = width // config_ncols
    else:
        return width - 1, 1

    ncols = width // divisor
    r = width % divisor
    if not r:
        return divisor - 1, ncols

    try:
        fill = r // ncols
    except ZeroDivisionError:
        return width - 1, 1

    col_width = divisor - 1 + fill
    return col_width, ncols


class WithinPhrase(NamedTuple):
    clicked: list[int]
    associated: list[int]


BORDER_PAD = 1
TOGGLEABLE = {'DEF', 'SUBDEF', 'SYN'}


class Screen:
    def __init__(self,
            stdscr: curses.window,
            dictionary: Dictionary,
            formatter: Callable[[Dictionary, int], tuple[list[list[curses.window]], int]]
    ) -> None:
        # For some reason:
        # 1. query a word
        # 2. press q
        # 3. resize terminal to a larger size
        # 4. query the same word
        # Leaves `hline` and `vline` artifacts from the previous stdscr.
        # clearing the screen fixes it.
        stdscr.clear()

        # Static.
        self.stdscr = stdscr
        self.dictionary = dictionary
        self.formatter = formatter

        # Screen dimensions.
        # Unfortunately Python's readline api does not expose functions and
        # variables responsible for signal handling, which makes it impossible
        # to reconcile curses' signal handling with the readline's one, so we
        # have to manage COLS and LINES variables ourselves.
        self.COLS, self.LINES = shutil.get_terminal_size()

        # Display
        _col_width, ncols = get_column_parameters(
            dictionary.contents,
            self.LINES - 2 * BORDER_PAD,
            self.COLS - 2 * BORDER_PAD
        )
        _col_width -= 2 * config['margin']
        if _col_width < 10:
            _col_width = 10

        _boxes, self.lines_total = formatter(dictionary, _col_width)
        self.boxes = _boxes
        self.col_width = _col_width
        self.columns = self._split_into_columns(_boxes, ncols)

        # User facing state.
        self.phraseno_to_ntoggles: Counter[int] = Counter()
        self.box_states = [curses.A_NORMAL] * len(_boxes)
        self.scroll_pos = 0

    def _split_into_columns(
            self, boxes: list[list[curses._CursesWindow]],
            ncols: int
    ) -> list[list[curses._CursesWindow]]:
        col_width = self.col_width
        max_col_height = self.lines_total // ncols
        result: list[list[curses._CursesWindow]] = [[]]
        current_height = 0
        # TODO: move certain boxes to the next column.
        for lines, dict_entry in zip(boxes, self.dictionary.contents):
            op = dict_entry[0]
            current_height += len(lines)
            if current_height > max_col_height:
                current_height = 0
                if op == 'HEADER' and not dict_entry[1]:
                    result.append([])
                else:
                    header = curses.newwin(1, col_width)
                    header.hline(0, col_width)
                    result.append([header])
                if op in ('LABEL', 'POS', 'ETYM'):
                    t = lines[1:]
                    result[-1].extend(t)
                    current_height -= 1
                else:
                    result[-1].extend(lines)
            else:
                result[-1].extend(lines)

        return result

    def displayable(self, lines: int, cols: int) -> bool:
        return cols > 4 and lines > 1

    def update_for_redraw(self) -> None:
        COLS, LINES = shutil.get_terminal_size()
        if not self.displayable(LINES, COLS):
            return

        _col_width, ncols = get_column_parameters(
            self.dictionary.contents,
            LINES - 2 * BORDER_PAD,
            COLS - 2 * BORDER_PAD
        )
        _col_width -= 2 * config['margin']
        if _col_width < 10:
            return

        self.COLS, self.LINES = COLS, LINES
        curses.resize_term(self.LINES, self.COLS)

        _boxes, self.lines_total = self.formatter(self.dictionary, _col_width)
        for lines, state in zip(_boxes, self.box_states):
            if state != curses.A_NORMAL:
                for line in lines:
                    line.bkgd(0, state)

        self.boxes = _boxes
        self.col_width = _col_width
        self.columns = self._split_into_columns(_boxes, ncols)

        eof = self.EOF
        if self.scroll_pos > eof:
            self.scroll_pos = eof

        self.stdscr.clear()

    def _draw_border(self) -> None:
        shift = BORDER_PAD + self.col_width + 2 * config['margin']
        try:
            for i in range(1, len(self.columns)):
                self.stdscr.vline(BORDER_PAD, i * shift, 0, self.LINES - 2 * BORDER_PAD)
        except curses.error:
            pass
        self.stdscr.box()
        self.stdscr.noutrefresh()

        try:
            header = self.columns[0][0]
        except IndexError:
            return
        header.mvwin(0, BORDER_PAD)
        header.noutrefresh()

    def draw(self) -> None:
        if not self.displayable(self.LINES, self.COLS):
            return

        self._draw_border()

        columns = self.columns
        col_width = self.col_width
        scroll_pos = self.scroll_pos
        lines = self.LINES
        margin = config['margin']

        # hide out of view windows behind the header to prevent
        # them from stealing clicks in the upper region.
        try:
            for column in self.columns:
                for box in islice(column, None, scroll_pos + BORDER_PAD):
                    box.mvwin(0, 1)
        except curses.error:
            pass

        tx = BORDER_PAD
        vertical_line_positions = []
        try:
            for column in self.columns:
                for y, box in enumerate(
                        islice(column, scroll_pos + BORDER_PAD, scroll_pos + lines - BORDER_PAD), 1
                ):
                    box.mvwin(y, tx + margin)
                    box.noutrefresh()
                tx += col_width + 1 + 2 * margin
                vertical_line_positions.append(tx)
        except curses.error:
            pass

        curses.doupdate()

    def _toggle_associated_boxes(self, to_toggle: Container, phraseno: int, i: int) -> None:
        ntoggles = self.phraseno_to_ntoggles[phraseno]
        if ntoggles == 0:
            new_state = curses.A_NORMAL
        elif ntoggles == 1:
            new_state = curses.A_BOLD
        else:
            return

        for j in range(i - 1, 0, -1):
            prev_op = self.dictionary.contents[j][0]
            if prev_op in to_toggle:
                for _line in self.boxes[j]:
                    _line.bkgd(0, new_state)
                self.box_states[j] = new_state
            if prev_op == 'PHRASE':
                break

        for j in range(i + 1, len(self.boxes)):
            next_op = self.dictionary.contents[j][0]
            if next_op == 'PHRASE':
                break
            if next_op in to_toggle:
                for _line in self.boxes[j]:
                    _line.bkgd(0, new_state)
                self.box_states[j] = new_state

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
        phraseno = 0
        for i, (state, lines) in enumerate(zip(self.box_states, self.boxes)):
            op = self.dictionary.contents[i][0]
            if op == 'PHRASE':
                phraseno += 1
            if op not in TOGGLEABLE:
                continue

            for line in lines:
                if id(line) not in not_in_view and line.enclose(y, x):
                    break
            else: # not found
                continue

            if state == curses.A_STANDOUT:
                new_state = curses.A_NORMAL
                self.phraseno_to_ntoggles[phraseno] -= 1
            else:
                new_state = curses.A_STANDOUT
                self.phraseno_to_ntoggles[phraseno] += 1

            for line in lines:
                line.bkgd(0, new_state)

            self.box_states[i] = new_state
            if op in ('DEF', 'SUBDEF'):
                self._toggle_associated_boxes({'ETYM', 'POS', 'PHRASE'}, phraseno, i)
            return

    def dump_screen_state(self) -> list[WithinPhrase]:
        result = []
        clicked_boxes: list[int] = []
        associated_boxes: list[int] = []
        for i in range(1, len(self.boxes)):
            op = self.dictionary.contents[i][0]
            box_state = self.box_states[i]
            if op == 'PHRASE' and (clicked_boxes or associated_boxes):
                result.append(WithinPhrase(clicked_boxes, associated_boxes))
                clicked_boxes = []
                associated_boxes = []
            elif box_state == curses.A_STANDOUT:
                clicked_boxes.append(i)
            elif box_state == curses.A_BOLD:
                associated_boxes.append(i)

        if clicked_boxes or associated_boxes:
            result.append(WithinPhrase(clicked_boxes, associated_boxes))

        return result

    @property
    def EOF(self) -> int:
        r = 2 + max(map(len, self.columns)) - self.LINES
        return r if r > 0 else 0

    def view_down(self, n: int = 1) -> None:
        EOF = self.EOF
        self.scroll_pos += n
        if self.scroll_pos > EOF:
            self.scroll_pos = EOF

    def view_up(self, n: int = 1) -> None:
        self.scroll_pos -= n
        if self.scroll_pos < 0:
            self.scroll_pos = 0


def get_wch_wsigwinch(stdscr: curses._CursesWindow) -> int | str | None:
    i = 1
    while i % 3:
        try:
            return stdscr.get_wch()
        except curses.error:
            # Ignore the first callback, report only if resized or not.
            i += 1

    return None


KEY_MAP = {
    '\x10': 'C-p',
    '\x0e': 'C-n',
    '\x18': 'C-x',
}

def _c_main(stdscr: curses.window, dictionaries: list[Dictionary]) -> int:
    dictionary = dictionaries[0]
    if not dictionary.contents:
        return -1

    screen = Screen(stdscr, dictionary, formatter=format_dictionary)
    buffer = []
    while True:
        screen.draw()

        c = get_wch_wsigwinch(stdscr)
        if c is None:
            curses.napms(175)
            screen.update_for_redraw()
            continue

        c = KEY_MAP.get(c, c)  # type: ignore
        if c in ('q', 'Q', 'C-x'):
            break
        elif c == curses.KEY_MOUSE:
            _, x, y, _, bstate = curses.getmouse()
            if bstate & curses.BUTTON1_PRESSED:
                screen.mark_box_at(y, x)
            elif bstate & curses.BUTTON4_PRESSED:
                screen.view_up(2)
            elif bstate & curses.BUTTON5_PRESSED:
                screen.view_down(2)
        elif c in (curses.KEY_DOWN, 'j', 'C-n'):
            screen.view_down(2)
        elif c in (curses.KEY_UP, 'k', 'C-p'):
            screen.view_up(2)
        elif c == curses.KEY_SNEXT:
            screen.view_down(screen.LINES - 2 * BORDER_PAD - 1)
        elif c == curses.KEY_SPREVIOUS:
            screen.view_up(screen.LINES - 2 * BORDER_PAD - 1)
        elif c == 'G':
            screen.scroll_pos = screen.EOF
        elif c == 'A':
            screen.dump_screen_state()

        if c == 'g':
            buffer.append(c)
            if buffer == ['g', 'g']:
                screen.scroll_pos = 0
        else:
            buffer.clear()
            # raise AssertionError(repr(c))

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
