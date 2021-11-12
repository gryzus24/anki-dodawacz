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

from src.Dictionaries.audio_dictionaries import diki_audio
from src.Dictionaries.dictionary_base import Dictionary
from src.Dictionaries.input_fields import InputField
from src.Dictionaries.utils import wrap_lines, request_soup
from src.colors import \
    R, \
    def1_c, \
    exsen_c, index_c, phrase_c, \
    err_c
from src.data import field_config, config


class FarlexIdioms(Dictionary):
    name = 'farlex'
    allow_thesaurus = False

    def __init__(self):
        super().__init__()
        self.phrases = []
        self.definitions = []
        self.example_sentences = []

    def __repr__(self):
        return (f'{__class__}\n'
                f'{self.phrases=}\n'
                f'{self.definitions=}\n'
                f'{self.example_sentences=}')

    def input_cycle(self):
        def_field = InputField(*field_config['definitions'])
        exsen_field = InputField(*field_config['example_sentences'], spec_split='<br>')

        chosen_defs = def_field.get_element(self.definitions, auto_choice='1')
        if chosen_defs is None:
            return None

        choices = def_field.get_choices()
        fc = choices.first_choice_or_zero
        self.chosen_phrase = self.phrases[fc]

        auto_choice = choices.as_exsen_auto_choice(self.example_sentences)
        chosen_exsen = exsen_field.get_element(self.example_sentences, auto_choice)
        if chosen_exsen is None:
            return None

        return {
            'def': chosen_defs,
            'exsen': chosen_exsen
        }

    def get_audio(self):
        return diki_audio(raw_phrase=self.chosen_phrase, flag='')


def ask_farlex(query, **kwargs):
    soup = request_soup('https://idioms.thefreedictionary.com/' + query)
    if soup is None:
        return None

    relevant_content = soup.find('section', {'data-src': 'FarlexIdi'})
    if relevant_content is None:
        print(f'{err_c.color}Nie znaleziono {R}"{query}"{err_c.color} w Farlex Idioms')
        return None

    farlex = FarlexIdioms()
    farlex.manage_terminal_size()
    farlex.print_title('Farlex Idioms', end='')

    last_phrase = ''
    content_blocks = relevant_content.find_all('div', class_=('ds-single', 'ds-list'), recursive=False)
    for blockindex, content_block in enumerate(content_blocks, start=1):
        # Gather idiom phrases
        idiom_phrase = content_block.find_previous_sibling('h2').text.strip()
        farlex.phrases.append(idiom_phrase)

        if last_phrase != idiom_phrase:
            last_phrase = idiom_phrase
            farlex.print(f'\n  {phrase_c.color}{idiom_phrase}')

        # Gather definitions
        idiom_definition = content_block.find('span', class_='illustration', recursive=False)
        # idiom_definition can be None if there are no illustrations
        if idiom_definition is None:
            idiom_definition = content_block.text.lstrip('1234567890.').strip()
        else:
            idiom_definition = idiom_definition.previous_element.lstrip('1234567890.').strip()
        farlex.definitions.append(idiom_definition)

        len_str_blockindex = len(str(blockindex))
        idiom_def_tp = wrap_lines(idiom_definition, farlex.textwidth, len_str_blockindex, farlex.indent - 1, 1)
        farlex.print(f'{index_c.color}{blockindex} {def1_c.color}{idiom_def_tp}')

        # Gather idiom examples
        illustrations = content_block.find_all('span', class_='illustration', recursive=False)
        temp = []
        for illust in illustrations:
            illust = "'" + illust.text.strip() + "'"
            temp.append(illust)
            if config['showexsen']:
                illust_tp = wrap_lines(illust, farlex.textwidth, len_str_blockindex, farlex.indent, 1)
                farlex.print(f'{len_str_blockindex * " "} {exsen_c.color}{illust_tp}')
        farlex.example_sentences.append('<br>'.join(temp))

    if config['top']:
        print('\n' * (farlex.usable_height - 2))
    else:
        print()
    return farlex
