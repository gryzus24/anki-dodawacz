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
from itertools import chain, zip_longest
from typing import Any, Callable, Iterable, Optional, Sequence

from src.Dictionaries.utils import wrap_and_pad
from src.colors import (BOLD, DEFAULT, R, def1_c, def2_c, defsign_c, delimit_c, etym_c,
                        exsen_c, index_c, inflection_c, label_c, phon_c, phrase_c, pos_c,
                        syn_c, syngloss_c)
from src.data import HORIZONTAL_BAR


def multi_split(string: str, splits: set[str]) -> list[str]:
    # Splits a string at multiple places discarding redundancies just like `.split()`.
    result = []
    elem = ''
    for letter in string:
        if letter in splits:
            if elem:
                result.append(elem)
                elem = ''
        else:
            elem += letter
    if elem:
        result.append(elem)
    return result


def should_skip(labels: Sequence[str], flags: Iterable[str]) -> bool:
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


def columnize(buffer: Sequence[str], textwidth: int, height: int, ncols: int) -> list[list[str]]:
    longest_section = nheaders = _current = 0
    for line in buffer:
        if HORIZONTAL_BAR in line:
            _current = 0
            nheaders += 1
        else:
            _current += 1
            if _current > longest_section:
                longest_section = _current

    if longest_section < height and 1 < nheaders <= ncols:
        res: list[list[str]] = []
        for line in buffer:
            if HORIZONTAL_BAR in line:
                res.append([])
            res[-1].append(line.lstrip('$!'))
        return res

    blank = textwidth * ' '
    col_no = lines_to_move = 0
    _buff_len = len(buffer)
    col_break = _buff_len // ncols + _buff_len % ncols

    formatted: list[list[str]] = [[] for _ in range(ncols)]
    li = -1
    for line in buffer:
        control_symbol = line[0]
        line = line.lstrip('$!')
        li += 1

        if control_symbol == '!' or line == blank or HORIZONTAL_BAR in line:
            formatted[col_no].append(line)
            lines_to_move += 1
        elif li < col_break:
            formatted[col_no].append(line)
            lines_to_move = 0
        elif control_symbol == '$':
            formatted[col_no].append(line)
        elif line == blank and not lines_to_move:
            continue
        else:
            # start next column
            if lines_to_move:
                # This might produce an empty column which is removed before returning.
                for _i in range(-lines_to_move, 0):
                    swapped, formatted[col_no][_i] = formatted[col_no][_i], ''
                    if swapped == blank and _i == -lines_to_move:
                        continue
                    formatted[col_no + 1].append(swapped)

            lines_to_move = 0
            col_no += 1
            formatted[col_no].append(line)

            if not formatted[col_no] or HORIZONTAL_BAR not in formatted[col_no][0]:
                # Remove an empty header.
                if formatted[col_no][0].strip() == str(delimit_c):
                    del formatted[col_no][0]
                    li = -1
                else:
                    li = 0
                formatted[col_no].insert(0, f'{delimit_c}{textwidth * HORIZONTAL_BAR}')
            else:
                li = -1

    # filter out blank lines and columns, as they are not guaranteed to be of
    # uniform height and should be easily printable with the help of zip_longest.
    r = [[line for line in column if line] for column in formatted if column]
    if not r[0]:
        del r[0]
    return r


def format_title(textwidth: int, filling: str, title: str) -> str:
    title = f'{filling}[ {BOLD}{title}{DEFAULT}{delimit_c} ]'
    esc_seq_len = len(BOLD) + len(DEFAULT) + len(delimit_c)
    return f'{delimit_c}{title.ljust(textwidth + esc_seq_len, HORIZONTAL_BAR)}'


class FieldFormat(namedtuple('FieldFormat', ('fl_fmt', 'l_fmt', 'gaps'))):
    # Make it truly immutable.
    __slots__ = ()

    def __new__(
            cls, first_line_format: str,
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

    PHRASE = FieldFormat('! {phrase_c}{phrase}  {phon_c}{phon}')
    PHRASE_S = FieldFormat('! {phrase_c}{first_line}', '!{phrase_c}{line}')
    PHON_S = FieldFormat('! {phon_c}{first_line}', '!{phon_c}{line}')
    LABEL = FieldFormat('! {label_c}{label}  {inflection_c}{inflections}')
    LABEL_S = FieldFormat('! {label_c}{first_line}', '!{label_c}{line}')
    INFLECTIONS_S = FieldFormat('! {inflection_c}{first_line}', '!{inflection_c}{line}')
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
        return f'{type(self).__name__}()'

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
        r = ['{' + b[2] + '} ' + b[0] if b[2] else b[0]
             for op, *b in self.contents if 'DEF' in op]
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
        del result[0]
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

    def count(self, key: Callable[[Sequence[str]], bool]) -> int:
        # Count the number of key matches in `self.contents`.
        return sum(map(key, self.contents))

    def to_auto_choice(self, choices: Sequence[int], type_: str) -> str:
        # Convert a list of direct user inputs or inputs already passed through the
        # `get_positions_in_sections` method into a string based on what's in the Dictionary.
        ntype = self.count(lambda x: type_ in x[0])
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
            self, width: int, height: int, fold_at: float, ncolumns: Optional[int] = None
    ) -> tuple[int, int, int]:
        # width:  screen width in columns.
        # wrap_height:  wrap into columns when dictionary takes up this many rows.
        # columns:  number of columns: uint or None (auto).
        # Returns:
        #   individual column's width.
        #   number of columns.
        #   division remainder used to fill the last column.

        approx_lines = sum(
            2 if op in ('LABEL', 'ETYM') or ('DEF' in op and body[1]) else 1
            for op, *body in self.contents
        )
        if approx_lines < 0.01 * fold_at * height:
            return width, 1, 0

        if ncolumns is None:
            max_columns = width // 39
            nheaders = self.count(lambda x: x[0] == 'HEADER' and HORIZONTAL_BAR in x[1])
            if approx_lines < height and nheaders > 1:
                ncolumns = nheaders if nheaders < max_columns else max_columns
            else:
                for i in range(2, max_columns + 1):
                    if approx_lines // i < height:
                        ncolumns = i
                        break
                else:
                    ncolumns = max_columns

        try:
            column_width = width // ncolumns
        except ZeroDivisionError:
            return width, 1, 0
        else:
            remainder = width % ncolumns
            if remainder < ncolumns - 1:
                return column_width - 1, ncolumns, remainder + 1
            return column_width, ncolumns, 0

    def format_dictionary(self, textwidth: int, wrap_style: str, indent: int) -> list[str]:
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
        #  (NOTE,   'note')

        buffer = []

        def _push(fmt: str, **kwargs: Any) -> None:
            buffer.append(fmt.format(**kwargs, **COLOR_FORMATS))

        def _multi_push(*format_content: tuple[FieldFormat, str]) -> None:
            for _fmt, _c in format_content:
                if _c:
                    _fl, *_r = wrap_method(_c, _fmt.gaps, 0)
                    buffer.append(_fmt.fl_fmt.format(first_line=_fl, **COLOR_FORMATS))
                    for _l in _r:
                        buffer.append(_fmt.l_fmt.format(line=_l, **COLOR_FORMATS))

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
                _push(
                    self.DEF.fl_fmt,
                    sign=' ' if 'SUB' in op else '>',
                    index=index,
                    label=_label,
                    def_c=def_c,
                    first_line=first_line
                )
                for line in rest:
                    _push(self.DEF.l_fmt, def_c=def_c, line=line)

                if _exsen:
                    for ex in _exsen.split('<br>'):
                        first_line, *rest = wrap_method(ex, self.EXSEN.gaps + index_len, indent + 1)
                        _push(self.EXSEN.fl_fmt, index_pad=index_len * ' ', first_line=first_line)
                        for line in rest:
                            _push(self.EXSEN.l_fmt, line=line)
            elif op == 'LABEL':
                buffer.append(blank)
                label, inflections = body
                if label:
                    label_len = len(label) + self.LABEL.gaps
                    if label_len < textwidth:
                        first_line, *rest = wrap_method(inflections, label_len, 1 - label_len)
                        _push(self.LABEL.fl_fmt, label=label, inflections=first_line)
                        for line in rest:
                            _push(self.INFLECTIONS_S.l_fmt, line=line)
                    else:
                        _multi_push((self.LABEL_S, label), (self.INFLECTIONS_S, inflections))
            elif op == 'PHRASE':
                phrase, phon = body
                phrase_len = len(phrase) + self.PHRASE.gaps
                if phrase_len < textwidth:
                    first_line, *rest = wrap_method(phon, phrase_len, 1 - phrase_len)
                    _push(self.PHRASE.fl_fmt, phrase=phrase, phon=first_line)
                    for line in rest:
                        _push(self.PHON_S.l_fmt, line=line)
                else:
                    _multi_push((self.PHRASE_S, phrase), (self.PHON_S, phon))
            elif op == 'HEADER':
                filling, title = body
                if title:
                    buffer.append(format_title(textwidth, filling, title))
                else:
                    buffer.append(f'{delimit_c}{textwidth * filling}')
            elif op == 'ETYM':
                etym = body[0]
                if etym:
                    buffer.append(blank)
                    first_line, *rest = wrap_method(etym, self.ETYM.gaps, indent)
                    _push(self.ETYM.fl_fmt, first_line=first_line)
                    for line in rest:
                        _push(self.ETYM.l_fmt, line=line)
            elif op == 'POS':
                if body[0].strip(' |'):
                    buffer.append(blank)
                    for elem in body:
                        pos, phon = elem.split('|')
                        padding = (textwidth - len(pos) - len(phon) - self.POS.gaps) * ' '
                        _push(self.POS.fl_fmt, pos=pos, phon=phon, padding=padding)
            elif op == 'AUDIO':
                pass
            elif op == 'NOTE':
                note = body[0]
                padding = (textwidth + len(phrase_c) - len(note)) * ' '
                buffer.append(f'!{R}{BOLD}{note}{DEFAULT}{padding}')
            else:
                raise AssertionError(f'unreachable dictionary operation: {op!r}')

        return buffer

    def prepare_to_print(
            self, ncols: Optional[int], width: int, height: int,
            fold_at: float, wrap_style: str, indent: int
    ) -> tuple[zip_longest, int]:
        # Return value of this method should be passed to the `print_dictionary` method.
        column_width, ncols, last_col_fill = self.get_display_parameters(
            width, height, fold_at, ncols
        )
        formatted = self.format_dictionary(column_width, wrap_style, indent)
        if ncols == 1:
            columns = [[line.lstrip('$!') for line in formatted]]
        else:
            columns = columnize(formatted, column_width, height, ncols)

        return zip_longest(*columns, fillvalue=column_width * ' '), last_col_fill

    @staticmethod
    def print_dictionary(zipped_columns: zip_longest, last_col_fill: int) -> None:
        sys.stdout.write(
            f"{'┬'.join(next(zipped_columns))}{last_col_fill * HORIZONTAL_BAR}\n"
        )
        for line in zipped_columns:
            if line[-1][-1] == HORIZONTAL_BAR:
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

        # Builds a hierarchy of labels so that HEADERS are parents and LABELS,
        # DEFS and SUBDEFS their children.
        # TODO: Find a cleaner way of filtering with easier to manage rules.
        header_ptr = label_ptr = def_ptr = 0
        skip_mapping: list[set[str]] = []
        inclusive = not any(flag.startswith('!') for flag in flags)
        header_labels = ''
        for i, elem in enumerate(self.contents):
            op = elem[0]
            if op == 'HEADER':
                if elem[2]:
                    header_labels = self.contents[i][2]  # title
                # point all pointers to the header.
                header_ptr = label_ptr = def_ptr = i
                skip_mapping.append({header_labels})
                continue

            skip_mapping.append({header_labels})
            if op == 'DEF':
                def_ptr = i
                skips = elem[3]
                if inclusive:
                    skip_mapping[header_ptr].add(skips)
                    skip_mapping[label_ptr].add(skips)
                skip_mapping[def_ptr].add(skips)
                lc = self.contents[label_ptr]
                if lc[0] == 'LABEL':
                    skip_mapping[def_ptr].add(lc[1])
                hc = self.contents[header_ptr]
                if hc[0] == 'HEADER':
                    skip_mapping[def_ptr].add(hc[2])
            elif op == 'SUBDEF':
                skip_mapping[def_ptr].add(elem[3])
                skip_mapping[i].update(skip_mapping[def_ptr])
            elif op == 'LABEL':
                label_ptr = i
                skips = elem[1]
                if inclusive:
                    skip_mapping[header_ptr].add(skips)
                skip_mapping[label_ptr].add(skips)
                hc = self.contents[header_ptr]
                if hc[0] == 'HEADER':
                    skip_mapping[label_ptr].add(hc[2])
            elif op == 'AUDIO':
                # this is a hack to make it work with Lexico, as Lexico puts its
                # AUDIO instructions after definitions and just before etymologies.
                # We might say this is allowed as long as AUDIO instructions
                # immediately succeed definitions.
                skip_mapping[i] = skip_mapping[label_ptr]
            else:
                skip_mapping[i] = skip_mapping[header_ptr]

        result: list[Sequence[str]] = []
        for elem, skip_check in zip(self.contents, skip_mapping):
            labels = tuple(chain.from_iterable(
                map(lambda x: multi_split(x.lower(), {' ', '.', '&'}), skip_check)
            ))
            if not should_skip(labels, flags):
                result.append(elem)

        if result:
            if result[0][0] == 'HEADER':
                if not result[0][2]:  # title
                    result[0] = self.contents[0]
            else:
                result.insert(0, self.contents[0])

            self.contents = result
