from __future__ import annotations

import contextlib
import curses
from collections import Counter
from itertools import islice, zip_longest
from typing import Callable, TypeVar, Reversible, Sequence, Iterator, TYPE_CHECKING

import src.Curses.env as env
import src.anki_interface as anki
from src.Curses.colors import Color, init_colors, BLACK_ON_RED, BLACK_ON_GREEN, BLACK_ON_YELLOW
from src.Curses.pager import Pager
from src.Curses.prompt import Prompt
from src.Curses.utils import (
    clipboard_or_selection,
    get_key,
    hide_cursor,
    mouse_wheel_clicked,
    new_stdscr,
    terminal_resize,
    truncate_if_needed,
    update_global_lines_cols,
)
from src.Dictionaries.dictionary_base import filter_dictionary
from src.Dictionaries.utils import wrap_and_pad
from src.cards import create_and_add_card
from src.commands import INTERACTIVE_COMMANDS, NO_HELP_ARG_COMMANDS, HELP_ARG_COMMANDS
from src.data import STRING_TO_BOOL, HORIZONTAL_BAR, WINDOWS, config
from src.search import search_dictionaries

if TYPE_CHECKING:
    from src.Dictionaries.dictionary_base import Dictionary
    from src.search import QuerySettings

# Pythons < 3.10 and ncurses < 6 do not
# define BUTTON5_PRESSED. (mouse wheel down)
BUTTON5_PRESSED = 2097152


def highlight() -> int:
    mask = config['-hlmode']
    result = Color.heed
    if mask[0] == 'y':
        result |= curses.A_STANDOUT
    if mask[1] == 'y':
        result |= curses.A_BOLD

    return result


# TODO: Writer is not really useful on its own, because we want to have
#       at least some control over drawing in the ScreenBuffer.
#       We should consider merging it with the Status class.
class Writer:
    __slots__ = 'win', 'screen_coverage', 'margin_bottom', 'buffer'

    def __init__(self,
            win: curses._CursesWindow, screen_coverage: float, margin_bottom: int
    ) -> None:
        if screen_coverage < 0 or screen_coverage > 1:
            raise ValueError(
                f'Invalid screen_coverage, expected: float 0-1, got: {screen_coverage!r}'
            )
        if margin_bottom < 0:
            raise ValueError(
                f'Invalid margin_bottom, expected: unsigned int, got: {margin_bottom!r}'
            )

        self.win = win
        self.screen_coverage = screen_coverage
        self.margin_bottom = margin_bottom
        self.buffer: list[list[tuple[str, int]]] = []

    def writeln(self, s: str) -> None:
        self.buffer.extend(Color.parse_ansi_str(s))

    def newline(self, s: str, pair_number: int) -> None:
        self.buffer.append([(s, curses.color_pair(pair_number))])

    @property
    def visible_buffer(self) -> list[list[tuple[str, int]]]:
        height = int(env.LINES * self.screen_coverage)
        if height <= 0:
            return []
        if len(self.buffer) > height:
            return self.buffer[-height:]
        else:
            return self.buffer

    def flush(self) -> None:
        if not self.buffer:
            return

        lines = self.visible_buffer
        for y, line in enumerate(lines, env.LINES - self.margin_bottom - len(lines)):
            x = 0
            try:
                self.win.hline(y, x, ' ', env.COLS)
                for text, attr in line:
                    self.win.addstr(y, x, text, attr)
                    x += len(text)
            except curses.error:  # text too long or env.LINES too small
                pass


class Status:
    def __init__(self, win: curses._CursesWindow, *, persistence: int) -> None:
        self.writer = Writer(win, 0.9, 0)
        self.persistence = persistence if persistence > 0 else 1
        self.lock = False
        self.ticks = 1

    @contextlib.contextmanager
    def change(self, *, lock: bool, margin_bottom: int) -> Iterator[None]:
        _orig_mb, _orig_lock = self.writer.margin_bottom, self.lock
        self.writer.margin_bottom = margin_bottom
        self.lock = lock
        try:
            yield
        finally:
            self.lock = _orig_lock
            self.writer.margin_bottom = _orig_mb

    def _pad(self, s: str) -> str:
        return ' ' + s.ljust(env.COLS - 1)

    def notify(self, line: str, pair_number: int) -> None:
        self.ticks = 1
        if not self.writer.buffer:
            return self.writer.newline(self._pad(line), pair_number)

        last_line, last_color = self.writer.buffer[-1][-1]
        if last_color != curses.color_pair(pair_number):
            return self.writer.newline(self._pad(line), pair_number)

        new_line = self._pad(f'{last_line.strip()}  {line.strip()}')
        if len(new_line) > env.COLS:
            new_line = new_line[-env.COLS:]
        self.writer.buffer[-1][-1] = (new_line, curses.color_pair(pair_number))

    def writeln(self, s: str) -> None:
        self.ticks = 1
        self.writer.writeln(s)

    def newline(self, s: str, pair_number: int) -> None:
        self.ticks = 1
        self.writer.newline(s, pair_number)

    def success(self, s: str) -> None:
        self.notify(s, BLACK_ON_GREEN)

    def nlerror(self, s: str) -> None:
        self.newline(self._pad(s), BLACK_ON_RED)

    def error(self, s: str) -> None:
        self.notify(s, BLACK_ON_RED)

    def addstr(self, s: str) -> None:
        for line in s.splitlines():
            self.newline(' ' + line, 0)

    def draw_if_available(self) -> None:
        self.writer.flush()
        if not self.lock and self.ticks >= self.persistence:
            self.writer.buffer.clear()
        else:
            self.ticks += 1


class RefreshWriter:
    def __init__(self, screen_buffer: ScreenBuffer) -> None:
        self.screen_buffer = screen_buffer

    def writeln(self, s: str) -> None:
        self.screen_buffer.status.writeln(s)
        self.screen_buffer.draw()
        curses.doupdate()


class CardWriter:
    def __init__(self, screen_buffer: ScreenBuffer) -> None:
        self.screen_buffer = screen_buffer

    def writeln(self, s: str) -> None:
        self.screen_buffer.status.writeln(s)
        self.screen_buffer.draw()
        curses.doupdate()

    def preview_card(self, card: dict[str, str]) -> None:
        # TODO: Find a nice and concise way to preview cards in curses.
        pass


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
            rest: tuple[list[str], int] | None = None
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


BORDER_PAD = 1

def draw_help(stdscr: curses._CursesWindow) -> None:
    top_line = [
        ('F1', ' Help '), ('j/k', ' Move down/up '), ('1-9', ' Select cell '),
        ('B ', ' Card browser '), ('g ', ' Go top '), ('^F', ' Filter '),
        ('p ', ' Paste from selection '), ('^J', ' Reset filters '),
    ]
    bot_line = [
        ('q ', ' Exit '), ('h/l', ' Swap screens '), ('d ', ' Deselect all '),
        ('C ', ' Create cards '), ('G ', ' Go EOF '), ('/ ', ' Search '),
        ('P ', ' Paste current phrase '), ('^L', ' Redraw screen '), ('F8', ' Rearrange columns '),
    ]

    top_bot_pairs = []
    space_occupied = 0
    space_to_occupy = env.COLS - 2*BORDER_PAD
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
        gap = space_left // (len(top_bot_pairs)-1) * ' '
    except ZeroDivisionError:
        gap = ''

    bot_y, top_y = env.LINES-2, env.LINES-3
    a_standout = curses.A_STANDOUT
    try:
        for (top_cmd, top_msg), (bot_cmd, bot_msg) in reversed(top_bot_pairs):
            stdscr.insstr(top_y, BORDER_PAD, top_msg + gap)
            stdscr.insstr(top_y, BORDER_PAD, top_cmd, a_standout)
            stdscr.insstr(bot_y, BORDER_PAD, bot_msg + gap)
            stdscr.insstr(bot_y, BORDER_PAD, bot_cmd, a_standout)
    except curses.error:  # window too small, because of env.LINES
        pass


def corollary_boxes_to_toggle_on() -> set[str]:
    result = {'PHRASE'}
    if config['-audio'] != '-':
        result.add('AUDIO')
    if config['-pos']:
        result.add('POS')
    if config['-etym']:
        result.add('ETYM')
    return result


COROLLARY_DICTIONARY_OPS = {'PHRASE', 'AUDIO', 'POS', 'ETYM'}
DIRECTLY_TOGGLEABLE = {'DEF', 'SUBDEF', 'SYN'}
AUTO_COLUMN_WIDTH = 47
MINIMUM_TEXT_WIDTH = 26


def _read_columns_config() -> int:
    val = config['-columns']
    return 0 if 'auto' in val else int(val)


def _one_to_five(n: int) -> int:
    if n < 1:
        return 1
    if n > 5:
        return 5
    return n


def _create_layout(
    dictionary: Dictionary, height: int
) -> tuple[list[list[curses._CursesWindow]], list[list[curses._CursesWindow]], int, int]:
    width = env.COLS - 2*BORDER_PAD + 1

    config_columns = _read_columns_config()
    if config_columns > 0:
        min_columns = max_columns = _one_to_five(config_columns)
    else:  # auto
        min_columns = 1
        max_columns = _one_to_five(width // AUTO_COLUMN_WIDTH)

    margin = config['-margin']
    while True:
        col_width = (width // min_columns) - 1
        col_text_width = col_width - 2*margin
        if col_text_width < MINIMUM_TEXT_WIDTH:
            margin -= ((MINIMUM_TEXT_WIDTH - col_text_width) // 2)
            if margin < 0:
                margin = 0
            col_text_width = col_width - 2*margin
            if col_text_width < 1:
                col_text_width = 1

        _boxes, _lines = format_dictionary(dictionary, col_text_width)
        if (_lines // min_columns < height) or (min_columns >= max_columns):
            break
        else:
            min_columns += 1

    columns: list[list[curses._CursesWindow]] = [[] for _ in range(min_columns)]
    cur = 0
    max_height = (_lines // min_columns) + 1
    move_ops = []
    for lines, entry in zip(_boxes, dictionary.contents):
        op = entry[0]

        if len(columns[cur]) < max_height:
            if op in ('LABEL', 'PHRASE', 'HEADER'):
                move_ops.append((op, len(lines)))
            elif op == 'AUDIO':
                continue
            else:
                move_ops.clear()
        else:
            if cur < min_columns - 1:
                cur += 1
            else:
                columns[cur].extend(lines)
                continue

            if op == 'HEADER' and not entry[0]:
                columns[cur].extend(lines)
            else:
                header = curses.newwin(1, col_text_width)
                header.hline(0, col_text_width)
                columns[cur].append(header)

            t_move = []
            while move_ops:
                t_op, t_len = move_ops.pop()
                t_lines = [columns[cur-1].pop() for _ in range(t_len)]
                if t_op == 'LABEL' and not move_ops:
                    t_lines.pop()
                t_move.extend(t_lines)

            columns[cur].extend(reversed(t_move))
            if op in ('LABEL', 'POS', 'ETYM'):
                lines = lines[1:]

        columns[cur].extend(lines)

    return _boxes, columns, col_width, margin


class Screen:
    def __init__(self, dictionary: Dictionary) -> None:
        self._orig_dictionary = self.dictionary = dictionary
        self.margin_bottom = 0 if config['-nohelp'] else 2

        self._boxes, self.columns, self.col_width, self.margin = _create_layout(
            dictionary, self.screen_height
        )

        self._ptoggled: Counter[int] = Counter()
        self._box_states = [curses.A_NORMAL] * len(self._boxes)
        self._scroll_i = 0

    @property
    def screen_height(self) -> int:
        r = env.LINES - self.margin_bottom - 2*BORDER_PAD
        return r if r > 0 else 0

    def update_for_redraw(self) -> None:
        self._boxes, self.columns, self.col_width, self.margin = _create_layout(
            self.dictionary, self.screen_height
        )
        a_normal = curses.A_NORMAL
        for lines, state in zip(self._boxes, self._box_states):
            if state != a_normal:
                for line in lines:
                    line.bkgd(state)

    def _scroll_end(self) -> int:
        r = max(map(len, self.columns)) - self.screen_height
        return r if r > 0 else 0

    def draw(self) -> None:
        # scroll_pos can be bigger than eof if self.margin_bottom
        # has decreased or window has been resized.
        bound = self._scroll_end()
        if self._scroll_i > bound:
            self._scroll_i = bound

        columns = self.columns
        from_index = self._scroll_i + 1  # +1 skips headers
        try:
            # hide out of view windows behind the header to prevent
            # them from stealing clicks in the upper region.
            for column in columns:
                for box in islice(column, None, from_index):
                    box.mvwin(0, 1)

            col_width, margin = self.col_width, self.margin
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
        self._box_states[i] = state
        for line in self._boxes[i]:
            line.bkgd(state)

    def _toggle_related_boxes(self, current_state: int, phraseno: int, box_index: int) -> None:
        if current_state == curses.A_NORMAL:
            self._toggle_box(box_index, highlight())
            self._ptoggled[phraseno] += 1
        else:
            self._toggle_box(box_index, curses.A_NORMAL)
            self._ptoggled[phraseno] -= 1

        try:
            static_entries_to_index = self.dictionary.static_entries_to_index_from_index(box_index)
        except ValueError:  # Dictionary has no PHRASE entries.
            return

        # Accounts for the possibility of -pos, -etym etc.
        # changing state when selections are active.
        for op in COROLLARY_DICTIONARY_OPS:
            if op in static_entries_to_index:
                self._toggle_box(static_entries_to_index[op], curses.A_NORMAL)

        if self._ptoggled[phraseno] > 0:
            for op in corollary_boxes_to_toggle_on():
                if op in static_entries_to_index:
                    self._toggle_box(static_entries_to_index[op], curses.A_BOLD)


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
        not_in_view = set()
        for column in self.columns:
            for i in range(self._scroll_i):
                try:
                    not_in_view.add(id(column[i]))
                except IndexError:
                    break

        phraseno = 0
        for i, (state, lines) in enumerate(zip(self._box_states, self._boxes)):
            op = self.dictionary.contents[i][0]
            if op == 'PHRASE':
                phraseno += 1
            if op in DIRECTLY_TOGGLEABLE:
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
        for i, (state, lines) in enumerate(zip(self._box_states, self._boxes)):
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
        return [i for i, x in enumerate(self._box_states) if x != curses.A_NORMAL]

    def restore_original_dictionary(self) -> None:
        self.dictionary = self._orig_dictionary
        self.update_for_redraw()

    def deselect_all(self) -> None:
        self._ptoggled.clear()
        a_normal = curses.A_NORMAL
        for i, state in enumerate(self._box_states):
            if state != a_normal:
                self._toggle_box(i, a_normal)

    def move_down(self, n: int = 2) -> None:
        self._scroll_i += n
        bound = self._scroll_end()
        if self._scroll_i > bound:
            self._scroll_i = bound

    def move_up(self, n: int = 2) -> None:
        self._scroll_i -= n
        if self._scroll_i < 0:
            self._scroll_i = 0

    def go_bottom(self) -> None:
        self._scroll_i = self._scroll_end()

    def go_top(self) -> None:
        self._scroll_i = 0

    def page_down(self) -> None:
        self.move_down(self.screen_height - 2)

    def page_up(self) -> None:
        self.move_up(self.screen_height - 2)

    ACTIONS: dict[bytes, Callable[[Screen], None]] = {
        b'^J': restore_original_dictionary, b'^M': restore_original_dictionary,
        b'd': deselect_all,
        b'j': move_down, b'^N': move_down, b'KEY_DOWN': move_down,
        b'k': move_up,   b'^P': move_up,   b'KEY_UP': move_up,
        b'G': go_bottom, b'KEY_END': go_bottom,
        b'g': go_top,    b'KEY_HOME': go_top,
        b'KEY_NPAGE': page_down, b'KEY_SNEXT': page_down,
        b'KEY_PPAGE': page_up,   b'KEY_SPREVIOUS': page_up,
    }


T = TypeVar('T')
class InteractiveCommandHandler:
    def __init__(self, screen_buffer: ScreenBuffer) -> None:
        self.screen_buffer = screen_buffer
        self.prompt = Prompt(
            screen_buffer, screen_buffer.stdscr, exit_if_empty=False
        )

    def writeln(self, s: str) -> None:
        self.screen_buffer.status.writeln(s)

    def choose_item(self, prompt_name: str, seq: Sequence[T], default: int = 1) -> T | None:
        self.prompt.prompt = f'{prompt_name} [{default}]: '
        typed = self.prompt.run()
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
        self.prompt.prompt = f'{prompt_name} [{"Y/n" if default else "y/N"}]: '
        typed = self.prompt.run()
        if typed is None:
            return default
        return STRING_TO_BOOL.get(typed.strip().lower(), default)


class ScreenBuffer:
    def __init__(self, stdscr: curses._CursesWindow, screens: Sequence[Screen]) -> None:
        self.stdscr = stdscr
        self.screens = screens
        self.status = Status(stdscr, persistence=2)
        self._cursor = 0

    @property
    def current(self) -> Screen:
        return self.screens[self._cursor]

    def next(self) -> Screen:
        if self._cursor < len(self.screens) - 1:
            self._cursor += 1
        return self.current

    def previous(self) -> Screen:
        if self._cursor > 0:
            self._cursor -= 1
        return self.current

    def _draw_status_bar(self, y: int) -> None:
        stdscr = self.stdscr
        stdscr.addch(y, 0, curses.ACS_LLCORNER)
        stdscr.hline(y, 1, curses.ACS_HLINE, env.COLS - 2)
        try:
            stdscr.addch(y, env.COLS - 1, curses.ACS_LRCORNER)
        except curses.error:  # it's idiomatic I guess
            pass

        nscreens = len(self.screens)
        if nscreens < 2:
            return
        screen_hint = truncate_if_needed(f'{self._cursor+1}/{nscreens}', env.COLS - 4)
        if screen_hint is None:
            return
        hint_x = env.COLS - len(screen_hint) - 2
        stdscr.addch(y, hint_x - 1, '╴')
        stdscr.addstr(y, hint_x, screen_hint, Color.delimit | curses.A_BOLD)
        stdscr.addch(y, hint_x + len(screen_hint), '╶')

    def _draw_border(self) -> None:
        screen = self.current
        stdscr = self.stdscr
        stdscr.box()

        header = truncate_if_needed(screen.dictionary.contents[0][1], env.COLS - 8)
        if header is not None:
            stdscr.addstr(0, 2, '[ ')
            stdscr.addstr(0, 4, header, Color.delimit | curses.A_BOLD)
            stdscr.addstr(0, 4 + len(header), ' ]')

        shift = BORDER_PAD + screen.col_width
        screen_height = screen.screen_height
        try:
            for i in range(1, len(screen.columns)):
                stdscr.vline(BORDER_PAD, i * shift, 0, screen_height)
        except curses.error:
            pass

    def draw(self) -> None:
        stdscr = self.stdscr
        screen = self.current

        stdscr.erase()
        stdscr.attrset(Color.delimit)

        # a little bit hacky, but to prevent flickering, we have to ensure
        # that 'screen.draw' comes last.
        v_buf_height = len(
            self.status.writer.visible_buffer
        ) + self.status.writer.margin_bottom
        if v_buf_height < 3:
            if config['-nohelp']:
                screen.margin_bottom = v_buf_height
            else:
                screen.margin_bottom = 2
                draw_help(stdscr)
        else:
            screen.margin_bottom = v_buf_height

        self._draw_border()
        self._draw_status_bar(env.LINES - v_buf_height - 1)
        self.status.draw_if_available()

        stdscr.noutrefresh()
        screen.draw()

    def resize(self) -> None:
        # This is noticeably slow when there are more than 10 screens.
        # Updating lazily doesn't help, because terminal_resize takes
        # the majority of the time.
        terminal_resize()

        for screen in self.screens:
            screen.update_for_redraw()

        self.stdscr.clearok(True)

    def rearrange_columns(self) -> None:
        state = _read_columns_config()
        config['-columns'] = 'auto' if state > 4 else str(state + 1)

        for screen in self.screens:
            screen.update_for_redraw()

        self.status.success(config['-columns'].capitalize())

    def filter_prompt(self) -> None:
        typed = Prompt(self, self.stdscr, 'Filter (~n, ~/n): ').run()
        if typed is None:
            return
        typed = typed.lstrip()
        if not typed:
            return

        screen = self.current
        screen.dictionary = filter_dictionary(screen._orig_dictionary, (typed,))
        screen.update_for_redraw()

    def _dispatch_command(self, s: str) -> bool:
        args = s.split()
        cmd = args[0]
        if cmd in NO_HELP_ARG_COMMANDS:
            result = NO_HELP_ARG_COMMANDS[cmd](*args)
        elif cmd in HELP_ARG_COMMANDS:
            func, note, usage = HELP_ARG_COMMANDS[cmd]
            if (len(args) == 1 or
               (len(args) == 2 and args[1].strip(' -').lower() in ('h', 'help'))
            ):
                self.status.notify(note, BLACK_ON_YELLOW)
                self.status.addstr(f'{cmd} {usage}')
                return True
            else:
                result = func(*args)
        elif cmd in INTERACTIVE_COMMANDS:
            # change margin_bottom to leave one line for the prompt.
            with self.status.change(margin_bottom=1, lock=True):
                result = INTERACTIVE_COMMANDS[cmd](
                    InteractiveCommandHandler(self), *args
                )
            self.status.writer.buffer.clear()
        elif cmd.startswith('-'):
            self.status.nlerror(f'{cmd}: command not found')
            return True
        else:
            return False

        # TODO: dedicated dispatch functions for updating
        #       relevant states after issuing commands?
        outs = result.output
        if outs:
            self.status.writer.buffer.clear()
            if outs.count('\n') < self.status.writer.screen_coverage * env.LINES - 2:
                self.status.writeln(outs)
            else:
                Pager(self.stdscr, outs).run()
        if result.error:
            self.status.nlerror(result.error)
        if result.reason:
            self.status.addstr(result.reason)

        return True

    def search_prompt(self, *, pretype: str = '') -> tuple[ScreenBuffer, QuerySettings] | None:
        pretype = ' '.join(pretype.split())
        with self.status.change(margin_bottom=0, lock=True):
            typed = Prompt(self, self.stdscr, 'Search $ ', pretype=pretype).run()
        if typed is None:
            return None
        typed = typed.strip()
        if not typed:
            return None

        if self._dispatch_command(typed):
            self.current.update_for_redraw()
            return None

        ret = search_dictionaries(RefreshWriter(self), typed)
        if ret is None:
            return None

        dictionaries, settings = ret

        return ScreenBuffer(self.stdscr, tuple(map(Screen, dictionaries))), settings

    ACTIONS = {
        b'l': next,     b'KEY_RIGHT': next,
        b'h': previous, b'KEY_LEFT': previous,
        b'KEY_RESIZE': resize, b'^L': resize,
        b'KEY_F(8)': rearrange_columns,
        b'^F': filter_prompt, b'KEY_F(4)': filter_prompt,
    }


def perror_clipboard_or_selection(status: Status) -> str | None:
    try:
        return clipboard_or_selection()
    except ValueError as e:
        status.error(str(e))
    except LookupError as e:
        status.nlerror(
            f'Could not access the {"clipboard" if WINDOWS else "primary selection"}:'
        )
        status.addstr(str(e))

    return None


def perror_currently_reviewed_phrase(status: Status) -> str | None:
    try:
        return anki.currently_reviewed_phrase()
    except anki.AnkiError as e:
        status.nlerror('Paste from the "Phrase" field failed:')
        status.addstr(str(e))
        return None


SEARCH_ENTER_ACTIONS = {
    b'p': perror_clipboard_or_selection,
    b'P': perror_currently_reviewed_phrase,
    b'-': lambda _: '-',
    b'/': lambda _: '',
}


def _curses_main(
        stdscr: curses._CursesWindow,
        _dictionaries: list[Dictionary],
        _settings: QuerySettings
) -> None:
    update_global_lines_cols()

    # Resizing the terminal after calling curses.endwin inserts the resize
    # character into the buffer. Let's always start with a fresh buffer.
    curses.flushinp()

    settings = _settings
    screen_buffer = ScreenBuffer(stdscr, tuple(map(Screen, _dictionaries)))
    while True:
        screen_buffer.draw()
        curses.doupdate()

        c = curses.keyname(get_key(stdscr))
        if c in Screen.ACTIONS:
            Screen.ACTIONS[c](screen_buffer.current)
        elif c in Screen.KEYBOARD_SELECTOR_CHARS:
            screen_buffer.current.mark_box_by_selector(c)
        elif c in ScreenBuffer.ACTIONS:
            ScreenBuffer.ACTIONS[c](screen_buffer)
        elif c == b'KEY_MOUSE':
            _, x, y, _, bstate = curses.getmouse()
            if bstate & curses.BUTTON1_PRESSED:  # left mouse
                screen_buffer.current.mark_box_at(y, x)
            elif bstate & curses.BUTTON4_PRESSED:  # mouse wheel
                screen_buffer.current.move_up()
            elif bstate & BUTTON5_PRESSED:  # mouse wheel
                screen_buffer.current.move_down()
            elif mouse_wheel_clicked(bstate):
                pretype = perror_clipboard_or_selection(screen_buffer.status)
                if pretype is None:
                    continue
                ret = screen_buffer.search_prompt(pretype=pretype)
                if ret is not None:  # new query
                    screen_buffer, settings = ret
        elif c in SEARCH_ENTER_ACTIONS:
            pretype = SEARCH_ENTER_ACTIONS[c](screen_buffer.status)
            if pretype is None:
                continue
            ret = screen_buffer.search_prompt(pretype=pretype)
            if ret is not None:  # new query
                screen_buffer, settings = ret
        elif c == b'B':
            try:
                anki.invoke('guiBrowse', query='added:1')
            except anki.AnkiError as e:
                screen_buffer.status.nlerror('Could not open the card browser:')
                screen_buffer.status.addstr(str(e))
            else:
                screen_buffer.status.success('Anki card browser opened')
        elif c == b'C':
            _screen = screen_buffer.current
            selection_data = _screen.get_indices_of_selected_boxes()
            if selection_data:
                create_and_add_card(
                    CardWriter(screen_buffer),
                    _screen.dictionary,
                    selection_data,
                    settings
                )
                _screen.deselect_all()
            else:
                screen_buffer.status.error('Nothing selected')
        elif c == b'KEY_F(1)':
            config['-nohelp'] = not config['-nohelp']
        elif c in (b'q', b'Q', b'^X'):
            return


def curses_entry(dictionaries: list[Dictionary], settings: QuerySettings) -> None:
    with new_stdscr() as stdscr:
        hide_cursor()
        init_colors()

        curses.mousemask(-1)
        curses.mouseinterval(0)

        _curses_main(stdscr, dictionaries, settings)

