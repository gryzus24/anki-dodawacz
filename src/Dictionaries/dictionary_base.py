# Copyright 2021-2022 Gryzus
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

import sys
from collections import namedtuple
from itertools import zip_longest
from typing import Any, Callable, Iterable, Optional, Sequence

from src.Dictionaries.utils import wrap_and_pad
from src.colors import (BOLD, DEFAULT, R, def1_c, def2_c, defsign_c, delimit_c, etym_c,
                        exsen_c, index_c, inflection_c,
                        phon_c, phrase_c, pos_c, label_c, syn_c, syngloss_c)
from src.data import HORIZONTAL_BAR


def multi_split(string: str, *split_args: str) -> list[str]:
    # Splits a string at multiple places discarding redundancies just like `.split()`.
    result = []
    elem = ''
    for letter in string.strip():
        if letter in split_args:
            if elem:
                result.append(elem)
                elem = ''
        else:
            elem += letter
    if elem:
        result.append(elem)
    return result


def should_skip(label: str, flags: Iterable[str]) -> bool:
    labels = tuple(map(str.lower, multi_split(label, ' ', '.', '&')))

    skip_if_match = False
    for flag in flags:
        if flag.startswith('!'):
            skip_if_match = True
            flag = flag[1:]
        else:
            skip_if_match = False

        for label in labels:
            if label.startswith(flag) or flag.startswith(label):
                return skip_if_match

    return not skip_if_match


def columnize(buffer: Sequence[str], textwidth: int, ncols: int) -> list[list[str]]:
    blank = textwidth * ' '
    header = 2 * HORIZONTAL_BAR
    buff_len = len(buffer)
    initial_col_height = buff_len // ncols + buff_len % ncols

    col_no = lines_to_move = 0
    cbreak = current_col_height = initial_col_height
    formatted: list[list[str]] = [[] for _ in range(ncols)]
    for li, line in enumerate(buffer):
        control_symbol = line[0]
        line = line.lstrip('$!')

        if li < cbreak:
            formatted[col_no].append(line)
            if control_symbol == '!' or line == blank or header in line:
                lines_to_move += 1
            else:
                lines_to_move = 0
        elif control_symbol == '$':
            formatted[col_no].append(line)
            current_col_height += 1
        elif line == blank or header in line:
            continue
        else:
            if lines_to_move:
                for _i in range(-lines_to_move, 0):
                    m, formatted[col_no][_i] = formatted[col_no][_i], blank
                    if (m == blank and _i == -lines_to_move) or header in m:
                        continue
                    formatted[col_no + 1].append(m)
            col_no += 1
            formatted[col_no].append(line)
            cbreak += current_col_height
            current_col_height = initial_col_height

    return formatted


class FieldFormat(namedtuple('FieldFormat', ('fl_fmt', 'l_fmt', 'gaps'))):
    # Make it truly immutable.
    __slots__ = ()

    def __new__(
            cls,
            first_line_format: str,
            lines_format: Optional[str] = None,
            _gaps: Optional[int] = None
    ) -> FieldFormat:
        if lines_format is None:
            lines_format = first_line_format
        if _gaps is None:
            _gaps = first_line_format.count(' ')
            if '{sign}' in first_line_format:
                _gaps += 1
        return super().__new__(cls, first_line_format, lines_format, _gaps)


COLOR_FORMATS = {
    'exsen_c': exsen_c,
    'defsign_c': defsign_c,
    'index_c': index_c,
    'phrase_c': phrase_c,
    'phon_c': phon_c,
    'pos_c': pos_c,
    'label_c': label_c,
    'inflection_c': inflection_c,
    'etym_c': etym_c,
    'syn_c': syn_c,
    'syngloss_c': syngloss_c,
    'R': R,
    'BOLD': BOLD,
    'DEFAULT': DEFAULT,
}


class Dictionary:
    allow_thesaurus: bool
    name: str  # name in config
    title: str

    PHRASE = FieldFormat('! {phrase_c}{phrase}  {phon_c}{phon}{padding}')
    LABEL = FieldFormat('! {label_c}{label}  {inflection_c}{inflections}{padding}')
    DEF = FieldFormat(
        '{defsign_c}{sign}{index_c}{index} {label_c}{label}{def_c}{first_line}', '${def_c}{line}'
    )
    EXSEN = FieldFormat('${index_pad}  {exsen_c}{first_line}', '${exsen_c}{line}')
    POS = FieldFormat(' {pos_c}{pos}  {phon_c}{phon}{padding}')
    ETYM = FieldFormat(' {etym_c}{first_line}', '${etym_c}{line}')

    def __init__(self) -> None:
        self.contents: list[Sequence[str]] = []

    def __repr__(self) -> str:
        for op, *body in self.contents:
            sys.stdout.write(f'{op:7s}{body}\n')
        return f'{type(self).__name__}(self.contents ^)'

    # For subclassing.
    def input_cycle(self) -> dict[str, str] | None:
        raise NotImplementedError

    def add(self, op: str, body: str, *args: str) -> None:
        # Add an instruction to the dictionary.
        # Value must be a Sequence containing 2 or more fields:
        # ('OPERATION', 'BODY', ... )
        self.contents.append((op, body, *args))

    @property
    def phrases(self) -> list[str]:
        r = [b[0] for op, *b in self.contents if op == 'PHRASE']
        return r if r else ['']

    @property
    def audio_urls(self) -> list[str]:
        r = [b[0] for op, *b in self.contents if op == 'AUDIO']
        return r if r else ['']

    @property
    def synonyms(self) -> list[str]:
        r = [b[0] for op, *b in self.contents if op == 'SYN']
        return r if r else ['']

    @property
    def definitions(self) -> list[str]:
        r = [b[0] for op, *b in self.contents if 'DEF' in op]
        return r if r else ['']

    @property
    def example_sentences(self) -> list[str]:
        r = [b[1] for op, *b in self.contents if 'DEF' in op]
        return r if r else ['']

    def _by_header(self, type_: str, method: Callable[[list[str]], str]) -> list[str]:
        # Return a list of (`type_'s` bodies if `type_` is present within
        # HEADER instructions or empty string if `type_` is not present.)
        result = []
        t = ''
        for op, *body in self.contents:
            if op == type_:
                t = method(body)
            elif op == 'HEADER':
                result.append(t)
                t = ''
        result.append(t)
        return result

    @property
    def parts_of_speech(self) -> list[str]:
        # ['pos|phon', 'pos1|phon1'] -> 'pos phon<br>pos1 phon1'
        return self._by_header(
            'POS', lambda x: '<br>'.join(map(lambda y: y.replace('|', ' '), x)))

    @property
    def etymologies(self) -> list[str]:
        return self._by_header('ETYM', lambda x: x[0])

    def to_auto_choice(self, choices: Sequence[int], type_: str) -> str:
        # Convert a list of direct user inputs or inputs already passed through the
        # `get_positions_in_sections` method into a string based on what's in the Dictionary.
        ntype = 0
        for op, *_ in self.contents:
            if type_ in op:
                ntype += 1
        if not ntype:
            return '0'

        if ntype > 1 and ntype == len(choices) and all(
                map(lambda x, y: x == y, choices, range(1, ntype + 1))):
            return '-1'
        else:
            return ','.join(map(str, choices))

    def get_positions_in_sections(
            self, choices: Sequence[int], from_within: str = 'HEADER', choices_of: str = 'DEF'
    ) -> list[int]:
        # Returns a list of indexes of sections which contain user's choices.
        # If no `from_within` and `choices_of` instructions present in the dictionary return [1].
        # e.g.  [D1, D2, D3, HEADER, D4, D5, HEADER, D6]
        #       User picks D1 and D4,  function returns "[1,2]"
        #       User picks D1 and D2,  function returns "[1]"
        #       User picks D6 and D3,  function returns "[3,1]"

        # Determine what instruction comes first, so we know how to start counting.
        for op, *_ in self.contents:
            if choices_of in op:
                section_no = 1
                break
            if from_within in op:
                section_no = 0
                break
        else:
            return [1]

        section_no_per_choice = []
        for op, *_ in self.contents:
            if from_within in op:
                section_no += 1
            elif choices_of in op:
                section_no_per_choice.append(section_no)

        result = []
        len_s = len(section_no_per_choice)
        for choice in choices:
            if 0 < choice <= len_s:
                index = section_no_per_choice[choice - 1]
                if index not in result:
                    result.append(index)

        return result if result and result[0] else [1]

    def get_display_parameters(
            self, width: int, wrap_height: int, columns: Optional[int] = None
    ) -> tuple[int, int, int]:
        # width:  screen width in columns.
        # wrap_height:  wrap into columns when dictionary takes up this many rows.
        # columns:  number of columns: uint or None (auto).
        # Returns:
        #   individual column's width.
        #   number of columns.
        #   division remainder used to fill the last column.

        # approx_lines initially = 3 to include title and prompt.
        approx_lines = 3 + sum(
            2 if op in ('LABEL', 'ETYM')
            or
            ('DEF' in op and body[1]) else 1
            for op, *body in self.contents
        )
        if approx_lines < wrap_height:
            return width, 1, 0

        if columns is None:
            columns = width // 39
            for i in range(2, columns + 1):
                if approx_lines // i < wrap_height:
                    columns = i
                    break

        try:
            column_width = width // columns
        except ZeroDivisionError:
            return width, 1, 0
        else:
            remainder = width % columns
            if remainder < columns - 1:
                return column_width - 1, columns, remainder + 1
            return column_width, columns, 0

    def format_dictionary(self, textwidth: int, wrap_style: str, indent: int) -> list[str]:
        # Format self.contents' list of (op, body)
        # into wrapped, colored and padded body lines.
        # Available instructions:
        #  (DEF,    'definition', 'example_sentence', 'label')
        #  (SUBDEF, 'definition', 'example_sentence')
        #  (LABEL,  'pos_label', 'additional_info')
        #  (PHRASE, 'phrase', 'phonetic_spelling')
        #  (HEADER, 'filling_character')
        #  (POS,    'pos|phonetic_spelling', ...)  ## `|` acts as a separator.
        #  (AUDIO,  'audio_url')
        #  (NOTE,   'note')

        buffer = []

        def _format_push(fmt: str, **kwargs: Any) -> None:
            buffer.append(fmt.format(**kwargs, **COLOR_FORMATS))

        blank = textwidth * ' '
        wrap_method = wrap_and_pad(wrap_style, textwidth)

        index = 0
        for op, *body in self.contents:
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

                def_c = def1_c if index % 2 else def2_c

                first_line, *rest = wrap_method(
                    _def, self.DEF.gaps + index_len + label_len, indent - label_len
                )
                _format_push(
                    self.DEF.fl_fmt,
                    sign=' ' if 'SUB' in op else '>',
                    index=index,
                    label=_label,
                    def_c=def_c,
                    first_line=first_line
                )
                for line in rest:
                    _format_push(self.DEF.l_fmt, def_c=def_c, line=line)

                if _exsen:
                    for ex in _exsen.split('<br>'):
                        first_line, *rest = wrap_method(ex, self.EXSEN.gaps + index_len, indent + 1)
                        _format_push(self.EXSEN.fl_fmt, index_pad=index_len * ' ', first_line=first_line)
                        for line in rest:
                            _format_push(self.EXSEN.l_fmt, line=line)
            elif op == 'LABEL':
                buffer.append(blank)
                label, inflections = body
                if label:
                    padding = (textwidth - len(label) - len(inflections) - self.LABEL.gaps) * ' '
                    if padding:
                        _format_push(self.LABEL.fl_fmt, label=label, inflections=inflections, padding=padding)
                    else:
                        padding = (textwidth - len(label) - 1) * ' '
                        buffer.append(f'! {label_c}{label}{padding}')
                        padding = (textwidth - len(inflections) - 1) * ' '
                        buffer.append(f'! {inflection_c}{inflections}{padding}')
            elif op == 'PHRASE':
                phrase, phon = body
                padding = (textwidth - len(phrase) - len(phon) - self.PHRASE.gaps) * ' '
                if padding:
                    _format_push(self.PHRASE.fl_fmt, phrase=phrase, phon=phon, padding=padding)
                else:
                    first_line, *rest = wrap_method(phrase, 1, 0)
                    buffer.append(f'! {phrase_c}{first_line}')
                    for line in rest:
                        buffer.append(f'!{phrase_c}{line}')
                    if phon:
                        padding = (textwidth - len(phon) - 1) * ' '
                        buffer.append(f'! {phon_c}{phon}{padding}')
            elif op == 'HEADER':
                buffer.append(f'{delimit_c}{textwidth * body[0]}')
            elif op == 'ETYM':
                etym = body[0]
                if etym:
                    buffer.append(blank)
                    first_line, *rest = wrap_method(etym, self.ETYM.gaps, indent)
                    _format_push(self.ETYM.fl_fmt, first_line=first_line)
                    for line in rest:
                        _format_push(self.ETYM.l_fmt, line=line)
            elif op == 'POS':
                if body[0].strip(' |'):
                    buffer.append(blank)
                    for elem in body:
                        pos, phon = elem.split('|')
                        padding = (textwidth - len(pos) - len(phon) - self.POS.gaps) * ' '
                        _format_push(self.POS.fl_fmt, pos=pos, phon=phon, padding=padding)
            elif op == 'AUDIO':
                pass
            elif op == 'NOTE':
                note = body[0]
                padding = (textwidth + len(phrase_c) - len(note)) * ' '
                buffer.append(f'{R}{BOLD}{note}{DEFAULT}{padding}')
            else:
                raise AssertionError(f'unreachable dictionary operation: {op!r}')

        return buffer

    def prepare_to_print(
            self, colwidth: int, ncols: int, wrap_style: str, indent: int
    ) -> list[list[str]]:
        # Prepare content for printing. Return value of this function should be
        # passed to the `print_dictionary` method.
        formatted = self.format_dictionary(colwidth, wrap_style, indent)
        if ncols == 1:
            return [[line.lstrip('$!') for line in formatted]]
        else:
            return columnize(formatted, colwidth, ncols)

    def _format_title(self, textwidth: int) -> str:
        t = f'[ {BOLD}{self.title}{DEFAULT}{delimit_c} ]'
        esc_seq_len = len(BOLD) + len(DEFAULT) + len(delimit_c)
        return f'{delimit_c}{t.center(textwidth + esc_seq_len, HORIZONTAL_BAR)}'

    def print_dictionary(
            self, columns: list[list[str]], column_width: int, last_col_fill: int
    ) -> None:
        sys.stdout.write(
            self._format_title(column_width)
            + (len(columns) - 1) * ('┬' + column_width * HORIZONTAL_BAR)
            + last_col_fill * HORIZONTAL_BAR
            + '\n'
        )
        for line in zip_longest(*columns, fillvalue=column_width * ' '):
            if line[-1][0] == HORIZONTAL_BAR:
                sys.stdout.write(f"{delimit_c}│{R}".join(line) + last_col_fill * HORIZONTAL_BAR + '\n')
            else:
                sys.stdout.write(f"{delimit_c}│{R}".join(line) + '\n')
        sys.stdout.write('\n')

    def filter_contents(self, flags: Sequence[str]) -> None:
        flags = [x.replace(' ', '').replace('.', '').lower() for x in flags]

        if 'f' in flags or 'fsubdefs' in flags:
            self.contents = [instr for instr in self.contents if instr[0] != 'SUBDEF']
            flags = [flag for flag in flags if flag not in ('f', 'fsubdefs')]

        if not flags:
            return

        # We have to first build the list of [header_skip][label_skip], otherwise we
        # wouldn't be able to tell whether to include HEADER and PHRASE instructions.
        skips_in_headers: list[list[bool]] = [[]]
        for op, *body in self.contents:
            if op == 'LABEL':
                skips_in_headers[-1].append(should_skip(body[0], flags))
            elif op == 'HEADER':
                skips_in_headers.append([])

        if all(skip for header in skips_in_headers for skip in header):
            return

        # Example skips_in_headers: [[True, False], [False, False, True], [True]]
        # Change current skip state by moving
        # header cursor and label cursor through these skips.
        skip_state = all(skips_in_headers[0])
        result: list[Sequence[str]] = []
        header_cur = label_cur = 0
        for op, *body in self.contents:
            if op == 'LABEL':
                skip_state = skips_in_headers[header_cur][label_cur]
                label_cur += 1
                if skip_state:
                    continue
            elif op == 'HEADER':
                header_cur += 1
                skip_state = all(skips_in_headers[header_cur])
                label_cur = 0
            elif op in ('POS', 'ETYM'):
                skip_state = all(skips_in_headers[header_cur])

            if skip_state or (not result and op == 'HEADER'):
                continue
            result.append((op, *body))

        self.contents = result
