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
from src.Dictionaries.input_fields import InputField
from src.Dictionaries.utils import wrap_lines
from src.colors import \
    R, syn_c, poslabel_c, \
    syngloss_c, index_c, err_c
from src.data import field_config, config


class WordNet(Dictionary):
    URL = 'http://wordnetweb.princeton.edu/perl/webwn?s='
    name = 'wordnet'

    def __init__(self):
        super().__init__()
        self.synonyms = []

    def __repr__(self):
        return (f'{__class__}\n'
                f'{self.synonyms=}\n')

    def get_thesaurus(self, query):
        self.chosen_phrase = query
        if config['thesaurus'] == '-':
            # without skipping
            return self

        syn_soup = request_soup(self.URL + query)
        header = syn_soup.find('h3').text
        if header.startswith('Your') or header.startswith('Sorry'):
            print(f'{err_c.color}Nie znaleziono {R}"{query}"{err_c.color} na WordNecie')
            return None

        self.manage_terminal_size()
        self.print_title('WordNet')

        syn_elems = syn_soup.find_all('li')
        for index, ele in enumerate(syn_elems, start=1):
            pos = '(' + ele.text.split(') ', 1)[0].split('(')[-1] + ')'
            syn = (ele.text.split(') ', 1)[-1].split(' (')[0]).strip()
            gloss = '(' + ((ele.text.rsplit(') ', 1)[0] + ')').strip('S: (').split(' (', 1)[-1])

            self.synonyms.append(syn)

            syn_tp = wrap_lines(syn, self.textwidth, len(str(index)), indent=1, gap=2 + len(str(pos)))
            gloss_tp = wrap_lines(gloss, self.textwidth, len(str(index)), indent=1, gap=1)

            self.print(f'{index_c.color}{index} {poslabel_c.color}{pos} {syn_c.color}{syn_tp}')
            self.print(f'{(len(str(index)) + 1) * " "}{syngloss_c.color}{gloss_tp}\n')

        if config['top']:
            print('\n' * (self.usable_height - 2))
        return self

    def input_cycle(self):
        syn_field = InputField(**field_config['synonyms'], connector=' | ', spec_split=',')

        chosen_synonyms = syn_field.get_element(self.synonyms, auto_choice='0')
        if chosen_synonyms is None:
            return None
        if config['hide_synonym_word'] and chosen_synonyms:
            chosen_synonyms.hide(self.chosen_phrase)

        return {'synonimy': chosen_synonyms.content}
