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

from src.Dictionaries.utils import wrap_lines, get_textwidth
from src.colors import R, BOLD, END, def1_c, syn_c, exsen_c, pos_c, etym_c, phrase_c, \
    err_c, delimit_c, def2_c, defsign_c, index_c, phon_c, poslabel_c, inflection_c
from src.data import config, labels, SEARCH_FLAGS, WINDOWS, POSIX


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
    HORIZONTAL_BAR = '─'

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
            elif op == 'HEADER' and not body[0]:
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

    def get_positions_in_sections(self, choices, section_at='HEADER', choices_of='DEF', *, reverse=False):
        # Returns instruction's positions with respect to `self.contents` split at `section_at`
        # calculated from `choices` of `choices_of`.
        # Instruction of `section_at` should come before `choices_of`.
        # Otherwise, `reverse=True` may help.
        # If instruction from `section_at` is not present in `self.contents` return [1].

        locations = []
        section_no = 1 if reverse else 0
        for op, *_ in self.contents:
            if section_at in op:
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

    def format_title(self, title, textwidth):
        title = f'[ {BOLD}{title}{END}{delimit_c.color} ]'
        esc_seq_len = len(BOLD) + len(END) + len(delimit_c.color)
        return f'{delimit_c.color}{title.center(textwidth + esc_seq_len, self.HORIZONTAL_BAR)}\n'

    def print_dictionary(self):
        textwidth = get_textwidth()
        indent = config['indent'][0]
        show_exsen = config['showexsen']
        # buffering might reduce flicker on slow terminal emulators
        buffer = []
        communal_index = 0
        for op, *body in self.contents:
            # print(f'{op}\n\n{body}'); continue  # DEBUG
            if 'DEF' in op:
                communal_index += 1
                def_c = def1_c if communal_index % 2 else def2_c
                sign = ' ' if 'SUB' in op else '>'
                def_index_len = len(str(communal_index))
                def_tp = wrap_lines(body[0], textwidth, def_index_len, indent, 2)
                buffer.append(f'{defsign_c.color}{sign}{index_c.color}{communal_index} {def_c.color}{def_tp}\n')
                if show_exsen and len(body) > 1:
                    exsen = wrap_lines(body[1], textwidth, def_index_len, indent + 1, 2)
                    buffer.append(f'{def_index_len * " "}  {exsen_c.color}{exsen}\n')
            elif op == 'LABEL':
                label = body[0]
                if label:
                    buffer.append(f'\n {poslabel_c.color}{label}  {inflection_c.color}{body[1]}\n')
                else:
                    buffer.append('\n')
            elif op == 'HEADER':
                title = body[0]
                if title:
                    buffer.append(self.format_title(title, textwidth))
                else:
                    buffer.append(f'{delimit_c.color}{textwidth * self.HORIZONTAL_BAR}\n')
            elif op == 'PHRASE':
                buffer.append(f' {phrase_c.color}{body[0]}  {phon_c.color}{body[1]}\n')
            elif op == 'POS':
                if body[0]:
                    buffer.append('\n')
                    for pos_phon in body:
                        buffer.append(f' {pos_c.color}{f"{phon_c.color}  ".join(pos_phon)}\n')
            elif op == 'ETYM':
                etym = body[0]
                if etym:
                    buffer.append(f'\n {etym_c.color}{wrap_lines(etym, textwidth, 0, 1, 1)}\n')
            elif op == 'AUDIO':
                pass
            elif op == 'NOTE':
                buffer.append(f'{R}{body[0]}\n')
            else:
                assert False, f'unreachable dictionary operation: {op!r}'
        # colorama does not support `writelines`, so for colors to display
        # on Windows we have to first join the buffer and use plain `write`.
        sys.stdout.write(''.join(buffer) + '\n')

    def show(self):
        if not self.contents:
            return None

        try:
            if config['top']:
                # Clearing the screen also helps reduce flicker from printing everything at once.
                if WINDOWS:
                    subprocess.run(['cls'])
                elif POSIX:
                    sys.stdout.write('\033[?25l')  # Hide cursor
                    sys.stdout.flush()
                    subprocess.run(['clear', '-x'])  # I hope the `-x` option works on macOS.
                else:
                    sys.stdout.write(f'{err_c.color}Komenda {R}"-top on"{err_c.color} nieobsługiwana na {sys.platform!r}.\n')

            self.print_dictionary()
        finally:
            if POSIX:
                sys.stdout.write('\033[?25h')  # Show cursor
                sys.stdout.flush()

    def display_card(self, field_values):
        # field coloring
        color_of = {
            'def': def1_c.color, 'syn': syn_c.color, 'exsen': exsen_c.color,
            'phrase': phrase_c.color, 'pz': '', 'pos': pos_c.color,
            'etym': etym_c.color, 'audio': '', 'recording': '',
        }
        textwidth = get_textwidth()
        delimit = textwidth * self.HORIZONTAL_BAR

        print(f'\n{delimit_c.color}{delimit}')
        try:
            for field_number, field in config['fieldorder'].items():
                if field == '-':
                    continue

                for line in field_values[field].split('<br>'):
                    sublines = wrap_lines(line, textwidth).split('\n')
                    for subline in sublines:
                        print(f'{color_of[field]}{subline.center(textwidth)}')

                if field_number == config['fieldorder_d']:  # d = delimitation
                    print(f'{delimit_c.color}{delimit}')

            print(f'{delimit_c.color}{delimit}')
        except (NameError, KeyError):
            print(f'{err_c.color}\nDodawanie karty do pliku nie powiodło się\n'
                  f'Spróbuj przywrócić domyślne ustawienia pól wpisując {R}-fo default\n')
            return 1  # skip
        else:
            return 0
