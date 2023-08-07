from __future__ import annotations

from src.Dictionaries.base import Dictionary
from src.Dictionaries.base import DictionaryError
from src.Dictionaries.base import HEADER
from src.Dictionaries.base import LABEL
from src.Dictionaries.base import PHRASE
from src.Dictionaries.base import SYN
from src.Dictionaries.util import parse_response
from src.Dictionaries.util import prepare_check_text
from src.Dictionaries.util import try_request

DICTIONARY = 'WordNet'
DICTIONARY_URL = 'http://wordnetweb.princeton.edu/perl/webwn'


def ask_wordnet(query: str) -> Dictionary:
    soup = parse_response(try_request(DICTIONARY_URL, {'s': query}))

    h3_tag = soup.find('.//h3')
    if h3_tag is None:
        raise DictionaryError(f'ERROR: {DICTIONARY}: no header tag')

    check_text = prepare_check_text(DICTIONARY)

    h3_tag_text = check_text(h3_tag)
    if h3_tag_text.startswith(('Your', 'Sorry')):
        raise DictionaryError(f'{DICTIONARY}: {query!r} not found')

    wordnet = Dictionary()

    wordnet.add(HEADER(DICTIONARY))
    wordnet.add(PHRASE(query, ''))
    wordnet.add(LABEL(h3_tag_text, ''))
    for tag in h3_tag.itersiblings():
        if tag.tag == 'h3':
            wordnet.add(LABEL(check_text(tag), ''))
        elif tag.tag == 'ul':
            for li in tag.iterchildren('li'):
                li_text = ''.join(li.itertext())  # type: ignore[arg-type]
                _, _, body = li_text.partition('(')
                pos, _, body = body.partition(')')
                syn, _, body = body.partition('(')
                gloss, _, examples = body.rpartition(')')

                wordnet.add(
                    SYN(
                        syn.strip(),
                        f'({gloss.strip()})',
                        [x for x in map(str.strip, examples.split(';')) if x],
                    )
                )

    return wordnet
