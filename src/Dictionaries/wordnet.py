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

from src.Dictionaries.dictionary_base import Dictionary, format_title
from src.Dictionaries.utils import request_soup, wrap_and_pad
from src.colors import R, err_c, exsen_c, index_c, label_c, syn_c, syngloss_c
from src.input_fields import get_user_input


class WordNet(Dictionary):
    name = 'wordnet'

    # TODO: Merge WordNet's formatting logic with AH Dictionary's synonyms.
    def format_dictionary(self, textwidth: int, wrap_style: str, indent: int) -> list[str]:
        # Available instructions:
        #   (SYN, synonyms, glosses, pos_label)

        buffer = []
        wrap_method = wrap_and_pad(wrap_style, textwidth)
        index = 0
        for op, *body in self.contents:
            if op == 'SYN':
                index += 1
                index_len = len(str(index))

                synonyms, gloss, examples, pos = body
                first_line, *rest = wrap_method(synonyms, len(pos) + index_len + 2, 0)
                buffer.append(f'{index_c}{index} {label_c}{pos} {syn_c}{first_line}')
                for line in rest:
                    buffer.append(f'{syn_c}{line}')

                first_line, *rest = wrap_method(gloss, index_len + 1, 0)
                buffer.append(f'{index_len * " "} {syngloss_c}{first_line}')
                for line in rest:
                    buffer.append(f'{syngloss_c}{line}')

                for ex in examples.split('<br>'):
                    first_line, *rest = wrap_method(ex, index_len + 1, 1)
                    buffer.append(f'{index_len * " "} {exsen_c}{first_line}')
                    for line in rest:
                        buffer.append(f'{exsen_c}{line}')
            elif op == 'HEADER':
                buffer.append(format_title(textwidth, body[0]))
            else:
                raise AssertionError(f'unreachable wordnet operation: {op!r}')

        return buffer

    def input_cycle(self) -> dict[str, str] | None:
        syn_input = get_user_input('syn', self.synonyms, '0')
        if syn_input is None:
            return None
        return {'syn': syn_input.content}


def ask_wordnet(query: str) -> Dictionary:
    soup = request_soup('http://wordnetweb.princeton.edu/perl/webwn', {'s': query})
    if soup is None:
        return WordNet()

    if soup.h3.text.startswith(('Your', 'Sorry')):
        print(f'{err_c}Could not find {R}"{query}"{err_c} on WordNet')
        return WordNet()

    wordnet = WordNet()
    wordnet.add('HEADER', 'WordNet')
    for t in soup.find_all('li'):
        _, _, body = t.text.partition('(')
        pos, _, body = body.partition(')')
        syn, _, body = body.partition('(')
        gloss, _, examples = body.rpartition(')')

        wordnet.add(
            'SYN', syn.strip(),
            f'({gloss.strip()})',
            '<br>'.join(map(str.strip, examples.split(';'))),
            f'({pos})'
        )

    return wordnet
