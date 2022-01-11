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

from src.Dictionaries.dictionary_base import Dictionary
from src.Dictionaries.utils import request_soup, wrap_and_pad
from src.colors import R, def1_c, def2_c, index_c, exsen_c, phrase_c, err_c
from src.data import config
from src.input_fields import input_field


class FarlexIdioms(Dictionary):
    name = 'farlex'
    allow_thesaurus = False

    def __init__(self):
        super().__init__()

    def print_dictionary(self):
        textwidth, ncols, last_col_fill = self._get_term_parameters()

        indent = config['indent'][0]
        show_exsen = config['showexsen']

        buffer = []
        communal_index = 0
        for op, *body in self.contents:
            if op == 'DEF':
                communal_index += 1
                def_c = def1_c if communal_index % 2 else def2_c
                def_index_len = len(str(communal_index))

                first_line, *rest = wrap_and_pad(body[0], textwidth, def_index_len, indent -1, 1)
                buffer.append(f'{index_c}{communal_index} {def_c}{first_line}')
                for def_tp in rest:
                    buffer.append(f'${def_c}{def_tp}')

                if show_exsen and body[1]:
                    for exsen in body[1].split('<br>'):
                        first_line, *rest = wrap_and_pad(exsen, textwidth, def_index_len, 2, 1)
                        buffer.append(f'${def_index_len * " "} {exsen_c}{first_line}')
                        for wrapped_line in rest:
                            buffer.append(f'${exsen_c}{wrapped_line}')
            elif op == 'PHRASE':
                wrapped = wrap_and_pad(body[0], textwidth - 1, 0, 0, 0)
                for phrase_chunk in wrapped:
                    buffer.append(f'! {phrase_c}{phrase_chunk}')
            elif op == 'HEADER':
                buffer.append(textwidth * body[0])
            else:
                assert False, f'unreachable farlex idioms operation: {op!r}'

        self._format_and_print_dictionary(buffer, textwidth, ncols, last_col_fill)

    def input_cycle(self):
        chosen_defs, def_choices = input_field('def')(self.definitions, auto_choice='1')
        if chosen_defs is None:
            return None

        phrase_choice = self.get_positions_in_sections(def_choices, from_within='PHRASE')[0]
        phrase = self.phrases[phrase_choice - 1]

        auto_choice = self.to_auto_choice(def_choices, 'DEF')
        chosen_exsen, _ = input_field('exsen')(self.example_sentences, auto_choice)
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
        print(f'{err_c}Could not find {R}"{query}"{err_c} in Farlex Idioms')
        return None

    farlex = FarlexIdioms()
    farlex.title = 'Farlex Idioms'

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
        # definition can be None if there are no examples
        if definition is None:
            definition = content_block.text.lstrip('1234567890.').strip()
        else:
            definition = definition.previous_element.lstrip('1234567890.').strip()

        # Gather idiom examples
        examples = content_block.find_all('span', class_='illustration', recursive=False)
        if examples:
            examples = '<br>'.join('‘' + e.text.strip() + '’' for e in examples)
        else:
            examples = ''

        farlex.add(('DEF', definition, examples))
        farlex.add(('HEADER', ' '))

    return farlex
