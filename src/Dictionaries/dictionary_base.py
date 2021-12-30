# Copyright 2021 Gryzus
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

from src.Dictionaries.utils import wrap_lines, get_config_terminal_size
from src.colors import R, BOLD, END, def1_c, syn_c, exsen_c, pos_c, etym_c, phrase_c, \
    err_c, delimit_c, def2_c, defsign_c, index_c, phon_c, poslabel_c, inflection_c
from src.data import config, labels, \
    SEARCH_FLAGS, WINDOWS, POSIX, HORIZONTAL_BAR, ON_WINDOWS_CMD


def expand_labels(label_set):
    # By expanding these sets we get more leeway when specifying flags
    for item in label_set.copy():
        try:
            label_set.update(labels[item])
        except KeyError:
            pass
    return label_set


def prepare_flags(flags):
    return {
        x.replace(' ', '').replace('.', '').lower()
        for x in flags
        if x.replace('!', '').replace(' ', '').replace('.', '').lower()
        not in SEARCH_FLAGS
    }


def evaluate_skip(labels_, flags):
    if not flags:
        return False

    labels_ = {x.replace(' ', '').replace('.', '').lower() for x in labels_}
    expanded_labels = expand_labels(labels_)

    inclusive = True
    for flag in flags:
        if flag.startswith('!'):
            inclusive = False
            for label in expanded_labels:
                if label.startswith(flag[1:]):
                    return True
        else:
            for label in expanded_labels:
                if label.startswith(flag):
                    return False
    if inclusive:
        return True
    return False


class Dictionary:
    title = 'Dictionary'

    def __init__(self):
        self.contents = []

    def __repr__(self):
        for op, *body in self.contents:
            print(f'{op:7s}{body}')

    def add(self, value):
        # Value must be a Sequence containing at least 2 fields:
        # ('OPERATION', 'BODY', ... )
        try:
            assert value[0] or value[1], 'no instruction specified'
        except IndexError:
            raise ValueError('instruction must contain at least 2 fields')
        else:
            self.contents.append(value)

    @property
    def phrases(self):
        return [b[0] for op, *b in self.contents if op == 'PHRASE']

    @property
    def audio_urls(self):
        return [b[0] for op, *b in self.contents if op == 'AUDIO']

    @property
    def synonyms(self):
        return [b[0] for op, *b in self.contents if op == 'SYN']

    @property
    def definitions(self):
        return [b[0] for op, *b in self.contents if 'DEF' in op]

    @property
    def example_sentences(self):
        return [body[1] if len(body) > 1 else '' for op, *body in self.contents if 'DEF' in op]

    def _by_header(self, type_, method=lambda x: x[0]):
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
    def parts_of_speech(self):
        return self._by_header('POS', lambda x: ' | '.join(map(lambda y: y[0], x)))

    @property
    def etymologies(self):
        return self._by_header('ETYM')

    def count_ops(self, type_):
        ntype = 0
        for op, *_ in self.contents:
            if type_ in op:
                ntype += 1
        return ntype

    def to_auto_choice(self, choices, type_):
        ntype = self.count_ops(type_)
        if not ntype:
            return '0'

        uniq_choices = sorted(set(choices))
        if ntype > 1 and ntype == len(uniq_choices) and uniq_choices == choices:
            return '-1'
        return ','.join(map(str, choices))

    def get_positions_in_sections(self, choices, from_within='HEADER', choices_of='DEF', *, expect_choice_first=False):
        # Returns instruction's positions with respect to `self.contents`
        # from within `from_within` calculated from `choices` of `choices_of`.
        # If `choices_of` always comes before `from_within` use expect_choice_first=True.
        # If instruction from `from_within` is not present in `self.contents` return [1].

        locations = []
        section_no = 1 if expect_choice_first else 0
        for op, *_ in self.contents:
            if from_within in op:
                section_no += 1
            elif choices_of in op:
                locations.append(section_no)

        result = []
        locations_len = len(locations)
        for choice in choices:
            if 0 < choice <= locations_len:
                index = locations[choice - 1]
                if index not in result:
                    result.append(index)

        return result if result and result[0] else [1]

    def format_title(self, textwidth):
        t = f'[ {BOLD}{self.title}{END}{delimit_c} ]'
        esc_seq_len = len(BOLD) + len(END) + len(delimit_c)
        return f'{delimit_c}{t.center(textwidth + esc_seq_len, HORIZONTAL_BAR)}'

    def _get_term_parameters(self):
        # Returns:
        #   column's text width,
        #   number of columns,
        #   division remainder used to fill the last column
        full_textwidth, height = get_config_terminal_size()
        approx_lines = sum(
            2 if op in ('LABEL', 'ETYM')
            or
            ('DEF' in op and len(body) > 1) else 1
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

    def _format_and_print_dictionary(self, buffer, textwidth, ncols, last_col_fill):
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

    def print_dictionary(self):
        # Available instructions:
        #  (DEF,    definition, example_sentence)
        #  (SUBDEF, definition, example_sentence)
        #  (LABEL,  pos label, additional_info)
        #  (PHRASE, phrase, phonetic_spelling)
        #  (HEADER, filling character)
        #  (POS,    [pos, phonetic_spelling], ...)
        #  (AUDIO,  audio_url)
        #  (NOTE,   note)

        textwidth, ncols, last_col_fill = self._get_term_parameters()

        blank = textwidth * ' '
        indent = config['indent'][0]
        show_exsen = config['showexsen']

        # TODO:
        #  Easier way to correctly wrap elements without having to
        #  hardcode padding values and iterate over wrapped lines[1:].
        buffer = []
        communal_index = 0
        for op, *body in self.contents:
            # print(f'{op}\n\n{body}'); continue  # DEBUG
            if 'DEF' in op:
                communal_index += 1
                def_c = def1_c if communal_index % 2 else def2_c
                sign = ' ' if 'SUB' in op else '>'
                def_index_len = len(str(communal_index))

                wrapped_def = wrap_lines(body[0], textwidth, def_index_len, indent, 2)
                padding = (textwidth - len(wrapped_def[0]) - def_index_len - 2) * ' '
                buffer.append(f'{defsign_c}{sign}{index_c}{communal_index} {def_c}{wrapped_def[0]}{padding}')
                for def_tp in wrapped_def[1:]:
                    padding = (textwidth - len(def_tp)) * ' '
                    buffer.append(f'${def_c}{def_tp}{padding}')

                if show_exsen and len(body) > 1:
                    wrapped_exsen = wrap_lines(body[1], textwidth, def_index_len, 3, 2)
                    padding = (textwidth - def_index_len - len(wrapped_exsen[0]) - 2) * ' '
                    buffer.append(f'${def_index_len * " "}  {exsen_c}{wrapped_exsen[0]}{padding}')
                    for exsen in wrapped_exsen[1:]:
                        padding = (textwidth - len(exsen)) * ' '
                        buffer.append(f'${exsen_c}{exsen}{padding}')
            elif op == 'LABEL':
                buffer.append(blank)
                label, inflections = body
                if label:
                    padding = (textwidth - len(label) - len(inflections) - 3) * ' '
                    if padding:
                        buffer.append(f'! {poslabel_c}{label}  {inflection_c}{inflections}{padding}')
                    else:
                        padding = (textwidth - len(label) - 1) * ' '
                        buffer.append(f'! {poslabel_c}{label}{padding}')
                        padding = (textwidth - len(inflections) - 1) * ' '
                        buffer.append(f'! {inflection_c}{inflections}{padding}')
            elif op == 'PHRASE':
                phrase, phon = body
                padding = (textwidth - len(phrase) - len(phon) - 3) * ' '
                if padding:
                    buffer.append(f'! {phrase_c}{phrase}  {phon_c}{phon}{padding}')
                else:
                    wrapped_phrase = wrap_lines(phrase, textwidth, 0, 0, 1)
                    padding = (textwidth - len(wrapped_phrase[0]) - 1) * ' '
                    buffer.append(f'! {phrase_c}{wrapped_phrase[0]}{padding}')
                    for phrase_line in wrapped_phrase[1:]:
                        padding = (textwidth - len(phrase_line) - 1) * ' '
                        buffer.append(f'! {phrase_c}{phrase_line}{padding}')
                    padding = (textwidth - len(phon) - 1) * ' '
                    if phon:
                        buffer.append(f'! {phon_c}{phon}{padding}')
            elif op == 'HEADER':
                buffer.append(f'{delimit_c}{textwidth * body[0]}')
            elif op == 'ETYM':
                etym = body[0]
                if etym:
                    buffer.append(blank)
                    wrapped_etym = wrap_lines(etym, textwidth, 0, 1, 1)
                    padding = (textwidth - len(wrapped_etym[0]) - 1) * ' '
                    buffer.append(f' {etym_c}{wrapped_etym[0]}{padding}')
                    for e in wrapped_etym[1:]:
                        padding = (textwidth - len(e)) * ' '
                        buffer.append(f'${etym_c}{e}{padding}')
            elif op == 'POS':
                if body[0]:
                    buffer.append(blank)
                    for pos, phon in body:
                        padding = (textwidth - len(pos) - len(phon) - 3) * ' '
                        buffer.append(f' {pos_c}{pos}  {phon_c}{phon}{padding}')
            elif op == 'AUDIO':
                pass
            elif op == 'NOTE':
                note = body[0]
                padding = (textwidth + len(phrase_c) - len(note)) * ' '
                buffer.append(f'{R}{BOLD}{note}{END}{padding}')
            else:
                assert False, f'unreachable dictionary operation: {op!r}'

        self._format_and_print_dictionary(buffer, textwidth, ncols, last_col_fill)

    def show(self):
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

            self.print_dictionary()
        finally:
            if POSIX:
                sys.stdout.write('\033[?25h')  # Show cursor
                sys.stdout.flush()

    @staticmethod
    def display_card(field_values):
        # field coloring
        color_of = {
            'def': def1_c, 'syn': syn_c, 'exsen': exsen_c,
            'phrase': phrase_c, 'pz': '', 'pos': pos_c,
            'etym': etym_c, 'audio': '', 'recording': '',
        }
        textwidth, _ = get_config_terminal_size()
        delimit = textwidth * HORIZONTAL_BAR

        print(f'\n{delimit_c}{delimit}')
        try:
            for field_number, field in config['fieldorder'].items():
                if field == '-':
                    continue

                for line in field_values[field].split('<br>'):
                    for subline in wrap_lines(line, textwidth):
                        print(f'{color_of[field]}{subline.center(textwidth)}')

                if field_number == config['fieldorder_d']:  # d = delimitation
                    print(f'{delimit_c}{delimit}')

            print(f'{delimit_c}{delimit}')
        except (NameError, KeyError):
            print(f'{err_c}\nCould not save the card to a file\n'
                  f'Try restoring the default field order {R}`-fo {{std|tsc}}`\n')
            return 1  # skip
        else:
            return 0
