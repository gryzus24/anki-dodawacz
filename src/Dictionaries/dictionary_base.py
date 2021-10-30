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

from shutil import get_terminal_size

from src.Dictionaries.audio_dictionaries import diki_audio
from src.Dictionaries.utils import wrap_lines
from src.colors import R, BOLD, END, YEX, \
    def1_c, syn_c, exsen_c, pos_c, etym_c, phrase_c, \
    err_c, delimit_c
from src.commands import save_command
from src.data import config, labels, SEARCH_FLAGS


def expand_labels(label_set: set) -> set:
    # Expanding these sets offers more leeway when specifying flags
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


def evaluate_skip(labels_: set, flags: set) -> bool:
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
    # textwidth has to be a class attribute as it can be changed between dictionary lookups
    textwidth = config['textwidth'][0]

    def __init__(self):
        self.chosen_phrase = None
        self.chosen_audio_url = None
        self.usable_height = 24
        self.indent = config['indent'][0]

    def get_audio(self):
        audio_url = self.chosen_audio_url
        if audio_url is not None:
            return audio_url, audio_url.rsplit('/')[-1]

        print(f'{err_c.color}Słownik nie posiada audio dla {R}{self.chosen_phrase}\n'
              f'{YEX.color}Sprawdzam diki...')
        return diki_audio(self.chosen_phrase, '')

    def print(self, *args, end='\n', **kwargs):
        self.usable_height -= end.count('\n')

        if args:
            self.usable_height -= args[0].count('\n')
        print(*args, end=end, **kwargs)

    def print_title(self, title, end='\n'):
        title = f'[ {BOLD}{title}{END}{delimit_c.color} ]'
        magic_len = len(BOLD) + len(END) + len(delimit_c.color)
        self.print(
            f'{delimit_c.color}{title.center(self.textwidth + magic_len, self.HORIZONTAL_BAR)}', end=end
        )

    def display_card(self, field_values):
        # field coloring
        color_of = {
            'definicja': def1_c.color, 'synonimy': syn_c.color, 'przyklady': exsen_c.color,
            'phrase': phrase_c.color, 'zdanie': '', 'czesci_mowy': pos_c.color,
            'etymologia': etym_c.color, 'audio': '', 'sentence_audio': ''
        }
        self.manage_terminal_size()
        print(f'\n{delimit_c.color}{self.textwidth * self.HORIZONTAL_BAR}')

        try:
            for field_number, field in config['fieldorder'].items():
                formatted_lines = field_values[field].split('<br>')
                for line in formatted_lines:
                    sublines = wrap_lines(line, self.textwidth - 1).split('\n')
                    for subline in sublines:
                        print(f'{color_of[field]}{subline.center(self.textwidth)}')

                if field_number == config['fieldorder_d']:  # d = delimitation
                    print(f'{delimit_c.color}{self.textwidth * self.HORIZONTAL_BAR}')

            print(f'{delimit_c.color}{self.textwidth * self.HORIZONTAL_BAR}')
        except (NameError, KeyError):
            print(f'{err_c.color}\nDodawanie karty do pliku nie powiodło się\n'
                  f'Spróbuj przywrócić domyślne ustawienia pól wpisując {R}-fo default\n')
            return 1  # skip
        else:
            return 0

    def manage_terminal_size(self):
        current_term_width, self.usable_height = get_terminal_size()

        if config['textwidth'][1] == '* auto':
            if __class__.textwidth != current_term_width:
                save_command('textwidth', [current_term_width, '* auto'])
                __class__.textwidth = current_term_width
        else:
            __class__.textwidth = config['textwidth'][0]
            if __class__.textwidth > current_term_width:
                __class__.textwidth = current_term_width
