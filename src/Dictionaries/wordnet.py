from __future__ import annotations

from src.Dictionaries.dictionary_base import Dictionary
from src.Dictionaries.utils import request_soup
from src.colors import Color, R


def ask_wordnet(query: str) -> Dictionary | str:
    soup_or_error = request_soup('http://wordnetweb.princeton.edu/perl/webwn', {'s': query})
    if isinstance(soup_or_error, str):
        return soup_or_error
    else:
        soup = soup_or_error

    if soup.h3.text.startswith(('Your', 'Sorry')):
        return f'{Color.err}Could not find {R}"{query}"{Color.err} on WordNet'

    wordnet = Dictionary(name='wordnet')

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
