from __future__ import annotations

from src.Dictionaries.base import DEF
from src.Dictionaries.base import Dictionary
from src.Dictionaries.base import DictionaryError
from src.Dictionaries.base import HEADER
from src.Dictionaries.base import LABEL
from src.Dictionaries.base import PHRASE
from src.Dictionaries.util import parse_response
from src.Dictionaries.util import prepare_check_tail
from src.Dictionaries.util import prepare_check_text
from src.Dictionaries.util import quote_example
from src.Dictionaries.util import try_request

DICTIONARY = 'Farlex'
DICTIONARY_URL = 'https://idioms.thefreedictionary.com'
LSTRIP_CHARS = '1234567890. '


def ask_farlex(query: str) -> Dictionary:
    soup = parse_response(try_request(f'{DICTIONARY_URL}/{query}'))

    section_farlex_idi = soup.find('.//section[@data-src="FarlexIdi"]')
    if section_farlex_idi is None:
        raise DictionaryError(f'{DICTIONARY}: {query!r} not found')

    farlex = Dictionary()
    check_text = prepare_check_text(DICTIONARY)
    check_tail = prepare_check_tail(DICTIONARY)

    farlex.add(HEADER(f'{DICTIONARY} Idioms'))
    for tag in section_farlex_idi.iter('h2', 'div'):
        if tag.tag == 'h2':
            farlex.add(PHRASE(check_text(tag), ''))  # no phonetic spelling
        elif (tag_clas := tag.get('class')) in ('ds-single', 'ds-list'):
            i_tag = tag.find('./i')
            if i_tag is None:
                label = ''
                definition = check_text(tag).lstrip(LSTRIP_CHARS)
            elif tag.text is None or not tag.text.lstrip(LSTRIP_CHARS):
                label = check_text(i_tag)
                definition = check_tail(i_tag)
            else:
                label = ''
                definition = tag.text
                for i_i_tag in tag.iter('i'):
                    definition += check_text(i_i_tag) + check_tail(i_i_tag)

            examples = [
                quote_example(check_text(x))
                for x in tag.findall('./span[@class="illustration"]')
            ]
            farlex.add(DEF(definition, examples, label, subdef=False))
            farlex.add(LABEL('', ''))  # padding
        elif tag.tag == 'div' and tag_clas is None:
            i_tag = tag.find('./i')
            if i_tag is not None:
                farlex.add(LABEL(check_text(i_tag), ''))

    return farlex
