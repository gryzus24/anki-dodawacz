from __future__ import annotations

import contextlib
import copy
import curses
import functools
from typing import Callable, Iterator, NamedTuple, Type

import src.anki as anki
from src.Curses.color import Color, COLOR_NAME_TO_COLOR
from src.Curses.prompt import Prompt
from src.Curses.proto import ScreenBufferInterface
from src.Curses.util import (
    Attr,
    BORDER_PAD,
    draw_border,
    truncate,
)
from src.data import config, config_save, TConfig


class Option(NamedTuple):
    path:        str
    description: str
    constraint:  Type[bool] | list[str] | Callable[[], list[str]] | None
    # `strict`: option can be set only if it is contained within `constraint`.
    strict:      bool = False

    @property
    def basename(self) -> str:
        return self.path.rpartition('.')[2]

    def set_to(self, _c: TConfig, value: str | bool) -> None:
        left, _, right = self.path.partition('.')
        if right:
            _c[left][right] = value  # type: ignore[literal-required]
        else:
            _c[left] = value  # type: ignore[literal-required]

    def get_from(self, _c: TConfig) -> str | bool:
        left, _, right = self.path.partition('.')
        if right:
            return _c[left][right]  # type: ignore[literal-required]
        else:
            return _c[left]  # type: ignore[literal-required]


class Section(NamedTuple):
    header:  str
    options: list[Option]


class Column(NamedTuple):
    sections: list[Section]

    @property
    def noptions(self) -> int:
        return sum(len(x.options) for x in self.sections)

    def get_option(self, i: int) -> Option:
        for section in self.sections:
            if i < len(section.options):
                return section.options[i]

            i -= len(section.options)

        raise AssertionError(f'unreachable: {i}')

    def section_index(self, i: int) -> int:
        for section_i, section in enumerate(self.sections):
            if i < len(section.options):
                return section_i

            i -= len(section.options)

        raise AssertionError(f'unreachable: {i}')


_colors = list(COLOR_NAME_TO_COLOR)

CONFIG_COLUMNS: list[Column] = [
    Column([
        Section(
            'Cards',
            [
            Option('audio', 'Add audio', bool),
            Option('pos', 'Add parts of speech', bool),
            Option('etym', 'Add etymologies', bool),
            Option('exsen', 'Add example sentences', bool),
            Option('formatdefs', 'Add HTML formatting to definitions', bool),
            Option('hidedef', 'Replace target word with `-hides` in definitions', bool),
            Option('hidesyn', 'Replace target word with `-hides` in synonyms', bool),
            Option('hideexsen', 'Replace target word with `-hides` in example sentences', bool),
            Option('hidepreps', 'Replace all prepositions with `-hides`', bool),
            Option('hides', 'Sequence of characters to use as target word replacement', ['___', '...', '———']),
            ]
        )
    ]),
    Column([
        Section(
            'Anki-connect',
            [
            Option('note', 'Note used for adding cards', functools.partial(anki.invoke, 'modelNames')),
            Option('deck', 'Deck used for adding cards', functools.partial(anki.invoke, 'deckNames')),
            Option('mediapath', 'Audio save location', anki.collection_media_paths),
            Option('duplicates', 'Allow duplicates', bool),
            Option('dupescope', 'Look for duplicates in deck/collection', ['deck', 'collection'], strict=True),
            Option('tags', 'Anki tags (comma separated list)', None),
            ]
        ),
        Section(
            'Sources',
            [
            Option('primary', 'Dictionary queried by default', ['ahd', 'collins', 'farlex', 'wordnet'], strict=True),
            Option('secondary', 'Dictionary queried if first query fails', ['ahd', 'collins', 'farlex', 'wordnet', '-'], strict=True),
            ]
        ),
        Section(
            'Miscellaneous',
            [
            Option('toipa', 'Translate AH Dictionary phonetic spelling into IPA', bool, strict=True),
            Option('shortetyms', 'Shorten and simplify etymologies in AH Dictionary', bool, strict=True),
            ]
        )
    ]),
    Column([
        Section(
            'Colors',
            [
            Option('colors.def1', 'Color of odd definitions', _colors, strict=True),
            Option('colors.def2', 'Color of even definitions', _colors, strict=True),
            Option('colors.delimit', 'Color of delimiters', _colors, strict=True),
            Option('colors.err', 'Color of error indicators', _colors, strict=True),
            Option('colors.etym', 'Color of etymologies', _colors, strict=True),
            Option('colors.exsen', 'Color of example sentences', _colors, strict=True),
            Option('colors.heed', 'Color of attention indicators', _colors, strict=True),
            Option('colors.index', 'Color of definition indices', _colors, strict=True),
            Option('colors.infl', 'Color of inflections', _colors, strict=True),
            Option('colors.label', 'Color of labels', _colors, strict=True),
            Option('colors.phon', 'Color of phonologies', _colors, strict=True),
            Option('colors.phrase', 'Color of phrases', _colors, strict=True),
            Option('colors.pos', 'Color of parts of speech', _colors, strict=True),
            Option('colors.sign', 'Color of main definition signs', _colors, strict=True),
            Option('colors.success', 'Color of success indicators', _colors, strict=True),
            Option('colors.syn', 'Color of synonyms', _colors, strict=True),
            ]
        )
    ])
]

OPTION_NAME_MIN_WIDTH = 13
OPTION_VALUE_MIN_WIDTH = 3
COLUMN_MIN_WIDTH = OPTION_NAME_MIN_WIDTH + OPTION_VALUE_MIN_WIDTH
DESCRIPTION_BOX_HEIGHT = 3
COLUMN_PAD = 2
SECTION_PAD = 1


class ConfigMenu(ScreenBufferInterface):
    # 1st +1 - space for the header of the topmost section
    # 2nd +1 - space for the prompt
    CONFIG_MIN_HEIGHT = max(
        x.noptions + (1 + SECTION_PAD) * (len(x.sections) - 1)
        for x in CONFIG_COLUMNS
    ) + 1 + 1

    CONFIG_MIN_WIDTH = (
          len(CONFIG_COLUMNS) * COLUMN_MIN_WIDTH
        + (len(CONFIG_COLUMNS) - 1) * COLUMN_PAD
    )

    def __init__(self, win: curses._CursesWindow) -> None:
        self.win = win
        self.grid = CONFIG_COLUMNS
        self.min_y = self.CONFIG_MIN_HEIGHT + 2*BORDER_PAD + DESCRIPTION_BOX_HEIGHT
        self.min_x = self.CONFIG_MIN_WIDTH + 2*BORDER_PAD
        self.margin_bot = 0

        self._initial_config = copy.deepcopy(config)
        self._phantom_cursors = [0] * len(CONFIG_COLUMNS)
        self._col = self._line = 0

    @contextlib.contextmanager
    def extra_margin(self, n: int) -> Iterator[None]:
        t = self.margin_bot
        self.margin_bot += n
        try:
            yield
        finally:
            self.margin_bot = t

    def _value_of_option(self, option: Option, max_attr_span: int) -> tuple[str, Attr]:
        value = option.get_from(config)
        if option.constraint is bool:
            assert isinstance(value, bool)
            if value:
                return 'ON', Attr(0, 2, Color.success)
            else:
                return 'OFF', Attr(0, 3, Color.err)

        assert isinstance(value, str)
        if option.path.startswith('colors.'):
            return value, Attr(0, min(len(value), max_attr_span), getattr(Color, option.basename))
        else:
            return value, Attr(0, 0, 0)

    def draw(self) -> None:
        if curses.COLS < self.min_x or curses.LINES < self.min_y:
            raise ValueError(f'window too small (need at least {self.min_x}x{self.min_y})')

        win = self.win
        win.erase()
        draw_border(win, self.margin_bot)

        width = curses.COLS - 2*BORDER_PAD
        col_free_space = (width - self.CONFIG_MIN_WIDTH) // len(CONFIG_COLUMNS)
        value_max_width = OPTION_VALUE_MIN_WIDTH + col_free_space
        col_max_width = COLUMN_MIN_WIDTH + col_free_space

        option = self.grid[self._col].get_option(self._line)

        value, attr = self._value_of_option(option, value_max_width)
        value_text = truncate(f'-> {value}', width)
        if value_text is None:
            return

        description = truncate(option.description, width)
        if description is None:
            return

        win.addstr(BORDER_PAD, BORDER_PAD, description)
        win.addstr(BORDER_PAD + 1, BORDER_PAD, value_text)
        # TODO: `BORDER_PAD + 3` *might* break.
        win.chgat(BORDER_PAD + 1, BORDER_PAD + 3 + attr.i, attr.span, attr.attr)
        win.hline(BORDER_PAD + 2, BORDER_PAD, 0, width)

        y = BORDER_PAD + DESCRIPTION_BOX_HEIGHT
        x = BORDER_PAD

        def CHECK_PLUS_Y(_n: int) -> bool:
            nonlocal y
            if y >= curses.LINES - self.margin_bot - 2:
                return True
            y += _n
            return False

        for col_i, column in enumerate(self.grid):#{
            opt_i = 0
            for sec_i, section in enumerate(column.sections):#{
                win.addstr(
                    y,
                    x,
                    f'{section.header:{col_max_width}s}',
                    curses.A_BOLD | curses.A_UNDERLINE
                )
                if CHECK_PLUS_Y(1):
                    break

                for option in section.options:#{
                    value_text, attr = self._value_of_option(option, value_max_width)
                    modified = option.get_from(self._initial_config) != option.get_from(config)

                    entry = truncate(
                        f'{("* " if modified else "") + option.basename:{OPTION_NAME_MIN_WIDTH}s}'
                        f'{value_text}',
                        col_max_width
                    )
                    if entry is None:
                        return

                    win.addstr(y, x, entry)
                    win.chgat(y, x + OPTION_NAME_MIN_WIDTH + attr.i, attr.span, attr.attr)
                    if (
                            self._line == opt_i
                        and self._col == col_i
                        and column.section_index(self._line) == sec_i
                    ):
                        win.chgat(
                            y,
                            x,
                            col_max_width,
                            Color.heed | curses.A_STANDOUT | curses.A_BOLD
                        )
                    elif self._phantom_cursors[col_i] == opt_i:
                        win.chgat(y, x, col_max_width, curses.A_STANDOUT)

                    if CHECK_PLUS_Y(1):
                        break

                    opt_i += 1
                #}
                if CHECK_PLUS_Y(SECTION_PAD):
                    break
            #}
            y = BORDER_PAD + DESCRIPTION_BOX_HEIGHT
            x += col_max_width + COLUMN_PAD
        #}

    def resize(self) -> None:
        curses.update_lines_cols()

    def move_down(self) -> None:
        if self._line < self.grid[self._col].noptions - 1:
            self._line += 1
            self._phantom_cursors[self._col] += 1

    def move_up(self) -> None:
        if self._line > 0:
            self._line -= 1
            self._phantom_cursors[self._col] -= 1

    def move_right(self) -> None:
        if self._col < len(self.grid) - 1:
            self._col += 1
            self._line = self._phantom_cursors[self._col]

    def move_left(self) -> None:
        if self._col > 0:
            self._col -= 1
            self._line = self._phantom_cursors[self._col]

    def change_selected(self) -> None:
        option = self.grid[self._col].get_option(self._line)
        value = option.get_from(config)
        constraint = option.constraint

        if constraint is bool:
            assert isinstance(value, bool)
            option.set_to(config, not value)
            return

        assert isinstance(value, str)
        if constraint is None:
            completions = []
        elif isinstance(constraint, list):
            completions = constraint
        elif callable(constraint):
            completions = constraint()  # type: ignore[assignment]
        else:
            raise AssertionError('unreachable')

        with self.extra_margin(1):
            typed = Prompt(
                self,
                f'New value ({"listed" if option.strict else "arbitrary"}): ',
                exiting_bspace=False
            ).run(completions)

        if typed is None:
            return

        typed = typed.strip()
        if option.strict:
            if typed in completions:
                option.set_to(config, typed)
        else:
            option.set_to(config, typed)

        Color.refresh()

    def apply_changes(self) -> bool:
        if self._initial_config == config:
            return False
        config_save(config)
        self._initial_config = copy.deepcopy(config)
        return True

    ACTIONS: dict[bytes, Callable[[ConfigMenu], None]] = {
        b'KEY_RESIZE': resize, b'^L': resize,
        b'j': move_down,  b'KEY_DOWN': move_down,
        b'k': move_up,    b'KEY_UP': move_up,
        b'l': move_right, b'KEY_RIGHT': move_right,
        b'h': move_left,  b'KEY_LEFT': move_left,
        b'^J': change_selected, b'^M': change_selected,
    }

    def run(self) -> None:
        while True:
            self.draw()

            key = curses.keyname(self.win.getch())
            if key in self.ACTIONS:
                self.ACTIONS[key](self)
            elif key in (b'q', b'Q', b'^X', b'KEY_F(2)'):
                return

