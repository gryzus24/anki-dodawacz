from __future__ import annotations

import curses
import os
import shutil
from collections import Counter, deque
from itertools import islice
from typing import Any, Callable, Iterable, NamedTuple, Optional, Reversible, TYPE_CHECKING

import src.anki_interface as anki
import src.cards as cards
from src.Dictionaries.utils import wrap_and_pad
from src.colors import Color as _Color
from src.data import HORIZONTAL_BAR, LINUX, config

if TYPE_CHECKING:
    from ankidodawacz import QuerySettings
    from src.Dictionaries.dictionary_base import Dictionary
    from src.anki_interface import AnkiResponse

# Pythons < 3.10 do not define BUTTON5_PRESSED.
# Also, mouse wheel requires ncurses >= 6.
BUTTON5_PRESSED = 2097152

# Assume the 16-bit color capability. Don't be silly.
os.environ['TERM'] = 'xterm-256color'

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
        f.write(f'{f.tell()} {" ".join(messages)}\n')


def format_dictionary(
        dictionary: Dictionary,
        column_width: int,
) -> tuple[list[list[curses._CursesWindow]], int]:
    # Format self.contents' list of (op, body)
    # into wrapped, colored and padded body lines.
    # Available instructions:
    #  (DEF,    'definition', 'example_sentence', 'label')
    #  (SUBDEF, 'definition', 'example_sentence')
    #  (LABEL,  'os_label', 'additional_info')
    #  (PHRASE, 'phrase', 'phonetic_spelling')
    #  (HEADER, 'filling_character', 'header_title')
    #  (POS,    'pos|phonetic_spelling', ...)  ## `|` acts as a separator.
    #  (AUDIO,  'audio_url')
    #  (SYN,    'synonyms', 'gloss', 'examples')
    #  (NOTE,   'note')

    wrap_method = wrap_and_pad(config['-textwrap'], column_width)
    indent = config['-indent'][0]
    signed = config['-showsign']

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
                _def_sign = ' ' if 'SUB' in op else '>'
                gaps = 2
            else:
                _def_sign = ''
                gaps = 1

            first_line, rest = wrap_method(
                _def, gaps + index_len + label_len, indent - label_len
            )
            def_color = Color.def1 if index % 2 else Color.def2
            temp_boxes.extend(_into_boxes(
                (
                   (_def_sign, Color.sign),
                   (f'{index} ', Color.index),
                   (_label, Color.label),
                   (first_line, def_color)
                ), (rest, def_color)
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


def create_and_add_card_to_anki(
        dictionary: Dictionary,
        status_bar: StatusBar,
        definition_indices: list[int],
        settings: QuerySettings
) -> None:
    grouped_by_phrase = dictionary.group_phrases_to_definitions(definition_indices)
    if not grouped_by_phrase:
        status_bar.error('This dictionary does not support creating cards')
        return

    ok_response = None
    ncards_added = 0
    for card, audio_error, error_info in cards.cards_from_definitions(
            dictionary, grouped_by_phrase, settings
    ):
        if audio_error is not None:
            status_bar.error(audio_error, newline=True)
            status_bar.add_lines(error_info, curses.color_pair(0))

        card = cards.format_and_prepare_card(card)

        if config['-ankiconnect']:
            response = anki.add_card_to_anki(card)
            if response.error:
                status_bar.send_anki_response(f'({card["phrase"]}) Could not add card:', response)
            else:
                ncards_added += 1
                if ok_response is None:
                    ok_response = response

        if config['-savecards']:
            cards.save_card_to_file(card)
            status_bar.success(f'Card saved to a file: {os.path.basename(cards.CARD_SAVE_LOCATION)!r}')

    if ok_response is not None:
        status_bar.send_anki_response(
            f'Successfully added {ncards_added} card{"s" if ncards_added > 1 else ""}',
            ok_response
        )


def _draw_help() -> None:
    try:
        help_win = curses.newwin(2, COLS - 2, LINES - 3, 1)
    except curses.error:
        return

    messages = [
        ('S ', ' Cards per cell'), ('1-9', ' Select cell'), ('gg', ' Go top'),
        ('j/k', ' Move down/up'), ('F1', ' Help'),
        ('C ', ' Card from cells'), ('dd', ' Deselect all'), ('G ', ' Go EOF'),
        ('h/l', ' Swap screens'), ('q ', ' Exit'),
    ]
    # As the second row is longer - and we can easily tell - to simplify
    # things let's start from the hard coded 5 as long as:
    # TODO: Display additional help cells as terminal width increases and hide
    #       as it decreases, but keep 5 elements per row when width is 80.
    #       Something similar to what nano does.
    line_len = sum(len(''.join(x)) for x in messages[5:])
    free_per_cell = (COLS - 3 - line_len) // 4
    if free_per_cell < 1:
        free_per_cell = 1

    gaps = 4 * [free_per_cell * ' '] + ['']
    y = gap_i = 0
    for i, (key, msg) in enumerate(messages, 1):
        help_win.insstr(y, 0, msg)
        help_win.insstr(y, 0, key, curses.color_pair(17))
        help_win.insstr(y, 0, gaps[gap_i])
        if not i % 5:
            y += 1
            gap_i = 0
        else:
            gap_i += 1

    help_win.noutrefresh()


BORDER_PAD = 1

class StatusBar:
    def __init__(self, *, persistence: int) -> None:
        self.persistence = persistence if persistence > 0 else 1
        self.ticks = 1
        # (message, color_pair_number)
        self.buffer: list[tuple[str, int]] = []
        self.nohelp = config['-nohelp']

    def add_lines(self, lines: Iterable[str], color_pair: int) -> None:
        self.ticks = 1
        for line in lines:
            self.buffer.append((line, color_pair))

    def append_line(self, line: str, color_pair: int) -> None:
        self.ticks = 1
        if not self.buffer:
            return self.buffer.append((line, color_pair))

        last_line, last_color = self.buffer[-1]
        if last_color != color_pair:
            return self.buffer.append((line, color_pair))

        new_line = last_line + '  ' + line
        space_missing = COLS - len(new_line) - 2*BORDER_PAD
        if space_missing < 0:
            self.buffer[-1] = (
                # this uses this idiom: a[-n:]
                new_line[-len(new_line) - space_missing:],
                color_pair
            )
        else:
            self.buffer[-1] = (new_line, color_pair)

    def success(self, line: str, *, newline: bool = False) -> None:
        if newline:
            self.add_lines([line], curses.color_pair(18))
        else:
            self.append_line(line, curses.color_pair(18))

    def error(self, line: str, *, newline: bool = False) -> None:
        if newline:
            self.add_lines([line], curses.color_pair(19))
        else:
            self.append_line(line, curses.color_pair(19))

    def send_anki_response(self, msg: str, response: AnkiResponse) -> None:
        self.buffer.append(
            (msg, curses.color_pair(19) if response.error else curses.color_pair(18))
        )
        self.add_lines(response.body.split('\n'), curses.color_pair(0))

    def draw_if_available(self) -> None:
        if not self.nohelp:
            _draw_help()
        if not self.buffer:
            return

        y_topleft = LINES - len(self.buffer)
        y_bound = LINES // 2
        if y_topleft < y_bound:
            buffer = self.buffer[y_bound - y_topleft:]
            y_topleft = y_bound
        else:
            buffer = self.buffer

        win = curses.newwin(len(self.buffer), COLS, y_topleft, 0)
        for i, (line, color) in enumerate(buffer):
            line = ' ' + line
            padding = COLS - len(line)
            if padding < 0:
                line = line[:COLS-3] + '...'
            else:
                line = line + padding * ' '
            win.insstr(i, 0, line, color)

        win.noutrefresh()
        if not self.ticks % self.persistence:
            self.buffer.clear()
        else:
            self.ticks += 1


class ColumnParameters(NamedTuple):
    ncols: int
    width: int
    margin: int


def get_corollaries() -> set[str]:
    result = {'PHRASE'}
    if config['-audio'] != '-':
        result.add('AUDIO')
    if config['-pos']:
        result.add('POS')
    if config['-etym']:
        result.add('ETYM')
    return result


DIRECTLY_TOGGLEABLE = {'DEF', 'SUBDEF', 'SYN'}
AUTO_COLUMN_WIDTH = 43
MINIMAL_TEXT_WIDTH = 24

class Screen:
    def __init__(self,
            stdscr: curses._CursesWindow,
            dictionary: Dictionary,
            formatter: Callable[[Dictionary, int], tuple[list[list[curses._CursesWindow]], int]]
    ) -> None:
        # Static.
        self.stdscr = stdscr
        self.status_bar = StatusBar(persistence=3)
        self.dictionary = dictionary
        self.formatter = formatter

        # Display
        conf_ncols, state = config['-columns']
        self.column_state = 0 if 'auto' in state else conf_ncols

        _boxes, self.lines_total, self.column_params = \
            self._box_dictionary_entries_and_get_column_params(config['-margin'])
        self.boxes = _boxes
        self.columns = self._split_into_columns(_boxes)

        # User facing state.
        self.COROLLARY_BOXES = get_corollaries()
        self.phraseno_to_ntoggles: Counter[int] = Counter()
        self.box_states = [curses.A_NORMAL] * len(_boxes)
        self.scroll_pos = 0

    @property
    def screen_height(self) -> int:
        return LINES - 2*BORDER_PAD - (0 if self.status_bar.nohelp else 2)

    def _box_dictionary_entries_and_get_column_params(self,
            margin: int
    ) -> tuple[list[list[curses._CursesWindow]], int, ColumnParameters]:
        width = COLS - 2*BORDER_PAD + 1

        if self.column_state > 0:
            min_columns = max_columns = self.column_state
        else:  # auto
            min_columns = 1
            max_columns = width // AUTO_COLUMN_WIDTH
            if max_columns < 1:
                max_columns = 1

        height = self.screen_height
        while True:
            col_width = (width // min_columns) - 1
            col_text_width = col_width - 2*margin
            if col_text_width < MINIMAL_TEXT_WIDTH:
                margin -= (MINIMAL_TEXT_WIDTH - col_text_width) // 2
                if margin < 0:
                    margin = 0
                col_text_width = col_width - 2*margin
                if col_text_width < 1:
                    col_text_width = 1

            _boxes, _lines = self.formatter(self.dictionary, col_text_width)
            if (_lines // min_columns < height) or (min_columns >= max_columns):
                break
            else:
                min_columns += 1

        # Prevent crash if self.column_state > 0
        if col_width < 0:
            col_width = 0

        return _boxes, _lines, ColumnParameters(min_columns, col_width, margin)

    def _split_into_columns(self,
            boxes: list[list[curses._CursesWindow]]
    ) -> list[list[curses._CursesWindow]]:
        ncols, col_width, margin = self.column_params
        col_text_width = col_width - 2*margin

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
                    header = curses.newwin(1, col_text_width)
                    header.hline(0, col_text_width)
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

    def update_for_redraw(self) -> None:
        _boxes, self.lines_total, self.column_params =\
            self._box_dictionary_entries_and_get_column_params(config['-margin'])

        self.boxes = _boxes
        self.columns = self._split_into_columns(_boxes)

        for lines, state in zip(_boxes, self.box_states):
            if state != curses.A_NORMAL:
                for line in lines:
                    line.bkgd(0, state)

        eof = self.get_EOF()
        if self.scroll_pos > eof:
            self.scroll_pos = eof

    def _draw_border(self) -> None:
        ncols, col_width, _ = self.column_params
        shift = BORDER_PAD + col_width
        try:
            for i in range(1, ncols):
                self.stdscr.vline(BORDER_PAD, i * shift, 0, LINES - 2 * BORDER_PAD)

            header = self.columns[0][0]
            header.mvwin(0, BORDER_PAD)
        except (IndexError, curses.error):
            return

        self.stdscr.box()
        self.stdscr.bkgd(0, Color.delimit)
        self.stdscr.noutrefresh()
        header.noutrefresh()

    def draw(self) -> None:
        self._draw_border()

        columns = self.columns
        scroll_pos = self.scroll_pos
        _, col_width, margin = self.column_params

        # hide out of view windows behind the header to prevent
        # them from stealing clicks in the upper region.
        try:
            for column in columns:
                for box in islice(column, None, scroll_pos + BORDER_PAD):
                    box.mvwin(0, 1)
        except curses.error:
            pass

        try:
            tx = BORDER_PAD
            for column in columns:
                for y, box in enumerate(
                        islice(column, scroll_pos + BORDER_PAD, scroll_pos + LINES - BORDER_PAD), 1
                ):
                    box.mvwin(y, tx + margin)
                    box.noutrefresh()
                tx += col_width + 1
        except curses.error:
            pass

        self.status_bar.draw_if_available()
        curses.doupdate()

    def _toggle_box(self, i: int, state: int) -> None:
        for line in self.boxes[i]:
            line.bkgd(0, state)
        self.box_states[i] = state

    def _toggle_related_boxes(self, current_state: int, phraseno: int, box_index: int) -> None:
        if current_state == curses.A_STANDOUT:
            self._toggle_box(box_index, curses.A_NORMAL)
            self.phraseno_to_ntoggles[phraseno] -= 1
        else:
            self._toggle_box(box_index, curses.A_STANDOUT)
            self.phraseno_to_ntoggles[phraseno] += 1

        currently_toggled = self.phraseno_to_ntoggles[phraseno]
        if currently_toggled == 0:
            new_corollary_state = curses.A_NORMAL
        elif currently_toggled == 1:
            new_corollary_state = curses.A_BOLD
        else:
            return

        static_entries_to_index = self.dictionary.static_entries_to_index_from_index(box_index)
        for op in self.COROLLARY_BOXES:
            if op in static_entries_to_index:
                self._toggle_box(static_entries_to_index[op], new_corollary_state)

    def mark_box_at(self, y: int, x: int) -> None:
        if y < 1:  # header clicked.
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
            id(column[i])
            for column in self.columns
            for i in range(self.scroll_pos)
        }
        phraseno = 0
        for i, (state, lines) in enumerate(zip(self.box_states, self.boxes)):
            op = self.dictionary.contents[i][0]
            if op == 'PHRASE':
                phraseno += 1
            if op not in DIRECTLY_TOGGLEABLE:
                continue
            for line in lines:
                if id(line) not in not_in_view and line.enclose(y, x):
                    self._toggle_related_boxes(state, phraseno, i)
                    return

    def mark_box_by_number(self, n: int) -> None:
        if n < 1:
            return

        cur = phraseno = 0
        for i, (state, lines) in enumerate(zip(self.box_states, self.boxes)):
            op = self.dictionary.contents[i][0]
            if op == 'PHRASE':
                phraseno += 1
            if op not in DIRECTLY_TOGGLEABLE:
                continue
            if cur == 20:  # pressing S-0, current max
                return
            cur += 1
            if n == cur:
                self._toggle_related_boxes(state, phraseno, i)
                return

    def deselect_all(self) -> None:
        self.phraseno_to_ntoggles.clear()
        for i, state in enumerate(self.box_states):
            if state != curses.A_NORMAL:
                self._toggle_box(i, curses.A_NORMAL)

    def get_indices_of_selected_boxes(self) -> list[int]:
        return [i for i, x in enumerate(self.box_states) if x == curses.A_STANDOUT]

    def get_EOF(self) -> int:
        extra_pad = 2 if self.status_bar.nohelp else 4
        r = max(map(len, self.columns)) + extra_pad - LINES
        return r if r > 0 else 0

    def view_down(self, n: int = 1) -> None:
        self.scroll_pos += n
        eof = self.get_EOF()
        if self.scroll_pos > eof:
            self.scroll_pos = eof

    def view_up(self, n: int = 1) -> None:
        self.scroll_pos -= n
        if self.scroll_pos < 0:
            self.scroll_pos = 0


class ScreenBuffer:
    def __init__(self, screens: list[Screen]) -> None:
        self.screens = screens
        self.cursor = 0

    @property
    def current(self) -> Screen:
        return self.screens[self.cursor]

    def next(self) -> Screen:
        if self.cursor < len(self.screens) - 1:
            self.cursor += 1
        return self.current

    def previous(self) -> Screen:
        if self.cursor > 0:
            self.cursor -= 1
        return self.current

    def update_after_resize(self, _lines: int, _cols: int) -> None:
        # This is noticeably slow when there are more than 10 screens.
        # Updating lazily doesn't help, because `curses.resize_term` is what
        # takes the majority of the time.
        curses.resize_term(_lines, _cols)
        for screen in self.screens:
            screen.update_for_redraw()
        # prevents stalling when updating takes a noticeable amount of time.
        curses.flushinp()


KEY_MAP = {
    '\x02': 'C-b',
    '\x06': 'C-f',
    '\x0c': 'C-l',
    '\x0e': 'C-n',
    '\x10': 'C-p',
    '\x18': 'C-x',
}

# Unfortunately Python's readline api does not expose functions and variables
# responsible for signal handling, which makes it impossible to reconcile
# curses' signal handling with the readline's one, so we have to manage
# COLS and LINES variables ourselves. It also affects the `curses.keyname`
# function. But there's more! When curses is de-initialized, readline's
# sigwinch handler does not raise "no input", but ungets the correct "410"
# code as soon as curses comes back to the battlefield! This is worked around
# by flushing any typeahead in the main function.
# Let's enjoy the hacky code that follows.

Wch_key_t = int | str | None

if LINUX:
    # if using readline.
    def is_resized(c: Wch_key_t) -> bool:
        return c is None
else:
    def is_resized(c: Wch_key_t) -> bool:
        return c == curses.KEY_RESIZE and curses.is_term_resized(LINES, COLS)


def get_wch_sigwinch(stdscr: curses._CursesWindow) -> int | str | None:
    try:
        return stdscr.get_wch()
    except curses.error:
        return None


COLS = LINES = 0
###############################################################################


def _curses_main(
        stdscr: curses._CursesWindow,
        dictionaries: list[Dictionary],
        settings: QuerySettings
) -> int:
    global COLS, LINES
    COLS, LINES = shutil.get_terminal_size()

    # Resizing the terminal while curses in de-initialized inserts the resize
    # character into the buffer. This behavior depends on whether we are using
    # readline or not. Let's always start with a fresh buffer.
    curses.flushinp()

    screen_buffer = ScreenBuffer(
        [Screen(stdscr, d, formatter=format_dictionary) for d in dictionaries]
    )
    screen = screen_buffer.current
    char_queue: deque[str] = deque(maxlen=2)
    while True:
        stdscr.erase()
        screen.draw()

        c = get_wch_sigwinch(stdscr)
        if is_resized(c):
            curses.napms(125)
            COLS, LINES = shutil.get_terminal_size()
            screen_buffer.update_after_resize(LINES, COLS)
            stdscr.clearok(True)
            continue

        c = KEY_MAP.get(c, c)  # type: ignore
        if c in ('q', 'Q', 'C-x'):
            break
        elif c == 'C':
            selection_data = screen.get_indices_of_selected_boxes()
            if selection_data:
                create_and_add_card_to_anki(
                    screen.dictionary,
                    screen.status_bar,
                    selection_data,
                    settings
                )
                screen.deselect_all()
            else:
                screen.status_bar.error('Nothing selected')
        elif c == 'S':
            screen.status_bar.success('...')
        elif c == curses.KEY_MOUSE:
            _, x, y, _, bstate = curses.getmouse()
            if bstate & curses.BUTTON1_PRESSED:
                screen.mark_box_at(y, x)
            elif bstate & curses.BUTTON4_PRESSED:
                screen.view_up(2)
            elif bstate & BUTTON5_PRESSED:
                screen.view_down(2)
        elif c in (curses.KEY_DOWN, 'j', 'C-n'):
            screen.view_down(2)
        elif c in (curses.KEY_UP, 'k', 'C-p'):
            screen.view_up(2)
        elif c in (curses.KEY_LEFT, 'h', 'C-b'):
            screen = screen_buffer.previous()
        elif c in (curses.KEY_RIGHT, 'l', 'C-f'):
            screen = screen_buffer.next()
        # 338: PageDown, 339: PageUp
        elif c in (curses.KEY_SNEXT, 338):
            screen.view_down(LINES - 2 * BORDER_PAD - 1)
        elif c in (curses.KEY_SPREVIOUS, 339):
            screen.view_up(LINES - 2 * BORDER_PAD - 1)
        elif c == 'G':
            screen.scroll_pos = screen.get_EOF()
        elif isinstance(c, str):
            n = {
                '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
                '8': 8, '9': 9, '0': 10, '!': 11, '@': 12, '#': 13, '$': 14,
                '%': 15, '^': 16, '&': 17, '*': 18, '(': 19, ')': 20
            }.get(c)
            if n is not None:
                screen.mark_box_by_number(n)
        elif c == 'C-l':
            COLS, LINES = shutil.get_terminal_size()
            screen_buffer.update_after_resize(LINES, COLS)
            stdscr.clearok(True)
        elif c == curses.KEY_F1:
            screen.status_bar.nohelp = not screen.status_bar.nohelp
        elif c == curses.KEY_F8:
            col_state = screen.column_state
            if col_state > 4:
                col_state = 0
            else:
                col_state += 1 
            screen.column_state = col_state
            screen.update_for_redraw()
            screen.status_bar.success(str(col_state) if col_state else 'Auto')

        if c in ('g', 'd'):
            char_queue.append(c)  # type: ignore
            if char_queue.count('g') == 2:
                screen.scroll_pos = 0
            elif char_queue.count('d') == 2:
                screen.deselect_all()
        else:
            char_queue.clear()

    return 0


def curses_ui_entry(dictionaries: list[Dictionary], settings: QuerySettings) -> int:
    try:
        stdscr = curses.initscr()

        curses.curs_set(0)
        curses.cbreak()
        curses.noecho()
        curses.mousemask(-1)
        curses.mouseinterval(0)

        stdscr.keypad(True)
        stdscr.notimeout(True)

        try:
            curses.start_color()
        except:
            pass

        curses.use_default_colors()
        for i in range(16):
            curses.init_pair(i + 1, i, -1)
        curses.init_pair(17, 16, 251)  # -> Black on white
        curses.init_pair(18, curses.COLOR_BLACK, curses.COLOR_GREEN)
        curses.init_pair(19, curses.COLOR_BLACK, curses.COLOR_RED)

        return _curses_main(stdscr, dictionaries, settings)
    finally:
        if 'stdscr' in locals():
            stdscr.clear()    # Repaint the whole window to prevent a flash
            stdscr.refresh()  # of contents from the previous draw.
            stdscr.notimeout(False)
            stdscr.keypad(False)
            curses.echo()
            curses.nocbreak()
            curses.endwin()
