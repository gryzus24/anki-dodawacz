from __future__ import annotations

import contextlib
import curses
from typing import Callable, Iterator, NamedTuple

from src.Curses.color import Color
from src.Curses.prompt import Prompt
from src.Curses.proto import ScreenBufferInterface
from src.Curses.util import Attr, truncate, draw_border, BORDER_PAD
from src.data import config, config_save


class COption(NamedTuple):
    name: str
    description: str
    constraint: list[str] | None


class CColumn(NamedTuple):
    header: str
    options: list[COption]

    @property
    def noptions(self) -> int:
        return len(self.options)


class CRow(NamedTuple):
    columns: list[CColumn]

    @property
    def height(self) -> int:
        return max(x.noptions for x in self.columns) + 1

    def get_option(self, _col_i: int, _opt_i: int) -> COption:
        return self.columns[_col_i].options[_opt_i]


CONFIG_COLUMNS: list[CRow] = [
    CRow(
    [
        CColumn(
        'Cards',
        [
            COption('audio', 'Add audio', None),
            COption('pos', 'Add parts of speech', None),
            COption('etym', 'Add etymologies', None),
            COption('exsen', 'Add example sentences', None),
            COption('formatdefs', 'Add HTML formatting to definitions', None),
            COption('hidedef', 'Replace target word with `-hides` in definitions', None),
            COption('hidesyn', 'Replace target word with `-hides` in synonyms', None),
            COption('hideexsen', 'Replace target word with `-hides` in example sentences', None),
            COption('hidepreps', 'Replace all prepositions with `-hides`', None),
            COption('hides', 'Sequence of characters to use as target word replacement', None),
        ]
        ),
        CColumn(
        'Anki-connect',
        [
            COption('note', 'Note used for adding cards', None),
            COption('deck', 'Deck used for adding cards', None),
            COption('mediapath', 'Audio save location', None),
            COption('duplicates', 'Allow duplicates', None),
            COption('dupescope', 'Look for duplicates in', ['deck', 'collection']),
            COption('tags', 'Anki tags (comma separated list)', None),
        ]
        ),
    ]),
    CRow(
    [
        CColumn(
        'Sources',
        [
            COption('dict', 'Primary dictionary', ['ahd', 'collins', 'farlex', 'wordnet']),
            COption('dict2', 'Secondary dictionary', ['ahd', 'collins', 'farlex', 'wordnet', '-']),
        ]),
        CColumn(
        'Miscellaneous',
        [
            COption('toipa', 'Translate AH Dictionary phonetic spelling into IPA', None),
            COption('shortetyms', 'Shorten and simplify etymologies in AH Dictionary', None),
        ]),
    ]),
]

class ConfigMenu(ScreenBufferInterface):
    OPTION_NAME_WIDTH = 13
    OPTION_VALUE_WIDTH = 10
    COLUMN_WIDTH = OPTION_NAME_WIDTH + OPTION_VALUE_WIDTH
    COLUMN_PAD = 3

    CONFIG_MIN_HEIGHT = (
          sum(x.height for x in CONFIG_COLUMNS)
        + (len(CONFIG_COLUMNS) - 1)
    )

    CONFIG_MIN_WIDTH = (
          len(CONFIG_COLUMNS) * COLUMN_WIDTH
        + (len(CONFIG_COLUMNS) - 1) * COLUMN_PAD
    )

    def __init__(self, win: curses._CursesWindow) -> None:
        self.win = win
        self.grid = CONFIG_COLUMNS
        self.min_y = ConfigMenu.CONFIG_MIN_HEIGHT + 2*BORDER_PAD + 4
        self.min_x = ConfigMenu.CONFIG_MIN_WIDTH + 2*BORDER_PAD
        self.margin_bot = 0
        self._row = self._col = self._line = 0
        self._initial_config = config.copy()

    @contextlib.contextmanager
    def extra_margin(self, n: int) -> Iterator[None]:
        t = self.margin_bot
        self.margin_bot += n
        yield
        self.margin_bot = t

    def _value_of_option(self, option: COption) -> tuple[str, Attr]:
        if isinstance(config[option.name], bool):  # type: ignore[literal-required]
            if config[option.name]:  # type: ignore[literal-required]
                return 'ON', Attr(0, 2, Color.success)
            else:
                return 'OFF', Attr(0, 3, Color.err)
        else:
            return str(config[option.name]), Attr(0, 0, 0)  # type: ignore[literal-required]

    def _description_of_option(self, option: COption) -> str:
        if option.constraint is not None:
            return f'{option.description} ({"/".join(option.constraint)})'
        else:
            return option.description

    def draw(self) -> None:
        if curses.COLS < self.min_x or curses.LINES < self.min_y:
            raise ValueError(f'window too small (need at least {self.min_x}x{self.min_y})')

        win = self.win
        win.erase()

        draw_border(win, self.margin_bot)

        width = curses.COLS - 2*BORDER_PAD

        current_option = self.grid[self._row].get_option(self._col, self._line)
        optdesc = truncate(self._description_of_option(current_option), width)
        if optdesc is None:
            return

        value, attr = self._value_of_option(current_option)
        value_text = truncate(f'-> {value}', width)
        if value_text is None:
            return

        win.addstr(BORDER_PAD, BORDER_PAD, optdesc)
        win.addstr(BORDER_PAD + 1, BORDER_PAD, value_text)
        # TODO: `BORDER_PAD + 3` might break.
        win.chgat(BORDER_PAD + 1, BORDER_PAD + 3 + attr.i, attr.span, attr.attr)
        win.hline(BORDER_PAD + 2, BORDER_PAD, curses.ACS_HLINE, width)

        row_y = BORDER_PAD + 3
        row_x = 1
        for row_i, row in enumerate(self.grid):
            for col_i, column in enumerate(row.columns):
                win.addstr(
                    row_y,
                    row_x,
                    f'{column.header:{self.COLUMN_WIDTH}s}',
                    curses.A_BOLD | curses.A_UNDERLINE
                )
                for line_i, option in enumerate(column.options):
                    if (
                            self._row == row_i
                        and self._col == col_i
                        and self._line == line_i
                    ):
                        selection_hl = curses.A_STANDOUT | curses.A_BOLD
                    else:
                        selection_hl = 0

                    value_text, attr = self._value_of_option(option)
                    modified = self._initial_config[option.name] != config[option.name]  # type: ignore[literal-required]

                    entry = truncate(
                        f'{option.name + ("*" if modified else ""):{self.OPTION_NAME_WIDTH}s}'
                        f'{value_text:{self.OPTION_VALUE_WIDTH}s}',
                        self.COLUMN_WIDTH
                    )
                    if entry is None:
                        return

                    y = row_y + line_i + 1
                    win.addstr(y, row_x, entry, selection_hl)
                    if modified:
                        win.chgat(y, row_x + len(option.name), 1, Color.heed | curses.A_BOLD)
                    win.chgat(y, row_x + 13 + attr.i, attr.span, attr.attr | selection_hl)

                row_x += self.COLUMN_WIDTH + self.COLUMN_PAD

            row_y += row.height + 1
            row_x = 1

    def resize(self) -> None:
        curses.update_lines_cols()

    def _rows_in_current_column(self) -> int:
        result = 0
        for row in self.grid:
            try:
                row.columns[self._col]
            except IndexError:
                break
            else:
                result += 1

        return result

    def move_down(self) -> None:
        line_bound = self.grid[self._row].columns[self._col].noptions - 1
        if self._line < line_bound:
            self._line += 1
            return

        if self._row < self._rows_in_current_column() - 1:
            self._row += 1
            self._line = 0

    def move_up(self) -> None:
        if self._line > 0:
            self._line -= 1
            return

        if self._row > 0:
            self._row -= 1
            self._line = self.grid[self._row].columns[self._col].noptions - 1

    def move_right(self) -> None:
        column_bound = max(len(x.columns) for x in self.grid) - 1
        if self._col >= column_bound:
            return

        self._col += 1

        row_column_bound = self._rows_in_current_column() - 1
        if self._row > row_column_bound:
            self._row = row_column_bound

        line_bound = self.grid[self._row].columns[self._col].noptions - 1
        if self._line > line_bound:
            self._line = line_bound

    def move_left(self) -> None:
        if self._col <= 0:
            return

        self._col -= 1

        line_bound = self.grid[self._row].columns[self._col].noptions - 1
        if self._line > line_bound:
            self._line = line_bound

    def change_selected(self) -> None:
        name, _, constraint = self.grid[self._row].get_option(self._col, self._line)
        if isinstance(config[name], bool):  # type: ignore[literal-required]
            config[name] = not config[name]  # type: ignore[literal-required]
            return

        if not isinstance(config[name], str):  # type: ignore[literal-required]
            return

        if constraint is None:
            with self.extra_margin(1):
                typed = Prompt(
                    self, 'Enter new value: ', pretype=config[name], exiting_bspace=False  # type: ignore[literal-required]
                ).run()
            if typed is not None:
                config[name] = typed.strip()  # type: ignore[literal-required]
        else:
            config[name] = constraint[  # type: ignore[literal-required]
                (constraint.index(config[name]) + 1) % len(constraint)  # type: ignore[literal-required]
            ]

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
                config_save(config)
                return

