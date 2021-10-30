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
from src.Dictionaries.input_fields import InputField
from src.Dictionaries.utils import wrap_lines, request_soup
from src.colors import \
    R, syn_c, poslabel_c, \
    syngloss_c, index_c, err_c
from src.data import field_config, config


class WordNet(Dictionary):
    name = 'wordnet'

    def __init__(self):
        super().__init__()
        self.synonyms = []

    def __repr__(self):
        return (f'{__class__}\n'
                f'{self.synonyms=}\n')

    def get_thesaurus(self, query):
        self.chosen_phrase = query
        if config['thes'] == '-':
            # without skipping
            return self

        syn_soup = request_soup('http://wordnetweb.princeton.edu/perl/webwn?s=' + query)
        if syn_soup is None:
            return None

        header = syn_soup.find('h3').text
        if header.startswith('Your') or header.startswith('Sorry'):
            print(f'{err_c.color}Nie znaleziono {R}"{query}"{err_c.color} na WordNecie')
            return None

        self.manage_terminal_size()
        self.print_title('WordNet')

        syn_elems = syn_soup.find_all('li')
        for index, ele in enumerate(syn_elems, start=1):
            ele = ele.text.replace('S:', '', 1).strip()
            temp = ele.split(')', 1)
            pos, temp = temp[0] + ')', temp[1].split('(', 1)
            syn = temp[0].strip()
            gloss = '(' + temp[1].rsplit(')', 1)[0].strip() + ')'

            self.synonyms.append(syn)

            silen = len(str(index))
            syn_tp = wrap_lines(syn, self.textwidth, silen, 1, 2 + len(str(pos)))
            gloss_tp = wrap_lines(gloss, self.textwidth, silen, 1, 1)

            self.print(f'{index_c.color}{index} {poslabel_c.color}{pos} {syn_c.color}{syn_tp}')
            self.print(f'{silen * " "} {syngloss_c.color}{gloss_tp}\n')

        if config['top']:
            print('\n' * (self.usable_height - 2))
        return self

    def input_cycle(self):
        syn_field = InputField(*field_config['synonyms'], connector=' | ')

        chosen_synonyms = syn_field.get_element(self.synonyms, auto_choice='0')
        if chosen_synonyms is None:
            return None

        if config['usyn'] and chosen_synonyms:
            chosen_synonyms.hide(self.chosen_phrase)

        return {'synonimy': chosen_synonyms.content}
