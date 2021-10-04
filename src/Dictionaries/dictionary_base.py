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

import requests
from bs4 import BeautifulSoup

from src.Dictionaries.diki import get_audio_from_diki
from src.Dictionaries.utils import handle_connection_exceptions, wrap_lines
from src.colors import R, YEX, BOLD, END, \
    def1_c, syn_c, exsen_c, pos_c, etym_c, phrase_c, \
    err_c, delimit_c
from src.commands import save_commands
from src.data import config, labels, USER_AGENT, SEARCH_FLAGS

request_session = requests.Session()
request_session.headers.update(USER_AGENT)


@handle_connection_exceptions
def request_soup(url):
    reqs = request_session.get(url, timeout=10)
    reqs.encoding = 'UTF-8'
    return BeautifulSoup(reqs.text, 'lxml')


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

    @staticmethod
    def map_choices(mapping, choices) -> list:
        # example mapping = [0, 7, 16, 21]
        indexes = []
        for choice in choices:
            for i, elem in enumerate(mapping[1:]):
                if mapping[i] < choice <= elem:
                    if i in indexes:
                        break
                    indexes.append(i)
        return [0] if not indexes else indexes

    @staticmethod
    def choices_to_auto_choice(choices: list) -> str:
        fc = choices[0]
        if fc in (0, -1):
            return str(fc)
        return ','.join(map(str, choices))

    def _get_audio(self, phrase_, dict_name='Słownik', fallback_func=None):
        if phrase_ is None:
            phrase_ = self.chosen_phrase
            audio_url = self.chosen_audio_url
        else:
            if fallback_func is None:
                audio_url = None
            else:
                audio_url = fallback_func(phrase_)

        if audio_url is None:
            print(f'{err_c.color}{dict_name} nie posiada audio dla {R}{phrase_}\n'
                  f'{YEX.color}Sprawdzam diki...')
            return get_audio_from_diki(raw_phrase=phrase_, flag='')

        audiofile_name = audio_url.rsplit('/', 1)[-1]
        return audio_url, audiofile_name

    def print(self, *args, end='\n', **kwargs):
        self.usable_height -= end.count('\n')

        if args:
            self.usable_height -= args[0].count('\n')
        print(*args, end=end, **kwargs)

    def print_title(self, title):
        title = f'[ {BOLD}{title}{END}{delimit_c.color} ]'
        self.print(f'{delimit_c.color}{title.center(self.textwidth + 13, self.HORIZONTAL_BAR)}')

    def display_card(self, field_values):
        self.manage_terminal_size()
        # field coloring
        color_of = {
            'definicja': def1_c.color, 'synonimy': syn_c.color, 'przyklady': exsen_c.color,
            'phrase': phrase_c.color, 'zdanie': '', 'czesci_mowy': pos_c.color,
            'etymologia': etym_c.color, 'audio': '', 'sentence_audio': ''
        }
        try:
            print(f'\n{delimit_c.color}{self.textwidth * self.HORIZONTAL_BAR}')

            for field_number, field_name in config['fieldorder'].items():
                formatted_lines = field_values[field_name].replace('<br>', '\n').split('\n')
                for line in formatted_lines:
                    sublines = wrap_lines(line, term_width=self.textwidth).split('\n')
                    for subline in sublines:
                        print(f'{color_of[field_name]}{subline.center(self.textwidth)}')

                if field_number == config['fieldorder_d']:  # d = delimitation
                    print(f'{delimit_c.color}{self.textwidth * self.HORIZONTAL_BAR}')

            print(f'{delimit_c.color}{self.textwidth * self.HORIZONTAL_BAR}')
        except (NameError, KeyError):
            print(f'{err_c.color}\nDodawanie karty do pliku nie powiodło się\n'
                  f'Spróbuj przywrócić domyślne ustawienia pól wpisując {R}-fo default\n')
            return 1  # skip

    def manage_terminal_size(self):
        current_term_width, self.usable_height = get_terminal_size()

        if config['textwidth'][1] == '* auto':
            if __class__.textwidth != current_term_width:
                save_commands(entry='textwidth', value=[current_term_width, '* auto'])
                __class__.textwidth = current_term_width
        else:
            __class__.textwidth = config['textwidth'][0]
            if __class__.textwidth > current_term_width:
                __class__.textwidth = current_term_width
