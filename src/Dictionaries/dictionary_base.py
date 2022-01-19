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

import subprocess
import sys
from itertools import zip_longest
from shutil import get_terminal_size

from src.Dictionaries.utils import wrap_and_pad, get_config_terminal_size
from src.colors import (
    R, BOLD, DEFAULT, def1_c, exsen_c, pos_c, etym_c, phrase_c, err_c, syngloss_c,
    delimit_c, def2_c, defsign_c, index_c, phon_c, poslabel_c, inflection_c, syn_c
)
from src.data import (
    config, WINDOWS, POSIX, HORIZONTAL_BAR, ON_WINDOWS_CMD
)

COLOR_FORMATS = {
    'exsen_c': exsen_c,
    'defsign_c': defsign_c,
    'index_c': index_c,
    'phrase_c': phrase_c,
    'phon_c': phon_c,
    'pos_c': pos_c,
    'poslabel_c': poslabel_c,
    'inflection_c': inflection_c,
    'etym_c': etym_c,
    'syn_c': syn_c,
    'syngloss_c': syngloss_c,
    'R': R,
    'BOLD': BOLD,
    'DEFAULT': DEFAULT,
}
# Part of speech labels used to extend commonly used
# abbreviations so that full flags can be matched.
LABELS = {
    # These have to be len 1 iterables, as they are fed to the `set.update()` method.
    'adj': ('adjective',),
    'adv': ('adverb',),
    'conj': ('conjunction',),
    'defart': ('def',),
    'indef': ('indefart',),
    'interj': ('interjection',),
    'n': ('noun',),

    'pl': ('plural', 'pln', 'npl', 'noun'),
    'npl': ('plural', 'pl', 'pln', 'noun'),
    'pln': ('plural', 'npl', 'noun'),
    'plural': ('pln', 'npl', 'noun'),

    'prep': ('preposition',),
    'pron': ('pronoun',),

    # verbs shouldn't be expanded when in labels, -!v won't work
    # not all verbs are tr.v. or intr.v. ... etc.
    'v': ('verb',),

    'tr': ('transitive', 'trv', 'vtr', 'verb'),
    'trv': ('transitive', 'vtr', 'verb'),
    'vtr': ('transitive', 'trv', 'verb'),

    'intr': ('intransitive', 'intrv', 'vintr', 'verb'),
    'intrv': ('intransitive', 'vintr', 'verb'),
    'vintr': ('intransitive', 'intrv', 'verb'),

    'intr&trv': (
        'intransitive', 'transitive', 'v',
        'intrv', 'trv', 'vintr', 'vtr', 'verb'
    ),
    'tr&intrv': (
        'intransitive', 'transitive', 'v',
        'intrv', 'trv', 'vintr', 'vtr', 'verb'
    ),

    'aux': ('auxiliary', 'auxv'),
    'auxv': ('auxiliary',),

    'pref': ('prefix',),
    'suff': ('suffix',),
    'abbr': ('abbreviation',),
}


def expand_labels(label_set):
    for item in label_set.copy():
        try:
            label_set.update(LABELS[item])
        except KeyError:
            pass
    return label_set


def evaluate_skip(labels_, flags):
    labels_ = expand_labels(
        {x.replace(' ', '').replace('.', '').lower() for x in labels_}
    )
    skip = True
    for flag in flags:
        if flag.startswith('!'):
            skip = False
            for label in labels_:
                if label.startswith(flag[1:]):
                    return True
        else:
            for label in labels_:
                if label.startswith(flag):
                    return False
    return skip


class Dictionary:
    title = 'Dictionary'

    # (First line format, rest of lines)
    PHRASE_FMT = ('! {phrase_c}{phrase}  {phon_c}{phon}{padding}',)
    LABEL_FMT  = ('! {poslabel_c}{label}  {inflection_c}{inflections}{padding}',)
    DEF_FMT    = ('{defsign_c}{sign}{index_c}{index} {def_c}{first_line}', '${def_c}{line}',)
    EXSEN_FMT  = ('${index_pad}  {exsen_c}{first_line}', '${exsen_c}{line}',)
    POS_FMT    = (' {pos_c}{pos}  {phon_c}{phon}{padding}',)
    ETYM_FMT   = (' {etym_c}{first_line}', '${etym_c}{line}')

    def __init__(self):
        self.DEF_GAPS = self._gap_count(self.DEF_FMT[0])
        self.EXSEN_GAPS = self._gap_count(self.EXSEN_FMT[0])
        self.LABEL_GAPS = self._gap_count(self.LABEL_FMT[0])
        self.PHRASE_GAPS = self._gap_count(self.PHRASE_FMT[0])
        self.ETYM_GAPS = self._gap_count(self.ETYM_FMT[0])
        self.POS_GAPS = self._gap_count(self.POS_FMT[0])

        self.contents = []

    def __repr__(self):
        for op, *body in self.contents:
            sys.stdout.write(f'{op:7s}{body}\n')

    def add(self, op, body, *args):
        # Add an instruction to the dictionary.
        # Value must be a Sequence containing 2 or more fields:
        # ('OPERATION', 'BODY', ... )
        self.contents.append((op, body, *args))

    @property
    def phrases(self):
        r = [b[0] for op, *b in self.contents if op == 'PHRASE']
        return r if r else ['']

    @property
    def audio_urls(self):
        r = [b[0] for op, *b in self.contents if op == 'AUDIO']
        return r if r else ['']

    @property
    def synonyms(self):
        r = [b[0] for op, *b in self.contents if op == 'SYN']
        return r if r else ['']

    @property
    def definitions(self):
        r = [b[0] for op, *b in self.contents if 'DEF' in op]
        return r if r else ['']

    @property
    def example_sentences(self):
        r = [b[1] for op, *b in self.contents if 'DEF' in op]
        return r if r else ['']

    def _by_header(self, type_, method):
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
        return result if result else ['']

    @property
    def parts_of_speech(self):
        return self._by_header('POS', lambda x: '<br>'.join(map(' '.join, x)))

    @property
    def etymologies(self):
        return self._by_header('ETYM', lambda x: x[0])

    def to_auto_choice(self, choices, type_):
        # Convert a list of direct user inputs or inputs already passed through the
        # `get_positions_in_sections` method into a string based on what's in the Dictionary.
        ntype = 0
        for op, *_ in self.contents:
            if type_ in op:
                ntype += 1
        if not ntype:
            return '0'

        uniq_choices = sorted(set(choices))
        if ntype > 1 and ntype == len(uniq_choices) and uniq_choices == choices:
            return '-1'
        return ','.join(map(str, choices))

    def get_positions_in_sections(self, choices, from_within='HEADER', choices_of='DEF'):
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

    def _get_term_parameters(self):
        # Returns:
        #   column's text width,
        #   number of columns,
        #   division remainder used to fill the last column
        full_textwidth, height = get_config_terminal_size()
        approx_lines = sum(
            2 if op in ('LABEL', 'ETYM')
            or
            ('DEF' in op and body[1]) else 1
            for op, *body in self.contents
        )
        if approx_lines < height * 0.01 * config['colviewat'][0]:
            return full_textwidth, 1, 0

        ncols, state = config['columns']
        if state == '* auto':
            ncols = full_textwidth // 39
            for i in range(2, ncols + 1):
                if approx_lines // i < height:
                    ncols = i
                    break

        try:
            textwidth = full_textwidth // ncols
        except ZeroDivisionError:
            return full_textwidth, 1, 0
        else:
            remainder = full_textwidth % ncols
            if remainder < ncols - 1:
                return textwidth - 1, ncols, remainder + 1
            return textwidth, ncols, 0

    def format_title(self, textwidth):
        t = f'[ {BOLD}{self.title}{DEFAULT}{delimit_c} ]'
        esc_seq_len = len(BOLD) + len(DEFAULT) + len(delimit_c)
        return f'{delimit_c}{t.center(textwidth + esc_seq_len, HORIZONTAL_BAR)}'

    def _gap_count(self, fstring):
        n = fstring.count(' ')
        return n + 1 if '{sign}' in fstring else n

    def format_dictionary(self, textwidth):
        # Format self.contents' list of (op, body)
        # into wrapped, colored and padded body lines.
        # Available instructions:
        #  (DEF,    definition, example_sentence)
        #  (SUBDEF, definition, example_sentence)
        #  (LABEL,  pos label, additional_info)
        #  (PHRASE, phrase, phonetic_spelling)
        #  (HEADER, filling character)
        #  (POS,    [pos, phonetic_spelling], ...)
        #  (AUDIO,  audio_url)
        #  (NOTE,   note)

        blank = textwidth * ' '
        indent = config['indent'][0]

        buffer = []

        def _format_push(fmt, **kwargs):
            buffer.append(fmt.format(**kwargs, **COLOR_FORMATS))

        index = 0
        for op, *body in self.contents:
            # print(f'{op}\n{body}'); continue  # DEBUG
            if 'DEF' in op:
                index += 1
                def_c = def1_c if index % 2 else def2_c
                sign = ' ' if 'SUB' in op else '>'
                index_len = len(str(index))

                first_line, *rest = wrap_and_pad(body[0], textwidth, self.DEF_GAPS + index_len, indent)
                _format_push(self.DEF_FMT[0], sign=sign, index=index, def_c=def_c, first_line=first_line)
                for line in rest:
                    _format_push(self.DEF_FMT[1], def_c=def_c, line=line)

                if config['showexsen'] and body[1]:
                    for exsen in body[1].split('<br>'):
                        first_line, *rest = wrap_and_pad(exsen, textwidth, self.EXSEN_GAPS + index_len, indent + 1)
                        _format_push(self.EXSEN_FMT[0], index_pad=index_len * ' ', first_line=first_line)
                        for line in rest:
                            _format_push(self.EXSEN_FMT[1], line=line)
            elif op == 'LABEL':
                buffer.append(blank)
                label, inflections = body
                if label:
                    padding = (textwidth - len(label) - len(inflections) - self.LABEL_GAPS) * ' '
                    if padding:
                        _format_push(self.LABEL_FMT[0], label=label, inflections=inflections, padding=padding)
                    else:
                        padding = (textwidth - len(label) - 1) * ' '
                        buffer.append(f'! {poslabel_c}{label}{padding}')
                        padding = (textwidth - len(inflections) - 1) * ' '
                        buffer.append(f'! {inflection_c}{inflections}{padding}')
            elif op == 'PHRASE':
                phrase, phon = body
                padding = (textwidth - len(phrase) - len(phon) - self.PHRASE_GAPS) * ' '
                if padding:
                    _format_push(self.PHRASE_FMT[0], phrase=phrase, phon=phon, padding=padding)
                else:
                    wrapped = wrap_and_pad(phrase, textwidth - 1)
                    for line in wrapped:
                        buffer.append(f'! {phrase_c}{line}')
                    if phon:
                        padding = (textwidth - len(phon) - 1) * ' '
                        buffer.append(f'! {phon_c}{phon}{padding}')
            elif op == 'HEADER':
                buffer.append(f'{delimit_c}{textwidth * body[0]}')
            elif op == 'ETYM':
                etym = body[0]
                if etym:
                    buffer.append(blank)
                    first_line, *rest = wrap_and_pad(etym, textwidth, self.ETYM_GAPS, indent)
                    _format_push(self.ETYM_FMT[0], first_line=first_line)
                    for line in rest:
                        _format_push(self.ETYM_FMT[1], line=line)
            elif op == 'POS':
                if body[0]:
                    buffer.append(blank)
                    for pos, phon in body:
                        padding = (textwidth - len(pos) - len(phon) - self.POS_GAPS) * ' '
                        _format_push(self.POS_FMT[0], pos=pos, phon=phon, padding=padding)
            elif op == 'AUDIO':
                pass
            elif op == 'NOTE':
                note = body[0]
                padding = (textwidth + len(phrase_c) - len(note)) * ' '
                buffer.append(f'{R}{BOLD}{note}{DEFAULT}{padding}')
            else:
                assert False, f'unreachable dictionary operation: {op!r}'

        return buffer

    def print_dictionary_buffer(self, buffer, textwidth, ncols, last_col_fill):
        blank = textwidth * ' '
        header = 2 * HORIZONTAL_BAR
        buff_len = len(buffer)
        initial_col_height = buff_len // ncols + buff_len % ncols

        col_no = lines_to_move = 0
        cbreak = current_col_height = initial_col_height
        formatted = [[] for _ in range(ncols)]
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

        sys.stdout.write(
            self.format_title(textwidth)
            + (ncols - 1) * ('┬' + textwidth * HORIZONTAL_BAR)
            + last_col_fill * HORIZONTAL_BAR
            + '\n'
        )
        for line in zip_longest(*formatted, fillvalue=blank):
            if header in line[-1]:
                sys.stdout.write(f"{delimit_c}│{R}".join(line) + last_col_fill * HORIZONTAL_BAR + '\n')
            else:
                sys.stdout.write(f"{delimit_c}│{R}".join(line) + '\n')
        sys.stdout.write('\n')

    def filter_contents(self, flags):
        flags = {x.replace(' ', '').replace('.', '').lower() for x in flags}

        if config['fsubdefs'] or 'f' in flags or 'fsubdefs' in flags:
            i = 0
            while True:
                try:
                    op, *body = self.contents[i]
                except IndexError:
                    break
                if op == 'SUBDEF':
                    self.contents.pop(i)
                else:
                    i += 1
            flags.difference_update(('f', 'fsubdefs'))

        if config['fnolabel']:
            flags.add('')
        else:
            if not flags:
                return

        # We have to first build the "skip per label, per header" list, otherwise we
        # wouldn't be able to tell whether to include HEADER and PHRASE instructions.
        skips_in_headers = [[]]
        for op, *body in self.contents:
            if op == 'LABEL':
                s = evaluate_skip(set(body[0].split()), flags)
                skips_in_headers[-1].append(s)
            elif op == 'HEADER':
                skips_in_headers.append([])

        if all(skip for header in skips_in_headers for skip in header):
            return

        # Example skips_in_headers: [[True, False], [False, False, True], [True]]
        # Change current skip state by moving
        # header cursor and label cursor through these skips.
        skip_state = all(skips_in_headers[0])
        result = []
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

    def show(self, filter_flags=None):
        # High level method that does:
        #  - filter dictionary contents based on filter_flags and filter configuration.
        #  - move terminal cursor to the top.
        #  - print dictionary

        if filter_flags is None:
            filter_flags = []

        self.filter_contents(filter_flags)
        if not self.contents:
            return None

        try:
            if config['top']:
                if WINDOWS:
                    # There has to exist a less hacky way of doing `clear -x` on Windows.
                    # I'm not sure if it works on terminals other than cmd and WT
                    height = get_terminal_size().lines
                    if ON_WINDOWS_CMD:
                        # Move cursor up and down
                        h = height * '\n'
                        sys.stdout.write(f'{h}\033[{height}A')
                    else:
                        # Use Windows ANSI sequence to clear the screen
                        h = (height - 1) * '\n'
                        sys.stdout.write(f'{h}\033[2J')
                    sys.stdout.flush()
                elif POSIX:
                    # Even though `clear -x` is slower than using
                    # ANSI escapes it doesn't have flickering issues.
                    sys.stdout.write('\033[?25l')  # Hide cursor
                    sys.stdout.flush()
                    subprocess.run(['clear', '-x'])  # I hope the `-x` option works on macOS.
                else:
                    sys.stdout.write(f'{R}`-top on`{err_c} command unavailable on {sys.platform!r}\n')

            textwidth, ncols, last_col_fill = self._get_term_parameters()
            self.print_dictionary_buffer(
                self.format_dictionary(textwidth),
                textwidth,
                ncols,
                last_col_fill
            )
        finally:
            if POSIX:
                sys.stdout.write('\033[?25h')  # Show cursor
                sys.stdout.flush()
