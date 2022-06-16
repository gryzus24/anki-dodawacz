from __future__ import annotations

import collections
import contextlib
import curses
import os
import shutil
from itertools import islice, zip_longest, repeat
from typing import (
    Callable, Iterable, NamedTuple, Optional,
    Reversible, Sequence, Any, TYPE_CHECKING
)

import src.anki_interface as anki
import src.cards as cards
from src.Dictionaries.dictionary_base import filter_dictionary
from src.Dictionaries.utils import wrap_and_pad
from src.colors import Color as _Color
from src.commands import INTERACTIVE_COMMANDS, NO_HELP_ARG_COMMANDS, HELP_ARG_COMMANDS, CommandResult
from src.data import STRING_TO_BOOL, HORIZONTAL_BAR, LINUX, config

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

    # This is ugly, but saves on a LOT of __getattr__ calls, which are quite
    # expensive in this case, because we have to translate console's color API
    # to the curses one.
    def1_c, def2_c, sign_c = Color.def1, Color.def2, Color.sign
    index_c, label_c, exsen_c = Color.index, Color.label, Color.exsen
    inflection_c, phrase_c, phon_c = Color.inflection, Color.phrase, Color.phon
    delimit_c, etym_c, pos_c = Color.delimit, Color.etym, Color.pos
    syn_c, syngloss_c, heed_c = Color.syn, Color.syngloss, Color.heed

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

            first_line, rest = wrap_method(_def, gaps + index_len + label_len, -label_len)
            def_color = def1_c if index % 2 else def2_c
            temp_boxes.extend(_into_boxes(
                (
                   (_def_sign, sign_c),
                   (f'{index} ', index_c),
                   (_label, label_c),
                   (first_line, def_color)
                ), (rest, def_color)
            ))
            if _exsen:
                for ex in _exsen.split('<br>'):
                    first_line, rest = wrap_method(ex, gaps + index_len - 1, 1)
                    temp_boxes.extend(_into_boxes(
                        (
                           ((index_len + gaps - 1) * ' ', exsen_c),
                           (first_line, exsen_c)
                        ), (rest, exsen_c)
                    ))
        elif op == 'LABEL':
            label, inflections = entry[1], entry[2]
            temp_boxes.append(curses.newwin(1, column_width))
            if label:
                if inflections:
                    _push_chain(label, label_c, inflections, inflection_c)
                else:
                    first_line, rest = wrap_method(label, 1, 0)
                    temp_boxes.extend(_into_boxes(
                        (
                           (' ' + first_line, label_c),
                        ), (rest, label_c)
                    ))
        elif op == 'PHRASE':
            phrase, phon = entry[1], entry[2]
            if phon:
                _push_chain(phrase, phrase_c, phon, phon_c)
            else:
                first_line, rest = wrap_method(phrase, 1, 0)
                temp_boxes.extend(_into_boxes(
                    (
                       (' ' + first_line, phrase_c),
                    ), (rest, phrase_c)
                ))
        elif op == 'HEADER':
            title = entry[1]
            box = curses.newwin(1, column_width)
            if title:
                box.insstr(' ]' + column_width * HORIZONTAL_BAR, delimit_c)
                box.insstr(title, delimit_c | curses.A_BOLD)
                box.insstr(HORIZONTAL_BAR + '[ ', delimit_c)
            else:
                box.insstr(column_width * HORIZONTAL_BAR, delimit_c)
            temp_boxes.append(box)
        elif op == 'ETYM':
            etym = entry[1]
            if etym:
                temp_boxes.append(curses.newwin(1, column_width))
                first_line, rest = wrap_method(etym, 1, 0)
                temp_boxes.extend(_into_boxes(
                    (
                       (' ' + first_line, etym_c),
                    ), (rest, etym_c)
                ))
        elif op == 'POS':
            if entry[1].strip(' |'):
                temp_boxes.append(curses.newwin(1, column_width))
                for elem in entry[1:]:
                    pos, phon = elem.split('|')
                    _push_chain(pos, pos_c, phon, phon_c)
        elif op == 'AUDIO':
            pass
        elif op == 'SYN':
            first_line, rest = wrap_method(entry[1], 1, 0)
            temp_boxes.extend(_into_boxes(
                (
                   (' ' + first_line, syn_c),
                ), (rest, syn_c)
            ))
            first_line, rest = wrap_method(entry[2], 2, 0)
            temp_boxes.extend(_into_boxes(
                (
                   (': ', sign_c),
                   (first_line, syngloss_c)
                ), (rest, syngloss_c)
            ))
            for ex in entry[3].split('<br>'):
                first_line, rest = wrap_method(ex, 1, 1)
                temp_boxes.extend(_into_boxes(
                    (
                       (' ' + first_line, exsen_c),
                    ), (rest, exsen_c)
                ))
        elif op == 'NOTE':
            first_line, rest = wrap_method(entry[1], 2, 0)
            temp_boxes.extend(_into_boxes(
                (
                   ('> ', heed_c | curses.A_BOLD),
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
        notify: Notifications,
        definition_indices: list[int],
        settings: QuerySettings
) -> None:
    grouped_by_phrase = dictionary.group_phrases_to_definitions(definition_indices)
    if not grouped_by_phrase:
        notify.error('This dictionary does not support creating cards')
        return

    ok_response = None
    ncards_added = 0
    for card, audio_error, error_info in cards.cards_from_definitions(
            dictionary, grouped_by_phrase, settings
    ):
        if audio_error is not None:
            notify.nlerror(audio_error)
            notify.add_lines(error_info, curses.color_pair(0))

        card = cards.format_and_prepare_card(card)

        if config['-ankiconnect']:
            response = anki.add_card_to_anki(card)
            if response.error:
                notify.nlerror(f'({card["phrase"]}) Could not add card:')
                notify.addstr(response.body)
            else:
                ncards_added += 1
                if ok_response is None:
                    ok_response = response

        if config['-savecards']:
            cards.save_card_to_file(card)
            notify.success(f'Card saved to a file: {os.path.basename(cards.CARD_SAVE_LOCATION)!r}')

    if ok_response is not None:
        notify.nlsuccess(f'Successfully added {ncards_added} card{"s" if ncards_added > 1 else ""}')
        notify.addstr(ok_response.body)


BORDER_PAD = 1

def draw_help(stdscr: curses._CursesWindow) -> None:
    # These should be of uniform width, padded with spaces if needed.
    top_line = [
        ('F1', ' Help '), ('j/k', ' Move down/up '), ('1-9', ' Select cell '),
        ('B ', ' Card browser '), ('/ ', ' Filter/Search '), ('g ', ' Go top '),
        ('^l', ' Redraw screen     '),
    ]
    bot_line = [
        ('q ', ' Exit '), ('h/l', ' Swap screens '), ('d ', ' Deselect all '),
        ('C ', ' Create cards '), ('^J', ' Reset filters '), ('G ', ' Go EOF '),
        ('F8', ' Rearrange columns '),
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

    bot_y, top_y = LINES-2, LINES-3
    space_remaining = space_left % len(top_bot_pairs)
    try:
        # Insert remaining space to eliminate the need to clear
        # the stdscr everytime this function is called.
        stdscr.insstr(top_y, BORDER_PAD, space_remaining * ' ')
        stdscr.insstr(bot_y, BORDER_PAD, space_remaining * ' ')
    except curses.error:  # window too small, because of LINES
        return

    a_standout = curses.A_STANDOUT
    for (top_cmd, top_msg), (bot_cmd, bot_msg) in reversed(top_bot_pairs):
        stdscr.insstr(top_y, BORDER_PAD, f'{top_msg}{gap}')
        stdscr.insstr(top_y, BORDER_PAD, top_cmd, a_standout)
        stdscr.insstr(bot_y, BORDER_PAD, f'{bot_msg}{gap}')
        stdscr.insstr(bot_y, BORDER_PAD, bot_cmd, a_standout)


class Notifications:
    def __init__(self, *, persistence: int) -> None:
        self.persistence = persistence if persistence > 0 else 1
        self.ticks = 1
        # (message, color_pair_number)
        self.buffer: list[tuple[str, int]] = []

    def add_lines(self, lines: Iterable[str], color_pair: int) -> None:
        self.ticks = 1
        self.buffer.extend(zip(lines, repeat(color_pair)))

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

    def nlsuccess(self, s: str) -> None:
        self.add_lines([s], curses.color_pair(BLACK_ON_GREEN))

    def success(self, s: str) -> None:
        self.append_line(s, curses.color_pair(BLACK_ON_GREEN))

    def nlerror(self, s: str) -> None:
        self.add_lines([s], curses.color_pair(BLACK_ON_RED))

    def error(self, s: str) -> None:
        self.append_line(s, curses.color_pair(BLACK_ON_RED))

    def addstr(self, s: str) -> None:
        self.add_lines(s.splitlines(), curses.color_pair(0))

    def clear_on_next_draw(self) -> None:
        self.ticks = self.persistence

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
                line = line[:COLS-2] + '..'
            else:
                line += padding * ' '
            win.insstr(i, 0, line, color)

        win.noutrefresh()
        if self.ticks >= self.persistence:
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
        self._original_dictionary = self.dictionary = dictionary

        # Display
        conf_ncols, state = config['-columns']
        self.column_state = 0 if 'auto' in state else conf_ncols
        self.bottom_margin = 0 if config['-nohelp'] else 2

        _boxes, self.lines_total, self.column_params = \
            self._box_dictionary_entries_and_get_column_params(config['-margin'])
        self.boxes = _boxes
        self.columns = self._split_into_columns(_boxes)

        # User facing state.
        self.ptoggled: collections.Counter[int] = collections.Counter()
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

    def _get_scroll_EOF(self) -> int:
        r = max(map(len, self.columns)) - self.screen_height
        return r if r > 0 else 0

    def draw(self) -> None:
        # scroll_pos can be bigger than eof if self.bottom_margin
        # has decreased or window has been resized.
        eof = self._get_scroll_EOF()
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
            self.ptoggled[phraseno] -= 1
        else:
            self._toggle_box(box_index, curses.A_STANDOUT)
            self.ptoggled[phraseno] += 1

        currently_toggled = self.ptoggled[phraseno]
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

    KEYBOARD_SELECTOR_CHARS = (
        b'1', b'2', b'3', b'4', b'5', b'6', b'7', b'8', b'9', b'0',
        b'!', b'@', b'#', b'$', b'%', b'^', b'&', b'*', b'(', b')',
    )
    def mark_box_by_selector(self, s: bytes) -> None:
        box_i = self.KEYBOARD_SELECTOR_CHARS.index(s) + 1
        cur = phraseno = 0
        for i, (state, lines) in enumerate(zip(self.box_states, self.boxes)):
            op = self.dictionary.contents[i][0]
            if op == 'PHRASE':
                phraseno += 1
            if op not in DIRECTLY_TOGGLEABLE:
                continue
            if cur == len(self.KEYBOARD_SELECTOR_CHARS):
                return
            cur += 1
            if box_i == cur:
                self._toggle_related_boxes(state, phraseno, i)
                return

    def get_indices_of_selected_boxes(self) -> list[int]:
        return [i for i, x in enumerate(self.box_states) if x == curses.A_STANDOUT]

    def use_original_dictionary(self) -> None:
        self.dictionary = self._original_dictionary
        self.update_for_redraw()

    def deselect_all(self) -> None:
        self.ptoggled.clear()
        a_normal = curses.A_NORMAL
        for i, state in enumerate(self.box_states):
            if state != a_normal:
                self._toggle_box(i, a_normal)

    def move_down(self, n: int = 2) -> None:
        self.scroll_pos += n
        eof = self._get_scroll_EOF()
        if self.scroll_pos > eof:
            self.scroll_pos = eof

    def move_up(self, n: int = 2) -> None:
        self.scroll_pos -= n
        if self.scroll_pos < 0:
            self.scroll_pos = 0

    def go_bottom(self) -> None:
        self.scroll_pos = self._get_scroll_EOF()

    def go_top(self) -> None:
        self.scroll_pos = 0

    def page_down(self) -> None:
        self.move_down(self.screen_height - 1)

    def page_up(self) -> None:
        self.move_up(self.screen_height - 1)

    COMMANDS: dict[bytes, Callable[..., None]] = {
        b'^J': use_original_dictionary,
        b'd': deselect_all,
        b'j': move_down, b'^N': move_down, b'KEY_DOWN': move_down,
        b'k': move_up,   b'^P': move_up,   b'KEY_UP': move_up,
        b'G': go_bottom, b'KEY_END': go_bottom,
        b'g': go_top,    b'KEY_HOME': go_top,
        b'KEY_NPAGE': page_down, b'KEY_SNEXT': page_down,
        b'KEY_PPAGE': page_up,   b'KEY_SPREVIOUS': page_up,
    }


class call_on(contextlib.ContextDecorator):
    def __init__(self, *, enter: Callable[..., None], exit: Callable[..., None]) -> None:
        self._enter = enter
        self._exit = exit

    __enter__ = lambda self: self._enter()
    __exit__ = lambda self, *_: self._exit()


def prompt_run_enter() -> None:
    curses.raw()
    try:
        curses.curs_set(1)
    except curses.error:
        pass


def prompt_run_exit() -> None:
    curses.cbreak()
    try:
        curses.curs_set(0)
    except curses.error:
        pass


class CursesInputField:
    def __init__(self, sb: ScreenBuffer) -> None:
        self.prompt_inst = Prompt(sb)

    def write(self, s: str) -> None:
        self.prompt_inst.line_buffer.append(s)

    def choose_item(self, prompt_name: str, seq: Sequence[Any], default: int = 1) -> Any | None:
        self.prompt_inst.prompt = f'{prompt_name} [{default}]: '
        self.prompt_inst.exit_if_empty = False
        typed = self.prompt_inst.run()
        if typed is None:
            return None
        typed = typed.strip()
        try:
            choice = int(typed) if typed else default
        except ValueError:
            return None
        if 0 < choice <= len(seq):
            return seq[choice - 1]
        return None

    def ask_yes_no(self, prompt_name: str, *, default: bool) -> bool:
        d = 'Y/n' if default else 'y/N'
        self.prompt_inst.prompt = f'{prompt_name} [{d}]: '
        self.prompt_inst.exit_if_empty = False
        typed = self.prompt_inst.run()
        if typed is None:
            return default
        return STRING_TO_BOOL.get(typed.strip().lower(), default)


class Prompt:
    def __init__(self,
            screen_buffer: ScreenBuffer,
            prompt: str = '', *,
            pretype: str = '',
            lines: Optional[list[str]] = None,
            exit_if_empty: bool = True,
    ) -> None:
        self.win = screen_buffer.stdscr
        self.screen_buffer = screen_buffer
        self.prompt: str = prompt
        self.line_buffer: list[str] = lines or []
        self.exit_if_empty: bool = exit_if_empty
        self._entered = [*pretype]
        self._cursor = len(pretype)

    def _draw_line_buffer(self) -> None:
        y, x = LINES-2, 0
        if y <= len(self.line_buffer):
            return
        for line in reversed(self.line_buffer):
            self.win.move(y, x)
            self.win.clrtoeol()
            self.win.insstr(y, x, line)
            y -= 1

    def _draw_prompt(self) -> None:
        width = COLS - 1
        offset = width // 3

        headroom = width - len(self.prompt) - 6
        if headroom < 0:
            prompt_text = f'..{self.prompt[2-headroom:]}'
        else:
            prompt_text = self.prompt

        self.win.move(LINES-1, 0)
        self.win.clrtoeol()

        bogus_cursor = self._cursor + len(prompt_text)
        if bogus_cursor < width:
            self.win.insstr(LINES-1, 0, prompt_text)
            if len(self._entered) > width - len(prompt_text):
                text = f'{"".join(self._entered[:width - len(prompt_text)])}>'
            else:
                text = ''.join(self._entered)
            text_x = len(prompt_text)
        else:
            bogus_cursor -= len(prompt_text)
            while bogus_cursor >= width:
                bogus_cursor = bogus_cursor - width + offset

            start = self._cursor - bogus_cursor
            if start + width > len(self._entered):
                text = f'<{"".join(self._entered[start + 1:start + width])}'
            else:
                text = f'<{"".join(self._entered[start + 1:start + width])}>'
            text_x = 0

        self.win.insstr(LINES-1, text_x, text)
        self.win.move(LINES-1, bogus_cursor)

    def _delete_line(self) -> None:
        self._entered.clear()
        self._cursor = 0

    def draw(self) -> None:
        self.win.erase()
        self.screen_buffer.draw()

        self._draw_line_buffer()
        self._draw_prompt()

    def resize(self) -> None:
        self.screen_buffer.resize()

    def type(self, c: int) -> None:
        self._entered.insert(self._cursor, chr(c))
        self._cursor += 1

    def backspace(self) -> None:
        if self._cursor > 0:
            self._cursor -= 1
            del self._entered[self._cursor]

    def left(self) -> None:
        if self._cursor > 0:
            self._cursor -= 1

    def right(self) -> None:
        if self._cursor < len(self._entered):
            self._cursor += 1

    def delete(self) -> None:
        try:
            del self._entered[self._cursor]
        except IndexError:
            pass

    def home(self) -> None:
        self._cursor = 0

    def end(self) -> None:
        self._cursor = len(self._entered)

    def jump_left(self) -> None:
        skip = True
        entered = self._entered
        for i in range(self._cursor - 1, -1, -1):
            if entered[i].isspace():
                if skip:
                    continue
                self._cursor = i + 1
                break
            else:
                skip = False
        else:
            self._cursor = 0

    def jump_right(self) -> None:
        skip = True
        entered = self._entered
        for i in range(self._cursor + 1, len(entered)):
            if entered[i].isspace():
                if skip:
                    continue
                self._cursor = i
                break
            else:
                skip = False
        else:
            self._cursor = len(entered)

    def control_k(self) -> None:
        self._entered = self._entered[:self._cursor]

    COMMANDS = {
        410: resize,              12: resize,       # ^L
        curses.KEY_BACKSPACE: backspace,
        curses.KEY_LEFT: left,    2: left,          # KEY_LEFT, ^B
        curses.KEY_RIGHT: right,  6: right,         # KEY_RIGHT, ^F
        curses.KEY_DC: delete,    4: delete,        # Del, ^D
        curses.KEY_HOME: home,    1: home,          # HOME, ^A
        curses.KEY_END: end,      5: end,           # END, ^E
        546: jump_left,           544: jump_left,   # ^LEFT, Alt-LEFT
        561: jump_right,          559: jump_right,  # ^RIGHT, Alt-RIGHT
        11: control_k,
    }

    @call_on(enter=prompt_run_enter, exit=prompt_run_exit)
    def run(self) -> str | None:
        prompt_commands = Prompt.COMMANDS
        while True:
            self.draw()

            c = get_key(self.win)
            if 32 <= c <= 126:  # printable ascii
                self.type(c)
            elif c in prompt_commands:
                prompt_commands[c](self)
            elif c in (7, 10):  # ^J, \n
                ret = ''.join(self._entered)
                self._delete_line()
                return ret

            if (c in (3, 27) or  # ^C, ESC
               (self.exit_if_empty and not self._entered)
            ):
                return None


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

    def cycle_column_state(self) -> str:
        col_state = self.current.column_state
        if col_state > 4:
            col_state = 0
        else:
            col_state += 1

        for screen in self.screens:
            screen.column_state = col_state
            screen.update_for_redraw()

        if col_state > 0:
            return str(col_state)
        else:
            return 'Auto'

    def draw_border(self, screen: Screen) -> None:
        stdscr = self.stdscr
        ncols, col_width, _ = screen.column_params

        stdscr.box()

        header_title = screen.dictionary.contents[0][1]
        # 2 for padding, 2 for brackets, 4 for box drawing characters
        space = COLS - len(header_title) - 8
        if space < 0:
            truncated = header_title[:space-2]
            if truncated.strip():
                try:
                    stdscr.addstr(0, 2, '[ ')
                    stdscr.addstr(0, 4, f'{truncated}..', curses.A_BOLD)
                    stdscr.addstr(0, 6 + len(truncated), ' ]')
                except curses.error:  # window too small
                    pass
        else:
            # curses.error should not happen here, I assert that.
            stdscr.addstr(0, 2, '[ ')
            stdscr.addstr(0, 4, header_title, curses.A_BOLD)
            stdscr.addstr(0, 4 + len(header_title), ' ]')

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

    def draw(self) -> None:
        screen = self.current
        if self.nohelp:
            screen.bottom_margin = 0
        else:
            screen.bottom_margin = 2
            draw_help(self.stdscr)

        self.draw_border(screen)
        self.stdscr.noutrefresh()
        screen.draw()

    def resize(self) -> None:
        global LINES, COLS
        COLS, LINES = shutil.get_terminal_size()

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

    def search_prompt(self, screen: Screen) -> None:
        typed = Prompt(self, 'Search ', pretype='/').run()
        if typed is None:
            return
        if typed.startswith('/'):
            typed = typed[1:]

        screen.dictionary = filter_dictionary(screen._original_dictionary, (typed,))
        screen.update_for_redraw()

    def command_prompt(self, screen: Screen) -> CommandResult | None:
        typed = Prompt(self, '$ ', pretype='-').run()
        if typed is None:
            return None

        args = typed.split()
        cmd = args[0]
        if cmd in NO_HELP_ARG_COMMANDS:
            result = NO_HELP_ARG_COMMANDS[cmd](*args)
        elif cmd in HELP_ARG_COMMANDS:
            func, note, usage = HELP_ARG_COMMANDS[cmd]
            result = func(*args)
        elif cmd in INTERACTIVE_COMMANDS:
            result = INTERACTIVE_COMMANDS[cmd](CursesInputField(self), *args)
        elif typed.strip('-'):
            return CommandResult(error='Not a command')
        else:
            return None

        screen.update_for_redraw()

        return result


# Unfortunately Python's readline api does not expose functions and variables
# responsible for signal handling, which makes it impossible to reconcile
# curses' signal handling with the readline's one, so we have to manage
# COLS and LINES variables ourselves. Also, when curses is de-initialized,
# readline's sigwinch handler does not raise "no input", but ungets the
# correct b'KEY_RESIZE' code as soon as curses comes back. This is worked
# around by flushing any typeahead in the main function.

if LINUX:
    def get_key(win: curses._CursesWindow) -> int:
        c = win.getch()
        return 410 if c == -1 else c
else:
    def get_key(win: curses._CursesWindow) -> int:
        return win.getch()


COLS = LINES = 0
###############################################################################


def _curses_main(
        stdscr: curses._CursesWindow,
        dictionaries: list[Dictionary],
        settings: QuerySettings
) -> None:
    global COLS, LINES
    COLS, LINES = shutil.get_terminal_size()

    # Resizing the terminal while curses in de-initialized inserts the resize
    # character into the buffer. Let's always start with a fresh buffer.
    curses.flushinp()

    screen_buffer = ScreenBuffer(stdscr, tuple(map(Screen, dictionaries)))
    screen = screen_buffer.current
    notify = Notifications(persistence=3)

    screen_commands = Screen.COMMANDS
    while True:
        stdscr.erase()
        screen_buffer.draw()
        notify.draw_if_available()
        curses.doupdate()

        c = curses.keyname(get_key(stdscr))
        if c in (b'q', b'Q', b'^X'):
            break
        elif c in screen_commands:
            screen_commands[c](screen)
        elif c == b'KEY_MOUSE':
            _, x, y, _, bstate = curses.getmouse()
            if bstate & curses.BUTTON1_PRESSED:
                screen.mark_box_at(y, x)
            elif bstate & curses.BUTTON4_PRESSED:
                screen.move_up()
            elif bstate & BUTTON5_PRESSED:
                screen.move_down()
        elif c in screen.KEYBOARD_SELECTOR_CHARS:
            screen.mark_box_by_selector(c)
        elif c == b'KEY_RESIZE':
            curses.napms(100)
            screen_buffer.resize()
        elif c == b'^L':
            screen_buffer.resize()
        elif c in (b'h', b'KEY_LEFT'):
            screen = screen_buffer.previous()
        elif c in (b'l', b'KEY_RIGHT'):
            screen = screen_buffer.next()
        elif c == b'-':
            result = screen_buffer.command_prompt(screen)
            if result is not None:
                if result.error:
                    notify.nlerror(result.error)
                if result.reason:
                    notify.addstr(result.reason)
                notify.clear_on_next_draw()
        elif c == b'/':
            screen_buffer.search_prompt(screen)
        elif c == b'KEY_F(1)':
            screen_buffer.nohelp = not screen_buffer.nohelp
        elif c == b'KEY_F(8)':
            current = screen_buffer.cycle_column_state()
            notify.success(current)
        elif c == b'B':
            response = anki.gui_browse_cards()
            if response.error:
                notify.nlerror('Could not open the card browser:')
                notify.addstr(response.body)
            else:
                notify.success('Anki card browser opened')
        elif c == b'C':
            selection_data = screen.get_indices_of_selected_boxes()
            if selection_data:
                create_and_add_card_to_anki(
                    screen.dictionary, notify, selection_data, settings
                )
                screen.deselect_all()
            else:
                notify.error('Nothing selected')


def curses_ui_entry(dictionaries: list[Dictionary], settings: QuerySettings) -> None:
    try:
        stdscr = curses.initscr()

        try:
            # make the cursor invisible
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
        except curses.error:  # some internal table cannot be allocated?
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
