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

from src.Dictionaries.dictionary_base import Dictionary
from src.Dictionaries.utils import request_soup
from src.colors import R, err_c
from src.input_fields import get_user_input


class FarlexIdioms(Dictionary):
    name = 'farlex'
    allow_thesaurus = False

    def input_cycle(self) -> dict[str, str] | None:
        def_input = get_user_input('def', self.definitions, '1')
        if def_input is None:
            return None

        phrase = self.phrases[
            self.get_positions_in_sections(def_input.choices, from_within='PHRASE')[0] - 1]

        exsen_input = get_user_input(
            'exsen', self.example_sentences, self.to_auto_choice(def_input.choices, 'DEF'))
        if exsen_input is None:
            return None

        return {
            'phrase': phrase,
            'def': def_input.content,
            'exsen': exsen_input.content
        }


def ask_farlex(query: str) -> Dictionary | None:
    soup = request_soup('https://idioms.thefreedictionary.com/' + query)
    if soup is None:
        return None

    relevant_content = soup.find('section', {'data-src': 'FarlexIdi'})
    if relevant_content is None:
        print(f'{err_c}Could not find {R}"{query}"{err_c} in Farlex Idioms')
        return None

    farlex = FarlexIdioms()
    last_phrase = ''
    content_blocks = relevant_content.find_all('div', class_=('ds-single', 'ds-list'), recursive=False)
    farlex.add('HEADER', 'Farlex Idioms')
    for content_block in content_blocks:
        # Gather idiom phrases
        idiom_phrase = content_block.find_previous_sibling('h2').text.strip()
        if last_phrase != idiom_phrase:
            last_phrase = idiom_phrase
            farlex.add('PHRASE', idiom_phrase, '')  # no phonetic spelling

        # Gather definitions
        definition = content_block.find('span', class_='illustration', recursive=False)
        # definition can be None if there are no examples
        if definition is None:
            definition = content_block.text.lstrip('1234567890.').strip()
        else:
            definition = definition.previous_element.lstrip('1234567890.').strip()

        # Gather idiom examples
        found_examples = content_block.find_all('span', class_='illustration', recursive=False)
        if found_examples:
            examples = '<br>'.join('‘' + e.text.strip() + '’' for e in found_examples)
        else:
            examples = ''

        farlex.add('DEF', definition, examples, '')
        farlex.add('LABEL', '', '')

    return farlex
