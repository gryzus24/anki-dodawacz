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
from src.Dictionaries.input_fields import input_field
from src.Dictionaries.utils import request_soup, wrap_lines
from src.colors import R, index_c, syn_c, syngloss_c, poslabel_c, err_c
from src.data import config


class WordNet(Dictionary):
    name = 'wordnet'

    def __init__(self):
        super().__init__()

    def print_dictionary(self):
        # Available instructions:
        #   (SYN, synonyms, glosses, pos_label)

        textwidth, ncols, last_col_fill = self._get_term_parameters()

        buffer = []
        communal_index = 0
        for op, *body in self.contents:
            if op == 'SYN':
                communal_index += 1
                index_len = len(str(communal_index))

                pos = body[2]
                pos_len = len(pos)
                wrapped_synonyms = wrap_lines(body[0], textwidth, index_len, pos_len + 2, pos_len + 2)
                padding = (textwidth - len(wrapped_synonyms[0]) - index_len - pos_len - 2) * ' '
                buffer.append(
                    f'{index_c}{communal_index} {poslabel_c}{pos} {syn_c}{wrapped_synonyms[0]}{padding}'
                )
                for subsyn in wrapped_synonyms[1:]:
                    padding = (textwidth - len(subsyn)) * ' '
                    buffer.append(f'{syn_c}{subsyn}{padding}')

                wrapped_glosses = wrap_lines(body[1], textwidth, index_len, 1, 1)
                padding = (textwidth - len(wrapped_glosses[0]) - index_len - 1) * ' '
                buffer.append(f'{index_len * " "} {syngloss_c}{wrapped_glosses[0]}{padding}')
                for rest in wrapped_glosses[1:]:
                    padding = (textwidth - len(rest)) * ' '
                    buffer.append(f'{syngloss_c}{rest}{padding}')
            else:
                assert False, f'unreachable wordnet operation: {op!r}'

        self._format_and_print_dictionary(buffer, textwidth, ncols, last_col_fill)

    def input_cycle(self):
        syn_field = input_field('syn', 'Wybierz synonimy', connector=' | ')
        chosen_synonyms, _ = syn_field(self.synonyms, auto_choice='0')
        if chosen_synonyms is None:
            return None
        return {'syn': chosen_synonyms}


def ask_wordnet(query):
    wordnet = WordNet()
    if config['thes'] == '-':
        # without skipping
        return wordnet

    soup = request_soup('http://wordnetweb.princeton.edu/perl/webwn?s=' + query)
    if soup is None:
        return None

    header = soup.find('h3').text
    if header.startswith('Your') or header.startswith('Sorry'):
        print(f'{err_c}Nie znaleziono {R}"{query}"{err_c} na WordNecie')
        return None

    wordnet.title = 'WordNet'
    for elem in soup.find_all('li'):
        elem = elem.text.replace('S:', '', 1).strip()
        temp = elem.split(')', 1)
        pos, temp = temp[0] + ')', temp[1].split('(', 1)
        syn = temp[0].strip()
        gloss = '(' + temp[1].rsplit(')', 1)[0].strip() + ')'

        wordnet.add(('SYN', syn, gloss, pos))

    return wordnet
