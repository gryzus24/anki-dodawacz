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

from src.Dictionaries.dictionary_base import Dictionary, request_soup
from src.Dictionaries.diki import get_audio_from_diki
from src.Dictionaries.input_fields import InputField
from src.Dictionaries.utils import wrap_lines, valid_index_or_zero
from src.colors import \
    R, \
    def1_c, \
    exsen_c, index_c, phrase_c, \
    err_c, delimit_c
from src.data import field_config, config


class FarlexIdioms(Dictionary):
    URL = 'https://idioms.thefreedictionary.com/'
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

    def get_dictionary(self, query, **kw):
        soup = request_soup(self.URL + query)
        relevant_content = soup.find('section', {'data-src': 'FarlexIdi'})
        if relevant_content is None:
            print(f'{err_c.color}Nie znaleziono {R}"{query}"{err_c.color} w Farlex Idioms')
            return None

        self.manage_terminal_size()

        last_phrase = ''
        content_blocks = relevant_content.find_all('div', class_=('ds-single', 'ds-list'), recursive=False)
        for blockindex, content_block in enumerate(content_blocks, start=1):
            # Gather idiom phrases
            idiom_phrase = content_block.find_previous_sibling('h2').text.strip()
            self.phrases.append(idiom_phrase)

            if last_phrase == idiom_phrase:
                self.print()
            else:
                last_phrase = idiom_phrase
                if blockindex == 1:
                    self.print_title('Farlex Idioms')
                else:
                    self.print(f'{delimit_c.color}{self.textwidth * self.HORIZONTAL_BAR}')
                self.print(f'  {phrase_c.color}{idiom_phrase}')

            # Gather definitions
            idiom_definition = content_block.find('span', class_='illustration', recursive=False)
            idiom_definition = idiom_definition.previous_element.lstrip('1234567890.').strip()
            self.definitions.append(idiom_definition)

            idiom_def_tp = wrap_lines(idiom_definition, self.textwidth, len(str(blockindex)), indent=self.indent - 1,
                                      gap=1)
            self.print(f'{index_c.color}{blockindex} {def1_c.color}{idiom_def_tp}')

            # Gather idiom examples
            illustrations = content_block.find_all('span', class_='illustration', recursive=False)
            temp = ''
            for illust in illustrations:
                illust = "'" + illust.text.strip() + "'"
                illust_tp = wrap_lines(illust, self.textwidth, len(str(blockindex)), indent=2 + self.indent, gap=3)
                self.print(f'{len(str(blockindex)) * " "} {index_c.color}- {exsen_c.color}{illust_tp}')
                temp += illust + '<br>'
            self.example_sentences.append(temp[:-4])

        if config['top']:
            print('\n' * (self.usable_height - 2))
        else:
            print()
        return self

    def input_cycle(self):
        def_field = InputField(**field_config['definitions'])
        exsen_field = InputField(**field_config['example_sentences'], spec_split='<br>')

        chosen_defs = def_field.get_element(self.definitions, auto_choice='1')
        if chosen_defs is None:
            return None

        choices = def_field.get_choices()
        fc = valid_index_or_zero(choices)
        self.chosen_phrase = self.phrases[fc]

        if config['udef'] and chosen_defs:
            chosen_defs.hide(self.chosen_phrase)

        auto_choice = self.choices_to_auto_choice(choices)

        chosen_exsen = exsen_field.get_element(self.example_sentences, auto_choice)
        if chosen_exsen is None:
            return None

        if config['uexsen'] and chosen_exsen:
            chosen_exsen.hide(self.chosen_phrase)

        return {
            'phrase': self.chosen_phrase,
            'definicja': chosen_defs.content,
            'przyklady': chosen_exsen.content
        }

    def get_audio(self):
        return get_audio_from_diki(self.chosen_phrase, flag='')
