from __future__ import annotations

from src.Dictionaries.base import (
    Dictionary,
    DictionaryError,
    DEF,
    LABEL,
    PHRASE,
    HEADER,
)
from src.Dictionaries.util import request_soup


def ask_farlex(query: str) -> Dictionary:
    soup = request_soup('https://idioms.thefreedictionary.com/' + query)

    relevant_content = soup.find('section', {'data-src': 'FarlexIdi'})
    if relevant_content is None:
        raise DictionaryError(f'Farlex: {query!r} not found')

    farlex = Dictionary()

    last_phrase = ''
    content_blocks = relevant_content.find_all('div', class_=('ds-single', 'ds-list'), recursive=False)  # type: ignore[union-attr]
    farlex.add(HEADER('Farlex Idioms'))
    for content_block in content_blocks:
        # Gather idiom phrases
        idiom_phrase = content_block.find_previous_sibling('h2').text.strip()
        if last_phrase != idiom_phrase:
            last_phrase = idiom_phrase
            farlex.add(PHRASE(idiom_phrase, ''))  # no phonetic spelling

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
            examples = [f'‘{e.text.strip()}’' for e in found_examples]
        else:
            examples = []

        farlex.add(DEF(definition, examples, '', subdef=False))
        farlex.add(LABEL('', ''))

    return farlex
