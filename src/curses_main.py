from __future__ import annotations

import curses
import os
from collections import Counter, deque
from itertools import islice, zip_longest
from shutil import get_terminal_size
from typing import Iterable, NamedTuple, Optional, Reversible, Sequence, TYPE_CHECKING

import src.anki_interface as anki
import src.cards as cards
from src.Dictionaries.utils import wrap_and_pad
from src.colors import Color as _Color
from src.data import HORIZONTAL_BAR, LINUX, config

if TYPE_CHECKING:
    from ankidodawacz import QuerySettings
    from src.Dictionaries.dictionary_base import Dictionary

# Pythons < 3.10 do not define BUTTON5_PRESSED.
# Also, mouse wheel requires ncurses >= 6.
BUTTON5_PRESSED = 2097152

# Custom color pairs.
BLACK_ON_GREEN = 31
BLACK_ON_RED = 32

ANSI_COLORS = (
    '\033[39m',
    '\033[30m', '\033[31m', '\033[32m', '\033[33m',
    '\033[34m', '\033[35m', '\033[36m', '\033[37m',
    '\033[90m', '\033[91m', '\033[92m', '\033[93m',
    '\033[94m', '\033[95m', '\033[96m', '\033[97m',
)


class _CursesColor:
    _lookup = None

    # It's better to wait for "curses.COLORS" variable to become available,
    # instead of fiddling with terminfo or some environment variables to
    # properly initialize color_pair lookup. The instance of this class requires
    # calling "setup_colors" after curses.start_color. As far as I know, this
    # is the only way to provide a common API with that of console UI without
    # using metaclasses.

    def __getattr__(self, item: str) -> int:
        return self._lookup[getattr(_Color, item)]  # type: ignore[index]

    def setup_colors(self, ncolors: int) -> None:
        if self._lookup is not None:
            return
        # Curses does not throw an error when accessing uninitialized color pairs.
        # Wrap colors only when things may break.
        if ncolors == 8 or ncolors == 16777216:
            self._lookup = {k: curses.color_pair(i % 8) for i, k in enumerate(ANSI_COLORS)}
        else:
            self._lookup = {k: curses.color_pair(i) for i, k in enumerate(ANSI_COLORS)}


Color = _CursesColor()


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
                   ('> ', Color.heed | curses.A_BOLD),
                   (first_line, 0 | curses.A_BOLD)
                ), (rest, 0 | curses.A_BOLD)
            ))
        else:
            raise AssertionError(f'unreachable dictionary op: {op!r}')

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
                status_bar.error(f'({card["phrase"]}) Could not add card:', newline=True)
                status_bar.add_str(response.body)
            else:
                ncards_added += 1
                if ok_response is None:
                    ok_response = response

        if config['-savecards']:
            cards.save_card_to_file(card)
            status_bar.success(f'Card saved to a file: {os.path.basename(cards.CARD_SAVE_LOCATION)!r}')

    if ok_response is not None:
        status_bar.success(f'Successfully added {ncards_added} card{"s" if ncards_added > 1 else ""}', newline=True)
        status_bar.add_str(ok_response.body)


BORDER_PAD = 1

def draw_help(stdscr: curses._CursesWindow) -> None:
    top_line = [
        ('F1', ' Help '), ('j/k', ' Move down/up '), ('1-9', ' Select cell '),
        ('B ', ' Card browser '), ('gg', ' Go top '), ('^l', ' Redraw screen '),
    ]
    bot_line = [
        ('q ', ' Exit '), ('h/l', ' Swap screens '), ('dd', ' Deselect all '),
        ('C ', ' Create cards '), ('G ', ' Go EOF '), ('F8', ' Rearrange columns '),
    ]

    top_bot_pairs = []
    space_occupied = 0
    space_to_occupy = COLS - 2*BORDER_PAD
    for top_pair, bot_pair in zip_longest(top_line, bot_line, fillvalue=('', '')):
        pair_width = max(map(len, (''.join(top_pair), ''.join(bot_pair))))
        space_occupied += pair_width
        if space_occupied > space_to_occupy:
            space_occupied -= pair_width
            break
        else:
            top_bot_pairs.append((top_pair, bot_pair))

    space_left = space_to_occupy - space_occupied
    try:
        gap = (space_left // len(top_bot_pairs)) * ' '
    except ZeroDivisionError:  # window too small, because of COLS
        return

    bot_y = LINES - 2
    top_y = bot_y - 1
    a_standout = curses.A_STANDOUT
    try:
        for (top_cmd, top_msg), (bot_cmd, bot_msg) in reversed(top_bot_pairs):
            stdscr.insstr(top_y, BORDER_PAD, f'{top_msg}{gap}')
            stdscr.insstr(top_y, BORDER_PAD, top_cmd, a_standout)
            stdscr.insstr(bot_y, BORDER_PAD, f'{bot_msg}{gap}')
            stdscr.insstr(bot_y, BORDER_PAD, bot_cmd, a_standout)
    except curses.error:  # window too small, because of LINES
        pass


class StatusBar:
    def __init__(self, *, persistence: int) -> None:
        self.persistence = persistence if persistence > 0 else 1
        self.ticks = 1
        # (message, color_pair_number)
        self.buffer: list[tuple[str, int]] = []

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

        new_line = f'{last_line}  {line}'
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
            self.add_lines([line], curses.color_pair(BLACK_ON_GREEN))
        else:
            self.append_line(line, curses.color_pair(BLACK_ON_GREEN))

    def error(self, line: str, *, newline: bool = False) -> None:
        if newline:
            self.add_lines([line], curses.color_pair(BLACK_ON_RED))
        else:
            self.append_line(line, curses.color_pair(BLACK_ON_RED))

    def add_str(self, string: str) -> None:
        self.add_lines(string.splitlines(), curses.color_pair(0))

    def draw_if_available(self) -> None:
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


def corollary_boxes_to_toggle() -> set[str]:
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
MINIMUM_TEXT_WIDTH = 24

class Screen:
    def __init__(self, dictionary: Dictionary) -> None:
        self.dictionary = dictionary

        # Display
        conf_ncols, state = config['-columns']
        self.column_state = 0 if 'auto' in state else conf_ncols
        self.bottom_margin = 0 if config['-nohelp'] else 2

        _boxes, self.lines_total, self.column_params = \
            self._box_dictionary_entries_and_get_column_params(config['-margin'])
        self.boxes = _boxes
        self.columns = self._split_into_columns(_boxes)

        # User facing state.
        self.phraseno_to_ntoggles: Counter[int] = Counter()
        self.box_states = [curses.A_NORMAL] * len(_boxes)
        self.scroll_pos = 0

    @property
    def screen_height(self) -> int:
        r = LINES - self.bottom_margin - 2*BORDER_PAD
        return r if r > 0 else 0

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
            if col_text_width < MINIMUM_TEXT_WIDTH:
                margin -= (MINIMUM_TEXT_WIDTH - col_text_width) // 2
                if margin < 0:
                    margin = 0
                col_text_width = col_width - 2*margin
                if col_text_width < 1:
                    col_text_width = 1

            _boxes, _lines = format_dictionary(self.dictionary, col_text_width)
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

        a_normal = curses.A_NORMAL
        for lines, state in zip(_boxes, self.box_states):
            if state != a_normal:
                for line in lines:
                    line.bkgd(0, state)

    def draw(self) -> None:
        # scroll_pos can be bigger than eof if self.bottom_margin
        # has decreased or window has been resized.
        eof = self.get_scroll_EOF()
        if self.scroll_pos > eof:
            self.scroll_pos = eof

        columns = self.columns
        # stopgap +1 to ignore the header entry
        from_index = self.scroll_pos + 1
        try:
            # hide out of view windows behind the header to prevent
            # them from stealing clicks in the upper region.
            for column in columns:
                for box in islice(column, None, from_index):
                    box.mvwin(0, 1)

            _, col_width, margin = self.column_params
            to_index = from_index + self.screen_height
            tx = BORDER_PAD
            for column in columns:
                for y, box in enumerate(islice(column, from_index, to_index), 1):
                    box.mvwin(y, tx + margin)
                    box.noutrefresh()
                tx += col_width + 1
        except curses.error:  # window too small
            pass

    def _toggle_box(self, i: int, state: int) -> None:
        self.box_states[i] = state
        for line in self.boxes[i]:
            line.bkgd(0, state)

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

        try:
            static_entries_to_index = self.dictionary.static_entries_to_index_from_index(box_index)
        except ValueError:
            return

        for op in corollary_boxes_to_toggle():
            if op in static_entries_to_index:
                self._toggle_box(static_entries_to_index[op], new_corollary_state)

    def mark_box_at(self, y: int, x: int) -> None:
        if y < BORDER_PAD or y > self.screen_height:  # border clicked.
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
        a_normal = curses.A_NORMAL
        for i, state in enumerate(self.box_states):
            if state != a_normal:
                self._toggle_box(i, a_normal)

    def get_indices_of_selected_boxes(self) -> list[int]:
        return [i for i, x in enumerate(self.box_states) if x == curses.A_STANDOUT]

    def get_scroll_EOF(self) -> int:
        r = max(map(len, self.columns)) - self.screen_height
        return r if r > 0 else 0

    def view_down(self, n: int = 1) -> None:
        self.scroll_pos += n
        eof = self.get_scroll_EOF()
        if self.scroll_pos > eof:
            self.scroll_pos = eof

    def view_up(self, n: int = 1) -> None:
        self.scroll_pos -= n
        if self.scroll_pos < 0:
            self.scroll_pos = 0


class ScreenBuffer:
    def __init__(self, stdscr: curses._CursesWindow, screens: Sequence[Screen]) -> None:
        self.stdscr = stdscr
        self.screens = screens
        self.cursor = 0
        self.nohelp = config['-nohelp']

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

    def draw_border(self, screen: Screen) -> None:
        stdscr = self.stdscr
        ncols, col_width, _ = screen.column_params

        stdscr.box()

        header_title = screen.dictionary.contents[0][1]
        # 6: 2 for padding, 2 for brackets, 2 for spaces around the title
        space = COLS - len(header_title) - 6
        if space < 3:
            truncated = header_title[:space-5]
            if truncated.strip():
                try:
                    stdscr.addstr(0, 2, f'[ {truncated}... ]', curses.A_BOLD)
                except curses.error:  # window too small
                    pass
        else:
            # curses.error should not happen here, I assert that.
            stdscr.addstr(0, 2, f'[ {header_title} ]', curses.A_BOLD)

        nscreens = len(self.screens)
        if nscreens > 1:
            buffer_hint = f'{self.cursor+1}/{nscreens}'
            bhint_y = LINES - 1
            bhint_x = COLS - len(buffer_hint) - 2
            if bhint_x > 1:
                try:
                    stdscr.addch(bhint_y, bhint_x - 1, '╴')
                    stdscr.addstr(bhint_y, bhint_x, buffer_hint, curses.A_BOLD)
                    stdscr.addch(bhint_y, bhint_x + len(buffer_hint), '╶')
                except curses.error:  # window too small
                    pass

        shift = BORDER_PAD + col_width
        screen_height = screen.screen_height
        try:
            for i in range(1, ncols):
                stdscr.vline(BORDER_PAD, i * shift, 0, screen_height)
        except curses.error:
            pass

        stdscr.bkgd(0, Color.delimit)

    def draw(self, screen: Screen) -> None:
        if self.nohelp:
            screen.bottom_margin = 0
        else:
            screen.bottom_margin = 2
            draw_help(self.stdscr)

        self.draw_border(screen)
        self.stdscr.noutrefresh()
        screen.draw()

    def update_after_resize(self) -> None:
        global LINES, COLS
        COLS, LINES = get_terminal_size()

        # prevents malloc() errors from ncurses on 32-bit binaries.
        if COLS < 2:
            return

        # This is noticeably slow when there are more than 10 screens.
        # Updating lazily doesn't help, because `curses.resize_term` is what
        # takes the majority of the time.
        curses.resize_term(LINES, COLS)
        for screen in self.screens:
            screen.update_for_redraw()
        # prevents stalling when updating takes a noticeable amount of time.
        curses.flushinp()

        self.stdscr.clearok(True)


# Unfortunately Python's readline api does not expose functions and variables
# responsible for signal handling, which makes it impossible to reconcile
# curses' signal handling with the readline's one, so we have to manage
# COLS and LINES variables ourselves. It also affects the `curses.keyname`
# function. But there's more! When curses is de-initialized, readline's
# sigwinch handler does not raise "no input", but ungets the correct "410"
# code as soon as curses comes back to the battlefield! This is worked around
# by flushing any typeahead in the main function.
# Let's enjoy the hacky code that follows.

if LINUX:  # if using readline.
    def is_resized(c: int | str | None) -> bool:
        return c is None
else:
    def is_resized(c: int | str | None) -> bool:
        return c == curses.KEY_RESIZE and curses.is_term_resized(LINES, COLS)


def get_wch_sigwinch(stdscr: curses._CursesWindow) -> int | str | None:
    try:
        return stdscr.get_wch()
    except curses.error:  # readline is interfering
        return None


COLS = LINES = 0
###############################################################################


KEYBOARD_SELECTOR_CHARS = (
    '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
    '!', '@', '#', '$', '%', '^', '&', '*', '(', ')',
)

DOUBLE_TAP_CHARS = {'d', 'g'}

KEY_MAP = {
    #'\x02': 'C-b',
    #'\x06': 'C-f',
    '\x0c': 'C-l',
    '\x0e': 'C-n',
    # '\x0f': 'C-o',
    '\x10': 'C-p',
    #'\x14': 'C-t',
    '\x18': 'C-x',
}


def _curses_main(
        stdscr: curses._CursesWindow,
        dictionaries: list[Dictionary],
        settings: QuerySettings
) -> int:
    global COLS, LINES
    COLS, LINES = get_terminal_size()

    # Resizing the terminal while curses in de-initialized inserts the resize
    # character into the buffer. This behavior depends on whether we are using
    # readline or not. Let's always start with a fresh buffer.
    curses.flushinp()

    screen_buffer = ScreenBuffer(stdscr, tuple(map(Screen, dictionaries)))
    screen = screen_buffer.current
    status_bar = StatusBar(persistence=3)

    char_queue: deque[str] = deque(maxlen=2)
    while True:
        stdscr.erase()
        screen_buffer.draw(screen)
        status_bar.draw_if_available()
        curses.doupdate()

        c = get_wch_sigwinch(stdscr)
        if is_resized(c):
            curses.napms(125)
            screen_buffer.update_after_resize()
            continue

        c = KEY_MAP.get(c, c)  # type: ignore[arg-type]
        if c in DOUBLE_TAP_CHARS:
            char_queue.append(c)  # type: ignore[arg-type]
        else:
            char_queue.clear()

        ## Events
        if c in ('q', 'Q', 'C-x'):
            break
        elif c == curses.KEY_F1:
            screen_buffer.nohelp = not screen_buffer.nohelp

        elif c in (curses.KEY_LEFT, 'h'):
            screen = screen_buffer.previous()
        elif c in (curses.KEY_RIGHT, 'l'):
            screen = screen_buffer.next()
        elif c in (curses.KEY_DOWN, 'j', 'C-n'):
            screen.view_down(2)
        elif c in (curses.KEY_UP, 'k', 'C-p'):
            screen.view_up(2)

        elif char_queue.count('d') == 2:
            screen.deselect_all()
        elif c in KEYBOARD_SELECTOR_CHARS:
            screen.mark_box_by_number(KEYBOARD_SELECTOR_CHARS.index(c) + 1)

        elif c == 'C':
            selection_data = screen.get_indices_of_selected_boxes()
            if selection_data:
                create_and_add_card_to_anki(
                    screen.dictionary,
                    status_bar,
                    selection_data,
                    settings
                )
                screen.deselect_all()
            else:
                status_bar.error('Nothing selected')
        elif c == 'B':
            response = anki.gui_browse_cards()
            if response.error:
                status_bar.error('Could not open a card browser:', newline=True)
                status_bar.add_str(response.body)
            else:
                status_bar.success('Anki card browser opened.')

        elif c in ('G', curses.KEY_END):
            screen.scroll_pos = screen.get_scroll_EOF()
        elif char_queue.count('g') == 2 or c == curses.KEY_HOME:
            screen.scroll_pos = 0

        elif c == curses.KEY_F8:
            col_state = screen.column_state
            if col_state > 4:
                col_state = 0
            else:
                col_state += 1
            screen.column_state = col_state
            screen.update_for_redraw()
            status_bar.success(str(col_state) if col_state else 'Auto')
        elif c == 'C-l':
            screen_buffer.update_after_resize()

        elif c == curses.KEY_MOUSE:
            _, x, y, _, bstate = curses.getmouse()
            if bstate & curses.BUTTON1_PRESSED:
                screen.mark_box_at(y, x)
            elif bstate & curses.BUTTON4_PRESSED:
                screen.view_up(2)
            elif bstate & BUTTON5_PRESSED:
                screen.view_down(2)
        elif c in (curses.KEY_SNEXT, curses.KEY_NPAGE):
            screen.view_down(screen.screen_height - 1)
        elif c in (curses.KEY_SPREVIOUS, curses.KEY_PPAGE):
            screen.view_up(screen.screen_height - 1)

    return 0


def curses_ui_entry(dictionaries: list[Dictionary], settings: QuerySettings) -> int:
    try:
        stdscr = curses.initscr()

        try:
            # make the cursor invisible.
            curses.curs_set(0)
        except curses.error:  # not supported
            pass

        curses.cbreak()
        curses.noecho()
        curses.mousemask(-1)
        curses.mouseinterval(0)

        stdscr.keypad(True)
        stdscr.notimeout(True)

        try:
            curses.start_color()
        except:  # some internal table cannot be allocated?
            pass
        try:
            curses.use_default_colors()
        except curses.error:  # not supported
            pass

        ncolors = curses.COLORS
        Color.setup_colors(ncolors)
        if ncolors < 8:
            return _curses_main(stdscr, dictionaries, settings)

        if ncolors == 8:
            pairs_to_initialize = 8
        else:
            pairs_to_initialize = 16

        for i in range(pairs_to_initialize):
            curses.init_pair(i + 1, i, -1)

        curses.init_pair(31, curses.COLOR_BLACK, curses.COLOR_GREEN)
        curses.init_pair(32, curses.COLOR_BLACK, curses.COLOR_RED)

        return _curses_main(stdscr, dictionaries, settings)
    finally:
        if 'stdscr' in locals():
            # Repaint the whole window to prevent a flash
            # of contents from the previous draw.
            stdscr.clear()
            stdscr.refresh()
            curses.endwin()
