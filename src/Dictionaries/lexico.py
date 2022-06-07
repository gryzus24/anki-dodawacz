from __future__ import annotations

from typing import Any

from src.Dictionaries.dictionary_base import Dictionary
from src.Dictionaries.utils import request_soup
from src.colors import Color, R


def get_phonetic_spelling(block_: Any) -> str:
    pronunciation_block = block_.find('span', class_='phoneticspelling')
    if pronunciation_block is not None:
        return pronunciation_block.text.strip()

    pronunciation_block = block_.next_sibling.find('div', class_='pron')
    if pronunciation_block is None:
        return ''

    pspelling = pronunciation_block.find_all('span', class_='phoneticspelling', recursive=False)
    if pspelling:
        return ' '.join([x.text.strip() for x in pspelling])
    return ''


def get_def(block_: Any, *, recursive: bool = True) -> str:
    d = block_.find('span', class_='ind one-click-content', recursive=recursive)
    if d is None:
        return block_.find('div', class_='crossReference').text
    return d.text


def get_exsen(block_: Any) -> str:
    e = block_.find('div', class_='ex')
    return '' if e is None else e.text


def get_label(block_: Any) -> str:
    gn = block_.find('span', class_='grammatical_note')
    if gn is None:
        return ''
    return gn.text.strip()\
        .replace('with object', 'tr.')\
        .replace('no object', 'intr.')


#
# Lexico
##
_previous_query = None

def ask_lexico(query: str) -> Dictionary | None:
    def add_def(
            definition_: Any, example_: str = '', label_: str = '', deftype: str = 'DEF'
    ) -> None:
        # little cleanup to prevent random newlines inside of examples
        # as is the case with "suspicion"
        example_ = example_[1:-1].strip()
        if example_:
            example_ = f"‘{example_}’"
        lexico.add(deftype, definition_.strip(), example_, label_)

    global _previous_query

    query = query.strip(' ?/.#')
    if not query:
        print(f'{Color.err}Invalid query')
        return None

    soup = request_soup('https://www.lexico.com/definition/' + query)
    if soup is None:
        return None

    main_div = soup.find('div', class_='entryWrapper')
    if main_div is None:  # lexico probably denied access
        import time
        print(f'{Color.err}Lexico could not handle this many requests...\n'
              f'Try again in 1-5 minutes')
        time.sleep(2.5)
        raise SystemExit(1)

    page_check = main_div.find('div', class_='breadcrumbs layout', recursive=False)
    if page_check.get_text(strip=True) == 'HomeEnglish':
        new_query_tag = main_div.find('a', class_='no-transition')
        if new_query_tag is None:
            print(f'{Color.err}Could not find {R}"{query}"{Color.err} in Lexico')
            return None
        else:
            _previous_query = query  # global
            _, _, revive = new_query_tag.get('href').rpartition('/')
            return ask_lexico(revive)

    lexico = Dictionary(name='lexico')

    etym = ''
    before_phrase = True
    for block in page_check.find_next_siblings():
        block_id = block.get('id')
        if block_id is not None:  # header
            # Gather phrases
            phrase_ = block.find('span', class_='hw')
            phrase_ = phrase_.find(recursive=False, text=True)

            if before_phrase:
                before_phrase = False
                lexico.add('HEADER', 'Lexico')
                if _previous_query is not None and _previous_query != query:
                    lexico.add('NOTE', 'Showing results for:')
                    _previous_query = None  # global
            else:
                lexico.add('HEADER', '')

            lexico.add('PHRASE', phrase_, get_phonetic_spelling(block))

            # Gather etymologies
            # Etymologies are bound to more than one block so it's better to search
            # for them from within a header block and print them at the end
            next_sib = block.next_sibling
            while True:
                if next_sib is None or next_sib.get('class')[0] == 'entryHead':
                    etym = ''
                    break
                elif next_sib.get('class')[0] == 'etymology':
                    while next_sib is not None and next_sib.h3.text != 'Origin':  # until "Origin" header is found
                        next_sib = next_sib.next_sibling

                    # next_sib can be None if the last entry_block is
                    # an etymology div that has no Origin header  e.g. "ad -l"
                    if next_sib is not None:
                        t = next_sib.find('div', class_='senseInnerWrapper', recursive=False)
                        etym = '[' + t.text.strip() + ']'
                    break
                next_sib = next_sib.next_sibling

        elif block.get('class')[0] == 'gramb':
            pos_label = block.find('span', class_='pos').text.strip()
            if pos_label:
                trans_note = block.find('span', class_='transitivity').text.strip()
                if trans_note == '[with object]':
                    lexico.add('LABEL', 'tr. ' + pos_label, '')
                elif trans_note == '[no object]':
                    lexico.add('LABEL', 'intr. ' + pos_label, '')
                else:
                    lexico.add('LABEL', pos_label, trans_note)

            semb = block.find('ul', class_='semb', recursive=False)
            if semb is None:
                semb = block.find('div', class_='empty_sense', recursive=False)
                if not semb.text.strip():
                    _def = block.find('div', class_='variant', recursive=False)
                    add_def(_def.text)
                else:
                    _def = semb.find('p', class_='derivative_of', recursive=False)
                    if _def is not None:
                        add_def(_def.text, get_exsen(semb))
                    else:
                        _def = semb.find('div', class_='crossReference', recursive=False)
                        if _def is not None:
                            add_def(_def.text, get_exsen(semb))
                        else:  # boot
                            _def = semb.find('div', class_='exg', recursive=False)
                            add_def('Definition is missing! *_*', _def.text)
            else:
                for dlist in semb.find_all('li', recursive=False):
                    add_def(
                        get_def(dlist),
                        get_exsen(dlist),
                        get_label(dlist)
                    )
                    subdef_semb = dlist.find('ol', class_='subSenses')
                    if subdef_semb is not None:
                        for sdlist in subdef_semb.find_all('li', recursive=False):
                            add_def(
                                get_def(sdlist, recursive=False),
                                get_exsen(sdlist),
                                get_label(sdlist),
                                'SUBDEF'
                            )

            # Gather audio urls
            previous_blocks = block.find_previous_siblings()[:-1]  # without the breadcrumbs
            current_header_block = previous_blocks[0]
            if current_header_block.get('id') is None:
                for prev in previous_blocks[1:]:
                    if prev.get('id') is not None:
                        current_header_block = prev
                        break

            header_audio = current_header_block.find('audio')
            if header_audio is not None:
                lexico.add('AUDIO', header_audio.get('src'))
            else:
                gramb_audio = semb.next_sibling
                if gramb_audio is not None:
                    gram_urls = gramb_audio.find_all('audio')
                    if gram_urls:
                        lexico.add('AUDIO', gram_urls[-1]['src'])

        elif block['class'][0] == 'etymology' and block.h3.text == 'Origin' and etym:
            lexico.add('ETYM', etym)

    return lexico
