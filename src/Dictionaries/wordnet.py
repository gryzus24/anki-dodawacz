from __future__ import annotations

from src.Dictionaries.dictionary_base import Dictionary, DictionaryError
from src.Dictionaries.util import request_soup


def ask_wordnet(query: str) -> Dictionary:
    soup = request_soup('http://wordnetweb.princeton.edu/perl/webwn', {'s': query})

    header_tag = soup.find('h3')
    if header_tag is None:
        raise DictionaryError('WordNet: unexpected error, no header_tag')

    if header_tag.text.startswith(('Your', 'Sorry')):
        raise DictionaryError(f'WordNet: {query!r} not found')

    wordnet = Dictionary(name='wordnet')

    wordnet.add('HEADER', 'WordNet')
    wordnet.add('PHRASE', query, '')
    wordnet.add('LABEL', '', '')
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
