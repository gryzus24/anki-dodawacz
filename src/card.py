from __future__ import annotations

import os
from typing import TYPE_CHECKING

import src.anki as anki
from src.Dictionaries.dictionary_base import DictionaryError
from src.Dictionaries.diki import diki_audio
from src.Dictionaries.util import http
from src.data import config

if TYPE_CHECKING:
    from src.Dictionaries.dictionary_base import DictionarySelection
    from src.Curses.proto import StatusInterface

CARD_FIELDS_AVAILABLE = ('DEF', 'SYN', 'PHRASE', 'EXSEN', 'POS', 'ETYM', 'AUDIO')

PREPOSITIONS = {
    'beyond', 'of', 'outside', 'upon', 'with', 'within',
    'behind', 'from', 'like', 'opposite', 'to', 'under',
    'after', 'against', 'around', 'near', 'over', 'via',
    'among', 'except', 'for', 'out', 'since', 'through',
    'about', 'along', 'beneath', 'underneath', 'unlike',
    'below', 'into', 'on', 'onto', 'past', 'than', 'up',
    'across', 'by', 'despite', 'inside', 'off', 'round',
    'at', 'beside', 'between', 'in', 'towards', 'until',
    'above', 'as', 'before', 'down', 'during', 'without'
}


def save_audio(url: str) -> str:
    audio_bytes = http.urlopen('GET', url).data  # type: ignore[no-untyped-call]

    media_path = os.path.expanduser(config['mediapath'])
    _, _, filename = url.rpartition('/')

    try:
        with open(os.path.join(media_path, filename), 'wb') as f:
            f.write(audio_bytes)
    except Exception as e:
        raise anki.AnkiError(str(e))

    return f'[sound:{filename}]'


def case_replace(target: str, a: str, b: str) -> str:
    return target.replace(a, b).replace(a.capitalize(), b).replace(a.upper(), b.upper())


def hide(
        target: str,
        phrase_to_replace: str,
        mask: str = '...',
        *, hide_prepositions: bool = False,
) -> str:
    do_not_replace = {
        'the', 'and', 'a', 'is', 'an', 'it',
        'or', 'be', 'do', 'does', 'not', 'if', 'he'
    }
    words_to_replace = set(phrase_to_replace.lower().split()) - do_not_replace
    if not hide_prepositions:
        words_to_replace -= PREPOSITIONS

    for word in words_to_replace:
        target = case_replace(target, word, mask)
        if word.endswith('e'):
            target = case_replace(target, f'{word[:-1]}ing', f'{mask}ing')
            if word.endswith('ie'):
                target = case_replace(target, f'{word[:-2]}ying', f'{mask}ying')
        elif word.endswith('y'):
            target = case_replace(target, f'{word[:-1]}ies', f'{mask}ies')
            target = case_replace(target, f'{word[:-1]}ied', f'{mask}ied')

    return target


def format_definitions(definition_string: str) -> str:
    styles = (
        ('', ''),
        ('<span style="opacity: .6;">', '</span>'),
        ('<small style="opacity: .4;">', '</small>'),
        ('<small style="opacity: .2;"><sub>', '</sub></small>')
    )
    formatted = []
    style_no = len(styles)
    for i, item in enumerate(definition_string.split('<br>'), 1):
        style_i = style_no - 1 if i > style_no else i - 1
        prefix, suffix = styles[style_i]

        prefix += f'<small style="color: #4EAA72;">{i}.</small>  '
        formatted.append(prefix + item + suffix)

    return '<br>'.join(formatted)


def card_from_selection(selection: DictionarySelection) -> tuple[dict[str, str], str]:
    card = {k: '' for k in CARD_FIELDS_AVAILABLE}

    audio, content, etym, phrase, pos = selection
    if audio is not None:
        if audio[1]:
            audio_url = audio[1]
        else:
            audio_url = ''
    else:
        audio_url = ''

    definitions, example_sentences, synonyms = [], [], []
    for entry in content:
        op = entry[0]
        if 'DEF' in op:
            _, _def, _exsen, _label = entry
            if _label:
                definitions.append(f'{{{_label}}} {_def}')
            else:
                definitions.append(_def)
            if _exsen:
                example_sentences.append(_exsen)
        elif op == 'SYN':
            synonyms.append(entry[2] + ' ' + entry[1])

    card['DEF'] = '<br>'.join(definitions)
    if config['exsen']:
        card['EXSEN'] = '<br>'.join(example_sentences)
    card['SYN'] = '<br>'.join(synonyms)

    if etym is not None and config['etym']:
        card['ETYM'] = etym[1]
    if phrase is not None:
        card['PHRASE'] = phrase[1]
    if pos is not None and config['pos']:
        card['POS'] = '<br>'.join(
            x.replace('|', '  ') for x in pos[1:]
        ).strip()

    return card, audio_url


def create_and_add_card(implementor: StatusInterface, selections: list[DictionarySelection]) -> None:
    for selection in selections:
        card, audio_url = card_from_selection(selection)

        phrase = card['PHRASE']

        if not audio_url:
            try:
                audio_url = diki_audio(phrase)
            except DictionaryError as e:
                implementor.error(str(e))
                implementor.attention(f'No audio available for {phrase!r}')

        if audio_url:
            try:
                card['AUDIO'] = save_audio(audio_url)
            except anki.AnkiError as e:
                implementor.error('Saving audio failed:', str(e))
                card['AUDIO'] = ''
        else:
            card['AUDIO'] = ''

        if config['hidedef']:
            card['DEF'] = hide(
                card['DEF'], phrase, config['hides'],
                hide_prepositions=config['hidepreps']
            )
        if config['hideexsen']:
            card['EXSEN'] = hide(
                card['EXSEN'], phrase, config['hides'],
                hide_prepositions=config['hidepreps']
            )
        if config['hidesyn']:
            card['SYN'] = hide(
                card['SYN'], phrase, config['hides'],
                hide_prepositions=config['hidepreps']
            )

        card = {k: v.replace("'", "&#39;").replace('"', '&quot;') for k, v in card.items()}

        if config['formatdefs']:
            card['DEF'] = format_definitions(card['DEF'])

        try:
            anki.add_card(card)
        except anki.AnkiError as e:
            implementor.error('Adding card failed:', str(e))
        else:
            implementor.success('Card added successfully:', 'press "b" for details')
