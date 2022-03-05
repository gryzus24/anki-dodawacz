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
from itertools import chain, zip_longest
from typing import Callable, Optional, Sequence

from src.Dictionaries.utils import wrap_and_pad
from src.colors import (
    BOLD, DEFAULT, R, def1_c, def2_c, delimit_c, etym_c, exsen_c,
    index_c, inflection_c, label_c, phon_c, phrase_c, pos_c, sign_c,
    syn_c, syngloss_c
)
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


def should_skip(labels: tuple[str, ...], flags: tuple[str, ...]) -> bool:
    for label in labels:
        if label.startswith(flags):
            return False
    for flag in flags:
        if flag.startswith(labels):
            return False
    return True


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


def format_title(textwidth: int, title: str) -> str:
    title = f'{HORIZONTAL_BAR}[ {BOLD}{title}{DEFAULT}{delimit_c} ]'
    esc_seq_len = len(BOLD) + len(DEFAULT) + len(delimit_c)
    return f'{delimit_c}{title.ljust(textwidth + esc_seq_len, HORIZONTAL_BAR)}'


class Dictionary:
    allow_thesaurus: bool
    name: str  # name in config

    def __init__(self, contents: Optional[list[Sequence[str]]] = None) -> None:
        self.contents: list[Sequence[str]] = []
        if contents is not None:
            # Add in a loop to ensure instructions are valid.
            for x in contents:
                self.add(*x)

    def __repr__(self) -> str:
        for op, *body in self.contents:
            sys.stdout.write(f'{op:7s}{body}\n')
        sys.stdout.write('\n')
        return f'{type(self).__name__}({self.contents})'

    # For subclassing.
    def input_cycle(self) -> dict[str, str] | None:
        raise NotImplementedError

    def add(self, op: str, body: str, *args: str) -> None:
        # Add an instruction to the dictionary.
        # Value must be a Sequence containing 2 or more fields:
        # ('OPERATION', 'BODY', ... )
        # Particular care must be taken when adding elements meant to encompass
        # other elements, as is the case with AUDIO and DEF instructions. If the
        # encompassing instruction's body is empty it has to be added by the
        # virtue of providing a toehold for other non-empty AUDIO instructions
        # to preserve the integrity of later children element's extraction.
        self.contents.append((op.upper(), body, *args))

    @property
    def phrases(self) -> list[str]:
        r = [x[1] for x in self.contents if x[0] == 'PHRASE']
        return r if r else ['']

    @property
    def audio_urls(self) -> list[str]:
        r = [x[1] for x in self.contents if x[0] == 'AUDIO']
        if not r:
            return ['']
        if all(r):
            return r
        auset = set(filter(None, r))
        if len(auset) == 1:
            return [auset.pop()] * len(r)
        return r

    @property
    def synonyms(self) -> list[str]:
        r = [x[1] for x in self.contents if x[0] == 'SYN']
        return r if r else ['']

    @property
    def definitions(self) -> list[str]:
        r = ['{' + x[3] + '} ' + x[1] if x[3] else x[1]
             for x in self.contents if 'DEF' in x[0]]
        return r if r else ['']

    @property
    def example_sentences(self) -> list[str]:
        r = [x[2] for x in self.contents if 'DEF' in x[0]]
        return r if r else ['']

    @property
    def parts_of_speech(self) -> list[str]:
        # ['pos|phon', 'pos1|phon1'] -> 'pos phon<br>pos1 phon1'
        r = ['<br>'.join(x.replace('|', ' ') for x in b)
             for op, *b in self.contents if op == 'POS']
        return r if r else ['']

    @property
    def etymologies(self) -> list[str]:
        r = [x[1] for x in self.contents if x[0] == 'ETYM']
        return r if r else ['']

    def count(self, key: Callable[[Sequence[str]], bool]) -> int:
        # Count the number of key matches in `self.contents`.
        return sum(map(key, self.contents))

    def to_auto_choice(self, choices: Sequence[int], type_: str) -> str:
        # Convert a list of direct user inputs or inputs already passed through the
        # `get_positions_in_sections` method into a string based on what's in the Dictionary.
        ntype = self.count(lambda x: type_ in x[0])
        if not ntype:
            return '0'

        nchoices = len(choices)
        if 1 < ntype == nchoices and all(
                map(lambda x, y: x == y, choices, range(1, ntype + 1))):
            return '-1'
        elif nchoices > ntype:
            return ','.join(map(str, filter(lambda x: x <= ntype, choices)))
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
        for x in self.contents:
            if choices_of in x[0]:
                section_no = 1
                break
            if from_within in x[0]:
                section_no = 0
                break
        else:
            return [1]

        section_no_per_choice = []
        for x in self.contents:
            if from_within in x[0]:
                section_no += 1
            elif choices_of in x[0]:
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
            3 if op == 'SYN' else
            2 if op in ('LABEL', 'ETYM') or ('DEF' in op and body[1])
            else 1
            for op, *body in self.contents
        )
        if approx_lines < 0.01 * fold_at * height:
            return width, 1, 0

        if ncolumns is None:
            max_columns = width // 39
            nheaders = self.count(lambda x: x[0] == 'HEADER')
            if approx_lines < height and nheaders > 1:
                ncolumns = nheaders if nheaders < max_columns else max_columns
            else:
                for i in range(2, max_columns + 1):
                    if approx_lines // i < 0.8 * height:
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

    def format_dictionary(
            self, textwidth: int, wrap_style: str, indent: int, signed: bool
    ) -> list[str]:
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

        buffer = []
        blank = textwidth * ' '
        wrap_method = wrap_and_pad(wrap_style, textwidth)

        def _push_chain(_s1: str, _c1: str, _s2: str, _c2: str) -> None:
            _first_line, *_rest = wrap_method(f'{_s1} \0{_s2}', 1, 0)
            if '\0' in _first_line:
                _first_line = _first_line.replace('\0', ' ' + _c2)
                current_color = _c2
            else:
                current_color = _c1
            buffer.append(f'! {_c1}{_first_line}')
            for _line in _rest:
                if '\0' in _line:
                    _line = _line.replace('\0', ' ' + _c2)
                    buffer.append(f'!{current_color}{_line}')
                    current_color = _c2
                else:
                    buffer.append(f'!{current_color}{_line}')

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

                if signed:
                    _def_s = f"{sign_c}{' ' if 'SUB' in op else '>'}"
                    gaps = 2
                else:
                    _def_s = ''
                    gaps = 1

                first_line, *rest = wrap_method(
                    _def, gaps + index_len + label_len, indent - label_len
                )
                def_c = def1_c if index % 2 else def2_c
                buffer.append(f'{_def_s}{index_c}{index} {label_c}{_label}{def_c}{first_line}')
                for line in rest:
                    buffer.append(f'${def_c}{line}')

                if _exsen:
                    for ex in _exsen.split('<br>'):
                        first_line, *rest = wrap_method(ex, gaps + index_len - 1, 1 + indent)
                        buffer.append(f'${index_len * " "}{(gaps - 1) * " "}{exsen_c}{first_line}')
                        for line in rest:
                            buffer.append(f'${exsen_c}{line}')
            elif op == 'LABEL':
                buffer.append(blank)
                label, inflections = body
                if label:
                    if inflections:
                        _push_chain(label, str(label_c), inflections, str(inflection_c))
                    else:
                        first_line, *rest = wrap_method(label, 1, 0)
                        buffer.append(f'! {label_c}{first_line}')
                        for line in rest:
                            buffer.append(f'!{label_c}{line}')
            elif op == 'PHRASE':
                phrase, phon = body
                if phon:
                    _push_chain(phrase, str(phrase_c), phon, str(phon_c))
                else:
                    first_line, *rest = wrap_method(phrase, 1, 0)
                    buffer.append(f'! {phrase_c}{first_line}')
                    for line in rest:
                        buffer.append(f'!{phrase_c}{line}')
            elif op == 'HEADER':
                title = body[0]
                if title:
                    buffer.append(format_title(textwidth, title))
                else:
                    buffer.append(f'{delimit_c}{textwidth * HORIZONTAL_BAR}')
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
                note = body[0]
                padding = (textwidth + len(phrase_c) - len(note)) * ' '
                buffer.append(f'!{R}{BOLD}{note}{DEFAULT}{padding}')
            else:
                raise AssertionError(f'unreachable dictionary operation: {op!r}')

        return buffer

    def prepare_to_print(
            self, ncols: Optional[int], width: int, height: int,
            fold_at: float, wrap_style: str, indent: int, signed: bool
    ) -> tuple[zip_longest, int]:
        # Return value of this method should be passed to the `print_dictionary` method.
        column_width, ncols, last_col_fill = self.get_display_parameters(
            width, height, fold_at, ncols
        )
        formatted = self.format_dictionary(column_width, wrap_style, indent, signed)
        if ncols == 1:
            columns = [[line.lstrip('$!') for line in formatted]]
        else:
            columns = columnize(formatted, column_width, height, ncols)

        return zip_longest(*columns, fillvalue=column_width * ' '), last_col_fill

    @staticmethod
    def print_dictionary(zipped_columns: zip_longest, last_col_fill: int) -> None:
        hbfill = last_col_fill * HORIZONTAL_BAR
        sys.stdout.write(
            f"{'┬'.join(next(zipped_columns))}{hbfill}\n"
        )
        for line in zipped_columns:
            if line[-1][-1] == HORIZONTAL_BAR:
                sys.stdout.write(f"{delimit_c}│{R}".join(line) + hbfill + '\n')
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
        header_labels = ''
        for i, elem in enumerate(self.contents):
            op = elem[0]
            if op == 'HEADER':
                if elem[1]:
                    header_labels = self.contents[i][1]  # title
                # point all pointers to the header.
                header_ptr = label_ptr = def_ptr = i
                skip_mapping.append({header_labels})
                continue

            skip_mapping.append({header_labels})
            if op == 'DEF':
                def_ptr = i
                skips = elem[3]
                skip_mapping[header_ptr].add(skips)
                skip_mapping[label_ptr].add(skips)
                skip_mapping[def_ptr].add(skips)
                lc = self.contents[label_ptr]
                if lc[0] == 'LABEL':
                    skip_mapping[def_ptr].add(lc[1])
                hc = self.contents[header_ptr]
                if hc[0] == 'HEADER':
                    skip_mapping[def_ptr].add(hc[1])
            elif op == 'SUBDEF':
                skip_mapping[def_ptr].add(elem[3])
                skip_mapping[i].update(skip_mapping[def_ptr])
            elif op == 'LABEL':
                label_ptr = i
                skips = elem[1]
                skip_mapping[header_ptr].add(skips)
                skip_mapping[label_ptr].add(skips)
                hc = self.contents[header_ptr]
                if hc[0] == 'HEADER':
                    skip_mapping[label_ptr].add(hc[1])
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
            labels = chain.from_iterable(
                map(lambda x: multi_split(x.lower(), {' ', '.', '&'}), skip_check)
            )
            if not should_skip(tuple(labels), tuple(flags)):
                result.append(elem)

        if result:
            if result[0][0] == 'HEADER':
                if not result[0][1]:  # title
                    result[0] = self.contents[0]
            else:
                result.insert(0, self.contents[0])

            self.contents = result
