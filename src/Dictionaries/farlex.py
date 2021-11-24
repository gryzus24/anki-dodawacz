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

import sys

from src.Dictionaries.dictionary_base import Dictionary
from src.Dictionaries.input_fields import input_field
from src.Dictionaries.utils import request_soup, wrap_lines, get_textwidth
from src.colors import R, def1_c, def2_c, index_c, \
    exsen_c, defsign_c, phrase_c, phon_c, err_c
from src.data import config


class FarlexIdioms(Dictionary):
    name = 'farlex'
    allow_thesaurus = False

    def __init__(self):
        super().__init__()

    def print_dictionary(self):
        textwidth = get_textwidth()
        indent = config['indent'][0]
        show_exsen = config['showexsen']
        buffer = []
        communal_index = 0
        for op, *body in self.contents:
            if op == 'DEF':
                communal_index += 1
                def_c = def1_c if communal_index % 2 else def2_c
                def_index_len = len(str(communal_index))
                def_tp = wrap_lines(body[0], textwidth, def_index_len, indent, 1)
                buffer.append(f'{defsign_c.color}{index_c.color}{communal_index} {def_c.color}{def_tp}\n')
                if show_exsen and len(body) > 1:
                    for exsen in body[1].split('<br>'):
                        exsen = wrap_lines(exsen, textwidth, def_index_len, indent, 1)
                        buffer.append(f'{def_index_len * " "} {exsen_c.color}{exsen}\n')
            elif op == 'PHRASE':
                buffer.append(f'\n {phrase_c.color}{body[0]}  {phon_c.color}{body[1]}\n')
            elif op == 'HEADER':
                buffer.append(self.format_title(body[0], textwidth))
            else:
                assert False, f'unreachable farlex idioms operation: {op!r}'
        sys.stdout.write(''.join(buffer) + '\n')

    def input_cycle(self):
        def_field = input_field('def', 'Wybierz definicje')
        chosen_defs, def_choices = def_field(self.definitions, auto_choice='1')
        if chosen_defs is None:
            return None

        phrase_choice = self.get_positions_in_sections(def_choices, section_at='PHRASE')[0]
        phrase = self.phrases[phrase_choice - 1]

        auto_choice = self.to_auto_choice(def_choices, 'DEF')
        exsen_field = input_field('exsen', 'Wybierz przykłady', specifier_split='<br>')
        chosen_exsen, _ = exsen_field(self.example_sentences, auto_choice)
        if chosen_exsen is None:
            return None

        return {
            'phrase': phrase,
            'def': chosen_defs,
            'exsen': chosen_exsen
        }


def ask_farlex(query, **ignore):
    soup = request_soup('https://idioms.thefreedictionary.com/' + query)
    if soup is None:
        return None

    relevant_content = soup.find('section', {'data-src': 'FarlexIdi'})
    if relevant_content is None:
        print(f'{err_c.color}Nie znaleziono {R}"{query}"{err_c.color} w Farlex Idioms')
        return None

    farlex = FarlexIdioms()
    farlex.add(('HEADER', 'Farlex Idioms'))

    last_phrase = ''
    content_blocks = relevant_content.find_all('div', class_=('ds-single', 'ds-list'), recursive=False)
    for content_block in content_blocks:
        # Gather idiom phrases
        idiom_phrase = content_block.find_previous_sibling('h2').text.strip()
        if last_phrase != idiom_phrase:
            last_phrase = idiom_phrase
            farlex.add(('PHRASE', idiom_phrase, ''))  # no phonetic spelling

        # Gather definitions
        definition = content_block.find('span', class_='illustration', recursive=False)
        # definition can be None if there are no illustrations
        if definition is None:
            definition = content_block.text.lstrip('1234567890.').strip()
        else:
            definition = definition.previous_element.lstrip('1234567890.').strip()

        # Gather idiom examples
        illustrations = content_block.find_all('span', class_='illustration', recursive=False)
        exsen = ['‘' + illust.text.strip() + '’' for illust in illustrations]

        farlex.add(('DEF', definition, '<br>'.join(exsen)))

    return farlex
