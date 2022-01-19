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

from src.Dictionaries.dictionary_base import Dictionary
from src.Dictionaries.utils import request_soup, wrap_and_pad
from src.colors import R, index_c, syn_c, syngloss_c, poslabel_c, err_c
from src.data import config
from src.input_fields import input_field


class WordNet(Dictionary):
    title = 'WordNet'
    name = 'wordnet'

    def format_dictionary(self, textwidth):
        # Available instructions:
        #   (SYN, synonyms, glosses, pos_label)

        buffer = []
        index = 0
        for op, *body in self.contents:
            if op == 'SYN':
                index += 1
                index_len = len(str(index))

                pos = body[2]
                pos_len = len(pos)
                first_line, *rest = wrap_and_pad(body[0], textwidth, pos_len + index_len + 2)
                buffer.append(f'{index_c}{index} {poslabel_c}{pos} {syn_c}{first_line}')
                for line in rest:
                    buffer.append(f'{syn_c}{line}')

                first_line, *rest = wrap_and_pad(body[1], textwidth, config['indent'][0] + index_len + 1)
                buffer.append(f'{index_len * " "} {syngloss_c}{first_line}')
                for line in rest:
                    buffer.append(f'{syngloss_c}{line}')
            else:
                assert False, f'unreachable wordnet operation: {op!r}'

        return buffer

    def input_cycle(self):
        chosen_synonyms, _ = input_field('syn')(self.synonyms, auto_choice='0')
        if chosen_synonyms is None:
            return None
        return {'syn': chosen_synonyms}


def ask_wordnet(query):
    wordnet = WordNet()
    if config['thes'] == '-':
        # without skipping
        return wordnet

    soup = request_soup('http://wordnetweb.princeton.edu/perl/webwn', {'s': query})
    if soup is None:
        return None

    header = soup.find('h3').text
    if header.startswith('Your') or header.startswith('Sorry'):
        print(f'{err_c}Could not find {R}"{query}"{err_c} on WordNet')
        return None

    for elem in soup.find_all('li'):
        elem = elem.text.replace('S:', '', 1).strip()
        temp = elem.split(')', 1)
        pos, temp = temp[0] + ')', temp[1].split('(', 1)
        syn = temp[0].strip()
        gloss = '(' + temp[1].rsplit(')', 1)[0].strip() + ')'

        wordnet.add('SYN', syn, gloss, pos)

    return wordnet
