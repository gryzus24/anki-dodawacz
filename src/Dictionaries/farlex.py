from __future__ import annotations

from src.Dictionaries.dictionary_base import Dictionary
from src.Dictionaries.utils import request_soup
from src.colors import Color, R


def ask_farlex(query: str) -> Dictionary | str:
    soup_or_error = request_soup('https://idioms.thefreedictionary.com/' + query)
    if isinstance(soup_or_error, str):
        return soup_or_error
    else:
        soup = soup_or_error

    relevant_content = soup.find('section', {'data-src': 'FarlexIdi'})
    if relevant_content is None:
        return f'{Color.err}Could not find {R}"{query}"{Color.err} in Farlex Idioms'

    farlex = Dictionary(name='farlex')

    last_phrase = ''
    content_blocks = relevant_content.find_all('div', class_=('ds-single', 'ds-list'), recursive=False)
    farlex.add('HEADER', 'Farlex Idioms')
    for content_block in content_blocks:
        # Gather idiom phrases
        idiom_phrase = content_block.find_previous_sibling('h2').text.strip()
        if last_phrase != idiom_phrase:
            last_phrase = idiom_phrase
            farlex.add('PHRASE', idiom_phrase, '')  # no phonetic spelling

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
            examples = '<br>'.join('‘' + e.text.strip() + '’' for e in found_examples)
        else:
            examples = ''

        farlex.add('DEF', definition, examples, '')
        farlex.add('LABEL', '', '')

    return farlex
